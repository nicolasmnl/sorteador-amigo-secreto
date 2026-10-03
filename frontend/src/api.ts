import type { DrawStatus, Person } from "./types";

async function request(url: string, body?: unknown): Promise<DrawStatus> {
  let res: Response;
  try {
    res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Não foi possível conectar ao servidor. Verifique sua conexão.");
  }
  if (res.ok) return res.json();
  let message = "Algo deu errado. Tente novamente.";
  if (res.status === 422) message = "Confira os nomes e e-mails e tente de novo.";
  else {
    try {
      const data = await res.json();
      if (typeof data.detail === "string") message = data.detail;
    } catch {
      /* mantém a mensagem padrão */
    }
  }
  throw new Error(message);
}

export const createDraw = (eventId: string, people: Person[]) =>
  request("/api/draws", {
    event_id: eventId,
    participants: people.map((p) => ({ name: p.name.trim(), email: p.email.trim() })),
  });

export const resendDraw = (eventId: string) => request(`/api/draws/${eventId}/resend`);
