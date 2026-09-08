"""
Tests del EJERCICIO 6.

Te damos DOS: el camino feliz y el camino de abstención, que es el que de
verdad importa. Agrega al menos DOS más — el caso `DUDOSO` y algún borde
(pregunta vacía, workspace inexistente, pregunta sin ninguna palabra en común
con el corpus).

Fíjate que estos tests no levantan el servidor: llaman a `consultar()`
directamente. Si tu lógica quedó atrapada dentro del handler HTTP, no vas a
poder escribirlos, y eso ya es una señal sobre el diseño.
"""

import pytest

from app import UMBRAL_ALTO, UMBRAL_MINIMO, consultar


@pytest.mark.asyncio
async def test_pregunta_sustentada_devuelve_respuesta_con_fuente():
    r = await consultar("¿Cuántos días de garantía tiene el plan Pro?", "acme")

    assert r["veredicto"] == "APROBADO"
    assert r["respuesta"] is not None
    assert "15 días" in r["respuesta"]
    assert r["fragmentos"][0]["source_id"] == "src-1"
    assert r["fragmentos"][0]["similitud"] >= UMBRAL_MINIMO


@pytest.mark.asyncio
async def test_pregunta_sin_evidencia_no_inventa_respuesta():
    # El corpus no dice nada del plan Enterprise. El recuperador igual devuelve
    # fragmentos parecidos —habla de planes y de garantías— pero ninguno responde.
    r = await consultar("¿cuánto dura la garantía del plan Enterprise?", "acme")

    assert r["veredicto"] == "SIN_EVIDENCIA"
    assert r["respuesta"] is None
    assert r["fragmentos"], "el recuperador sí devolvió fragmentos"
    assert r["fragmentos"][0]["similitud"] < UMBRAL_MINIMO
    assert "0.55" in r["motivo"] or "55" in r["motivo"], "el motivo debe citar el umbral"


# --- TUS TESTS AQUÍ ---
@pytest.mark.asyncio
async def test_pregunta_dudosa_devuelve_respuesta_marcada_para_revision():
    """Valida el veredicto DUDOSO cuando la similitud está entre UMBRAL_MINIMO y UMBRAL_ALTO."""
    r = await consultar("olvidé mi contraseña, ¿cómo la restablezco?", "acme")

    assert r["veredicto"] == "DUDOSO"
    assert r["respuesta"] is not None
    assert UMBRAL_MINIMO <= r["fragmentos"][0]["similitud"] < UMBRAL_ALTO
    assert "0.75" in r["motivo"] or "75" in r["motivo"]


@pytest.mark.asyncio
async def test_pregunta_vacia_se_abstiene():
    """Borde: entrada vacía debe devolver SIN_EVIDENCIA y respuesta None."""
    r = await consultar("", "acme")

    assert r["veredicto"] == "SIN_EVIDENCIA"
    assert r["respuesta"] is None
    assert "No se recuperaron" in r["motivo"] or "0.55" in r["motivo"]


@pytest.mark.asyncio
async def test_pregunta_sin_palabras_en_comun_con_corpus():
    """Borde: términos completamente ajenos al corpus dan SIN_EVIDENCIA."""
    r = await consultar("astronauta asteroide telescopio galaxia", "acme")

    assert r["veredicto"] == "SIN_EVIDENCIA"
    assert r["respuesta"] is None