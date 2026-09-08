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
