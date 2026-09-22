import { act } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { mountIslands, type IslandRegistry } from "./mount";

function Saludo({ nombre, veces }: { nombre: string; veces: number }) {
  return <p>Hola {nombre} x{veces}</p>;
}

const registry: IslandRegistry = { Saludo };

// React 19 exige esta marca para que act() funcione fuera de un runner de React.
(globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;

function montar(html: string) {
  document.body.innerHTML = html;
  let n = 0;
  act(() => {
    n = mountIslands(document, registry);
  });
  return n;
}

describe("mountIslands", () => {
  beforeEach(() => vi.spyOn(console, "error").mockImplementation(() => {}));
  afterEach(() => vi.restoreAllMocks());

  it("monta el componente registrado con las props del atributo data-props", () => {
    const n = montar(`<div id="a" data-island="Saludo" data-props='{"nombre":"Cruz Roja","veces":2}'>Cargando…</div>`);
    expect(n).toBe(1);
    expect(document.getElementById("a")!.textContent).toBe("Hola Cruz Roja x2");
  });

  it("monta varias islas en la misma página", () => {
    const n = montar(`
      <div data-island="Saludo" data-props='{"nombre":"A","veces":1}'></div>
      <div data-island="Saludo" data-props='{"nombre":"B","veces":1}'></div>`);
    expect(n).toBe(2);
    expect(document.body.textContent).toContain("Hola A");
    expect(document.body.textContent).toContain("Hola B");
  });

  it("no vuelve a montar una isla ya montada", () => {
    montar(`<div data-island="Saludo" data-props='{"nombre":"A","veces":1}'></div>`);
    let n = -1;
    act(() => {
      n = mountIslands(document, registry);
    });
    expect(n).toBe(0);
  });

  it("marca y reporta una isla desconocida sin romper las demás", () => {
    const n = montar(`
      <div id="x" data-island="NoExiste"></div>
      <div data-island="Saludo" data-props='{"nombre":"A","veces":1}'></div>`);
    expect(n).toBe(1);
    expect(document.getElementById("x")!.dataset.islandError).toBe("desconocida");
    expect(console.error).toHaveBeenCalledWith('Isla desconocida: "NoExiste"');
  });

  it("marca las props que no son JSON válido", () => {
    const n = montar(`<div id="x" data-island="Saludo" data-props='{roto'></div>`);
    expect(n).toBe(0);
    expect(document.getElementById("x")!.dataset.islandError).toBe("props");
  });

  it("lee props escapadas como las genera Jinja (tojson + forceescape)", () => {
    const n = montar(
      `<div id="a" data-island="Saludo" data-props="{&#34;nombre&#34;: &#34;O\\u0027Higgins \\u003cb\\u003e&#34;, &#34;veces&#34;: 1}"></div>`,
    );
    expect(n).toBe(1);
    expect(document.getElementById("a")!.textContent).toBe("Hola O'Higgins <b> x1");
  });
});
