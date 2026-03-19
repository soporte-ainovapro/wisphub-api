"""
Tests para WispHubNetworkService — basados en respuestas reales de WispHub.

Patrones observados en producción (100+ clientes):
  A) STABLE_FIREWALL : IP privada=timeout + IP pública=host unreachable
  B) STABLE_REPLY    : received="1", packet-loss="0", sin campo "status"
  C) NO_INTERNET     : todos timeout, sin IP pública, ping-exitoso="0 de N"
  D) ERROR_MIKROTIK  : todos los ping-N son strings de error
"""

import pytest
import respx
import httpx
from app.services.providers.wisphub.wisphub_network_service import (
    WispHubNetworkService,
)
from app.core.config import settings
from app.schemas.connection_status import ConnectionStatus

MOCK_PING_TASK_CREATED = {"task_id": "123-abc", "status": "PROCESS"}

# A) Cliente activo con firewall: IP privada=timeout, IP pública=host unreachable
MOCK_TASK_RESULT_STABLE_FIREWALL = {
    "task": {
        "status": "SUCCESS",
        "result": [
            {
                "ping-1": {
                    "status": "timeout",
                    "host": "172.16.12.60",
                    "received": "0",
                    "sent": "1",
                    "packet-loss": "100",
                    "seq": "0",
                }
            },
            {
                "ping-2": {
                    "status": "host unreachable",
                    "host": "181.78.239.202",
                    "received": "0",
                    "sent": "1",
                    "packet-loss": "100",
                    "seq": "0",
                    "time": "563ms",
                    "ttl": "64",
                    "size": "84",
                }
            },
            {
                "ping-3": {
                    "status": "timeout",
                    "host": "172.16.12.60",
                    "received": "0",
                    "sent": "1",
                    "packet-loss": "100",
                    "seq": "0",
                }
            },
            {
                "ping-4": {
                    "status": "host unreachable",
                    "host": "181.78.239.202",
                    "received": "0",
                    "sent": "1",
                    "packet-loss": "100",
                    "seq": "0",
                    "time": "617ms",
                    "ttl": "64",
                    "size": "84",
                }
            },
            {"ping-exitoso": "2 de 4"},
        ],
    }
}

# B) Cliente con reply real a IP privada (sin firewall)
MOCK_TASK_RESULT_STABLE_REPLY = {
    "task": {
        "status": "SUCCESS",
        "result": [
            {
                "ping-1": {
                    "received": "1",
                    "host": "172.16.12.25",
                    "sent": "1",
                    "packet-loss": "0",
                    "seq": "0",
                    "time": "1ms287us",
                    "ttl": "64",
                    "min-rtt": "1ms287us",
                    "max-rtt": "1ms287us",
                    "avg-rtt": "1ms287us",
                    "size": "56",
                }
            },
            {
                "ping-2": {
                    "received": "1",
                    "host": "172.16.12.25",
                    "sent": "1",
                    "packet-loss": "0",
                    "seq": "0",
                    "time": "1ms168us",
                    "ttl": "64",
                    "min-rtt": "1ms168us",
                    "max-rtt": "1ms168us",
                    "avg-rtt": "1ms168us",
                    "size": "56",
                }
            },
            {
                "ping-3": {
                    "received": "1",
                    "host": "172.16.12.25",
                    "sent": "1",
                    "packet-loss": "0",
                    "seq": "0",
                    "time": "1ms178us",
                    "ttl": "64",
                    "min-rtt": "1ms178us",
                    "max-rtt": "1ms178us",
                    "avg-rtt": "1ms178us",
                    "size": "56",
                }
            },
            {
                "ping-4": {
                    "received": "1",
                    "host": "172.16.12.25",
                    "sent": "1",
                    "packet-loss": "0",
                    "seq": "0",
                    "time": "1ms230us",
                    "ttl": "64",
                    "min-rtt": "1ms230us",
                    "max-rtt": "1ms230us",
                    "avg-rtt": "1ms230us",
                    "size": "56",
                }
            },
            {"ping-exitoso": "4 de 4"},
        ],
    }
}

