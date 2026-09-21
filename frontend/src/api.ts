const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type Rol = "municipio" | "coordinador" | "ong" | "auditor";

export type Usuario = {
  id: number;
  username: string;
  nombre: string;
  rol: Rol;
  organizacion: string | null;
};

function authHeaders(): HeadersInit {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  const auth = authHeaders();
  Object.entries(auth).forEach(([k, v]) => headers.set(k, v));

  const res = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || res.statusText);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export async function login(username: string, password: string): Promise<string> {
  const body = new URLSearchParams({ username, password });
  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) throw new Error("Login falló");
  const data = (await res.json()) as { access_token: string };
  localStorage.setItem("token", data.access_token);
  return data.access_token;
}

export function logout() {
  localStorage.removeItem("token");
}

export const api = {
  me: () => request<Usuario>("/api/auth/me"),
  listEmergencias: () => request<Emergencia[]>("/api/emergencias"),
  createEmergencia: (payload: EmergenciaCreate) =>
    request<Emergencia>("/api/emergencias", { method: "POST", body: JSON.stringify(payload) }),
  listLotes: (id: number) => request<Lote[]>(`/api/emergencias/${id}/lotes`),
  createLote: (id: number, payload: LoteCreate) =>
    request<Lote>(`/api/emergencias/${id}/lotes`, { method: "POST", body: JSON.stringify(payload) }),
  publicar: (id: number, payload: { ventana_ofertas_iso: string; plazo_adjudicacion_iso: string }) =>
    request<Emergencia>(`/api/emergencias/${id}/publicar`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  createOferta: (id: number, payload: OfertaCreate) =>
    request<Oferta>(`/api/emergencias/${id}/ofertas`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

export type Emergencia = {
  id: number;
  municipio_id: number;
  tipo_desastre: string;
  nivel_gravedad: string;
  zona_afectada: string;
  descripcion: string;
  estado: string;
  bonita_case_id: string | null;
  ventana_ofertas_iso: string | null;
  plazo_adjudicacion_iso: string | null;
  created_at: string;
};

export type EmergenciaCreate = {
  tipo_desastre: string;
  nivel_gravedad: string;
  zona_afectada: string;
  descripcion: string;
  ventana_ofertas_iso?: string;
};

export type Lote = {
  id: number;
  emergencia_id: number;
  recurso: string;
  cantidad: number;
  tipo: "principal" | "apoyo";
  publicado: boolean;
  created_at: string;
};

export type LoteCreate = {
  recurso: string;
  cantidad: number;
  tipo: "principal" | "apoyo";
};

export type Oferta = {
  id: number;
  emergencia_id: number;
  lote_id: number;
  ong_id: number;
  detalle_recursos: string;
  cantidad_ofrecida: number;
  version: number;
};

export type OfertaCreate = {
  lote_id: number;
  detalle_recursos: string;
  cantidad_ofrecida: number;
};
