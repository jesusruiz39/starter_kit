# Notas de entrega Jesus David Ruiz Garcia

## Resumen
- Ejercicio 1 (Clasificador de intencion): Completado y pasado los test.
- Ejercicio 2 (Reporte de Cobertura): Completado con asincronia real, reutilización de singletons y 5 tests adicionales.
- Ejercicio 6 (La consola del asistente): Pipeline `consultar()` implementado y desacoplado, interfaz web nativa clara que prioriza la abstención activa con códigos visuales marcados, y suite de tests completa pasando (5 tests en total).


## Tiempo
- Hora de inicio 10:35 p.m. // 07 - Septiempre - 2026
- Hora de entrega:
- Horas por ejercicio: 
    - Ejercicio 1: ~35 min
    - Ejercicio 2: ~30 min
    - Ejercicio 6: ~45 min

## Decisiones
### Decisiones de las que estoy más seguro
1. **Propagar `KeyError` ante un workspace inexistente (Ejercicio 2):** Se decidió conscientemente no devolver un diccionario vacío `{}` ni conteos en `0`. Un workspace inexistente es un error semántico/404 de la petición o configuración. Silenciarlo devolvería una métrica falsa a producto, sugiriendo que el cliente tiene un workspace configurado pero sin mensajes.
2. **Abstención activa estricta en el pipeline (Ejercicio 6):** Forzar `respuesta: None` cuando el puntaje de similitud queda por debajo de `UMBRAL_MINIMO` o no hay fragmentos. Es el mecanismo fundamental para evitar alucinaciones en producción: el asistente prefiere callarse antes que entregar información sin sustento.
3. (Se completará con Ejercicio 5)

### Decisiones de las que estoy menos seguro
1. **Umbrales estáticos fijos de similitud (0.55 y 0.75 en Ejercicio 6):** Los puntajes léxicos basados en IDF y solapamiento varían drásticamente según la longitud de la pregunta del usuario. Una pregunta muy concisa puede generar un puntaje artificialmente bajo a pesar de ser relevante. En producción requeriría umbrales dinámicos calibrados contra un dataset de evaluación o un re-ranker.
2. (Se completará con Ejercicio 3 o 4)

## Ejercicio 1 - reglas vs LLM
Una ventaja clave de las reglas es el determinismo estricto, la latencia despreciable (<1 ms) y el costo operativo cero sin riesgo de alucinaciones sintácticas. Su desventaja principal es la fragilidad semántica ante variaciones léxicas, faltas ortográficas complejas, ambigüedad contextual o intenciones implícitas no mapeadas. Cambiaría a un clasificador entrenado (como un encoder ligero tipo SetFit o un LLM pequeño destilado) cuando el catálogo de intenciones crezca más allá de 30 categorías o cuando la tasa de mensajes caídos en "desconocido" crezca en producción debido a que los usuarios formulan preguntas de forma conversacional, indirecta o con lenguaje coloquial variado.

## Ejercicio 6 - cómo mejoraría el recuperador
El recuperador léxico actual falla con sinónimos ("restablecer contraseña" vs "recuperar acceso") porque indexa y pondera términos exactos mediante stems de 5 caracteres. Para resolverlo, implementaría una arquitectura híbrida: embeddings densos multilingües (como text-embedding-3-small o BAAI/bge-m3) combinados con BM25 mediante Reciprocal Rank Fusion (RRF). El vector captura proximidad semántica e intenciones equivalentes, mientras que BM25 preserva precisión en códigos o nombres de planes. El costo asociado implica latencia extra durante la ingestión (cálculo de embeddings asíncrono), consumo de memoria RAM o costo de base de datos vectorial (ej. pgvector/Qdrant) y costo monetario por token al generar representaciones vectoriales.

## Captura de Consola (Plan Enterprise)
![Captura Enterprise](captura_enterprise.jpeg)

## Uso de IA
- En general se esta utilizando IA para ayuda a la redacción.
- Ejercicio 1: Se utilizó Gemini para validar las reglas de normalización NFKD y el criterio del patrón más largo.
- Ejercicio 2: Se utilizó Gemini para estructurar la asincronía, los casos borde en `tests/test_intent_report.py` y la consulta a la base de datos respetando singletons. 
- Ejercicio 6: Se utilizó Gemini para desacoplar `consultar()` del servidor HTTP, depurar la llamada a `search()`, implementar los estilos de la interfaz web nativa y redactar los tests de abstención y casos dudosos.


## Qué haría con una semana más
(Pendiente)