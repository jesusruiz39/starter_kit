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

import collections
import logging
import threading

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
        self.max_calls = max_calls
        # Almacenamiento anidado: {session_id: {agent_name: conteo}}
        self._counts: dict[str, dict[str, int]] = collections.defaultdict(
            lambda: collections.defaultdict(int)
        )
        # ANÁLISIS DE CONCURRENCIA:
        # En Python con asyncio en un solo hilo de evento (single-threaded event loop),
        # las operaciones de incremento y lectura en diccionarios en memoria son atómicas
        # y cooperativas entre yields de await. Sin embargo, dado que en arquitecturas de agentes
        # los especialistas pueden ejecutarse en hilos separados (ej. asyncio.to_thread o
        # ThreadPoolExecutor para llamadas bloqueantes de I/O / SDKs de LLM), se incorpora un
        # threading.Lock() reentrante (RLock). Esto garantiza thread-safety absoluta y previene
        # race conditions en la verificación e incremento del contador bajo cualquier runtime.
        self._lock = threading.RLock()

    def record(self, session_id: str, agent_name: str) -> int:
        """Registra una llamada para el par (sesión, agente) y devuelve el conteo acumulado.

        Levanta ToolLoopError si el nuevo conteo excede `max_calls`.
        """
        with self._lock:
            current_calls = self._counts[session_id][agent_name] + 1
            self._counts[session_id][agent_name] = current_calls

            if current_calls > self.max_calls:
                msg = (
                    f"ToolLoopError [Alerta Operativa]: El agente '{agent_name}' ha excedido el límite "
                    f"máximo permitido de llamadas ({self.max_calls}) en la sesión '{session_id}'. "
                    f"Conteo registrado: {current_calls}. Posible bucle infinito en invocación de herramientas."
                )
                logger.error(msg)
                raise ToolLoopError(msg)

            logger.debug(
                "Guardia registrada para sesión '%s', agente '%s': %d/%d",
                session_id,
                agent_name,
                current_calls,
                self.max_calls,
            )
            return current_calls

    def reset(self, session_id: str) -> None:
        """Limpia los conteos de una sesión para prevenir fugas de memoria."""
        with self._lock:
            if session_id in self._counts:
                del self._counts[session_id]
                logger.debug("Guardia reseteada para sesión '%s'", session_id)

    def snapshot(self, session_id: str) -> dict[str, int]:
        """Devuelve una copia aislada de los conteos actuales para una sesión."""
        with self._lock:
            if session_id not in self._counts:
                return {}
            return dict(self._counts[session_id])