# B2) Cliente con reply real a MAC (mismo patrón, host es dirección MAC)
MOCK_TASK_RESULT_STABLE_REPLY_MAC = {
    "task": {
        "status": "SUCCESS",
        "result": [
            {
                "ping-1": {
                    "received": "1",
                    "host": "DC:EF:80:2C:CA:31",
                    "sent": "1",
                    "packet-loss": "0",
                    "seq": "0",
                    "time": "5ms",
                    "min-rtt": "5ms",
                    "max-rtt": "5ms",
                    "avg-rtt": "5ms",
                }
            },
            {
                "ping-2": {
                    "received": "1",
                    "host": "DC:EF:80:2C:CA:31",
                    "sent": "1",
                    "packet-loss": "0",
                    "seq": "0",
                    "time": "5ms",
                    "min-rtt": "5ms",
                    "max-rtt": "5ms",
                    "avg-rtt": "5ms",
                }
            },
            {
                "ping-3": {
                    "received": "1",
                    "host": "DC:EF:80:2C:CA:31",
                    "sent": "1",
                    "packet-loss": "0",
                    "seq": "0",
                    "time": "5ms",
                    "min-rtt": "5ms",
                    "max-rtt": "5ms",
                    "avg-rtt": "5ms",
                }
            },
            {"ping-exitoso": "3 de 3"},
        ],
    }
}

# C) Sin internet: todos timeout a IP privada, sin IP pública, ping-exitoso="0 de N"
MOCK_TASK_RESULT_NO_INTERNET = {
    "task": {
        "status": "SUCCESS",
        "result": [
            {
                "ping-1": {
                    "status": "timeout",
                    "host": "172.16.122.32",
                    "received": "0",
                    "sent": "1",
                    "packet-loss": "100",
                    "seq": "0",
                }
            },
            {
                "ping-2": {
                    "status": "timeout",
                    "host": "172.16.122.32",
                    "received": "0",
                    "sent": "1",
                    "packet-loss": "100",
                    "seq": "0",
                }
            },
            {
                "ping-3": {
                    "status": "timeout",
                    "host": "172.16.122.32",
                    "received": "0",
                    "sent": "1",
                    "packet-loss": "100",
                    "seq": "0",
                }
            },
            {
                "ping-4": {
                    "status": "timeout",
                    "host": "172.16.122.32",
                    "received": "0",
                    "sent": "1",
                    "packet-loss": "100",
                    "seq": "0",
                }
            },
            {"ping-exitoso": "0 de 4"},
        ],
    }
}

# D) Error de MikroTik: todos los ping-N son strings de error
MOCK_TASK_RESULT_ERROR_MIKROTIK = {
    "task": {
        "status": "SUCCESS",
        "result": [
            {
                "ping-1": "('Error \"input does not match any value of interface\" executing command /ping =count=1 =interface=bridge 2 =address=172.16.254.5 .tag=2', 'input does not match any value of interface')"
            },
            {
                "ping-2": "('Error \"input does not match any value of interface\" executing command /ping =count=1 =interface=bridge 2 =address=172.16.254.5 .tag=2', 'input does not match any value of interface')"
            },
            {
                "ping-3": "('Error \"input does not match any value of interface\" executing command /ping =count=1 =interface=bridge 2 =address=172.16.254.5 .tag=2', 'input does not match any value of interface')"
            },
            {
                "ping-4": "('Error \"input does not match any value of interface\" executing command /ping =count=1 =interface=bridge 2 =address=172.16.254.5 .tag=2', 'input does not match any value of interface')"
            },
            {"ping-exitoso": "0 de 4"},
        ],
    }
}


def _make_gateway():
    return WispHubNetworkService(
        base_url=settings.WISPHUB_NET_HOST,
        api_key=settings.WISPHUB_NET_KEY,
    )


