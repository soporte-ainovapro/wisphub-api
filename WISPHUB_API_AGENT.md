# WispHub API — Reference for AI Agents

> This document is written **for AI agents** that need to design chatbot conversation flows
> using the WispHub API. Read this before generating any flow or code.

---

## 1. API Overview

**Base URL:** Configured at runtime via `WISPHUB_NET_HOST`.  
**Authentication:** All endpoints require the header `X-API-Key: <WISPHUB_INTERNAL_API_KEY>`.  
**Public endpoint (no key):** `GET /health` → returns `{"status": "ok"}`.

The API is organized into five capability domains:

| Domain | Purpose |
|---|---|
| **Clients** | Look up, verify, search, and update ISP subscribers |
| **Internet Plans** | List and inspect bandwidth plans |
| **Tickets** | Open and query technical support tickets |
| **Network / Ping** | Diagnose a subscriber's internet connectivity |
| **Payment Methods** | List supported payment channels and gateways |

---

## 2. Data Models

### ClientResponse
Returned by all client lookup endpoints.

```json
{
  "service_id": 101,
  "name": "Juan García",
  "document": "12345678",
  "phone": "3001234567",
  "address": "Calle 10 # 5-20",
  "city": "Bogotá",
  "locality": "Chapinero",
  "payment_status": "Al dia",
  "zone_id": 3,
  "antenna_ip": "192.168.1.100",
  "cut_off_date": "2026-04-01",
  "outstanding_balance": 0.0,
  "lan_interface": "ether1",
  "internet_plan_name": "Plan 10MB",
  "internet_plan_price": 40000.0,
  "technician_id": 5
}
```

> **Key fields for chatbot context:**
> - `service_id` → primary identifier for all subsequent operations
> - `zone_id` → required when opening a support ticket
> - `payment_status` → tells you if the client is overdue (`"Al dia"` = current, otherwise overdue)
> - `outstanding_balance` → debt in local currency
> - `technician_id` → ID to assign when opening tickets

### TicketResponse
```json
{
  "ticket_id": 500,
  "subject": "No Tiene Internet",
  "created_at": "2026-03-01 10:00",
  "end_date": "2026-03-03 10:00",
  "status_ticket": "Abierto",
  "priority": "3",
  "answer_text": null
}
```

### InternetPlanListItem
```json
{ "plan_id": 10, "name": "Plan 10MB", "type": "PPPOE" }
```
Plan types: `PPPOE`, `SIMPLE QUEUE`, `PCQ`.

### InternetPlanResponse (detail)
```json
{ "name": "Plan 10MB", "price": 40000.0, "download_speed": "10", "upload_speed": "2" }
```

---

## 3. Complete Route Catalog

### 3.1 Clients

#### `GET /api/clients/by-document/{document}`
Look up a client by national ID (cédula).
- **Path param:** `document` (string)
- **Returns:** `ClientResponse` | 404
- **Use when:** User says *"mi cédula es 12345678"*

#### `GET /api/clients/by-phone/{phone}`
Look up a client by phone number.
- **Path param:** `phone` (string)
- **Returns:** `ClientResponse` | 404
- **Use when:** User says *"mi teléfono es 300..."*

#### `GET /api/clients/by-service-id/{service_id}`
Look up a client by their WispHub service ID.
- **Path param:** `service_id` (string)
- **Returns:** `ClientResponse` | 404
- **Use when:** You already have the `service_id` from a previous call

#### `GET /api/clients/search?q={query}`
Fuzzy text search across all clients.
- **Query param:** `q` (string)
- **Returns:** `List[ClientResponse]` (may be empty `[]`)
- **Use when:** You only have the user's name or a partial address

#### `GET /api/clients/`
Returns all active clients (cached, ~5 min TTL).
- **Returns:** `List[ClientResponse]`
- **Use when:** You need to enumerate clients (e.g., for batch ops)

#### `POST /api/clients/resolve`
Identifies a client **without a known service_id** using ≥3 data points.
- **Body:**
  ```json
  {
    "name": "Juan García",
    "address": "Calle 10",
    "internet_plan_name": "Plan 10MB",
    "internet_plan_price": 40000.0
  }
  ```
  At least **3 of the 4 fields** must be provided.
- **Returns:** `ClientResponse` | 400 (not enough fields) | 404 (no match)
- **Use when:** User doesn't know their service_id and you need to confirm their identity

