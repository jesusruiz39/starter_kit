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

from config.intents import classify_intent, specialist_for
from shared.retriever import search

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("consola")

PUERTO = 8000

# Umbrales de decisión. Son un punto de partida, no una verdad revelada:
# si los cambias, di por qué en NOTAS.md.
UMBRAL_MINIMO = 0.55   # por debajo de esto no hay evidencia suficiente
UMBRAL_ALTO = 0.75     # por debajo de esto la respuesta va marcada como dudosa


# ---------------------------------------------------------------------------
# PIPELINE: consultar()
# ---------------------------------------------------------------------------

async def consultar(pregunta: str, workspace_id: str = "acme") -> dict:
    """Ejecuta el pipeline completo sobre una pregunta y devuelve qué pasó.

    Esta función es el corazón del ejercicio y debe ser **testeable sin
    levantar el servidor**: recibe texto, devuelve un diccionario.
    """
    # 1. Clasificar intención y especialista
    intencion = classify_intent(pregunta)
    especialista = specialist_for(intencion)

    # 2. Recuperar fragmentos relevantes (search recibe query y top_k int)
    try:
        raw_fragmentos = await search(pregunta)
    except Exception as exc:
        logger.warning("Error en search: %s", exc)
        raw_fragmentos = []

    # Normalizar campos de los fragmentos a la forma requerida
    fragmentos = []
    for f in raw_fragmentos:
        fragmentos.append({
            "source_id": f.get("source_id") or f.get("id"),
            "titulo": f.get("titulo", "Sin título"),
            "chunk": f.get("chunk", 0),
            "texto": f.get("texto", ""),
            "similitud": round(float(f.get("similitud", 0.0)), 2),
        })

    # 3. Evaluar veredicto según el mejor puntaje de similitud
    mejor_similitud = fragmentos[0]["similitud"] if fragmentos else 0.0

    if not fragmentos or mejor_similitud < UMBRAL_MINIMO:
        veredicto = "SIN_EVIDENCIA"
        motivo = (
            f"Similitud {mejor_similitud:.2f}, por debajo del mínimo de {UMBRAL_MINIMO:.2f}"
            if fragmentos
            else f"No se recuperaron fragmentos relevantes (mínimo requerido: {UMBRAL_MINIMO:.2f})"
        )
        respuesta = None
    elif mejor_similitud < UMBRAL_ALTO:
        veredicto = "DUDOSO"
        motivo = (
            f"Similitud {mejor_similitud:.2f} supera el mínimo {UMBRAL_MINIMO:.2f} "
            f"pero no alcanza el umbral alto de {UMBRAL_ALTO:.2f} (requiere revisión)"
        )
        respuesta = fragmentos[0]["texto"]
    else:
        veredicto = "APROBADO"
        motivo = (
            f"Similitud {mejor_similitud:.2f} alcanza o supera el umbral alto de {UMBRAL_ALTO:.2f}"
        )
        respuesta = fragmentos[0]["texto"]

    return {
        "pregunta": pregunta,
        "workspace": workspace_id,
        "intencion": intencion,
        "especialista": especialista,
        "fragmentos": fragmentos,
        "veredicto": veredicto,
        "motivo": motivo,
        "respuesta": respuesta,
    }

# ---------------------------------------------------------------------------
# LA PÁGINA
# ---------------------------------------------------------------------------

