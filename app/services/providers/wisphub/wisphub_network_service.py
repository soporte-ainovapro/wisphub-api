"""
Servicio WispHub para diagnóstico de red (ping).

Combina acceso HTTP a la API de WispHub con la lógica de negocio:
inicio de tarea de ping y evaluación del resultado por ratio de pérdida.
"""

import logging
from typing import Optional

import httpx

from app.schemas.connection_status import ConnectionStatus

logger = logging.getLogger(__name__)


class WispHubNetworkService:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url
        self.headers = {"Authorization": f"Api-Key {api_key}"}

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    async def _get_task_id(self, pings: int, service_id: int) -> Optional[str]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.base_url}/api/clientes/{service_id}/ping/",
                headers=self.headers,
                json={"pings": pings},
            )

        if response.status_code != 202:
            return None

        try:
            data = response.json()
        except ValueError:
            return None

        task_id = data.get("task_id")
        return task_id if task_id else None

    async def _poll_ping(self, task_id: str) -> ConnectionStatus:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.base_url}/api/tasks/{task_id}/",
                headers=self.headers,
            )

        if response.status_code != 200:
            logger.warning(
                "_poll_ping: HTTP %s for task_id=%s", response.status_code, task_id
            )
            return ConnectionStatus.error

        try:
            data = response.json()
        except ValueError:
            logger.warning("_poll_ping: invalid JSON for task_id=%s", task_id)
            return ConnectionStatus.error

        task = data.get("task")
        if not task:
            logger.warning(
                "_poll_ping: no 'task' key in response for task_id=%s — raw: %s",
                task_id,
                data,
            )
            return ConnectionStatus.error

        status = task.get("status")
        logger.info(
            "_poll_ping: task_id=%s status=%s result=%s",
            task_id,
            status,
            task.get("result"),
        )

        if status in ("PENDING", "PROCESS"):
            return ConnectionStatus.pending

        if status != "SUCCESS":
            logger.warning(
                "_poll_ping: unexpected status=%s for task_id=%s", status, task_id
            )
            return ConnectionStatus.error

        results = task.get("result")
        if not isinstance(results, list) or not results:
            return ConnectionStatus.error

        # Separar ping items válidos (dict) de errores de MikroTik (string)
        all_ping_items = [
            v
            for item in results
            for k, v in item.items()
            if k.startswith("ping-") and k != "ping-exitoso"
        ]
        dict_pings = [v for v in all_ping_items if isinstance(v, dict)]
        string_pings = [v for v in all_ping_items if isinstance(v, str)]

        logger.info(
            "_poll_ping: task_id=%s dict_pings=%s string_pings=%d",
            task_id,
            [(p.get("host"), p.get("status"), p.get("received")) for p in dict_pings],
            len(string_pings),
        )

        # Todos son errores de MikroTik (interfaz inexistente / router inalcanzable)
        if string_pings and not dict_pings:
            return ConnectionStatus.error

        # Sin ningún ping válido
        if not dict_pings:
            return ConnectionStatus.error

        # Reply real: received >= 1 → el equipo respondió el ICMP
        if any(p.get("received", "0") != "0" for p in dict_pings):
            return ConnectionStatus.stable

        statuses = [p.get("status") for p in dict_pings]

        # Hay al menos un "host unreachable" (IP pública respondió) → firewall activo → conectado
        if "host unreachable" in statuses:
            return ConnectionStatus.stable

        # Todos son "timeout" sin ningún host unreachable → equipo sin ruta / offline
        return ConnectionStatus.no_internet

    # ------------------------------------------------------------------
    # Business logic
    # ------------------------------------------------------------------

    async def start_ping(self, service_id: int, pings: int) -> Optional[str]:
        return await self._get_task_id(pings=pings, service_id=service_id)

    async def get_ping_result(self, task_id: str) -> ConnectionStatus:
        return await self._poll_ping(task_id)
