# ListeningAgentAi (Social Listening & Lead Generation System)

A high-performance, asynchronous AI-driven social listening system built to track, ingest, filter, and process real-time market data from platforms like Reddit to extract intent-driven B2B leads. The system features a monolithic multi-process architecture orchestrated via Docker to run core API routing, database layers, caching layers, and background worker queues seamlessly in a single lightweight instance.

---

## 🏗 System Architecture & Flow

1. **Ingestion Layer:** Real-time data or webhook streams from scraping actors (e.g., Apify Reddit actors) feed transactional data into the FastAPI web server via token-validated routing (`/ingestion/reddit`).
2. **Task Distribution (Broker):** Ingested raw payloads are offloaded immediately to a localized internal Redis cache cluster to ensure zero-blocking, low-latency API response times.
3. **Background Worker Engine:** A distributed Celery worker pool processes the active queue, handling tokenization, system keyword alignment, and state mapping.
4. **AI Processing Layer (LangGraph):** The core AI engine executes structured mission graphs using state-of-the-art LLM supervisors to extract market gaps, intent patterns, and target lead profiles.
5. **Storage & Vector Layer:** Processed information and structured lead insights are finalized inside a vectorized PostgreSQL relational database using schema-managed extensions for efficient storage and later vector retrieval.

---

## 🛠 Tech Stack

* **Core Framework:** FastAPI (Asynchronous Python 3.11, Pydantic v2 data verification)
* **Database Layers:** PostgreSQL 17 (Vector-enabled schema configuration)
* **Asynchronous Processing:** Celery (Worker orchestration engine)
* **Caching & Brokerage:** Redis Server (High-throughput message broker)
* **AI & Multi-Agent Framework:** LangGraph / LangChain Core (Hierarchical multi-agent supervisor/worker architecture)
* **Schema & Migrations:** Alembic (Asynchronous database schema version control)

---

## 🚀 Monolithic Production Deployment Architecture

To achieve absolute cost-efficiency and reliable operation for demonstration environments, the system utilizes a **Monolithic Process Bootloader Model** encapsulated cleanly within a single production Docker container. 

When the system initializes, a low-level Linux shell bootloader script (`start.sh`) natively provisions, manages, and executes all structural subsystems concurrently:
1. **PostgreSQL Daemon Service** initialization, cluster creation, and active runtime management.
2. **Alembic Database Migration** auto-discovery and sequential execution against localhost targets.
3. **Redis Caching Server** daemonization to serve as the local atomic message broker.
4. **Celery Worker Engine** spawning and routing to asynchronous task queues (`default`, `matching`).
5. **FastAPI Web Engine** execution via Uvicorn on exposed production routing ports.

---

## 💻 Local Development Setup

### Prerequisites
* Python 3.11+
* Docker & Docker Compose (Optional, for multi-container local execution)

### 1. Manual Multi-Process Setup (Without Docker Compose)

**Initialize local cache database (Redis):**
```bash
docker run -d -p 6379:6379 redis