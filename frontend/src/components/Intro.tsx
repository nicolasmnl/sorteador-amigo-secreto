import Button from "./Button";

export default function Intro({ onStart }: { onStart: () => void }) {
  return (
    <section className="intro">
      <span className="badge">🎁 Amigo Secreto</span>
      <h1>Amigo Secreto, sem complicação.</h1>
      <p className="lead">Adicione os participantes, faça o sorteio e deixe o resto com a gente.</p>
      <Button onClick={onStart}>Criar sorteio</Button>
    </section>
  );
}