#### `POST /api/clients/{service_id}/verify`
Verifies a user's identity when you **already have** the `service_id`.
- **Path param:** `service_id` (int)
- **Body:**
  ```json
  {
    "name": "Juan García",
    "address": "Calle 10",
    "internet_plan_price": 40000.0
  }
  ```
  At least **3 of the 4 fields** must be sent.
- **Returns:**
  ```json
  { "is_valid": true, "matched_fields": ["name", "address", "internet_plan_price"], "message": "..." }
  ```
- **Use when:** You want to confirm the caller is who they claim to be.

#### `PUT /api/clients/{service_id}`
Updates profile fields in WispHub.
- **Path param:** `service_id` (int)
- **Body** (all optional, at least one must be sent):
  ```json
  {
    "name": "Juan",
    "last_name": "García",
    "document": "12345678",
    "address": "Calle 10 # 5-20",
    "locality": "Chapinero",
    "city": "Bogotá",
    "phone": "3001234567",
    "balance": "-50000"
  }
  ```
  > `balance`: negative = credit in favor, positive = pending debt. Changes are **not** reflected in the WispHub dashboard.
- **Returns:** `{"status": "ok", "message": "..."}` | 400
- **Common uses:**
  - Register a missing `document` or `phone` when the client doesn't have one on file
  - Correct mismatched `document` or `phone` that the client entered at the start of the conversation and don't match the database
  - Update `address`, `city`, or `locality` after a client relocation

---

### 3.2 Internet Plans

#### `GET /api/internet-plans/`
Lists all available internet plans (cached, ~15 min TTL).
- **Returns:** `List[InternetPlanListItem]`
- **Use when:** You need to resolve a plan name → `plan_id`, or list options

#### `GET /api/internet-plans/{plan_id}`
Gets speed and price details for a specific plan.
- **Path param:** `plan_id` (int)
- **Returns:** `InternetPlanResponse` | note for PCQ plans
- **Use when:** You need `price` or `download_speed`/`upload_speed` for context

---

### 3.3 Tickets

#### `GET /api/tickets/subjects`
Returns all allowed ticket subjects, grouped by priority.
- **Returns:**
  ```json
  {
    "by_priority": {
      "low":       ["Cambio de Contraseña en Router Wifi", "Cambio de Domicilio", "Recolección De Equipos", "Cancelación", "Desconexión"],
      "normal":    ["Internet Lento", "Internet Intermitente", "Antena Desalineada", "Cables Mal Colocados", "Cableado Para Modem Extra"],
      "high":      ["No Tiene Internet", "Antena Dañada", "No Responde la Antena", "No Responde el Router Wifi", "Router Wifi Reseteado (Valores de Fabrica)", "Cambio de Router Wifi", "Cambio de Antena", "Cambio de Antena + Router Wifi", "Cable UTP Dañado", "PoE Dañado", "Conector Dañado", "Antena valores De Fabrica", "Eliminador Dañado", "RJ45 Dañado", "Alambres Rotos", "Reconexión", "Cable Fibra Dañado", "Jumper Dañado"],
      "very_high": ["Troncal Dañado", "Caja Nap Dañada", "Cambio A Fibra Óptica"]
    },
    "all": [...]
  }
  ```
- **⚠️ When creating a ticket, the `subject` must be one of the strings in `all`.**

#### `GET /api/tickets/zone-blocked/{zone_id}`
Checks if a zone has hit the max open ticket limit (default: 3).
- **Returns:** `{"is_blocked": true, "max_tickets": 3}`
- **Use when:** Before trying to open a ticket, to warn the user early

#### `POST /api/tickets`
Opens a new support ticket.
- **Body:**
  ```json
  {
    "service_id": 101,
    "zone_id": 3,
    "subject": "No Tiene Internet",
    "technician_id": 5,
    "description": "El cliente reporta que no tiene internet desde esta mañana."
  }
  ```
  - `subject` → **must** be one of the valid subjects from `GET /api/tickets/subjects`
  - `zone_id` → from `client.zone_id`
  - `technician_id` → from `client.technician_id`
- **Returns:** `TicketResponse` | 400 (zone blocked or error)

#### `GET /api/tickets/{ticket_id}`
Retrieves a ticket by ID.
- **Returns:** `TicketResponse` | 404

---

### 3.4 Network / Ping

