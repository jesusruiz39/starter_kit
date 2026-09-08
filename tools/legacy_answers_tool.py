"""
EJERCICIO 3 — Código heredado con defectos.

Esta herramienta la escribió alguien con prisa y pasó a producción. Funciona
"en la mayoría de los casos", que es exactamente el problema.

Tu trabajo: encontrar los defectos, corregirlos y explicar cada uno.
NO reescribas la herramienta cambiando su propósito: debe seguir devolviendo
las respuestas de un workspace enriquecidas con el texto de su fuente.
"""

from __future__ import annotations

import asyncio
import logging

from shared.clients import get_db_client

logger = logging.getLogger(__name__)


async def get_workspace_answers(
    workspace_id: str,
    cache: dict | None = None,
    min_similitud: float = 0.0,
) -> list[dict]:
    """Devuelve las respuestas de un workspace enriquecidas con el título de su fuente.

    - Evita mutables por defecto inicializando cache local por llamada si no se provee.
    - Reutiliza el singleton DatabaseClient vía get_db_client().
    - Filtra antes de consultar fuentes para no desperdiciar I/O.
    - Resuelve fuentes concurrentemente evitando el cuello de botella N+1.
    - Maneja con seguridad fuentes inexistentes o campos ausentes.
    - Elimina la escritura insegura a /tmp para operar limpiamente en servicios sin estado.
    """
    if cache is not None and workspace_id in cache:
        return cache[workspace_id]

    db = get_db_client()

    # Consultar respuestas del workspace
    answers_records = await db.table("answers").where("workspace_id", workspace_id).get()

    # Filtrar primero por similitud antes de disparar consultas de fuentes
    candidatas = []
    for a in answers_records:
        data = a.to_dict()
        similitud = float(data.get("similitud", 0.0))
        if similitud >= min_similitud:
            data["similitud"] = similitud
            candidatas.append(data)

    if not candidatas:
        if cache is not None:
            cache[workspace_id] = []
        return []

    # Resolver fuentes únicas en paralelo (evita problema N+1 y consultas duplicadas)
    unique_source_ids = {item["source_id"] for item in candidatas if "source_id" in item}
    source_tasks = [db.table("sources").item(sid).get() for sid in unique_source_ids]
    source_records = await asyncio.gather(*source_tasks)

    source_titles = {}
    for sid, srec in zip(unique_source_ids, source_records):
        sdata = srec.to_dict() if srec else {}
        source_titles[sid] = sdata.get("titulo", "Fuente no disponible")

    # Enriquecer respuestas
    result = []
    for data in candidatas:
        sid = data.get("source_id")
        data["fuente_titulo"] = source_titles.get(sid, "Fuente no disponible")
        data["confianza"] = "alta" if data["similitud"] > 0.8 else "baja"
        result.append(data)

    if cache is not None:
        cache[workspace_id] = result

    return result
