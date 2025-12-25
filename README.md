## Architecture

Services:

- **api (FastAPI)**: REST APIs + SSE streaming gateway
- **worker**: consumes jobs from Redis queue and executes agent turns
- **postgres**: persists sessions, messages, events
- **redis**: job queue + pub/sub for streaming events
- **per-session VM container**: computer-use desktop with VNC/noVNC

### Data flow

1. Client `POST /v1/sessions` → creates DB session + starts VM container
2. Client opens SSE `GET /v1/sessions/{id}/events`
3. Client `POST /v1/sessions/{id}/messages` → stores user message + enqueues job
4. Worker processes job:
   - acquires **session lock** to prevent race conditions
   - emits events to DB + Redis pubsub
   - writes assistant message to DB

### Concurrency / race conditions

- A **Redis per-session lock** ensures only one active run per session.
- Concurrent sessions are supported; concurrent turns within the same session are serialized.

### Streaming

- SSE endpoint: `GET /v1/sessions/{id}/events`
- Events are persisted in Postgres and streamed live via Redis pub/sub.
- Event types: `status`, `token`, `tool_call`, `screenshot`, `log`, `message`

## API Endpoints

- `POST /v1/sessions` create session
- `GET /v1/sessions` list sessions
- `GET /v1/sessions/{id}` get session
- `POST /v1/sessions/{id}/messages` send user instruction (enqueue job)
- `GET /v1/sessions/{id}/history` chat history
- `POST /v1/sessions/{id}/stop` stop and remove VM container
- `GET /v1/sessions/{id}/events` SSE stream