#### `POST /api/network/{service_id}/ping/`
Initiates an async ICMP ping diagnostic for a client's equipment.
- **Path param:** `service_id` (int)
- **Body:** `{"pings": 4}` — number of ping packets (default 4)
- **Returns:** `{"task_id": "abc-123"}`
- **Use when:** User reports connectivity issues and you need to diagnose remotely

#### `GET /api/network/ping/{task_id}/`
Polls the result of a previously started ping task.
- **Path param:** `task_id` (string)
- **Returns:** Standardized `PingResultResponse` format:
  ```json
  {
    "status": "stable",
    "message": "Client device has an active connection."
  }
  ```
  **Possible statuses:**
  - `stable`: Connection healthy (CPE/Router responded).
  - `antenna_only`: Customer device (CPE) is down/unreachable, but the main sector antenna (public IP) responded.
  - `pending`: Task still running, poll again.
  - `no_internet`: Zero packets received on all interfaces.
  - `error`: MikroTik/Router errors or invalid host setup.
- **Pattern:** Poll every 2–3 seconds until `status` is not `"pending"`.

---

### 3.5 Payment Methods

#### `GET /api/payment-methods/`
- **Purpose:** Retrieves a list of supported payment channels and billing gateways for the ISP.
- **Use when:** The client wants to know where or how to pay their internet bill.

---

## 4. Chatbot Flow Patterns

Use these patterns as building blocks when assembling flows.

---

### Pattern A — Client Identification (by known ID)

**Goal:** Confirm who the caller is using a known identifier.

```
User provides: document / phone / service_id
  → call GET /api/clients/by-document/{doc}
        or GET /api/clients/by-phone/{phone}
        or GET /api/clients/by-service-id/{id}
  → if 404: inform not found, ask for alternative identifier
  → if 200: store ClientResponse in session context
```

---

### Pattern B — Client Resolution (identity unknown)

**Goal:** Identify a caller who does not know their service_id.

```
Collect ≥3 of: name, address, internet_plan_name, internet_plan_price
  → POST /api/clients/resolve  { name, address, ... }
  → if 400 "not enough fields": ask for more data
  → if 404: inform no match, suggest calling support
  → if 200: client identified → store ClientResponse
```

---

### Pattern C — Identity Verification (already have service_id)

**Goal:** Confirm the caller is the legitimate account owner.

```
You have: service_id (from prior step or user input)
Collect ≥3 of: name, address, internet_plan_name, internet_plan_price
  → POST /api/clients/{service_id}/verify  { fields... }
  → check response.is_valid
  → if false: inform mismatch, offer retry or escalation
  → if true: proceed to next step
```

---

### Pattern D — Open Support Ticket

**Goal:** Register a technical issue on behalf of the caller.

**Prerequisites:** Caller is identified → `ClientResponse` is in session context.

```
1. Collect problem description from user
2. Determine closest subject:
   → GET /api/tickets/subjects
   → match user description to one of the allowed subjects
3. Check zone capacity:
   → GET /api/tickets/zone-blocked/{client.zone_id}
   → if is_blocked: inform user zone is at capacity, suggest callback
4. Open ticket:
   → POST /api/tickets
     {
       "service_id": client.service_id,
       "zone_id":    client.zone_id,
       "subject":    <matched subject>,
       "technician_id": client.technician_id,
       "description": <user's description>
     }
5. Confirm ticket_id to user
```

---

### Pattern E — Network Diagnosis (Ping)

**Goal:** Remotely test a client's internet connection.

**Prerequisites:** Client is identified, `service_id` is known.

```
1. Inform user that a diagnostic will be run
2. → POST /api/network/{service_id}/ping/  { "pings": 4 }
   → store task_id
3. Poll (every 2–3 sec):
   → GET /api/network/ping/{task_id}/
   → loop while result.status == "pending"
4. Interpret result:
   - "stable"       → "your connection is working normally"
   - "antenna_only" → "we can reach your nearest tower, but not your router. Please check the power."
   - "no_internet"  → "we cannot reach your equipment or the tower."
   - "error"        → "diagnostic failed, please call support"
```

---

### Pattern F — Payment Status Check

**Goal:** Inform user of their current payment standing.

**Prerequisites:** Client is identified.

