import asyncio
import httpx
from typing import Optional
from app.core.config import settings
from app.schemas.connection_status import ConnectionStatus


async def get_task__id(
    pings: int,
    service_id: int
) -> Optional[str]:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            f"{settings.CLIENTS_URL}{service_id}/ping/",
            headers={
                "Authorization": f"Api-Key {settings.WISPHUB_NET_KEY}"
            },
            json={
                "pings": pings
            }
        )
        
        if response.status_code != 202:
            return None

        try:
            response = response.json()
        except ValueError:
            return None
        
        task_id = response.get("task_id")
                
        if not task_id:
            return None
        
        return task_id
    
async def ping(task_id: str) -> ConnectionStatus:
    async with httpx.AsyncClient(timeout=10) as client:

        response = await client.get(
            f"{settings.TASKS_URL}{task_id}/",
            headers={
                "Authorization": f"Api-Key {settings.WISPHUB_NET_KEY}"
            }
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

    

