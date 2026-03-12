# WispHub API Middleware

📖 **Full documentation:** [docs-wisphub.ainovapro.com](https://docs-wisphub.ainovapro.com/)

This repository contains a high-performance RESTful API built with FastAPI. It serves as an intermediate middleware layer connecting WispHub Net with third-party applications or conversational interfaces (e.g., WhatsApp bots via Twilio). This API abstracts, optimizes, and secures access to WispHub's billing, client, and support ticket management endpoints.

## Architecture & Core Capabilities

The API is structured following **Clean Architecture / Domain-Driven Design (DDD)** principles, aligned with its sibling project `factus-api`. The application is organized into three clear layers:

```
app/
├── domain/
│   ├── models/         # Pydantic models (data contracts)
│   ├── interfaces/     # Abstract gateway interfaces (ABC)
│   └── exceptions.py   # Domain-level custom exceptions
├── infrastructure/
│   └── gateways/       # Concrete WispHub HTTP implementations
├── api/
│   └── v1/
│       └── endpoints/  # FastAPI route handlers (inject gateways via Depends)
└── core/               # Settings and configuration
```

**Why this architecture?**
- **Testability:** Endpoints inject concrete gateway instances via `Depends()`, making it trivial to mock any gateway in tests without patching network calls.
- **Low coupling:** The API layer only depends on abstract interfaces — not on WispHub HTTP specifics. If WispHub changes, only the gateway implementation needs updating.
- **Consistency:** All Baiji microservices (`factus-api`, `wisphub-api`) share the same architecture, reducing cognitive load when switching between projects.

*   **Static Internal Authentication:** Secures internal backend communication utilizing a shared `X-API-Key` header mechanism.
*   **In-Memory Caching System:** Implements LRU caching via `async_lru` for resource-intensive data retrieval with TTL strategies (5 mins for clients, 15 mins for plans).
*   **Flexible Client Discovery:** Provides specialized search routes that leverage partial string matching when exact identifiers are unavailable.
*   **Algorithmic Identity Verification:** Implements `POST /verify`, which validates ownership by comparing incoming billing data against WispHub database records.
*   **Exception Handling Standard:** Consistent `{"detail": "..."}` error responses via global exception handlers.

## Technology Stack

*   **API Framework:** FastAPI (Python 3.12)
*   **Data Validation:** Pydantic V2
*   **Authentication:** python-jose (JWT) + passlib/bcrypt
*   **HTTP Client:** HTTPX (Asynchronous implementation)
*   **Caching Engine:** async_lru
*   **Application Server:** Uvicorn (ASGI) / Gunicorn (Process Manager)
*   **Testing Infrastructure:** Pytest, pytest-asyncio, Respx, Locust

## Setup and Deployment

### 1. Environment Configuration

Clone the repository and define the environment variables required to interact with the WispHub infrastructure in a `.env` file at the root level.

```env
WISPHUB_NET_KEY=<Your_WispHub_API_Key>
WISPHUB_NET_HOST=https://api.wisphub.net
MAX_ACTIVE_TICKETS_PER_ZONE=3

# Autenticación Interna (Estática)
WISPHUB_INTERNAL_API_KEY=<Shared_Secret_Between_Backends>
```

## Authentication

All protected endpoints require an `X-API-Key` header with the configured shared secret.

### Using the Token

Include the token in all subsequent requests:

```bash
curl -H "X-API-Key: <your-internal-secret>" http://localhost:8000/api/clients/
```

### Public Endpoints (No Authentication Required)

| Endpoint | Description |
|---|---|
| `GET /health` | Service health check |

## Testing Methodology

The codebase is governed by comprehensive testing standards to ensure stability and deterministic behavioral outcomes.

### Unit & Integration Testing
The `tests/` directory uses `pytest` and `respx` to inject mocked HTTP transport layers. This ensures that the WispHub API is isolated from local execution noise while preserving the validity of Pydantic parsing and endpoint routing.

Two fixtures are available in `conftest.py`:
- **`auth_client`** — Pre-configured with a valid Bearer token. Used for all business-logic endpoint tests.
- **`async_client`** — Unauthenticated. Used for testing public routes and `401 Unauthorized` scenarios.

```bash
pytest tests/ -v
```

### Stress & Load Testing
A `locustfile.py` script is included to validate concurrency thresholds and ensure caching decorators behave as intended. It mimics the randomized load of concurrent websocket/bot user sessions.

```bash
locust -f locustfile.py --host=http://localhost:8000
```
*Empirical evaluation demonstrates the server effectively handles >40 Requests Per Second (RPS) sustaining 0.00% failure rates on read-intensive cached routes under persistent load.*

## API Endpoints Reference

### Authentication Module
*   `POST /api/auth/token`: Authenticates with `username` + `password` form fields and returns a signed JWT Bearer token. **Public — no prior token required.**

### Clients Module
*   `GET /api/clients/`: Retrieves the globally cached client pool.
*   `GET /api/clients/by-document/{document_id}`: Performs exact matching lookup by national ID numeric strings.
*   `GET /api/clients/by-phone/{phone_number}`: Performs explicit client search by registered telephone strings.
*   `GET /api/clients/by-service-id/{service_id}`: Retrieves client information using the WispHub unique service identifier.
*   `GET /api/clients/search?q={query}`: Initiates a fuzzy search query against the WispHub index.
*   `PUT /api/clients/{service_id}`: Updates core profile attributes (Document, Phone) on the remote WispHub server.
*   `POST /api/clients/{service_id}/verify`: Evaluates user-provided data parameters (name, address, plan name, plan price) against the validated WispHub database profile. Requires at least 3 exact matches.
*   `POST /api/clients/resolve`: Combines search and verification in a single endpoint ("Single-pass"). Locates a client without a `service_id` using at least 3 exact matches across name, address, plan name, or plan price.

### Internet Plans Module
*   `GET /api/internet-plans/`: Acquires the synchronized, globally cached dataset of all available provider internet plans.
*   `GET /api/internet-plans/{plan_id}`: Locates and structures deep attributes (Download/Upload limitations, network type) of a specified plan identifier.

### Technical Tickets Module
*   `POST /api/tickets/`: Instantiates a standardized escalation sub-routine inside WispHub containing structured debugging metadata.
*   `GET /api/tickets/subjects`: Returns all valid ticket subjects grouped by priority level.
*   `GET /api/tickets/zone-blocked/{zone_id}`: Checks whether a zone has exceeded the maximum number of open tickets.
*   `GET /api/tickets/{ticket_id}`: Retrieves the full details of a technical support ticket by its unique ID.

### Network & Diagnostics Module
*   `POST /api/{service_id}/ping/`: Initiates an asynchronous ICMP PING diagnostic task against a client's equipment.
*   `GET /api/ping/{task_id}/`: Retrieves the result of a previously initialized PING task.
