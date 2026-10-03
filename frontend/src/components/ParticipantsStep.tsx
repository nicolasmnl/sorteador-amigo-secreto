import { useState } from "react";
import type { Person } from "../types";
import { validate } from "../validation";
import Button from "./Button";

interface Props {
  people: Person[];
  onChange: (people: Person[]) => void;
  onContinue: () => void;
}

export default function ParticipantsStep({ people, onChange, onContinue }: Props) {
  const [submitted, setSubmitted] = useState(false);
  const [touched, setTouched] = useState<Set<string>>(new Set());
  const { errors, form } = validate(people);

  const update = (id: string, patch: Partial<Person>) =>
    onChange(people.map((p) => (p.id === id ? { ...p, ...patch } : p)));
  const touch = (id: string, field: "name" | "email") =>
    setTouched((t) => new Set(t).add(`${id}:${field}`));
  const show = (id: string, field: "name" | "email") =>
    submitted || touched.has(`${id}:${field}`) ? errors[id]?.[field] : undefined;

  const add = () => onChange([...people, { id: crypto.randomUUID(), name: "", email: "" }]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
    if (validate(people).valid) onContinue();
  };

  return (
    <form className="step" onSubmit={submit} noValidate>
      <h2>Quem vai participar?</h2>
      <p className="muted">Cada pessoa receberá o resultado no próprio e-mail.</p>

      <ul className="people">
        {people.map((p, i) => (
          <li key={p.id} className="person">
            <span className="index">{i + 1}</span>
            <div className="fields">
              <div className="field">
                <input
                  aria-label={`Nome completo do participante ${i + 1}`}
                  placeholder="Nome completo"
                  autoComplete="off"
                  maxLength={100}
                  value={p.name}
                  aria-invalid={!!show(p.id, "name")}
                  onChange={(e) => update(p.id, { name: e.target.value })}
                  onBlur={() => touch(p.id, "name")}
                />
                {show(p.id, "name") && <small className="error">{show(p.id, "name")}</small>}
              </div>
              <div className="field">
                <input
                  type="email"
                  inputMode="email"
                  aria-label={`E-mail do participante ${i + 1}`}
                  placeholder="E-mail"
                  autoComplete="off"
                  value={p.email}
                  aria-invalid={!!show(p.id, "email")}
                  onChange={(e) => update(p.id, { email: e.target.value })}
                  onBlur={() => touch(p.id, "email")}
                />
                {show(p.id, "email") && <small className="error">{show(p.id, "email")}</small>}
              </div>
            </div>
            <button
              type="button"
              className="remove"
              aria-label={`Remover participante ${i + 1}`}
              onClick={() => onChange(people.filter((x) => x.id !== p.id))}
            >
              ×
            </button>
          </li>
        ))}
      </ul>

      <button type="button" className="add" onClick={add}>
        + Adicionar participante
      </button>
      {submitted && form && <p className="error form-error" role="alert">{form}</p>}

      <div className="actions">
        <Button type="submit">Continuar</Button>
      </div>
    </form>
  );
}
