import uuid

import pytest
from fastapi.testclient import TestClient

from app import main
from app.email_service import EmailError, build_message


class FakeMailer:
    dev_mode = False

    def __init__(self, fail_for=()):
        self.fail_for = set(fail_for)
        self.sent = []

    def send(self, name, email, friend):
        if email in self.fail_for:
            raise EmailError("falhou")
        self.sent.append((name, email, friend))


PEOPLE = [{"name": n, "email": f"{n.lower()}@x.com"} for n in ("Ana", "Beto", "Caio", "Duda")]


@pytest.fixture
def client(monkeypatch):
    mailer = FakeMailer()
    monkeypatch.setattr(main, "mailer", mailer)
    monkeypatch.setattr(main, "store", main.EventStore(3600))
    monkeypatch.setattr(main, "limiter", main.RateLimiter(1000))
    c = TestClient(main.app)
    c.mailer = mailer
    return c


def body(people=PEOPLE, event_id=None):
    return {"event_id": event_id or str(uuid.uuid4()), "participants": people}


def test_draw_sends_one_email_each_and_hides_results(client):
    r = client.post("/api/draws", json=body())
    assert r.status_code == 200
    assert set(r.json()) == {"event_id", "status", "total", "sent", "failed", "dev_mode"}
    assert r.json()["status"] == "completed" and r.json()["sent"] == 4
    assert len(client.mailer.sent) == 4
    assert all(name != friend for name, _, friend in client.mailer.sent)
    assert sorted(f for _, _, f in client.mailer.sent) == sorted(p["name"] for p in PEOPLE)


def test_same_event_id_does_not_draw_again(client):
    b = body()
    client.post("/api/draws", json=b)
    client.post("/api/draws", json=b)
    assert len(client.mailer.sent) == 4


def test_partial_failure_then_resend_keeps_same_draw(client):
    client.mailer.fail_for = {"beto@x.com"}
    b = body()
    r = client.post("/api/draws", json=b).json()
    assert r["status"] == "partial" and r["failed"] == 1
    first = {e: f for _, e, f in client.mailer.sent}
    assert "beto@x.com" not in first

    client.mailer.fail_for = set()
    r = client.post(f"/api/draws/{b['event_id']}/resend").json()
    assert r["status"] == "completed" and r["sent"] == 4
    assert len(client.mailer.sent) == 4  # só o que faltava foi reenviado
    # nenhum e-mail repetido e o sorteio continua válido
    final = {e: f for _, e, f in client.mailer.sent}
    assert sorted(final.values()) == sorted(p["name"] for p in PEOPLE)


def test_resend_unknown_event_404(client):
    assert client.post("/api/draws/does-not-exist-123/resend").status_code == 404


@pytest.mark.parametrize(
    "people",
    [
        PEOPLE[:2],
        PEOPLE[:2] + [{"name": "Dup", "email": "ANA@x.com"}],
        PEOPLE[:3] + [{"name": " ", "email": "z@x.com"}],
        PEOPLE[:3] + [{"name": "Zed", "email": "not-an-email"}],
    ],
)
def test_backend_validation(client, people):
    assert client.post("/api/draws", json=body(people)).status_code == 422
    assert client.mailer.sent == []


def test_rate_limit(client, monkeypatch):
    monkeypatch.setattr(main, "limiter", main.RateLimiter(2))
    codes = [client.post("/api/draws", json=body()).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_email_is_personal_and_escaped():
    msg = build_message("Amigo <a@x.com>", "Maria", "maria@x.com", "<b>João</b>")
    assert msg["To"] == "Maria <maria@x.com>"
    html = msg.get_body(("html",)).get_content()
    assert "&lt;b&gt;João&lt;/b&gt;" in html and "<b>João</b>" not in html
