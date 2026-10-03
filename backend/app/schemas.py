import re
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

MIN_PARTICIPANTS = 3
MAX_PARTICIPANTS = 100


class Participant(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        # Colapsa espaços e quebras de linha (evita injeção de cabeçalhos no e-mail).
        value = re.sub(r"\s+", " ", value).strip()
        if not value:
            raise ValueError("O nome não pode ficar vazio.")
        return value


class DrawRequest(BaseModel):
    # Gerado pelo frontend: torna o envio idempotente (duplo clique = mesmo sorteio).
    event_id: str = Field(pattern=r"^[A-Za-z0-9-]{8,64}$")
    participants: list[Participant] = Field(
        min_length=MIN_PARTICIPANTS, max_length=MAX_PARTICIPANTS
    )

    @model_validator(mode="after")
    def unique_emails(self) -> "DrawRequest":
        emails = [p.email.lower() for p in self.participants]
        if len(set(emails)) != len(emails):
            raise ValueError("Há e-mails duplicados.")
        return self


class DrawStatus(BaseModel):
    """Estado geral da operação. Nunca contém quem tirou quem."""

    event_id: str
    status: Literal["completed", "partial"]
    total: int
    sent: int
    failed: int
    dev_mode: bool
