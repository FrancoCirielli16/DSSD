"""Macros de Jinja para montar islas de React (frontend/)."""
import html
import json
import re

import pytest

from app.core import templating

USO = '{% from "_islands.html" import island, islands_script %}{{ island(nombre, props) }}|{{ islands_script() }}'


def render(nombre="EditorOfertas", props=None):
    return templating.templates.env.from_string(USO).render(nombre=nombre, props=props or {})


@pytest.fixture
def con_bundle(tmp_path, monkeypatch):
    bundle = tmp_path / "islands.js"
    bundle.write_text("// build")
    monkeypatch.setattr(templating, "ISLANDS_BUNDLE", bundle)
    return bundle


@pytest.fixture
def sin_bundle(tmp_path, monkeypatch):
    monkeypatch.setattr(templating, "ISLANDS_BUNDLE", tmp_path / "no-existe.js")


def test_props_llegan_intactas_aunque_tengan_comillas_y_html(con_bundle):
    props = {"emergenciaId": 7, "ong": 'O"Higgins <script>', "lotes": [1, 2]}
    out = render(props=props)
    attr = re.search(r'data-props="([^"]*)"', out).group(1)
    assert "<script>" not in attr and '"' not in attr  # escapado dentro del atributo
    assert json.loads(html.unescape(attr)) == props
    assert 'data-island="EditorOfertas"' in out


def test_con_bundle_incluye_el_script_versionado(con_bundle):
    out = render()
    v = int(con_bundle.stat().st_mtime)
    assert f'<script type="module" src="/static/islands/islands.js?v={v}"></script>' in out
    assert "Cargando" in out and "npm run build" not in out


def test_sin_bundle_avisa_como_compilarlo_y_no_incluye_script(sin_bundle):
    island_html, script = render().split("|")
    assert "npm run build" in island_html
    assert script.strip() == ""


def test_el_bundle_compilado_se_sirve_como_estatico(client):
    if templating.islands_version() is None:
        pytest.skip("frontend sin compilar (cd frontend && npm run build)")
    r = client.get("/static/islands/islands.js")
    assert r.status_code == 200 and "javascript" in r.headers["content-type"]
