import Button from "./Button";

interface Props {
  count: number;
  loading: boolean;
  error: string | null;
  onDraw: () => void;
  onBack: () => void;
}

export default function ConfirmStep({ count, loading, error, onDraw, onBack }: Props) {
  return (
    <section className="step center">
      <h2>Tudo pronto para o sorteio?</h2>
      <p className="lead">
        Você adicionou {count} participantes. Cada pessoa receberá seu amigo secreto por e-mail.
      </p>
      {error && <p className="error form-error" role="alert">{error}</p>}
      <div className="actions stack">
        <Button onClick={onDraw} loading={loading}>
          {loading ? "Sorteando…" : "Sortear agora"}
        </Button>
        <Button variant="ghost" onClick={onBack} disabled={loading}>
          Voltar e editar
        </Button>
      </div>
    </section>
  );
}
