import { useState } from "react";
import { createDraw, resendDraw } from "./api";
import ConfirmStep from "./components/ConfirmStep";
import DoneStep from "./components/DoneStep";
import Intro from "./components/Intro";
import ParticipantsStep from "./components/ParticipantsStep";
import Progress from "./components/Progress";
import type { DrawStatus, Person } from "./types";

type View = "intro" | "participants" | "confirm" | "done";

const blank = (): Person => ({ id: crypto.randomUUID(), name: "", email: "" });
const initialPeople = () => [blank(), blank(), blank()];

export default function App() {
  const [view, setView] = useState<View>("intro");
  const [people, setPeople] = useState<Person[]>(initialPeople);
  const [eventId, setEventId] = useState("");
  const [result, setResult] = useState<DrawStatus | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async (action: () => Promise<DrawStatus>, next?: View) => {
    if (busy) return; // impede cliques duplicados
    setBusy(true);
    setError(null);
    try {
      setResult(await action());
      if (next) setView(next);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Algo deu errado.");
    } finally {
      setBusy(false);
    }
  };

  const toConfirm = () => {
    setEventId(crypto.randomUUID()); // identifica este sorteio: reenviar a mesma requisição nunca sorteia de novo
    setError(null);
    setView("confirm");
  };

  const restart = () => {
    setPeople(initialPeople());
    setResult(null);
    setError(null);
    setView("participants");
  };

  const step = view === "participants" ? 0 : view === "confirm" ? 1 : 2;

  return (
    <main className="app">
      {view !== "intro" && <Progress step={step} />}
      <div className="view" key={view}>
        {view === "intro" && <Intro onStart={() => setView("participants")} />}
        {view === "participants" && (
          <ParticipantsStep people={people} onChange={setPeople} onContinue={toConfirm} />
        )}
        {view === "confirm" && (
          <ConfirmStep
            count={people.length}
            loading={busy}
            error={error}
            onDraw={() => run(() => createDraw(eventId, people), "done")}
            onBack={() => setView("participants")}
          />
        )}
        {view === "done" && result && (
          <DoneStep
            result={result}
            resending={busy}
            error={error}
            onResend={() => run(() => resendDraw(result.event_id))}
            onRestart={restart}
          />
        )}
      </div>
    </main>
  );
}
