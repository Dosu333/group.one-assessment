# Centralized License Service

## 1. Problem & Requirements (My Own Words)
The objective was to build a Single Source of Truth for software entitlements across a rapidly growing ecosystem of brands (RankMath, WP Rocket, etc.).

The core challenge wasn't just managing keys, but doing so in a multi-tenant environment where data isolation is non-negotiable, and performance must remain consistent even as seat activations scale into the millions. The system had to be "Brand-Agnostic" (serving many systems) yet "Brand-Specific" (isolating data and logic for each).

---

## 2. High-Level Architecture
I chose a Service-Oriented Architecture built on **Django** and **PostgreSQL**.

### The “Clean” Service Layer
Rather than placing business logic in Models or Views, I implemented a **dedicated Service layer** (e.g. `ProvisioningService`, `ActivationService`).

**Key benefits:**

* **Decoupling**
  Services are completely decoupled from the `HttpRequest` object.
  They consume only:

  * Pure data
  * A Metadata DTO

  This allows the same logic to be triggered by:

  * REST APIs
  * Celery background tasks
  * CLI tools
    without modification.

* **Atomicity**
  Every service uses `transaction.atomic()` to guarantee that complex operations (such as provisioning a multi-product bundle) either:

  * succeed fully, or
  * fail cleanly without leaving orphaned data.

---

## 3. Key Design Decisions & Trade-offs

### A. Multi-Tenancy & Security

* **Dual-Layer Authentication**
  Two distinct authentication schemes were implemented:

  * **Private API Key** for brand management tasks (US1, US2, US6)
  * **Public Brand Slug** for end-user activations (US3, US4)

  This ensures that a leaked public slug cannot compromise an entire brand’s license database.

* **Logical Isolation**
  Every database query is explicitly scoped by `brand_id`.
  This rule is enforced at the **service layer** to prevent any possibility of cross-tenant data leakage.

---

### B. Reliability & Concurrency

* **Idempotency (US1 & US2)**
  Using a custom `@idempotent_request` decorator and an `IdempotencyRecord` table, the system safely handles:

  * network retries
  * double-click provisioning
  * duplicate renewals

  This prevents duplicate billing or license creation.

* **Race Condition Protection (US3)**
  Seat activation uses PostgreSQL’s `select_for_update()` to lock the license row during the seat-check-and-increment phase.

  This guarantees that:

  * a 1-seat license cannot be activated twice by concurrent requests.

---

### C. Observability (Production Context)

* **Structured JSON Logging**
  Logs are emitted as machine-readable JSON rather than plain strings.
  This enables immediate integration with tools like **ELK** or **Datadog** for:

  * activation failure monitoring
  * seat saturation alerts

---

## 4. Scaling Plan: From Thousands to 10M+ Activations

To support millions of daily license checks, the following optimizations are planned:

* **Read-Optimized Caching**
  License status checks (US4) are high-frequency.
  Introduce Redis caching with a TTL, invalidated only on:

  * lifecycle changes
  * new activations

* **Database Partitioning**
  As the `Activation` table grows, apply table partitioning by:

  * `brand_id`, or
  * `created_at`

  This keeps index sizes manageable and query latency stable.

* **Global CDN / Edge Execution**
  Move the Status endpoint to:

  * AWS Lambda@Edge, or
  * Cloudflare Workers

  backed by geo-replicated read replicas for low-latency global access.

---

## 5. Implementation Status & Coverage

* **Unit & Integration Tests**
  ~74% code coverage, verified via GitHub Actions.

* **CI/CD Pipeline**
  Automated:

  * linting (`black`, `flake8`)
  * test execution
    on every push.

* **API Documentation**
  Fully interactive **OpenAPI 3.0** documentation available via Swagger UI at:

  ```
  /api/docs/
  ```

---

## 6. Gaps & Future Improvements

* **Rate Limiting**
  In production, I would add per-brand and per-IP rate limiting to prevent:

  * DDoS attacks
  * API key brute forcing

* **Webhook System**
  Introduce webhooks to notify brand systems (e.g. WP Rocket) in real time when:

  * a license is cancelled
  * a subscription expires
  * a lifecycle state changes

* **Audit Trails**
  Introduce an immutable `AuditLog` records every lifecycle change (Renew, Suspend, Cancel), capturing both:

  * **before** state
  * **after** state

  This will support debugging, customer support, and compliance needs.

