# Starter kit — Prueba Técnica IA (Parte 2)

Esqueleto autocontenido de un asistente de IA sobre contenido propio de cada
cliente. **No necesitas credenciales de ninguna nube ni conexión a internet**:
la base de datos y el almacenamiento están reemplazados por dobles en memoria
que leen de `fixtures/`. La API que ves tiene la misma forma que una real.

## Puesta en marcha

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest                 # verás tests fallando: esa es tu lista de trabajo
python app.py          # http://localhost:8000 — la consola, todavía sin implementar
```

Las dos cosas fallan al arrancar. Es correcto: ese es el punto de partida.

Requiere Python 3.10 o superior.

## Mapa del repo

```
app.py                        Ejercicio 6 — la consola. El servidor ya funciona.
config/intents.py             Ejercicio 1 — catálogo y clasificación de intención
tools/intent_report_tool.py   Ejercicio 2 — reporte de cobertura por intención
tools/legacy_answers_tool.py  Ejercicio 3 — código con defectos
prompts/verificador_v1.md     Ejercicio 4 — prompt actual, a mejorar
tools/loop_guard.py           Ejercicio 5 — guardia anti-loop
shared/clients.py             Clientes (dobles). LÉELO ANTES DE EMPEZAR. No lo modifiques.
shared/retriever.py           Buscador de fragmentos. Te lo damos hecho. No lo modifiques.
fixtures/                     Datos de la base y del almacenamiento. No los modifiques.
tests/                        Algunos hechos, otros los escribes tú
```

## Reglas

- **No modifiques** `shared/clients.py`, `shared/retriever.py`, `fixtures/`,
  `pytest.ini` ni `tests/test_classify_intent.py`. Todo lo demás es tuyo.
- **No agregues dependencias.** `requirements.txt` no debe crecer.
- Puedes agregar archivos y módulos si lo necesitas.
- Puedes usar asistentes de IA. Debes declararlo en `NOTAS.md` y vas a tener que
  defender cada línea en la sesión de revisión.

El enunciado completo, con puntajes y entregables, está en `parte2_practica.md`.