@pytest.mark.asyncio
@respx.mock
async def test_get_task_id_success():
    respx.post(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(202, json=MOCK_PING_TASK_CREATED)
    )

    gateway = _make_gateway()
    task_id = await gateway._get_task_id(4, 100)
    assert task_id == "123-abc"


@pytest.mark.asyncio
@respx.mock
async def test_get_task_id_failed():
    respx.post(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(400, json={})
    )

    gateway = _make_gateway()
    task_id = await gateway._get_task_id(4, 100)
    assert task_id is None


@pytest.mark.asyncio
@respx.mock
async def test_ping_stable_firewall():
    """IP privada=timeout + IP pública=host unreachable → equipo con firewall, conectado."""
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json=MOCK_TASK_RESULT_STABLE_FIREWALL)
    )

    gateway = _make_gateway()
    status = await gateway._poll_ping("123-abc")
    assert status == ConnectionStatus.stable


@pytest.mark.asyncio
@respx.mock
async def test_ping_stable_reply_ip():
    """received=1, packet-loss=0 en IP privada → reply real, conectado."""
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json=MOCK_TASK_RESULT_STABLE_REPLY)
    )

    gateway = _make_gateway()
    status = await gateway._poll_ping("123-abc")
    assert status == ConnectionStatus.stable


@pytest.mark.asyncio
@respx.mock
async def test_ping_stable_reply_mac():
    """received=1 en dirección MAC → reply real por capa 2, conectado."""
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json=MOCK_TASK_RESULT_STABLE_REPLY_MAC)
    )

    gateway = _make_gateway()
    status = await gateway._poll_ping("123-abc")
    assert status == ConnectionStatus.stable


@pytest.mark.asyncio
@respx.mock
async def test_ping_no_internet():
    """Todos timeout a IP privada sin IP pública → equipo sin ruta / offline."""
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json=MOCK_TASK_RESULT_NO_INTERNET)
    )

    gateway = _make_gateway()
    status = await gateway._poll_ping("123-abc")
    assert status == ConnectionStatus.no_internet


@pytest.mark.asyncio
@respx.mock
async def test_ping_error_mikrotik():
    """Todos los ping-N son strings de error de MikroTik → error de configuración."""
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json=MOCK_TASK_RESULT_ERROR_MIKROTIK)
    )

    gateway = _make_gateway()
    status = await gateway._poll_ping("123-abc")
    assert status == ConnectionStatus.error


# ---------------------------------------------------------------------------
# PENDING status
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_ping_pending():
    """task.status=PENDING → ConnectionStatus.pending (tarea en cola, no terminada)."""
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json={"task": {"status": "PENDING", "result": None}})
    )

    gateway = _make_gateway()
    status = await gateway._poll_ping("123-abc")
    assert status == ConnectionStatus.pending


@pytest.mark.asyncio
@respx.mock
async def test_ping_process_status_is_pending():
    """task.status=PROCESS también es pending (tarea en progreso en WispHub)."""
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json={"task": {"status": "PROCESS", "result": None}})
    )

    gateway = _make_gateway()
    status = await gateway._poll_ping("123-abc")
    assert status == ConnectionStatus.pending


# ---------------------------------------------------------------------------
# Missing / malformed task key
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@respx.mock
async def test_ping_missing_task_key_returns_error():
    """Response without 'task' key → ConnectionStatus.error (response inesperada)."""
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(200, json={"unexpected": "payload"})
    )

    gateway = _make_gateway()
    status = await gateway._poll_ping("123-abc")
    assert status == ConnectionStatus.error


@pytest.mark.asyncio
@respx.mock
async def test_ping_http_error_returns_error():
    """Non-200 HTTP response → ConnectionStatus.error."""
    respx.get(url__startswith=settings.WISPHUB_NET_HOST).mock(
        return_value=httpx.Response(500, json={})
    )

    gateway = _make_gateway()
    status = await gateway._poll_ping("123-abc")
    assert status == ConnectionStatus.error
