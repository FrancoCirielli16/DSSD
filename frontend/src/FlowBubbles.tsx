import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

type ZoneId = "municipio" | "centro" | "ong" | "rescate" | "ambulancia";

type Zone = {
  id: ZoneId;
  step: 1 | 2 | 3 | 4;
  label: string;
  hint: string;
  x: number;
  y: number;
  hit: { left: number; top: number; width: number; height: number };
  scale: number;
};

const ZONES: Zone[] = [
  {
    id: "municipio",
    step: 1,
    label: "Municipio",
    hint: "Alta de la emergencia",
    x: 18,
    y: 28,
    hit: { left: 5, top: 10, width: 26, height: 36 },
    scale: 1.9,
  },
  {
    id: "centro",
    step: 2,
    label: "Centro coordinador",
    hint: "Lotes y convocatoria",
    x: 48,
    y: 48,
    hit: { left: 33, top: 26, width: 28, height: 44 },
    scale: 1.75,
  },
  {
    id: "ong",
    step: 3,
    label: "Red de ONGs",
    hint: "Ofertas de ayuda",
    x: 84,
    y: 28,
    hit: { left: 68, top: 6, width: 28, height: 42 },
    scale: 1.95,
  },
  {
    id: "rescate",
    step: 1,
    label: "Equipo en campo",
    hint: "Respuesta operativa",
    x: 14,
    y: 78,
    hit: { left: 2, top: 56, width: 28, height: 40 },
    scale: 2.05,
  },
  {
    id: "ambulancia",
    step: 4,
    label: "Recursos y cierre",
    hint: "Adjudicación",
    x: 86,
    y: 78,
    hit: { left: 68, top: 54, width: 30, height: 42 },
    scale: 2.05,
  },
];

const STEPS = [
  {
    id: 1 as const,
    label: "Registrar",
    sub: "Municipio",
    detail: "Alta de la emergencia y arranque del caso en Bonita.",
    zone: "municipio" as ZoneId,
  },
  {
    id: 2 as const,
    label: "Lotes",
    sub: "Coordinador",
    detail: "Se desglosan necesidades y se publica la convocatoria.",
    zone: "centro" as ZoneId,
  },
  {
    id: 3 as const,
    label: "Ofertas",
    sub: "ONGs",
    detail: "La red carga ofertas dentro de la ventana de tiempo.",
    zone: "ong" as ZoneId,
  },
  {
    id: 4 as const,
    label: "Adjudicar",
    sub: "Cierre",
    detail: "Se eligen ofertas, se comprometen recursos y se cierra.",
    zone: "ambulancia" as ZoneId,
  },
];

const spring = { type: "spring" as const, stiffness: 130, damping: 24, mass: 0.8 };

function zoomTransform(zone: Zone | null, w: number, h: number) {
  if (!zone || w <= 0 || h <= 0) {
    return { scale: 1, x: 0, y: 0 };
  }
  const s = zone.scale;
  return {
    scale: s,
    x: w / 2 - (zone.x / 100) * w * s,
    y: h / 2 - (zone.y / 100) * h * s,
  };
}

export function FlowBubbles() {
  const stageRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 0, h: 0 });
  const [activeStep, setActiveStep] = useState(1);
  const [focus, setFocus] = useState<ZoneId | null>(null);
  const [pinned, setPinned] = useState(false);

  const current = STEPS.find((s) => s.id === activeStep) ?? STEPS[0];
  const activeZone = focus ? ZONES.find((z) => z.id === focus) ?? null : null;
  const frame = zoomTransform(activeZone, size.w, size.h);

  useEffect(() => {
    const el = stageRef.current;
    if (!el) return;
    const update = () => {
      const r = el.getBoundingClientRect();
      setSize({ w: r.width, h: r.height });
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    if (pinned || focus) return;
    const id = window.setInterval(() => {
      setActiveStep((prev) => {
        const idx = STEPS.findIndex((s) => s.id === prev);
        return STEPS[(idx + 1) % STEPS.length].id;
      });
    }, 4200);
    return () => window.clearInterval(id);
  }, [pinned, focus]);

  function focusZone(zoneId: ZoneId) {
    const zone = ZONES.find((z) => z.id === zoneId);
    if (!zone) return;
    setPinned(true);
    setFocus(zoneId);
    setActiveStep(zone.step);
  }

  function focusStep(stepId: number) {
    const step = STEPS.find((s) => s.id === stepId);
    if (!step) return;
    setPinned(true);
    setActiveStep(stepId);
    setFocus(step.zone);
  }

  function resetView() {
    setFocus(null);
  }

  const zoomed = Boolean(activeZone);

  return (
    <div className="flow-scene" aria-label="Flujo RescueSync">
      <div className={`flow-art ${zoomed ? "is-zoomed" : ""}`}>
        <div className="flow-stage" ref={stageRef}>
          <motion.div
            className="flow-stage-frame"
            animate={frame}
            transition={spring}
            style={{ transformOrigin: "0% 0%" }}
          >
            <img
              src="/hero-dssd.png"
              alt="Red de coordinación: municipio, centro, ONGs y respuesta en campo"
              className="flow-art-img"
              width={1774}
              height={887}
              decoding="async"
              draggable={false}
            />
          </motion.div>

          <div className="flow-hotspots">
            {ZONES.map((zone) => {
              const on = focus === zone.id;
              return (
                <button
                  key={zone.id}
                  type="button"
                  className={`flow-hotspot ${on ? "is-on" : ""}`}
                  style={{
                    left: `${zone.hit.left}%`,
                    top: `${zone.hit.top}%`,
                    width: `${zone.hit.width}%`,
                    height: `${zone.hit.height}%`,
                  }}
                  aria-label={`Enfocar ${zone.label}`}
                  aria-pressed={on}
                  onClick={() => {
                    if (focus === zone.id) resetView();
                    else focusZone(zone.id);
                  }}
                >
                  <span className="flow-hotspot-pulse" />
                  <span className="flow-hotspot-dot" />
                </button>
              );
            })}
          </div>

          <AnimatePresence>
            {zoomed && (
              <motion.div
                className="flow-vignette"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.35 }}
              />
            )}
          </AnimatePresence>

          <AnimatePresence mode="wait">
            {activeZone && (
              <motion.div
                key={activeZone.id}
                className="flow-focus-card"
                initial={{ opacity: 0, y: 16, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: 10, scale: 0.98 }}
                transition={{ duration: 0.28 }}
              >
                <span className="flow-focus-kicker">Paso {activeZone.step}</span>
                <strong>{activeZone.label}</strong>
                <span>{activeZone.hint}</span>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {zoomed && (
              <motion.button
                type="button"
                className="flow-reset"
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                onClick={resetView}
              >
                Ver panorama
              </motion.button>
            )}
          </AnimatePresence>
        </div>

        {!zoomed && (
          <p className="flow-hint">Tocá un punto de la red para acercarte</p>
        )}
      </div>

      <ol className="flow-steps">
        {STEPS.map((step) => {
          const isActive = activeStep === step.id;
          return (
            <li key={step.id}>
              <button
                type="button"
                className={`flow-step ${isActive ? "is-active" : ""}`}
                aria-pressed={isActive}
                aria-label={`${step.label}: ${step.detail}`}
                onClick={() => focusStep(step.id)}
                onMouseEnter={() => {
                  if (!focus) {
                    setPinned(true);
                    setActiveStep(step.id);
                  }
                }}
                onMouseLeave={() => {
                  if (!focus) setPinned(false);
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
