import logging
import os
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .draw import draw_pairs
from .email_service import EmailError, mailer_from_env
from .schemas import DrawRequest, DrawStatus, Participant

log = logging.getLogger("amigo_secreto")


@dataclass
class Event:
    lock: threading.Lock = field(default_factory=threading.Lock)
    created: float = field(default_factory=time.monotonic)
    drawn: bool = False
    total: int = 0
    # (quem recebe o e-mail, nome do amigo secreto). Vazio quando tudo foi enviado.
    pending: list[tuple[Participant, str]] = field(default_factory=list)


class EventStore:
    """Sorteios em memória. Só os pendentes guardam o mapeamento; ao concluir, ele é apagado."""

    def __init__(self, ttl_seconds: float):
        self.ttl = ttl_seconds
        self._events: dict[str, Event] = {}
        self._lock = threading.Lock()

    def get_or_create(self, event_id: str) -> Event:
        with self._lock:
            self._purge()
            return self._events.setdefault(event_id, Event())

    def get(self, event_id: str) -> Event | None:
        with self._lock:
            self._purge()
            return self._events.get(event_id)

    def _purge(self) -> None:
        now = time.monotonic()
        for key in [k for k, e in self._events.items() if now - e.created > self.ttl]:
            del self._events[key]


class RateLimiter:
    def __init__(self, limit: int, window: float = 60.0):
        self.limit, self.window = limit, window
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                raise HTTPException(429, "Muitas tentativas. Aguarde um instante e tente de novo.")
            hits.append(now)


mailer = mailer_from_env()
store = EventStore(float(os.getenv("EVENT_TTL_MINUTES", "120")) * 60)
limiter = RateLimiter(int(os.getenv("RATE_LIMIT_PER_MINUTE", "10")))

app = FastAPI(title="Amigo Secreto", docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


def deliver(event_id: str, event: Event) -> DrawStatus:
    """Envia os e-mails pendentes (chamar com event.lock). Sem resultados na resposta."""
    still_pending = []
    for person, friend in event.pending:
        try:
            mailer.send(person.name, person.email, friend)
        except EmailError:
            still_pending.append((person, friend))
    event.pending = still_pending
    failed = len(still_pending)
    log.info("Envio: %d/%d concluídos", event.total - failed, event.total)
    return DrawStatus(
        event_id=event_id,
        status="completed" if not failed else "partial",
        total=event.total,
        sent=event.total - failed,
        failed=failed,
        dev_mode=mailer.dev_mode,
    )


def client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


# Rotas síncronas: o FastAPI as executa em threads, então o SMTP bloqueante não trava o servidor.
@app.post("/api/draws", response_model=DrawStatus)
def create_draw(body: DrawRequest, request: Request) -> DrawStatus:
    limiter.check(client_key(request))
    event = store.get_or_create(body.event_id)
    with event.lock:  # requisições simultâneas com o mesmo id esperam e reutilizam o mesmo sorteio
        if not event.drawn:
            pairs = draw_pairs(body.participants)
            event.pending = [(giver, receiver.name) for giver, receiver in pairs]
            event.total = len(pairs)
            event.drawn = True
        return deliver(body.event_id, event)


@app.post("/api/draws/{event_id}/resend", response_model=DrawStatus)
def resend(event_id: str, request: Request) -> DrawStatus:
    limiter.check(client_key(request))
    event = store.get(event_id)
    if event is None or not event.drawn:
        raise HTTPException(404, "Este sorteio expirou. Será preciso criar um novo.")
    with event.lock:
        return deliver(event_id, event)


# Em produção, serve o frontend compilado (frontend/dist) na mesma origem.
_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _dist.is_dir():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")
