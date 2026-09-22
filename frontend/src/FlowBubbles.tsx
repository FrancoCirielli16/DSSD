import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const STEPS = [
  {
    id: 1,
    label: "Registrar",
    sub: "Municipio",
    detail: "Alta de la emergencia y arranque del caso en Bonita.",
  },
  {
    id: 2,
    label: "Lotes",
    sub: "Coordinador",
    detail: "Se desglosan necesidades y se publica la convocatoria.",
  },
  {
    id: 3,
    label: "Ofertas",
    sub: "ONGs",
    detail: "La red carga ofertas dentro de la ventana de tiempo.",
  },
  {
    id: 4,
    label: "Adjudicar",
    sub: "Cierre",
    detail: "Se eligen ofertas, se comprometen recursos y se cierra.",
  },
] as const;

export function FlowBubbles() {
  const [active, setActive] = useState(1);
  const [pinned, setPinned] = useState(false);
  const current = STEPS.find((s) => s.id === active) ?? STEPS[0];

  useEffect(() => {
    if (pinned) return;
    const id = window.setInterval(() => {
      setActive((prev) => {
        const idx = STEPS.findIndex((s) => s.id === prev);
        return STEPS[(idx + 1) % STEPS.length].id;
      });
    }, 3800);
    return () => window.clearInterval(id);
  }, [pinned]);

  return (
    <div className="flow-scene" aria-label="Flujo RescueSync">
      <div className="flow-art">
        <img
          src="/hero-dssd.png"
          alt="Red de coordinación: municipio, centro, ONGs y respuesta en campo"
          className="flow-art-img"
          width={1774}
          height={887}
          decoding="async"
        />
      </div>

      <ol className="flow-steps">
        {STEPS.map((step) => {
          const isActive = active === step.id;
          return (
            <li key={step.id}>
              <button
                type="button"
                className={`flow-step ${isActive ? "is-active" : ""}`}
                aria-pressed={isActive}
                aria-label={`${step.label}: ${step.detail}`}
                onMouseEnter={() => {
                  setPinned(true);
                  setActive(step.id);
                }}
                onMouseLeave={() => setPinned(false)}
                onFocus={() => {
                  setPinned(true);
                  setActive(step.id);
                }}
                onBlur={() => setPinned(false)}
                onClick={() => {
                  setPinned(true);
                  setActive(step.id);
                }}
              >
                <span className="flow-step-num">{step.id}</span>
                <span className="flow-step-text">
                  <strong>{step.label}</strong>
                  <small>{step.sub}</small>
                </span>
              </button>
            </li>
          );
        })}
      </ol>

      <AnimatePresence mode="wait">
        <motion.div
          key={current.id}
          className="flow-tooltip"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 6 }}
          transition={{ duration: 0.22 }}
        >
          <strong>
            {current.id}. {current.label}
          </strong>
          <span>{current.detail}</span>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}
