import { registry } from "./islands";
import { mountIslands } from "./mount";

mountIslands(document, registry);
document.body.addEventListener("htmx:afterSettle", () => mountIslands(document, registry));
