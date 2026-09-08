"""
Consola del Asistente — EJERCICIO 6.

Arranca así:

    python app.py            # http://localhost:8000

El servidor y el esqueleto de la página ya funcionan: si lo corres ahora mismo
verás la página, escribirás una pregunta y te devolverá un error porque
`consultar()` todavía no está implementada. Eso es lo que tú construyes.

NO agregues dependencias. Todo esto sale de la librería estándar a propósito:
nada de Flask, FastAPI, React ni CSS externo. Feo pero claro está bien —
no evaluamos diseño gráfico, evaluamos que se entienda lo que pasó.
"""

from __future__ import annotations

import asyncio
import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("consola")

PUERTO = 8000

# Umbrales de decisión. Son un punto de partida, no una verdad revelada:
# si los cambias, di por qué en NOTAS.md.
UMBRAL_MINIMO = 0.55   # por debajo de esto no hay evidencia suficiente
UMBRAL_ALTO = 0.75     # por debajo de esto la respuesta va marcada como dudosa


# ---------------------------------------------------------------------------
# LO QUE TIENES QUE IMPLEMENTAR
# ---------------------------------------------------------------------------

async def consultar(pregunta: str, workspace_id: str = "acme") -> dict:
    """Ejecuta el pipeline completo sobre una pregunta y devuelve qué pasó.

    Esta función es el corazón del ejercicio y debe ser **testeable sin
    levantar el servidor**: recibe texto, devuelve un diccionario.

    Pasos:

    1. **Clasificar** la intención con `config.intents.classify_intent`.
    2. **Recuperar** fragmentos con `shared.retriever.search`.
    3. **Decidir** el veredicto según el mejor puntaje de similitud:
       - `SIN_EVIDENCIA` si no hay fragmentos o el mejor queda por debajo de
         `UMBRAL_MINIMO`. En este caso **no se responde**: `respuesta` es
         `None`. Este camino es el más importante de los tres.
       - `DUDOSO` si el mejor está entre `UMBRAL_MINIMO` y `UMBRAL_ALTO`.
         Se responde, pero marcado para revisión.
       - `APROBADO` si el mejor llega a `UMBRAL_ALTO` o más.
    4. **Redactar**: en esta prueba no hay modelo de lenguaje ni llamadas a
       ninguna API. La "respuesta" es el texto literal del mejor fragmento.
       Así se garantiza que nada de lo que muestra la consola esté inventado.

    Devuelve exactamente esta forma (los tests y la página dependen de ella):

        {
          "pregunta":    "¿Cuántos días de garantía tiene el plan Pro?",
          "workspace":   "acme",
          "intencion":   "facturacion",
          "especialista": "billing_agent",     # o None si la intención es desconocida
          "fragmentos":  [ {source_id, titulo, chunk, texto, similitud}, ... ],
          "veredicto":   "APROBADO" | "DUDOSO" | "SIN_EVIDENCIA",
          "motivo":      "Similitud 0.37, por debajo del mínimo de 0.55",
          "respuesta":   "El plan Pro incluye…"   # None si SIN_EVIDENCIA
        }

    El `motivo` lo lee un humano cuando algo sale raro: que diga números.
    """
    raise NotImplementedError("EJERCICIO 6")


# ---------------------------------------------------------------------------
# LA PÁGINA
#
# Esto es un esqueleto que funciona pero no sirve de mucho: vuelca el JSON en
# crudo. Tu trabajo es que un humano entienda de un vistazo qué hizo el
# asistente y por qué. Como mínimo debe verse:
#
#   - la intención detectada
#   - los fragmentos recuperados, cada uno con su puntaje de similitud
#   - el veredicto, visualmente distinto en los tres casos
#   - la respuesta final, o el aviso de que no hay evidencia suficiente
#
# Debe quedar imposible confundir "esto está sustentado" con "esto no lo sé".
# ---------------------------------------------------------------------------

PAGINA = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>Consola del Asistente</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 820px; margin: 40px auto;
         padding: 0 20px; color: #1a2330; }
  input[type=text] { width: 100%; padding: 10px; font-size: 16px; }
  button { padding: 10px 18px; font-size: 15px; cursor: pointer; }
  pre { background: #f2f4f7; padding: 14px; overflow-x: auto; white-space: pre-wrap; }
</style>
</head><body>
  <h1>Consola del Asistente</h1>

  <form id="f">
    <input type="text" id="q" placeholder="Escribe una pregunta…" autofocus>
    <p>
      <select id="ws">
        <option value="acme">acme</option>
        <option value="globex">globex</option>
        <option value="initech">initech</option>
      </select>
      <button type="submit">Preguntar</button>
    </p>
  </form>

  <!-- TODO: reemplaza este volcado por algo legible -->
  <pre id="out">Escribe una pregunta para empezar.</pre>

<script>
document.getElementById('f').onsubmit = async (e) => {
  e.preventDefault();
  const q = document.getElementById('q').value;
  const ws = document.getElementById('ws').value;
  const out = document.getElementById('out');
  out.textContent = 'Consultando…';
  try {
    const r = await fetch(`/api/consulta?q=${encodeURIComponent(q)}&ws=${ws}`);
    const data = await r.json();
    out.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    out.textContent = 'Error: ' + err;
  }
};
</script>
</body></html>
"""


# ---------------------------------------------------------------------------
# SERVIDOR — ya funciona. Puedes tocarlo si lo necesitas, pero no hace falta.
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):

    def _send(self, code, body, content_type):
        payload = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        url = urlparse(self.path)

        if url.path in ("/", "/index.html"):
            return self._send(200, PAGINA, "text/html")

        if url.path == "/api/consulta":
            params = parse_qs(url.query)
            pregunta = (params.get("q") or [""])[0]
            workspace = (params.get("ws") or ["acme"])[0]
            try:
                data = asyncio.run(consultar(pregunta, workspace))
                return self._send(200, json.dumps(data, ensure_ascii=False), "application/json")
            except NotImplementedError as exc:
                return self._send(
                    501, json.dumps({"error": str(exc)}, ensure_ascii=False),
                    "application/json")
            except Exception:
                logger.exception("fallo al consultar %r", pregunta)
                return self._send(
                    500, json.dumps({"error": "error interno, revisa la consola"},
                                    ensure_ascii=False), "application/json")

        self._send(404, json.dumps({"error": "no encontrado"}), "application/json")

    def log_message(self, fmt, *args):
        logger.info("%s", fmt % args)


if __name__ == "__main__":
    print(f"\n  Consola del Asistente  →  http://localhost:{PUERTO}\n")
    HTTPServer(("127.0.0.1", PUERTO), Handler).serve_forever()
