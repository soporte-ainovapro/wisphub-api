# WispHub API Middleware

📖 **Full documentation:** [docs-wisphub.ainovapro.com](https://docs-wisphub.ainovapro.com/)

This repository contains a high-performance RESTful API built with FastAPI. It serves as an intermediate middleware layer connecting WispHub Net with third-party applications or conversational interfaces (e.g., WhatsApp bots via Twilio). This API abstracts, optimizes, and secures access to WispHub's billing, client, and support ticket management endpoints.

## Architecture & Core Capabilities

The architecture is designed to mitigate the inherent load placed on external services by conversational bots, reducing latency and preventing rate-limiting on the WispHub API.

*   **JWT Authentication:** Stateless Bearer token authentication (JSON Web Tokens, HS256). All business-logic routes require a valid token issued by `POST /api/v1/auth/token`. The `/health` endpoint remains public for load-balancer probes.
*   **In-Memory Caching System:** Implements Least Recently Used (LRU) caching via `async_lru` for resource-intensive data retrieval operations. The global client list and available internet plans are cached in RAM with custom Time-To-Live (TTL) strategies (5 and 15 minutes respectively), effectively eliminating repeated network roundtrips and dropping sub-second response queries to under 5 milliseconds.
*   **Flexible Client Discovery:** Provides specialized search routes that leverage partial string matching when exact identifiers (Document ID or Phone Number) are unavailable, enabling robust entity resolution from unstructured conversational input.
*   **Algorithmic Identity Verification:** Implements the `POST /verify` endpoint, a security mechanism that validates ownership logic by comparing incoming, loosely formatted billing and address data against the pristine WispHub database records.
*   **Dynamic Profiling & Patching:** Enables on-the-fly database updates (`PUT`) to enrich client profiles with missing critical information (such as missing documents or phone numbers extracted during bot interaction).
*   **Exception Handling Standard:** Features a unified JSON payload structure (`BackendResponse`) mapped over the standard Pydantic validation workflow and HTTP error status codes, providing a consistent consumption interface for frontend architectures.

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

# JWT Authentication
JWT_SECRET_KEY=<random-hex-secret-32-bytes>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
API_USERNAME=admin
API_PASSWORD_HASH=<bcrypt-hash-of-the-admin-password>
```

To generate the values for `JWT_SECRET_KEY` and `API_PASSWORD_HASH`, run:

```bash
python3 -c "
import secrets
from passlib.context import CryptContext
print('JWT_SECRET_KEY=' + secrets.token_hex(32))
print('API_PASSWORD_HASH=' + CryptContext(schemes=['bcrypt']).hash('your-password-here'))
"
```

### 2. Docker Deployment (Production)

The production environment is containerized using Docker, leveraging Gunicorn to manage Uvicorn worker processes to ensure maximum async throughput.

```bash
docker build -t wisphubapi:latest .
docker run -d --name wisphub_api_server -p 8000:8000 --env-file .env wisphubapi:latest
```

The self-documenting OpenAPI schema will be accessible at: `http://localhost:8000/docs`.

### 3. Local Development

To set up a local development environment, establish a virtual execution environment and install both application and testing dependencies.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Authentication

All protected endpoints require a Bearer JWT token in the `Authorization` header.

### Obtaining a Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -d "username=admin&password=<your-password>"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Using the Token

Include the token in all subsequent requests:

```bash
curl -H "Authorization: Bearer <access_token>" http://localhost:8000/api/v1/clients/
```

Tokens expire after `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` minutes (default: 60). Re-authenticate to obtain a new token.

### Public Endpoints (No Authentication Required)

| Endpoint | Description |
|---|---|
| `GET /health` | Service health check |
| `POST /api/v1/auth/token` | Obtain a JWT access token |

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
*   `POST /api/v1/auth/token`: Authenticates with `username` + `password` form fields and returns a signed JWT Bearer token. **Public — no prior token required.**

### Clients Module
*   `GET /api/v1/clients/`: Retrieves the globally cached client pool.
*   `GET /api/v1/clients/by-document/{document_id}`: Performs exact matching lookup by national ID numeric strings.
*   `GET /api/v1/clients/by-phone/{phone_number}`: Performs explicit client search by registered telephone strings.
*   `GET /api/v1/clients/by-service-id/{service_id}`: Retrieves client information using the WispHub unique service identifier.
*   `GET /api/v1/clients/search?q={query}`: Initiates a fuzzy search query against the WispHub index.
*   `PUT /api/v1/clients/{service_id}`: Updates core profile attributes (Document, Phone) on the remote WispHub server.
*   `POST /api/v1/clients/{service_id}/verify`: Evaluates user-provided data parameters (name, address, plan name, plan price) against the validated WispHub database profile. Requires at least 3 exact matches.
*   `POST /api/v1/clients/resolve`: Combines search and verification in a single endpoint ("Single-pass"). Locates a client without a `service_id` using at least 3 exact matches across name, address, plan name, or plan price.

### Internet Plans Module
*   `GET /api/v1/internet-plans/`: Acquires the synchronized, globally cached dataset of all available provider internet plans.
*   `GET /api/v1/internet-plans/{plan_id}`: Locates and structures deep attributes (Download/Upload limitations, network type) of a specified plan identifier.

### Technical Tickets Module
*   `POST /api/v1/tickets/`: Instantiates a standardized escalation sub-routine inside WispHub containing structured debugging metadata.
*   `GET /api/v1/tickets/subjects`: Returns all valid ticket subjects grouped by priority level.
*   `GET /api/v1/tickets/zone-blocked/{zone_id}`: Checks whether a zone has exceeded the maximum number of open tickets.
*   `GET /api/v1/tickets/{ticket_id}`: Retrieves the full details of a technical support ticket by its unique ID.

### Network & Diagnostics Module
*   `POST /api/v1/{service_id}/ping/`: Initiates an asynchronous ICMP PING diagnostic task against a client's equipment.
*   `GET /api/v1/ping/{task_id}/`: Retrieves the result of a previously initialized PING task.
