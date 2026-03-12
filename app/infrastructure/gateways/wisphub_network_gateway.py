import asyncio
import httpx
from typing import Optional

from app.domain.interfaces.network_gateway import INetworkGateway
from app.domain.models.connection_status import ConnectionStatus


class WispHubNetworkGateway(INetworkGateway):
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Api-Key {api_key}"}

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
                return ConnectionStatus.error

            try:
                data = response.json()
            except ValueError:
                return ConnectionStatus.error

            task = data.get("task")
            if not task:
                return ConnectionStatus.error

            status = task.get("status")

            if status == "PENDING":
                return ConnectionStatus.pending

            if status != "SUCCESS":
                return ConnectionStatus.error

            results = task.get("result")

            if not isinstance(results, list) or not results:
                return ConnectionStatus.error

            total_sent = 0
            total_received = 0

            for item in results:
                for key, value in item.items():
                    if key.startswith("ping-") and key != "ping-exitoso":
                        total_sent += int(value.get("sent", 0))
                        total_received += int(value.get("received", 0))

            if total_sent == 0:
                return ConnectionStatus.error

            loss_ratio = total_received / total_sent

            if total_received == 0:
                return ConnectionStatus.no_internet
            elif loss_ratio < 0.8:
                return ConnectionStatus.intermittent
            else:
                return ConnectionStatus.stable

        return ConnectionStatus.error

    async def reboot_antenna(self, service_id: int) -> bool:
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/clientes/{service_id}/reiniciar-antena/",
                    headers=self.headers,
                )
                return response.status_code in [200, 202, 204]
            except httpx.RequestError:
                return False

    async def check_connection(self, antenna_ip: str, router_ip: str) -> bool:
        return True
