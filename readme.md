# Centralized License Service (CLS)
This repository contains a multi-tenant license management system designed for an ecosystem of brands. It serves as the single source of truth for software entitlements, activations, and lifecycle management.

## 🚀 Quick Start

The easiest way to run and review the project is using **Docker Compose**. This will spin up the Django application, a PostgreSQL 15 database, and handle migrations automatically.

```bash
# 1. Clone the repository
git clone <https://github.com/Dosu333/group.one-assessment.git>
cd group.one-assessment

# 2. Start the services
docker-compose up --build

```

The API will be available at `http://127.0.0.1:8000`.

---

## 🛠 Features & User Stories Implemented

* **US1: Bundle Provisioning**: Atomic creation of license keys associated with multiple products.
* **US2: Lifecycle Management**: Secure state transitions (Renew, Suspend, Resume, Cancel).
* **US3 & US5: Activation/Deactivation**: Granular seat management for specific products within a bundle.
* **US4: Status Checks**: High-performance entitlement validation for end-user products.
* **US6: Global Lookup**: Cross-brand search by customer email with strict security logging.

---

## 🏗 Architectural Highlights

* **Service Layer Pattern**: Business logic is decoupled from HTTP views, ensuring testability and reusability.
* **Idempotency Guardrails**: Prevents duplicate license creation or double-billing via a custom `Idempotency-Key` implementation.
* **Concurrency Control**: Uses PostgreSQL `select_for_update` row-level locking to prevent race conditions during seat activations.
* **Structured JSON Logging**: Production-grade observability for seamless ELK/Datadog integration.
* **Multi-Tenant Security**: Dual-layer authentication (Private API Keys for Brands vs. Public Slugs for Products).

---

## 🧪 Testing & Verification

The project maintains high test coverage (~74%) focusing on critical business invariants.

### **Running Tests Locally**

```bash
docker-compose exec web python manage.py test

```

### **Running Coverage Reports**

```bash
docker-compose exec web coverage run manage.py test
docker-compose exec web coverage report

```

---

## 📖 API Documentation

Interactive documentation is provided via **Swagger/OpenAPI 3.0**. Once the server is running, visit:

* **Swagger UI**: `http://localhost:8000/api/docs/`
* **Schema (JSON)**: `http://localhost:8000/api/schema/`

---

## 🤖 CI/CD Integration

This repository includes a **GitHub Actions** workflow (`.github/workflows/ci.yml`) that automates:

1. **Linting**: Enforcing style compliance via `black` and `flake8`.
2. **Integration Testing**: Running the full test suite against a real PostgreSQL service container on every push.

---

## ⚖️ Scaling for 10M+ Activations

*For a detailed breakdown of the scaling strategy, database partitioning, and caching layers, please refer to the **Explanation.md** file.*

---

### **Final Checklist Completion**

* [x] **US1-US6** Fully implemented.

* [x] **PostgreSQL** used for persistence.
* [x] **Service Layer** architecture.
* [x] **Structured Logging** (JSON).
* [x] **Unit & Integration Tests** (CI Green).
* [x] **Dockerized** and ready for review.
