"""
Servicio WispHub para diagnóstico de red (ping).

Combina acceso HTTP a la API de WispHub con la lógica de negocio:
inicio de tarea de ping y evaluación del resultado por ratio de pérdida.
"""

import ipaddress
import logging
from typing import Optional

import httpx

from app.schemas.connection_status import ConnectionStatus, PingResultResponse

logger = logging.getLogger(__name__)


def is_private_ip(ip_str: str) -> bool:
    if ":" in ip_str and "." not in ip_str:
        return True  # Es una dirección MAC
    try:
        ip = ipaddress.ip_address(ip_str)
        if ip.is_private:
            return True
        if isinstance(ip, ipaddress.IPv4Address) and str(ip).startswith("172."):
            return True
        return False
    except ValueError:
        return False


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

    async def _poll_ping(self, task_id: str) -> PingResultResponse:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.base_url}/api/tasks/{task_id}/",
                headers=self.headers,
            )

        if response.status_code != 200:
            logger.warning(
                "_poll_ping: HTTP %s for task_id=%s", response.status_code, task_id
            )
            return PingResultResponse(status=ConnectionStatus.error, message="Ping API error.")

        try:
            data = response.json()
        except ValueError:
            logger.warning("_poll_ping: invalid JSON for task_id=%s", task_id)
            return PingResultResponse(status=ConnectionStatus.error, message="Invalid JSON response.")

        task = data.get("task")
        if not task:
            logger.warning(
                "_poll_ping: no 'task' key in response for task_id=%s — raw: %s",
                task_id,
                data,
            )
            return PingResultResponse(status=ConnectionStatus.error, message="Invalid task format.")

        status = task.get("status")
        logger.info(
            "_poll_ping: task_id=%s status=%s result=%s",
            task_id,
            status,
            task.get("result"),
        )

        if status in ("PENDING", "PROCESS"):
            return PingResultResponse(status=ConnectionStatus.pending, message="Ping task is still processing.")

        if status != "SUCCESS":
            logger.warning(
                "_poll_ping: unexpected status=%s for task_id=%s", status, task_id
            )
            return PingResultResponse(status=ConnectionStatus.error, message=f"Unexpected task status: {status}.")

        results = task.get("result")
        if not isinstance(results, list) or not results:
            return PingResultResponse(status=ConnectionStatus.error, message="No ping result data.")

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
            return PingResultResponse(status=ConnectionStatus.error, message="MikroTik interface error.")

        # Sin ningún ping válido
        if not dict_pings:
            return PingResultResponse(status=ConnectionStatus.error, message="No valid ping items found.")

        private_pings = [p for p in dict_pings if "host" in p and is_private_ip(p["host"])]
        public_pings = [p for p in dict_pings if "host" in p and not is_private_ip(p["host"])]

        # Determine if private or public IPs answered
        def has_active_response(pings_list):
            for p in pings_list:
                if p.get("received", "0") != "0":
                    return True
                if p.get("status") == "host unreachable":
                    return True
            return False

        if has_active_response(private_pings):
            return PingResultResponse(
                status=ConnectionStatus.stable,
                message="Client device has an active connection."
            )

        if has_active_response(public_pings):
            return PingResultResponse(
                status=ConnectionStatus.antenna_only,
                message="Customer device is unreachable, but the main antenna has connection."
            )

        return PingResultResponse(
            status=ConnectionStatus.no_internet,
            message="No connection to the customer device or the antenna."
        )

    # ------------------------------------------------------------------
    # Business logic
    # ------------------------------------------------------------------

    async def start_ping(self, service_id: int, pings: int) -> Optional[str]:
        return await self._get_task_id(pings=pings, service_id=service_id)

    async def get_ping_result(self, task_id: str) -> PingResultResponse:
        return await self._poll_ping(task_id)
