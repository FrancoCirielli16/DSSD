"""Listado y detalle de emergencias: qué ve cada perfil."""
from datetime import datetime, timezone

import pytest

from app.models import Emergencia, EstadoEmergencia, Gravedad, Lote, Municipio, TipoLote


@pytest.fixture
def emergencias(seeded):
    """Una emergencia del municipio del seed (registrada) y otra de otro municipio (en convocatoria)."""
    with seeded() as s:
        propio = s.query(Municipio).one()
        otro = Municipio(nombre="Tres Arroyos", provincia="Buenos Aires")
        s.add(otro)
        s.flush()
        propia = Emergencia(municipio_id=propio.id, tipo="inundacion", nivel_gravedad=Gravedad.ALTO,
                            zona_afectada="Centro", descripcion="Río desbordado", bonita_case_id=11,
                            creada_en=datetime(2026, 9, 22, 13, 0, tzinfo=timezone.utc))
        ajena = Emergencia(municipio_id=otro.id, tipo="incendio", nivel_gravedad=Gravedad.CRITICO,
                           zona_afectada="Sierra", descripcion="Foco activo", bonita_case_id=12,
                           estado=EstadoEmergencia.CONVOCATORIA)
        ajena.lotes = [Lote(recurso="Brigadistas", cantidad=20, unidad="personas", tipo=TipoLote.APOYO)]
        s.add_all([propia, ajena])
        s.commit()
        return propia.id, ajena.id


def test_listado_exige_sesion(client):
    assert client.get("/emergencias").status_code == 303


def test_municipio_ve_solo_las_de_su_municipio(login, emergencias):
    propia, ajena = emergencias
    c = login("operador.municipal")
    r = c.get("/emergencias")
    assert f'href="/emergencias/{propia}"' in r.text
    assert f'href="/emergencias/{ajena}"' not in r.text
    assert c.get(f"/emergencias/{ajena}").status_code == 404


@pytest.mark.parametrize("usuario", ["coordinador.regional", "auditor"])
def test_coordinador_y_auditor_ven_todas(login, emergencias, usuario):
    c = login(usuario)
    r = c.get("/emergencias")
    for eid in emergencias:
        assert f'href="/emergencias/{eid}"' in r.text
        assert c.get(f"/emergencias/{eid}").status_code == 200


def test_ong_ve_solo_convocatorias_abiertas(login, emergencias):
    propia, ajena = emergencias
    c = login("ong.bomberos")
    r = c.get("/emergencias")
    assert "Convocatorias abiertas" in r.text
    assert f'href="/emergencias/{ajena}"' in r.text
    assert f'href="/emergencias/{propia}"' not in r.text
    assert c.get(f"/emergencias/{propia}").status_code == 404


def test_detalle_muestra_datos_caso_y_lotes(login, emergencias):
    _, ajena = emergencias
    r = login("coordinador.regional").get(f"/emergencias/{ajena}")
    assert "Tres Arroyos" in r.text and "Foco activo" in r.text and "#12" in r.text
    assert "Brigadistas · 20 personas" in r.text and "Apoyo" in r.text
    assert "Convocatoria abierta" in r.text


def test_fecha_se_muestra_en_hora_local(login, emergencias):
    from app.core.templating import fecha

    propia, _ = emergencias
    r = login("operador.municipal").get(f"/emergencias/{propia}")
    assert fecha(datetime(2026, 9, 22, 13, 0, tzinfo=timezone.utc)) in r.text


def test_fecha_sin_zona_se_interpreta_como_utc():
    from app.core.templating import fecha

    assert fecha(datetime(2026, 9, 22, 13, 0)) == fecha(datetime(2026, 9, 22, 13, 0, tzinfo=timezone.utc))
    assert fecha(None) == "—"


def test_emergencia_inexistente_da_404_con_pagina(login):
    r = login("coordinador.regional").get("/emergencias/999")
    assert r.status_code == 404
    assert "Emergencia no encontrada" in r.text