PAGINA = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Consola del Asistente</title>
  <style>
    :root {
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --text: #0f172a;
      --muted: #475569;
      --border: #cbd5e1;
      --approved: #15803d;
      --approved-bg: #f0fdf4;
      --approved-border: #86efac;
      --doubtful: #b45309;
      --doubtful-bg: #fffbeb;
      --doubtful-border: #fcd34d;
      --no-evidence: #b91c1c;
      --no-evidence-bg: #fef2f2;
      --no-evidence-border: #fca5a5;
    }
    body {
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      max-width: 900px;
      margin: 30px auto;
      padding: 0 20px;
      color: var(--text);
      background: var(--bg);
      line-height: 1.5;
    }
    h1 { margin-bottom: 20px; font-size: 26px; }
    .form-box {
      background: var(--card-bg);
      padding: 20px;
      border-radius: 8px;
      border: 1px solid var(--border);
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .input-row { display: flex; gap: 10px; margin-bottom: 12px; }
    input[type=text] {
      flex: 1;
      padding: 12px;
      font-size: 15px;
      border: 1px solid var(--border);
      border-radius: 6px;
    }
    select, button {
      padding: 10px 16px;
      font-size: 15px;
      border-radius: 6px;
      border: 1px solid var(--border);
    }
    button {
      background: #2563eb;
      color: white;
      border: none;
      font-weight: 600;
      cursor: pointer;
    }
    button:hover { background: #1d4ed8; }
    .status-badge {
      display: inline-block;
      padding: 6px 14px;
      font-weight: 800;
      letter-spacing: 0.5px;
      border-radius: 20px;
      font-size: 14px;
      text-transform: uppercase;
      margin-bottom: 10px;
    }
    .badge-APROBADO { background: var(--approved-bg); color: var(--approved); border: 2px solid var(--approved-border); }
    .badge-DUDOSO { background: var(--doubtful-bg); color: var(--doubtful); border: 2px solid var(--doubtful-border); }
    .badge-SIN_EVIDENCIA { background: var(--no-evidence-bg); color: var(--no-evidence); border: 2px solid var(--no-evidence-border); }
    
    .panel {
      margin-top: 24px;
      border-radius: 8px;
      padding: 20px;
      background: var(--card-bg);
      border: 1px solid var(--border);
    }
    .panel-APROBADO { border-left: 8px solid var(--approved); }
    .panel-DUDOSO { border-left: 8px solid var(--doubtful); }
    .panel-SIN_EVIDENCIA { border-left: 8px solid var(--no-evidence); }

    .pipeline-meta {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin: 15px 0;
      padding: 12px;
      background: #f1f5f9;
      border-radius: 6px;
      font-size: 14px;
    }
    .pipeline-meta span { display: block; color: var(--muted); font-size: 12px; text-transform: uppercase; font-weight: bold; }
    .response-card {
      margin-top: 15px;
      padding: 16px;
      border-radius: 6px;
      font-size: 16px;
    }
    .response-APROBADO { background: #f0fdf4; border: 1px solid #bbf7d0; }
    .response-DUDOSO { background: #fffbeb; border: 1px solid #fef08a; }
    .response-SIN_EVIDENCIA { background: #fef2f2; border: 1px solid #fecaca; color: #991b1b; font-weight: 500; }
    
    .chunks-list { margin-top: 20px; }
    .chunk-item {
      background: #f8fafc;
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 12px;
      margin-bottom: 10px;
      font-size: 14px;
    }
    .chunk-header {
      display: flex;
      justify-content: space-between;
      font-weight: 600;
      color: var(--muted);
      margin-bottom: 6px;
      font-size: 13px;
    }
    .sim-score {
      background: #e2e8f0;
      padding: 2px 8px;
      border-radius: 4px;
      color: #0f172a;
    }
  </style>
</head>
<body>
  <h1>Consola del Asistente (SaaS IA)</h1>

  <div class="form-box">
    <form id="f">
      <div class="input-row">
        <input type="text" id="q" placeholder="Escribe una pregunta para consultar al asistente…" autofocus required>
        <button type="submit">Preguntar</button>
      </div>
      <div>
        <label for="ws" style="font-size: 14px; font-weight: 600;">Workspace:</label>
        <select id="ws">
          <option value="acme">acme</option>
          <option value="globex">globex</option>
          <option value="initech">initech</option>
        </select>
      </div>
    </form>
  </div>

  <div id="out" style="margin-top: 20px;">
    <p style="color: var(--muted);">Realiza una consulta para evaluar el comportamiento del pipeline.</p>
  </div>

<script>
document.getElementById('f').onsubmit = async (e) => {
  e.preventDefault();
  const q = document.getElementById('q').value;
  const ws = document.getElementById('ws').value;
  const out = document.getElementById('out');
  out.innerHTML = '<p>Procesando consulta en el pipeline…</p>';
  try {
    const r = await fetch(`/api/consulta?q=${encodeURIComponent(q)}&ws=${ws}`);
    const data = await r.json();

    const veredictoClass = data.veredicto;
    let respuestaHtml = '';

    if (data.veredicto === 'SIN_EVIDENCIA') {
      respuestaHtml = `
        <div class="response-card response-SIN_EVIDENCIA">
          <strong>ABSTENCIÓN ACTIVA (Sin respuesta):</strong><br>
          El asistente determinó que no hay evidencia suficiente en el corpus del workspace para responder con certeza. Se prefirió abstenerse a formular una respuesta infundada.
        </div>`;
    } else if (data.veredicto === 'DUDOSO') {
      respuestaHtml = `
        <div class="response-card response-DUDOSO">
          <strong>RESPUESTA PROVISIONAL (Marcada para revisión manual):</strong><br>
          ${escapeHtml(data.respuesta)}
        </div>`;
    } else {
      respuestaHtml = `
        <div class="response-card response-APROBADO">
          <strong>RESPUESTA SUSTENTADA:</strong><br>
          ${escapeHtml(data.respuesta)}
        </div>`;
    }

    let chunksHtml = data.fragmentos.length === 0
      ? '<p style="color: var(--muted); font-style: italic;">No se recuperaron fragmentos del almacenamiento.</p>'
      : data.fragmentos.map((f, i) => `
          <div class="chunk-item">
            <div class="chunk-header">
              <span>#${i+1} [${escapeHtml(f.source_id || 'sin-id')}] ${escapeHtml(f.titulo)} (chunk: ${f.chunk})</span>
              <span class="sim-score">Similitud: <strong>${f.similitud}</strong></span>
            </div>
            <div>${escapeHtml(f.texto)}</div>
          </div>
        `).join('');

    out.innerHTML = `
      <div class="panel panel-${veredictoClass}">
        <span class="status-badge badge-${veredictoClass}">${data.veredicto}</span>
        <div style="font-weight: 600; margin-bottom: 8px;">Motivo: ${escapeHtml(data.motivo)}</div>

        <div class="pipeline-meta">
          <div><span>Intención detectada</span><strong>${escapeHtml(data.intencion)}</strong></div>
          <div><span>Especialista asignado</span><strong>${escapeHtml(data.especialista || 'Ninguno')}</strong></div>
          <div><span>Workspace</span><strong>${escapeHtml(data.workspace)}</strong></div>
          <div><span>Fragmentos evaluados</span><strong>${data.fragmentos.length}</strong></div>
        </div>

        ${respuestaHtml}

        <div class="chunks-list">
          <h3 style="font-size: 16px; margin-bottom: 8px;">Fragmentos recuperados y similitud:</h3>
          ${chunksHtml}
        </div>
      </div>
    `;
  } catch (err) {
    out.innerHTML = `<div class="response-card response-SIN_EVIDENCIA">Error al ejecutar la consulta: ${escapeHtml(err.message || err)}</div>`;
  }
};

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
</script>
</body></html>
"""


# ---------------------------------------------------------------------------
# SERVIDOR
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