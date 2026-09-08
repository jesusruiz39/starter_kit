"""
Recuperador de fragmentos. TE LO DAMOS HECHO — no lo modifiques.

En producción esto sería un índice vectorial con embeddings. Aquí es un
buscador léxico determinista: no necesita red, ni claves, ni modelo, y para
efectos de la prueba se comporta igual — te devuelve fragmentos con un puntaje
de similitud entre 0 y 1, y a veces te devuelve basura con buen formato.

Eso último es el punto. Recuperar algo no significa haber encontrado la
respuesta.
"""

from __future__ import annotations

import logging
import math
import re
import unicodedata

from shared.clients import get_db_client

logger = logging.getLogger(__name__)

# Tamaño aproximado de cada fragmento, en caracteres.
FRAGMENT_CHARS = 230

# Palabras vacías: no aportan al parecido entre pregunta y fragmento.
STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al",
    "a", "en", "y", "o", "que", "se", "es", "son", "por", "para", "con", "sin",
    "su", "sus", "mi", "lo", "le", "me", "te", "cual", "cuales", "cuanto",
    "cuantos", "cuanta", "cuantas", "como", "donde", "cuando", "porque", "si",
    "no", "ya", "mas", "muy", "hay", "tiene", "tienen", "puedo", "puede",
    "quiero", "necesito", "desde", "hasta", "sobre", "entre", "esta", "este",
    "esto", "estos", "estas", "ese", "esa", "eso",
}


def normalize(text: str) -> str:
    """minúsculas, sin acentos, sin signos."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


# Raíz aproximada: los primeros 5 caracteres. Hace que "contraseña" y
# "contrasenas", o "restablecer" y "restablezco", cuenten como la misma palabra.
STEM = 5


def tokens(text: str) -> set[str]:
    return {t[:STEM] for t in normalize(text).split()
            if t and t not in STOPWORDS and len(t) > 1}


def split_fragments(texto: str) -> list[str]:
    """Parte un documento en fragmentos, respetando el final de las oraciones."""
    oraciones = re.split(r"(?<=[.:;])\s+", texto.strip())
    fragmentos, actual = [], ""
    for oracion in oraciones:
        if actual and len(actual) + len(oracion) + 1 > FRAGMENT_CHARS:
            fragmentos.append(actual.strip())
            actual = oracion
        else:
            actual = f"{actual} {oracion}".strip()
    if actual.strip():
        fragmentos.append(actual.strip())
    return fragmentos


async def search(query: str, top_k: int = 4) -> list[dict]:
    """Busca los fragmentos más parecidos a la pregunta.

    Devuelve una lista de diccionarios, ordenada de mayor a menor `similitud`:

        {
          "source_id": "src-1",
          "titulo":    "Guía de planes y garantías",
          "chunk":     2,              # índice del fragmento dentro del documento
          "texto":     "El plan Pro incluye una garantía de …",
          "similitud": 0.72,           # 0.0 – 1.0
        }

    Ojo: **siempre devuelve algo** mientras haya alguna palabra en común, por
    baja que sea la similitud. Decidir si eso alcanza para responder no es
    trabajo del recuperador.
    """
    db = get_db_client()
    docs = await db.table("sources").get()

    q = tokens(query)
    if not q:
        return []

    # Índice de fragmentos + frecuencia documental de cada término.
    fragmentos, df = [], {}
    for doc in docs:
        data = doc.to_dict()
        for i, texto in enumerate(split_fragments(data.get("texto", ""))):
            f = tokens(texto)
            if not f:
                continue
            fragmentos.append((doc.id, data.get("titulo", ""), i, texto, f))
            for t in f:
                df[t] = df.get(t, 0) + 1

    n = max(len(fragmentos), 1)

    def idf(t: str) -> float:
        return math.log((n + 1) / (df.get(t, 0) + 1)) + 1.0

    # La similitud es qué proporción del *peso* de la pregunta quedó cubierta.
    # Un término raro que no aparece penaliza mucho más que uno común.
    total = sum(idf(t) for t in q) or 1.0

    resultados = []
    for source_id, titulo, i, texto, f in fragmentos:
        comunes = q & f
        if not comunes:
            continue
        similitud = sum(idf(t) for t in comunes) / total
        resultados.append({
            "source_id": source_id,
            "titulo": titulo,
            "chunk": i,
            "texto": texto,
            "similitud": round(min(similitud, 1.0), 3),
        })

    resultados.sort(key=lambda r: (-r["similitud"], r["source_id"], r["chunk"]))
    logger.debug("search(%r) -> %d fragmentos", query, len(resultados))
    return resultados[:top_k]
