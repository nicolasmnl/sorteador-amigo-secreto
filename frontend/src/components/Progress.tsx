const STEPS = ["Participantes", "Confirmação", "Conclusão"];

export default function Progress({ step }: { step: number }) {
  return (
    <ol className="progress" aria-label="Progresso">
      {STEPS.map((label, i) => (
        <li
          key={label}
          className={i < step ? "done" : i === step ? "current" : ""}
          aria-current={i === step ? "step" : undefined}
        >
          <span className="dot" />
          <span className="label">{label}</span>
        </li>
      ))}
    </ol>
  );
}
