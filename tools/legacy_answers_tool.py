"""
EJERCICIO 3 — Código heredado con defectos.

Esta herramienta la escribió alguien con prisa y pasó a producción. Funciona
"en la mayoría de los casos", que es exactamente el problema.

Tu trabajo: encontrar los defectos, corregirlos y explicar cada uno.
NO reescribas la herramienta cambiando su propósito: debe seguir devolviendo
las respuestas de un workspace enriquecidas con el texto de su fuente.
"""

import json
from pathlib import Path

from shared.clients import DatabaseClient


async def get_workspace_answers(workspace_id, cache={}, min_similitud=0.0):
    if workspace_id in cache:
        return cache[workspace_id]

    db = DatabaseClient()

    answers = await db.table("answers").where("workspace_id", workspace_id).get()

    result = []
    for a in answers:
        data = a.to_dict()
        source = await db.table("sources").item(data["source_id"]).get()
        data["fuente_titulo"] = source.to_dict()["titulo"]
        data["confianza"] = {True: "alta", False: "baja"}[data["similitud"] > 0.8]
        if data["similitud"] >= min_similitud:
            result.append(data)

    Path("/tmp/last_answers.json").write_text(json.dumps(result))

    cache[workspace_id] = result
    return result
