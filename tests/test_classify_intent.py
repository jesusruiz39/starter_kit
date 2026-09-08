"""
Tests del EJERCICIO 1. Estos te los damos hechos: son el contrato.
NO los modifiques. Tu implementación debe pasarlos tal como están.

Si crees que un test está mal, no lo edites: anótalo en tu NOTAS.md y
explícalo. (Ninguno lo está, pero queremos ver qué haces con esa duda.)
"""

import pytest

from config.intents import UNKNOWN, classify_intent


@pytest.mark.parametrize(
    "message,expected",
    [
        # básicos
        ("Me llegó una factura duplicada este mes", "facturacion"),
        ("La app no funciona desde ayer", "soporte_tecnico"),
        ("Necesito agregar un usuario nuevo al equipo", "cuenta"),
        # mayúsculas, signos y separadores
        ("QUIERO UN REEMBOLSO", "facturacion"),
        ("olvide-mi-contrasena", "cuenta"),
        ("¿Cómo    cambiar   correo?", "cuenta"),
        # acentos y ñ
        ("Olvidé mi contraseña", "cuenta"),
        ("No puedo iniciar sesión", "cuenta"),
        # el patrón más largo gana
        ("No puedo iniciar sesión, me da error", "cuenta"),
        ("cargo duplicado en mi tarjeta", "facturacion"),
        ("La factura no carga en el portal", "soporte_tecnico"),
        # texto citado: se ignora
        ("> el error persiste\nGracias, ya hice el pago", "facturacion"),
        ("> no funciona", UNKNOWN),
        # bordes
        ("Hola", UNKNOWN),
        ("ok", UNKNOWN),
        ("   ", UNKNOWN),
        ("", UNKNOWN),
        (None, UNKNOWN),
    ],
)
def test_classify_intent(message, expected):
    assert classify_intent(message) == expected
