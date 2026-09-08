# Notas de entrega Jesus David Ruiz Garcia

## Resumen
- Ejercicio 1 (Clasificador de intencion): Completado y pasado los test.
- Ejercicio 2 (Reporte de Cobertura): Completado con asincronia real, reutilización de singletons y 5 tests adicionales.


## Tiempo
- Hora de inicio 10:35 p.m. // 07 - Septiempre - 2026
- Hora de entrega:
- Horas por ejercicio: 
    - Ejercicio 1: ~35 min
    - Ejercicio 2: ~30 min

## Decisiones
### Decisiones de las que estoy más seguro
1. **Propagar `KeyError` ante un workspace inexistente (Ejercicio 2):** Se decidió conscientemente no devolver un diccionario vacío `{}` ni conteos en `0`. Un workspace inexistente es un error semántico/404 de la petición o configuración. Silenciarlo devolvería una métrica falsa a producto, sugiriendo que el cliente tiene un workspace configurado pero sin mensajes.
2. (Se completará con Ejercicios 5 y 6)
3. (Se completará con Ejercicio 6)

### Decisiones de las que estoy menos seguro
1. (Se completará con Ejercicios 4 y 6)
2. (Se completará con Ejercicio 3)

## Ejercicio 1 - reglas vs LLM
Una ventaja clave de las reglas es el determinismo estricto, la latencia despreciable (<1 ms) y el costo operativo cero sin riesgo de alucinaciones sintácticas. Su desventaja principal es la fragilidad semántica ante variaciones léxicas, faltas ortográficas complejas, ambigüedad contextual o intenciones implícitas no mapeadas. Cambiaría a un clasificador entrenado (como un encoder ligero tipo SetFit o un LLM pequeño destilado) cuando el catálogo de intenciones crezca más allá de 30 categorías o cuando la tasa de mensajes caídos en "desconocido" crezca en producción debido a que los usuarios formulan preguntas de forma conversacional, indirecta o con lenguaje coloquial variado.

## Uso de IA
- En general se esta utilizando IA para ayuda a la redacción.
- Ejercicio 1: Se utilizó Gemini para validar las reglas de normalización NFKD y el criterio del patrón más largo.
- Ejercicio 2: Se utilizó Gemini para estructurar la asincronía, los casos borde en `tests/test_intent_report.py` y la consulta a la base de datos respetando singletons. 


## Qué haría con una semana más
(Pendiente)