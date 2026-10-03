import type { Person, PersonErrors } from "./types";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

export interface Validation {
  errors: Record<string, PersonErrors>;
  form?: string;
  valid: boolean;
}

export function validate(people: Person[]): Validation {
  const errors: Record<string, PersonErrors> = {};
  const seen = new Map<string, string>();

  for (const p of people) {
    const e: PersonErrors = {};
    const email = p.email.trim().toLowerCase();
    if (!p.name.trim()) e.name = "Informe o nome.";
    if (!email) e.email = "Informe o e-mail.";
    else if (!EMAIL_RE.test(email)) e.email = "E-mail inválido.";
    else if (seen.has(email)) e.email = "Este e-mail já foi adicionado.";
    else seen.set(email, p.id);
    if (e.name || e.email) errors[p.id] = e;
  }

  const form = people.length < 3 ? "Adicione pelo menos 3 participantes." : undefined;
  return { errors, form, valid: !form && Object.keys(errors).length === 0 };
}
