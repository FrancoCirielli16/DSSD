import { StrictMode, type ComponentType } from "react";
import { createRoot } from "react-dom/client";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type IslandRegistry = Record<string, ComponentType<any>>;

/**
 * Monta cada `<div data-island="Nombre" data-props='{...}'>` con el componente registrado.
 * Es idempotente: se puede volver a llamar después de que HTMX inserte HTML nuevo.
 */
export function mountIslands(root: ParentNode, registry: IslandRegistry): number {
  let montadas = 0;
  root.querySelectorAll<HTMLElement>("[data-island]").forEach((el) => {
    if (el.dataset.islandMounted || el.dataset.islandError) return;
    const nombre = el.dataset.island ?? "";
    const Component = registry[nombre];
    if (!Component) {
      el.dataset.islandError = "desconocida";
      console.error(`Isla desconocida: "${nombre}"`);
      return;
    }
    let props: Record<string, unknown>;
    try {
      props = JSON.parse(el.dataset.props ?? "{}");
    } catch {
      el.dataset.islandError = "props";
      console.error(`Props inválidas en la isla "${nombre}"`);
      return;
    }
    createRoot(el).render(
      <StrictMode>
        <Component {...props} />
      </StrictMode>,
    );
    el.dataset.islandMounted = "true";
    montadas++;
  });
  return montadas;
}
