import logging
import os
import re
import smtplib
import ssl
import time
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr
from html import escape
from pathlib import Path

log = logging.getLogger("amigo_secreto.email")

SUBJECT = "Você tirou alguém no Amigo Secreto 🎁"


class EmailError(Exception):
    """Falha ao enviar um e-mail. A mensagem nunca contém o conteúdo do sorteio."""


def render_text(recipient: str, friend: str) -> str:
    return (
        f"Oi, {recipient}!\n\n"
        f"Seu amigo secreto é:\n\n{friend}\n\n"
        "Agora é segredo! 🤫\n\nBoa sorte com o presente 🎁\n"
    )


def render_html(recipient: str, friend: str) -> str:
    r, f = escape(recipient), escape(friend)
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#faf7f0;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#faf7f0;">
<tr><td align="center" style="padding:32px 16px;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
  style="max-width:480px;background:#ffffff;border-radius:20px;border:1px solid #ece6d8;">
<tr><td style="padding:36px 32px;font-family:'DM Sans',Helvetica,Arial,sans-serif;color:#2b3a33;">
  <p style="margin:0 0 6px;font-size:13px;letter-spacing:.08em;text-transform:uppercase;color:#7c9a88;">Amigo Secreto</p>
  <h1 style="margin:0 0 24px;font-size:24px;line-height:1.3;font-weight:700;">Oi, {r}!</h1>
  <p style="margin:0 0 12px;font-size:16px;line-height:1.5;">Seu amigo secreto é:</p>
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
    <td align="center" style="background:#f6dfe0;border-radius:14px;padding:22px 16px;">
      <span style="font-size:26px;font-weight:700;color:#2b3a33;">{f}</span>
    </td></tr></table>
  <p style="margin:24px 0 4px;font-size:16px;line-height:1.5;">Agora é segredo! 🤫</p>
  <p style="margin:0;font-size:16px;line-height:1.5;">Boa sorte com o presente 🎁</p>
</td></tr></table>
</td></tr></table>
</body></html>"""


def build_message(sender: str, recipient_name: str, recipient_email: str, friend: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = SUBJECT
    msg["From"] = sender
    msg["To"] = formataddr((recipient_name, recipient_email))
    msg.set_content(render_text(recipient_name, friend))
    msg.add_alternative(render_html(recipient_name, friend), subtype="html")
    return msg


@dataclass(frozen=True)
class SmtpSettings:
    host: str
    port: int
    security: str
    user: str
    password: str
    mail_from: str
    from_name: str

    @classmethod
    def from_env(cls) -> "SmtpSettings":
        missing = [k for k in ("SMTP_HOST", "MAIL_FROM") if not os.getenv(k)]
        if missing:
            raise RuntimeError(f"Modo produção exige configurar: {', '.join(missing)}")
        security = os.getenv("SMTP_SECURITY", "starttls").lower()
        if security not in ("starttls", "ssl", "none"):
            raise RuntimeError("SMTP_SECURITY deve ser starttls, ssl ou none.")
        default_port = {"ssl": 465, "starttls": 587, "none": 25}[security]
        return cls(
            host=os.environ["SMTP_HOST"],
            port=int(os.getenv("SMTP_PORT", default_port)),
            security=security,
            user=os.getenv("SMTP_USER", ""),
            password=os.getenv("SMTP_PASSWORD", ""),
            mail_from=os.environ["MAIL_FROM"],
            from_name=os.getenv("MAIL_FROM_NAME", "Amigo Secreto"),
        )


class SmtpMailer:
    """Envio real. Só devolve sucesso depois que o servidor SMTP aceitar a mensagem."""

    dev_mode = False

    def __init__(self, settings: SmtpSettings):
        self.s = settings

    def send(self, recipient_name: str, recipient_email: str, friend: str) -> None:
        s = self.s
        msg = build_message(formataddr((s.from_name, s.mail_from)), recipient_name, recipient_email, friend)
        try:
            if s.security == "ssl":
                server = smtplib.SMTP_SSL(s.host, s.port, timeout=20, context=ssl.create_default_context())
            else:
                server = smtplib.SMTP(s.host, s.port, timeout=20)
            with server:
                if s.security == "starttls":
                    server.starttls(context=ssl.create_default_context())
                if s.user:
                    server.login(s.user, s.password)
                refused = server.send_message(msg)
                if refused:
                    raise EmailError("O servidor recusou o destinatário.")
        except EmailError:
            raise
        except (smtplib.SMTPException, OSError) as exc:
            # Só o tipo do erro é registrado: nada de endereços ou conteúdo.
            log.warning("Falha SMTP (%s)", type(exc).__name__)
            raise EmailError("Falha ao enviar o e-mail.") from exc


class DevMailer:
    """Não envia nada. Grava o HTML em uma pasta local para pré-visualização."""

    dev_mode = True

    def __init__(self, outbox: Path | None):
        self.outbox = outbox
        if outbox:
            outbox.mkdir(parents=True, exist_ok=True)

    def send(self, recipient_name: str, recipient_email: str, friend: str) -> None:
        log.info("[DEV] e-mail simulado (nada foi enviado)")
        if self.outbox:
            slug = re.sub(r"[^a-z0-9]+", "_", recipient_email.lower())
            path = self.outbox / f"{int(time.time() * 1000)}_{slug}.html"
            path.write_text(render_html(recipient_name, friend), encoding="utf-8")


def mailer_from_env():
    if os.getenv("APP_MODE", "dev").lower() == "production":
        return SmtpMailer(SmtpSettings.from_env())
    outbox = os.getenv("DEV_OUTBOX_DIR", "dev_outbox")
    return DevMailer(Path(outbox) if outbox else None)
