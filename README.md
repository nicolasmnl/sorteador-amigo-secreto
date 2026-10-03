# Amigo Secreto

Aplicação pequena para organizar um amigo secreto: adicione participantes, sorteie e cada pessoa recebe o resultado **individualmente por e-mail**. O resultado nunca aparece na tela, na API nem nos logs.

- **Backend:** Python 3.12+, FastAPI, Pydantic, `smtplib`
- **Frontend:** React + Vite + TypeScript, CSS simples
- **Armazenamento:** nenhum banco. O sorteio fica só em memória e é apagado assim que todos os e-mails são enviados.

```
backend/   app/{main,schemas,draw,email_service}.py · tests/ · .env.example
frontend/  src/{App.tsx, components/, styles.css}
```

## Requisitos

- Python 3.12+
- Node.js 20.19+ (ou 22.12+)

## Instalação

```bash
# backend
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env

# frontend
cd ../frontend
npm install
```

## Modo de desenvolvimento (sem e-mails reais)

Com `APP_MODE=dev` (padrão do `.env.example`) **nenhum e-mail é enviado**. As mensagens são gravadas como HTML em `backend/dev_outbox/` para você abrir no navegador, e a tela final avisa que é modo de desenvolvimento.

```bash
# terminal 1
cd backend && uvicorn app.main:app --reload --env-file .env

# terminal 2
cd frontend && npm run dev     # http://localhost:5173 (proxy de /api para :8000)
```

> A pasta `dev_outbox/` contém os resultados do sorteio em texto claro: é só para desenvolvimento.

## Produção (e-mails reais)

1. No `.env`, defina `APP_MODE=production` e preencha o SMTP (`SMTP_HOST`, `SMTP_PORT`, `SMTP_SECURITY`, `SMTP_USER`, `SMTP_PASSWORD`, `MAIL_FROM`). O servidor **não inicia** se faltar configuração, e nada é simulado: um envio só conta como bem-sucedido depois que o servidor SMTP aceita a mensagem.
2. Compile o frontend e suba só o backend, que serve `frontend/dist` na mesma origem:

```bash
cd frontend && npm run build
cd ../backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --env-file .env
```

Qualquer provedor com SMTP funciona (Resend, SendGrid, Mailgun, Gmail com senha de app etc.). Credenciais ficam apenas em variáveis de ambiente.

## Testes

```bash
cd backend && pytest
```

Cobrem o sorteio (permutação válida, ninguém tira a si mesmo, todos os derangements ocorrem), a validação, o envio individual, falha parcial + reenvio, idempotência e o limite de requisições.

## Como funciona

**Sorteio** ([draw.py](backend/app/draw.py)): `random.SystemRandom` embaralha a lista até não haver ponto fixo (derangement). A chance de acerto por tentativa é ~1/e, então bastam ~2,7 tentativas em média, e o resultado é uniforme entre todas as possibilidades válidas.

**Segurança e confiabilidade**
- Validação repetida no backend (nome, e-mail válido, sem duplicados ignorando maiúsculas, 3 a 100 participantes).
- A API responde só com `status`, `total`, `sent` e `failed`. Não há endpoint para consultar quem tirou quem, e os logs registram apenas contagens.
- Cada participante recebe um e-mail próprio (sem CC); nomes são escapados no HTML.
- O frontend gera um `event_id` por sorteio. Duplo clique ou requisições simultâneas com o mesmo id esperam por um lock e reutilizam o mesmo sorteio.
- Se algum e-mail falhar, o mapeamento dos pendentes continua na memória e `POST /api/draws/{id}/resend` reenvia só o que faltou, **sem novo sorteio**. Ao concluir, o mapeamento é apagado; sorteios com falha expiram após `EVENT_TTL_MINUTES`.
- Limite de requisições por IP (`RATE_LIMIT_PER_MINUTE`). Atrás de proxy reverso, configure o uvicorn com `--proxy-headers --forwarded-allow-ips=<ip do proxy>` para que o IP real seja usado.

**Limitação conhecida:** como não há banco, reiniciar o servidor com um envio parcialmente falho perde os pendentes (será preciso criar um novo sorteio). Se precisar sobreviver a reinícios, a próxima etapa natural é guardar os pendentes em SQLite e apagá-los após o envio. O limitador e o armazenamento são em memória, então rode **um único processo** (sem `--workers` > 1).
