export interface Person {
  id: string;
  name: string;
  email: string;
}

export interface DrawStatus {
  event_id: string;
  status: "completed" | "partial";
  total: number;
  sent: number;
  failed: number;
  dev_mode: boolean;
}

export type PersonErrors = { name?: string; email?: string };
