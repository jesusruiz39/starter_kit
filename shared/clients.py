"""
Clientes compartidos del pipeline.

En producción esto envuelve al SDK de la base de datos y al del almacenamiento
de objetos. Para esta prueba están reemplazados por dobles en memoria que leen
de `fixtures/`, para que puedas correr todo sin credenciales de ninguna nube.

La *forma* de la API es la misma que la real, y la regla de oro también:

    ⚠️  El cliente se crea UNA sola vez por proceso.
        Nunca instancies un cliente dentro de una función de herramienta.

`_INSTANTIATIONS` lleva la cuenta de cuántas veces se construyó cada cliente.
Los tests la usan para verificar que respetaste esa regla. No la modifiques.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"

# Contador de instanciaciones. Los tests lo leen. NO MODIFICAR.
_INSTANTIATIONS: dict[str, int] = {"db": 0, "storage": 0}


class Record:
    """Un registro devuelto por la base de datos."""

    def __init__(self, record_id: str, data: dict | None):
        self.id = record_id
        self._data = data

    def to_dict(self) -> dict:
        return dict(self._data) if self._data else {}

    @property
    def exists(self) -> bool:
        return self._data is not None


class TableRef:
    def __init__(self, rows: dict[str, dict], name: str):
        self._rows = rows
        self._name = name
        self._filters: list[tuple[str, object]] = []

    def where(self, field: str, value) -> "TableRef":
        clone = TableRef(self._rows, self._name)
        clone._filters = self._filters + [(field, value)]
        return clone

    def item(self, record_id: str) -> "ItemRef":
        return ItemRef(self._rows, record_id)

    async def get(self) -> list[Record]:
        await asyncio.sleep(0)  # simula la latencia de red
        out = [
            Record(rid, data)
            for rid, data in self._rows.items()
            if all(data.get(f) == v for f, v in self._filters)
        ]
        logger.debug("db: get %s -> %d filas", self._name, len(out))
        return out


class ItemRef:
    def __init__(self, rows: dict[str, dict], record_id: str):
        self._rows = rows
        self._id = record_id

    async def get(self) -> Record:
        await asyncio.sleep(0)
        return Record(self._id, self._rows.get(self._id))


class DatabaseClient:
    """Doble en memoria de la base de datos. API asíncrona."""

    def __init__(self, data: dict[str, dict] | None = None):
        _INSTANTIATIONS["db"] += 1
        if data is None:
            data = json.loads((FIXTURES / "db.json").read_text(encoding="utf-8"))
        self._data = data
        logger.info("DatabaseClient instanciado (total: %d)", _INSTANTIATIONS["db"])

    def table(self, name: str) -> TableRef:
        return TableRef(self._data.get(name, {}), name)


class StorageClient:
    """Doble en memoria del almacenamiento de mensajes por workspace."""

    def __init__(self, data: dict[str, list[str]] | None = None):
        _INSTANTIATIONS["storage"] += 1
        if data is None:
            data = json.loads((FIXTURES / "storage.json").read_text(encoding="utf-8"))
        self._data = data

    async def list_messages(self, workspace_id: str) -> list[str]:
        """Devuelve los mensajes de usuario de un workspace.

        Raises:
            KeyError: si el workspace no existe.
        """
        await asyncio.sleep(0)
        if workspace_id not in self._data:
            raise KeyError(f"workspace no encontrado: {workspace_id}")
        return list(self._data[workspace_id])


# ---------------------------------------------------------------------------
# Singletons. Este es el patrón que debes reutilizar en tus herramientas.
# ---------------------------------------------------------------------------
_db: DatabaseClient | None = None
_storage: StorageClient | None = None


def get_db_client() -> DatabaseClient:
    global _db
    if _db is None:
        _db = DatabaseClient()
    return _db


def get_storage_client() -> StorageClient:
    global _storage
    if _storage is None:
        _storage = StorageClient()
    return _storage


def _reset_clients_for_tests() -> None:
    """Solo para uso de la suite de tests."""
    global _db, _storage
    _db = None
    _storage = None
    _INSTANTIATIONS["db"] = 0
    _INSTANTIATIONS["storage"] = 0
