# WispHub API Middleware

This repository contains a high-performance RESTful API built with FastAPI. It serves as an intermediate middleware layer connecting WispHub Net with third-party applications or conversational interfaces (e.g., WhatsApp bots via Twilio). This API abstracts, optimizes, and secures access to WispHub's billing, client, and support ticket management endpoints.

## Architecture & Core Capabilities

The architecture is designed to mitigate the inherent load placed on external services by conversational bots, reducing latency and preventing rate-limiting on the WispHub API.

*   **In-Memory Caching System:** Implements Least Recently Used (LRU) caching via `async_lru` for resource-intensive data retrieval operations. The global client list and available internet plans are cached in RAM with custom Time-To-Live (TTL) strategies (5 and 15 minutes respectively), effectively eliminating repeated network roundrips and dropping sub-second response queries to under 5 milliseconds.
*   **Flexible Client Discovery:** Provides specialized search routes that leverage partial string matching when exact identifiers (Document ID or Phone Number) are unavailable, enabling robust entity resolution from unstructured conversational input.
*   **Algorithmic Identity Verification:** Implements the `POST /verify` endpoint, a security mechanism that validates ownership logic by comparing incoming, loosely formatted billing and address data against the pristine WispHub database records.
*   **Dynamic Profiling & Patching:** Enables on-the-fly database updates (`PUT`) to enrich client profiles with missing critical information (such as missing documents or phone numbers extracted during bot interaction).
*   **Exception Handling Standard:** Features a unified JSON payload structure (`BackendResponse`) mapped over the standard Pydantic validation workflow and HTTP error status codes, providing a consistent consumption interface for frontend architectures.

## Technology Stack

*   **API Framework:** FastAPI (Python 3.12)
*   **Data Validation:** Pydantic V2
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

## Testing Methodology

The codebase is governed by comprehensive testing standards to ensure stability and deterministic behavioral outcomes.

### Unit & Integration Testing
The `tests/` directory uses `pytest` and `respx` to inject mocked HTTP transport layers. This ensures that the WispHub API is isolated from local execution noise while preserving the validity of Pydantic parsing and endpoint routing.

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

### Clients Module
*   `GET /api/v1/clients/`: Retrieves the globally cached client pool.
*   `GET /api/v1/clients/by-document/{document_id}`: Performs exact matching lookup by national ID numeric strings.
*   `GET /api/v1/clients/by-phone/{phone_number}`: Performs explicit client search by registered telephone strings.
*   `GET /api/v1/clients/search?q={query}`: Initiates a fuzzy search query against the WispHub index.
*   `PUT /api/v1/clients/{service_id}`: Updates core profile attributes (Document, Phone) on the remote WispHub server.
*   `POST /api/v1/clients/{service_id}/verify`: Evaluates user-provided data parameters (name, address, plan name, plan price) against the validated WispHub database profile directly. Requiere al menos 3 coincidencias exactas.
*   `POST /api/v1/clients/resolve`: Combina búsqueda y verificación en un solo endpoint ("Single-pass"). Localiza un cliente sin `service_id` utilizando al menos 3 coincidencias exactas entre nombre, dirección, nombre de plan o precio tarifario.

### Internet Plans Module
*   `GET /api/v1/internet-plans/`: Acquires the synchronized, globally cached dataset of all available provider internet plans.
*   `GET /api/v1/internet-plans/{plan_id}`: Locates and structures deep attributes (Download/Upload limitations, network type) of a specified plan identifier.

### Technical Tickets Module
*   `POST /api/v1/tickets/`: Instantiates a standardized escalation sub-routine inside WispHub containing structured debugging metadata. Translates payload definitions natively into WispHub accepted schemas.
