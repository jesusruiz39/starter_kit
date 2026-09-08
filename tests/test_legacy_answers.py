"""
Test de regresión para EJERCICIO 3.

Demuestra que el código original mezclaba y filtraba erróneamente los datos
entre llamadas consecutivas debido al mutable por defecto en `cache={}`.
"""

import pytest

from shared import clients
from tools.legacy_answers_tool import get_workspace_answers


@pytest.fixture(autouse=True)
def reset_state():
    clients._reset_clients_for_tests()
    yield


@pytest.mark.asyncio
async def test_regresion_cache_mutable_no_contamina_llamadas_consecutivas():
    """El defecto más grave: cache={} como mutable por defecto contamina peticiones.

    En el código original:
      1. Usuario A consulta 'acme' con min_similitud=0.9 -> se guarda una lista filtrada pequeña en cache['acme'].
      2. Usuario B consulta 'acme' con min_similitud=0.0 -> la función devolvía de inmediato la lista filtrada
         del usuario A en vez de todas las respuestas del workspace.

    Con la corrección, cada llamada sin caché explícita evalúa sus propios datos y parámetros.
    """
    # 1. Petición restrictiva: solo respuestas de alta similitud
    respuestas_filtradas = await get_workspace_answers("acme", min_similitud=0.9)

    # 2. Petición abierta: todas las respuestas del workspace
    todas_las_respuestas = await get_workspace_answers("acme", min_similitud=0.0)

    # Si el código tiene el bug del mutable por defecto, ambas llamadas devuelven la misma lista
    # y este assert falla. Con el arreglo, la segunda llamada recupera el total de registros.
    assert len(todas_las_respuestas) > len(respuestas_filtradas)
    assert any(r["similitud"] < 0.9 for r in todas_las_respuestas)


@pytest.mark.asyncio
async def test_reutiliza_singleton_db_client():
    """Verifica que no se instancien clientes nuevos en cada llamada."""
    await get_workspace_answers("acme")
    assert clients._INSTANTIATIONS["db"] == 1

    await get_workspace_answers("acme")
    assert clients._INSTANTIATIONS["db"] == 1