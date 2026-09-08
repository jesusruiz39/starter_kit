"""
EJERCICIO 5 — Guardia contra loops de agentes.

Problema real: un agente entra en bucle llamando a la misma herramienta una y
otra vez (típicamente la que escribe en el estado compartido). Un loop no se ve
como un crash: se ve como una factura del proveedor de modelos que se dispara y
una petición que nunca termina. Ya existe una instrucción en el prompt pidiendo
al agente que no lo haga, pero un prompt es una sugerencia, no un control.

Necesitamos una guardia en código.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

MAX_CALLS = 3


class ToolLoopError(RuntimeError):
    """Se levanta cuando un agente supera el límite de llamadas a una herramienta."""


class LoopGuard:
    """Cuenta llamadas por (sesión, agente) y aborta al excederse.

    Requisitos:

    - `record(session_id, agent_name)` registra una llamada y devuelve el
      conteo actualizado.
    - A la llamada número `MAX_CALLS + 1` del **mismo agente en la misma
      sesión**, levanta `ToolLoopError` con un mensaje que incluya el nombre
      del agente, el id de sesión y el conteo. Un mensaje que solo diga "loop
      detectado" no sirve a las 3 a.m.
    - Los conteos son independientes por agente y por sesión: que `classifier`
      llame 3 veces en la sesión A no afecta a `verifier` ni a la sesión B.
    - `reset(session_id)` limpia los conteos de una sesión terminada. Sin esto,
      un proceso de larga vida acumula memoria durante horas.
    - `snapshot(session_id)` devuelve `{agente: conteo}` para poder loguearlo.

    Piensa en la concurrencia: los especialistas corren en paralelo dentro del
    mismo proceso. Documenta en un comentario si tu implementación es segura y
    por qué (o por qué no hace falta que lo sea).
    """

    def __init__(self, max_calls: int = MAX_CALLS):
        raise NotImplementedError("EJERCICIO 5")

    def record(self, session_id: str, agent_name: str) -> int:
        raise NotImplementedError("EJERCICIO 5")

    def reset(self, session_id: str) -> None:
        raise NotImplementedError("EJERCICIO 5")

    def snapshot(self, session_id: str) -> dict[str, int]:
        raise NotImplementedError("EJERCICIO 5")
