"""
Herramienta del paso Clasificador: reporte de cobertura por intención.

EJERCICIO 2.

Contexto de producto: antes de activar el asistente en un workspace, el equipo
quiere ver "de tus 200 preguntas, 80 son de facturación, 40 de soporte y 60 no
supe de qué son". Ese último número es el que decide si el asistente está listo
o si al cliente le falta subir contenido.
"""

from __future__ import annotations

import logging

from config.intents import UNKNOWN, classify_intent
from shared.clients import get_db_client, get_storage_client

logger = logging.getLogger(__name__)


async def count_messages_by_intent(workspace_id: str) -> dict[str, int]:
    """Cuenta los mensajes de un workspace agrupados por intención.

    Comportamiento esperado:

    1. Lee las intenciones válidas de la tabla `intents` de la base de datos.
       Solo cuentan las que tienen `active: true`.
    2. Lista los mensajes del workspace con el cliente de almacenamiento.
    3. Clasifica cada mensaje con `config.intents.classify_intent`.
    4. Devuelve `{intencion: conteo}` incluyendo:
       - todas las intenciones activas, **aunque su conteo sea 0**;
       - la intención `desconocido`, siempre presente.
       Las intenciones inactivas no aparecen en el resultado.

    Restricciones (se evalúan):
    - Reutiliza los singletons de `shared.clients`. No construyas clientes
      nuevos dentro de esta función.
    - Es `async`: usa `await` sobre las llamadas de los clientes.
    - Si el workspace no existe, el cliente levanta `KeyError`. Decide qué hace
      la herramienta en ese caso y **documenta tu decisión en un comentario**:
      propagar, devolver dict vacío o devolver ceros no son equivalentes para
      el agente que la llama.
    - Deja al menos un log útil, siguiendo el patrón del módulo.

    Args:
        workspace_id: por ejemplo `acme`.

    Returns:
        Diccionario `{intencion: conteo}`.
    """
    db = get_db_client()
    storage = get_storage_client()

    # 1. Obtener intenciones activas desde la base de datos
    records = await db.table("intents").where("active", True).get()

    # Inicializar conteos con 0 para todas las activas
    counts: dict[str, int] = {
        (rec.to_dict().get("name") or rec.id): 0 for rec in records
    }
    # Asegurar que UNKNOWN ("desconocido") siempre esté presente
    counts[UNKNOWN] = 0

    # 2. Listar mensajes del storage con manejo explícito de KeyError:
    # DECISIÓN DE DISEÑO: Propagar KeyError si el workspace no existe.
    # Justificación: Un workspace no encontrado es un error semántico de solicitud
    # o de configuración del llamante (ej. 404), no un workspace legítimo con 0
    # mensajes. Devolver ceros o dict vacío enmascararía identificadores erróneos,
    # reportando falsamente que un workspace inexistente está analizado y listo.
    try:
        messages = await storage.list_messages(workspace_id)
    except KeyError:
        logger.warning(
            "Workspace no encontrado en almacenamiento: '%s'", workspace_id
        )
        raise

    # 3. Clasificar cada mensaje
    for msg in messages:
        intent = classify_intent(msg)
        # Solo contabilizar si es una intención activa o UNKNOWN
        if intent in counts:
            counts[intent] += 1
        else:
            # Si clasificó en una intención inactiva en la BD, computa como UNKNOWN
            counts[UNKNOWN] += 1

    logger.info(
        "Reporte de intención completado para workspace '%s' (%d mensajes procesados)",
        workspace_id,
        len(messages),
    )
    return counts
