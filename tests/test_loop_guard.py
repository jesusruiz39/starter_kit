"""
Tests del EJERCICIO 5.

Aquí no te damos nada hecho a propósito: queremos ver qué casos se te ocurren.
Escribe la suite completa. Como mínimo debe cubrir:

  - se permiten hasta MAX_CALLS llamadas
  - la siguiente levanta ToolLoopError
  - el mensaje de error contiene agente, sesión y conteo
  - los conteos no se cruzan entre agentes
  - los conteos no se cruzan entre sesiones
  - reset() limpia una sesión y no afecta a las demás
  - snapshot() refleja los conteos actuales
"""
"""
Tests del EJERCICIO 5.
"""

import pytest

from tools.loop_guard import MAX_CALLS, LoopGuard, ToolLoopError


def test_permite_hasta_max_calls_llamadas():
    guard = LoopGuard(max_calls=3)
    session_id = "session-123"
    agent_name = "retriever_agent"

    assert guard.record(session_id, agent_name) == 1
    assert guard.record(session_id, agent_name) == 2
    assert guard.record(session_id, agent_name) == 3


def test_llamada_excedente_levanta_tool_loop_error():
    guard = LoopGuard(max_calls=MAX_CALLS)
    session_id = "session-test"
    agent = "billing_agent"

    for _ in range(MAX_CALLS):
        guard.record(session_id, agent)

    with pytest.raises(ToolLoopError):
        guard.record(session_id, agent)


def test_mensaje_de_error_contiene_agente_sesion_y_conteo():
    guard = LoopGuard(max_calls=2)
    session_id = "sess-alpha-9"
    agent = "support_agent"

    guard.record(session_id, agent)
    guard.record(session_id, agent)

    with pytest.raises(ToolLoopError) as exc_info:
        guard.record(session_id, agent)

    error_msg = str(exc_info.value)
    assert agent in error_msg, "El mensaje debe contener el nombre del agente"
    assert session_id in error_msg, "El mensaje debe contener el id de sesión"
    assert "3" in error_msg, "El mensaje debe contener el conteo exacto de la llamada"


def test_conteos_no_se_cruzan_entre_agentes_en_misma_sesion():
    guard = LoopGuard(max_calls=2)
    session = "sess-shared"

    assert guard.record(session, "classifier") == 1
    assert guard.record(session, "classifier") == 2

    # Otro agente en la misma sesión debe empezar en 1 sin verse afectado
    assert guard.record(session, "retriever") == 1
    assert guard.record(session, "retriever") == 2


def test_conteos_no_se_cruzan_entre_sesiones_distintas():
    guard = LoopGuard(max_calls=2)
    agent = "verifier"

    assert guard.record("session-A", agent) == 1
    assert guard.record("session-A", agent) == 2

    # Misma agente en sesión distinta empieza desde 1
    assert guard.record("session-B", agent) == 1


def test_reset_limpia_sesion_y_no_afecta_a_las_demas():
    guard = LoopGuard(max_calls=3)
    guard.record("session-1", "agent-x")
    guard.record("session-1", "agent-x")
    guard.record("session-2", "agent-x")

    guard.reset("session-1")

    # Sesión 1 reseteada empieza de nuevo en 1
    assert guard.snapshot("session-1") == {}
    assert guard.record("session-1", "agent-x") == 1

    # Sesión 2 preserva su conteo previo de 1
    assert guard.snapshot("session-2") == {"agent-x": 1}


def test_snapshot_refleja_conteos_actuales_sin_mutar_estado():
    guard = LoopGuard(max_calls=5)
    guard.record("session-k", "agent-a")
    guard.record("session-k", "agent-b")
    guard.record("session-k", "agent-b")

    snap = guard.snapshot("session-k")
    assert snap == {"agent-a": 1, "agent-b": 2}

    # Modificar el snapshot devuelto no debe corromper el estado interno
    snap["agent-a"] = 99
    assert guard.snapshot("session-k")["agent-a"] == 1