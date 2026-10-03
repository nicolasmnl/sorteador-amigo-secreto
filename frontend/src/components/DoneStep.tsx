import type { DrawStatus } from "../types";
import Button from "./Button";

interface Props {
  result: DrawStatus;
  resending: boolean;
  error: string | null;
  onResend: () => void;
  onRestart: () => void;
}

export default function DoneStep({ result, resending, error, onResend, onRestart }: Props) {
  const ok = result.status === "completed";
  return (
    <section className="step center">
      <h2>Sorteio realizado! 🎉</h2>
      {ok ? (
        <p className="lead">
          {result.dev_mode
            ? "Modo de desenvolvimento: o sorteio foi feito, mas nenhum e-mail real foi enviado."
            : "Pronto! Todos receberam seu amigo secreto por e-mail."}
        </p>
      ) : (
        <>
          <p className="lead">
            O envio não foi concluído para todos: {result.failed} de {result.total} e-mails
            ainda não saíram.
          </p>
          <p className="muted">
            O sorteio já foi feito e não muda. Ao tentar de novo, só reenviamos o que faltou.
          </p>
          {error && <p className="error form-error" role="alert">{error}</p>}
        </>
      )}
      <div className="actions stack">
        {!ok && (
          <Button onClick={onResend} loading={resending}>
            {resending ? "Reenviando…" : "Tentar reenviar"}
          </Button>
        )}
        <Button variant="ghost" onClick={onRestart} disabled={resending}>
          Novo sorteio
        </Button>
      </div>
    </section>
  );
}
