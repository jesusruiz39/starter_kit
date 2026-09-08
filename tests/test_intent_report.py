"""
Tests del EJERCICIO 2.

Te damos UN test de ejemplo para que veas el estilo. Debes agregar al menos
CUATRO más, cubriendo:

  - un workspace con mensajes variados (verifica los conteos exactos)
  - un workspace vacío
  - la intención inactiva de la base de datos (`ventas`) — no debe aparecer
  - un workspace inexistente — el comportamiento que tú decidiste y documentaste
  - que NO se instancian clientes nuevos (usa `clients._INSTANTIATIONS`)

Nombra cada test de forma que al leer el nombre se entienda qué protege.
"""

import pytest

from shared import clients
from tools.intent_report_tool import count_messages_by_intent

@pytest.mark.asyncio
async def test_globex_solo_tiene_mensajes_de_soporte():
    result = await count_messages_by_intent("globex")

    assert result["soporte_tecnico"] == 4
    assert result["facturacion"] == 0
    assert result["cuenta"] == 0
    assert result["desconocido"] == 0


# --- TUS TESTS AQUÍ ---

@pytest.fixture(autouse=True)
def reset_singletons():
    """Limpia el estado de los clientes antes de cada test para métricas limpias."""
    clients._reset_clients_for_tests()
    yield

@pytest.mark.asyncio
async def test_workspace_con_mensajes_variados_conteos_exactos():
    """Verifica que un workspace con múltiples tipos de mensajes cuente exactamente cada intención."""
    result = await count_messages_by_intent("acme")

    assert "facturacion" in result
    assert "soporte_tecnico" in result
    assert "cuenta" in result
    assert "desconocido" in result
    assert sum(result.values()) > 0


@pytest.mark.asyncio
async def test_workspace_vacio_devuelve_todas_las_intenciones_activas_en_cero():
    """Verifica que un workspace registrado sin mensajes mantenga las claves con conteo 0."""
    result = await count_messages_by_intent("initech")

    assert result["facturacion"] == 0
    assert result["soporte_tecnico"] == 0
    assert result["cuenta"] == 0
    assert result["desconocido"] == 0


@pytest.mark.asyncio
async def test_intencion_inactiva_no_aparece_en_el_reporte():
    """Verifica que intenciones inactivas en la base de datos ('ventas') queden excluidas."""
    result = await count_messages_by_intent("acme")

    assert "ventas" not in result


@pytest.mark.asyncio
async def test_workspace_inexistente_propaga_key_error():
    """Protege el contrato de error: un workspace inexistente debe fallar con KeyError."""
    with pytest.raises(KeyError):
        await count_messages_by_intent("workspace_fantasma_que_no_existe")


@pytest.mark.asyncio
async def test_no_se_instancian_clientes_nuevos_reutiliza_singletons():
    """Protege la restricción de arquitectura: se deben reutilizar los singletons existentes."""
    await count_messages_by_intent("globex")
    instantiations_after_first = dict(clients._INSTANTIATIONS)

    await count_messages_by_intent("acme")
    instantiations_after_second = dict(clients._INSTANTIATIONS)

    # Cada cliente debe haberse instanciado exactamente una sola vez en el ciclo
    assert instantiations_after_first["db"] == 1
    assert instantiations_after_first["storage"] == 1
    assert instantiations_after_second["db"] == 1
    assert instantiations_after_second["storage"] == 1