```
→ Use existing ClientResponse (no extra API call needed)
→ check client.payment_status
  → "Al dia"      → "your service is up to date"
  → other value   → "your service has a balance of {client.outstanding_balance}"
→ optionally show client.cut_off_date
```

---

### Pattern G — Plan Information

**Goal:** Tell the user about their current or available internet plans.

```
→ GET /api/internet-plans/
→ find item where name == client.internet_plan_name to get plan_id
→ GET /api/internet-plans/{plan_id}
→ return name, price, download_speed, upload_speed
```

---

### Pattern H — Profile Update

**Goal:** Update a missing or corrected profile field.

**Prerequisites:** Client is identified and verified (Pattern B or C).

**Updatable fields:**

| Field | Type | Notes |
|---|---|---|
| `name` | string | First name |
| `last_name` | string | Last name(s) |
| `document` | string | National ID (cédula/DNI/CC) |
| `address` | string | Street address |
| `locality` | string | Neighborhood / barrio / ubigeo |
| `city` | string | City or municipality |
| `phone` | string | Phone number(s), multiple separated by comma |
| `balance` | string | Negative = credit, positive = debt (**not shown in dashboard**) |

```
Collect new value(s) from user
  → PUT /api/clients/{service_id}  { field: value, ... }
  → if 200: confirm update to user
  → if 400: inform failure and offer retry
```

**⚠️ Key scenario — document/phone missing or mismatched:**

Use this pattern when at the **start of the conversation** the user provides a document number or phone that:
- Returns **no client** (not registered in WispHub), OR
- The client was identified by other means but the identifier they gave **does not match** the database

In that case, after verifying their identity via Pattern B or C, offer to register the correct value:

```
User identified via resolve (Pattern B) → client.document is null or mismatched
  → ask: "¿Desea registrar su número de cédula para futuras consultas?"
  → if yes: PUT /api/clients/{service_id}  { "document": "<value user provided>" }

User identified via resolve (Pattern B) → client.phone is null or mismatched
  → ask: "¿Desea registrar su número de teléfono?"
  → if yes: PUT /api/clients/{service_id}  { "phone": "<value user provided>" }
```

---

## 5. Composing Custom Flows

When a user describes the chatbot they want to build, map their requirements to these patterns:

| User want | Pattern(s) to use |
|---|---|
| "Consultar estado de cuenta" | A or B → F |
| "Ver plan actual y velocidad" | A or B → G |
| "Abrir ticket de soporte" | A or B → C → D |
| "Diagnosticar mi internet" | A or B → E |
| "Actualizar mi teléfono o cédula" | A or B → C → H |
| "Identificar cliente por nombre" | B (resolve) |
| "Verificar identidad antes de actuar" | C |
| "Checar si la zona puede recibir tickets" | D (step 3 only) |

### Flow Assembly Rules

1. **Always start with identification** (Pattern A or B) before performing any action.
2. **Add verification (Pattern C)** when the action has billing/security impact (tickets, profile updates).
3. **Never open a ticket without checking `zone_id`** — it is required in the request body.
4. **`subject` must be an exact match** from `GET /api/tickets/subjects`. If the user's description doesn't map to a known subject, ask a clarifying question or pick the closest one from the list.
5. **Ping is async** — always poll the result in a loop; do not present the result until it stops returning `"pending"`.
6. **Session context:** After identifying a client, store the full `ClientResponse` so you can reuse `service_id`, `zone_id`, `technician_id`, and `payment_status` without extra API calls.

---

## 6. Error Handling Reference

| HTTP Status | Meaning | Recommended bot action |
|---|---|---|
| `401` | Missing or invalid `X-API-Key` | Internal error, do not expose to user |
| `400` with `"Se requieren al menos 3 campos"` | Not enough identity fields | Ask user to provide more data |
| `400` with `"Zona límite alcanzado"` | Too many open tickets in zone | Inform user and suggest calling office |
| `400` with `"No se pudo actualizar"` | service_id invalid for update | Confirm ID and retry once |
| `404` | Resource not found | Inform not found, offer alternative |
| `422` | Invalid request payload | Internal error — fix the payload |
| `500` | WispHub upstream error | "Servicio momentáneamente no disponible, intente más tarde" |

---

## 7. Authentication Setup

Include this header on **every** request:

```
X-API-Key: <value of WISPHUB_INTERNAL_API_KEY env var>
```

There is no token rotation or expiry — this is a static shared secret between backend services.
