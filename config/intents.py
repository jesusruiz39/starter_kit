"""
Catálogo de intenciones y clasificación de mensajes.

Es el primer paso del pipeline del asistente: decide de qué trata la pregunta
del usuario para elegir qué especialista la atiende y qué contenido buscar.
Es la pieza más pequeña del sistema y la que más daño hace cuando se equivoca:
una pregunta de facturación ruteada a soporte técnico busca en el corpus
equivocado y produce una respuesta segura y falsa.

EJERCICIO 1: implementa `classify_intent`. No modifiques `INTENTS`.
"""

from __future__ import annotations

import re
import unicodedata

# ---------------------------------------------------------------------------
# Catálogo. NO MODIFICAR.
# Los patrones ya están normalizados: minúsculas, sin acentos, palabras
# separadas por un solo espacio.
# ---------------------------------------------------------------------------
INTENTS: dict[str, dict] = {
    "facturacion": {
        "specialist": "billing_agent",
        "patterns": [
            "factura",
            "cobro",
            "pago",
            "tarjeta",
            "reembolso",
            "garantia",
            "devolucion",
            "cargo duplicado",
        ],
    },
    "soporte_tecnico": {
        "specialist": "support_agent",
        "patterns": [
            "error",
            "no funciona",
            "falla",
            "lento",
            "no carga",
            "se cierra",
        ],
    },
    "cuenta": {
        "specialist": "account_agent",
        "patterns": [
            "contrasena",
            "iniciar sesion",
            "cerrar mi cuenta",
            "cambiar correo",
            "permisos",
            "usuario nuevo",
        ],
    },
}

# Longitud mínima del mensaje (ya normalizado) para intentar clasificarlo.
MIN_LENGTH = 3

# Intención de los mensajes que no matchean nada.
# Los mensajes sin clasificar NO se descartan: alimentan el reporte de
# cobertura del asistente. Ese número es el que le importa a producto.
UNKNOWN = "desconocido"

def normalize_text(text: str) -> str:
    """Normaliza texto: elimina acentos/diacríticos, pasa a minúsculas, reemplaza caracteres no alfanuméricos por espacios y colapsa espacios múltiples.
    """
    # Descompone caracteres con tildes/acentos y elimina marcas diacríticas
    nfkd = unicodedata.normalize("NFKD", text)
    without_accents = "".join(c for c in nfkd if not unicodedata.combining(c))
    lowered = without_accents.lower()
    # Sustituye cualquier caracter no alfanumérico por espacio y colapsa
    cleaned = re.sub(r"[^\w\s]", " ", lowered)
    return " ".join(cleaned.split())


def classify_intent(message: str) -> str:
    """Devuelve la intención de un mensaje del usuario.

    Reglas que debe cumplir tu implementación:

    1. La comparación es **insensible a mayúsculas, acentos y signos**.
       `¿OLVIDÉ MI CONTRASEÑA?`, `olvide-mi-contrasena` y
       `Olvidé mi contraseña...` son todos "cuenta".
    2. Si el mensaje matchea patrones de más de una intención, gana el patrón
       **más largo** (el más específico). Ejemplo:
       `no puedo iniciar sesion, me da error` es "cuenta", no
       "soporte_tecnico", porque `iniciar sesion` es más largo que `error`.
    3. Los mensajes llegan a veces con la conversación previa citada: las
       líneas que empiezan con `>` son texto citado y **se ignoran por
       completo** para clasificar.
    4. Si el mensaje normalizado tiene menos de `MIN_LENGTH` caracteres,
       devuelve `UNKNOWN` sin intentar clasificar.
    5. Si no matchea ningún patrón, devuelve `UNKNOWN`.
    6. Un mensaje vacío, en blanco o `None` devuelve `UNKNOWN` (no revienta).

    Args:
        message: el texto del usuario, tal como llega del chat.

    Returns:
        Una de las claves de `INTENTS`, o `UNKNOWN`.
    """
    if not message or not isinstance(message, str):
        return UNKNOWN

    # Regla 3: Ignorar líneas citadas (las que comienzan con '>')
    lines = [
        line.strip()
        for line in message.splitlines()
        if not line.strip().startswith(">")
    ]
    raw_unquoted = " ".join(lines)

    # Regla 1: Normalización centralizada
    normalized_message = normalize_text(raw_unquoted)

    # Regla 4 y 6: Longitud mínima
    if len(normalized_message) < MIN_LENGTH:
        return UNKNOWN

    # Regla 2: Seleccionar la intención con el patrón coincidente más largo
    best_intent = UNKNOWN
    best_pattern_len = -1

    for intent, data in INTENTS.items():
        for pattern in data.get("patterns", []):
            norm_pattern = normalize_text(pattern)
            # Verificación de subsecuencia de palabras/patrón completo
            if norm_pattern in normalized_message:
                pattern_len = len(norm_pattern)
                if pattern_len > best_pattern_len:
                    best_pattern_len = pattern_len
                    best_intent = intent

    return best_intent


def specialist_for(intent: str) -> str | None:
    """Devuelve el agente especialista responsable de una intención."""
    entry = INTENTS.get(intent)
    return entry["specialist"] if entry else None
