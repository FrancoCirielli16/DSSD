import { useEffect, useState, type FormEvent } from "react";
import { api, login, logout, type Emergencia, type Lote, type Usuario } from "./api";
import "./App.css";

const DEMO = [
  "operador.municipal / bpm",
  "coordinador.regional / bpm",
  "ong.cruzroja / bpm",
];

export default function App() {
  const [user, setUser] = useState<Usuario | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [emergencias, setEmergencias] = useState<Emergencia[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [lotes, setLotes] = useState<Lote[]>([]);

  async function refresh() {
    const list = await api.listEmergencias();
    setEmergencias(list);
  }

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;
    api
      .me()
      .then(async (u) => {
        setUser(u);
        await refresh();
      })
      .catch(() => logout());
  }, []);

  useEffect(() => {
    if (!selectedId) {
      setLotes([]);
      return;
    }
    api.listLotes(selectedId).then(setLotes).catch((e) => setError(String(e)));
  }, [selectedId]);

  async function onLogin(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    const fd = new FormData(e.currentTarget);
    try {
      await login(String(fd.get("username")), String(fd.get("password")));
      const me = await api.me();
      setUser(me);
      await refresh();
    } catch (err) {
      setError(String(err));
    }
  }

  async function onCreateEmergencia(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    const fd = new FormData(e.currentTarget);
    try {
      await api.createEmergencia({
        tipo_desastre: String(fd.get("tipo_desastre")),
        nivel_gravedad: String(fd.get("nivel_gravedad")),
        zona_afectada: String(fd.get("zona_afectada")),
        descripcion: String(fd.get("descripcion")),
      });
      e.currentTarget.reset();
      await refresh();
    } catch (err) {
      setError(String(err));
    }
  }

  async function onCreateLote(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!selectedId) return;
    setError(null);
    const fd = new FormData(e.currentTarget);
    try {
      await api.createLote(selectedId, {
        recurso: String(fd.get("recurso")),
        cantidad: Number(fd.get("cantidad")),
        tipo: String(fd.get("tipo")) as "principal" | "apoyo",
      });
      e.currentTarget.reset();
      setLotes(await api.listLotes(selectedId));
    } catch (err) {
      setError(String(err));
    }
  }

  async function onPublicar() {
    if (!selectedId) return;
    setError(null);
    try {
      await api.publicar(selectedId, {
        ventana_ofertas_iso: "PT72H",
        plazo_adjudicacion_iso: "PT48H",
      });
      await refresh();
      setLotes(await api.listLotes(selectedId));
    } catch (err) {
      setError(String(err));
    }
  }

  async function onCreateOferta(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!selectedId) return;
    setError(null);
    const fd = new FormData(e.currentTarget);
    try {
      await api.createOferta(selectedId, {
        lote_id: Number(fd.get("lote_id")),
        detalle_recursos: String(fd.get("detalle_recursos")),
        cantidad_ofrecida: Number(fd.get("cantidad_ofrecida")),
      });
      e.currentTarget.reset();
    } catch (err) {
      setError(String(err));
    }
  }

  if (!user) {
    return (
      <main className="wrap">
        <h1>RescueSync</h1>
        <p className="muted">Entrega 2 — formularios iniciales</p>
        <form className="card" onSubmit={onLogin}>
          <label>
            Usuario
            <input name="username" defaultValue="operador.municipal" required />
          </label>
          <label>
            Clave
            <input name="password" type="password" defaultValue="bpm" required />
          </label>
          <button type="submit">Entrar</button>
        </form>
        <ul className="muted">
          {DEMO.map((d) => (
            <li key={d}>{d}</li>
          ))}
        </ul>
        {error && <p className="error">{error}</p>}
      </main>
    );
  }

  return (
    <main className="wrap">
      <header className="row">
        <div>
          <h1>RescueSync</h1>
          <p className="muted">
            {user.nombre} · {user.rol}
          </p>
        </div>
        <button
          type="button"
          onClick={() => {
            logout();
            setUser(null);
          }}
        >
          Salir
        </button>
      </header>

      {error && <p className="error">{error}</p>}

      {user.rol === "municipio" && (
        <section className="card">
          <h2>Alta de emergencia</h2>
          <form onSubmit={onCreateEmergencia} className="grid">
            <input name="tipo_desastre" placeholder="Tipo (inundación…)" required />
            <input name="nivel_gravedad" placeholder="Gravedad (ALTA)" required />
            <input name="zona_afectada" placeholder="Zona afectada" required />
            <textarea name="descripcion" placeholder="Descripción" required />
            <button type="submit">Registrar e instanciar Bonita</button>
          </form>
        </section>
      )}

      {user.rol === "coordinador" && selectedId && (
        <section className="card">
          <h2>Lotes — emergencia #{selectedId}</h2>
          <form onSubmit={onCreateLote} className="grid">
            <input name="recurso" placeholder="Recurso (paramédicos…)" required />
            <input name="cantidad" type="number" min={1} defaultValue={5} required />
            <select name="tipo" defaultValue="principal">
              <option value="principal">principal</option>
              <option value="apoyo">apoyo</option>
            </select>
            <button type="submit">Agregar lote</button>
          </form>
          <button type="button" onClick={onPublicar}>
            Publicar convocatoria
          </button>
          <ul>
            {lotes.map((l) => (
              <li key={l.id}>
                #{l.id} {l.recurso} × {l.cantidad} ({l.tipo}) {l.publicado ? "· publicado" : ""}
              </li>
            ))}
          </ul>
        </section>
      )}

      {user.rol === "ong" && selectedId && (
        <section className="card">
          <h2>Oferta de ayuda — emergencia #{selectedId}</h2>
          <form onSubmit={onCreateOferta} className="grid">
            <select name="lote_id" required>
              <option value="">Elegí lote</option>
              {lotes
                .filter((l) => l.publicado)
                .map((l) => (
                  <option key={l.id} value={l.id}>
                    #{l.id} {l.recurso} (pedido {l.cantidad})
                  </option>
                ))}
            </select>
            <input name="cantidad_ofrecida" type="number" min={1} defaultValue={1} required />
            <textarea name="detalle_recursos" placeholder="Detalle de recursos/personal" required />
            <button type="submit">Cargar oferta</button>
          </form>
        </section>
      )}

      <section className="card">
        <h2>Emergencias</h2>
        <ul className="list">
          {emergencias.map((em) => (
            <li key={em.id}>
              <button type="button" className="linkish" onClick={() => setSelectedId(em.id)}>
                #{em.id} {em.tipo_desastre} · {em.nivel_gravedad} · {em.estado}
              </button>
              <div className="muted">
                {em.zona_afectada}
                {em.bonita_case_id ? ` · Bonita case ${em.bonita_case_id}` : " · Bonita pendiente"}
              </div>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
