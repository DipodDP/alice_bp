# Documentation Index

This directory contains comprehensive documentation for the Alice BP Monitoring System, generated from a multi-expert security and architecture inspection.

## Available Documents

### 📊 [Inspection Report](inspection_report.md)
**Complete security and architecture analysis**

- 87 files examined, 15,000+ lines of code analyzed
- 12 security findings (2 critical, 4 high/medium, 6 informational)
- Data flow diagrams and sequence diagrams
- PHI/PII inventory and privacy compliance checklist
- Test coverage analysis (2,887 lines of tests)
- API documentation
- Deployment checklist

**Read this first** to understand the current state of the system.

---

### 🔧 [Prioritized Fixes](fixes.md)
**7 actionable fixes with code diffs and validation steps**

**Priority 1: CRITICAL (Before Production)**
1. Enforce Alice webhook secret (2 min)
2. Change DEBUG default to False (1 min)

**Priority 2: HIGH (Week 1)**
3. Add production readiness checks (15 min)
4. Add CI/CD pipeline with security scanning (30 min)
5. Document PostgreSQL production setup (20 min)

**Priority 3: MEDIUM (Month 1-2)**
6. Add audit logging (2 hours)
7. Enhanced API authentication with JWT (4 hours)

**Total time to production-ready: ~8 hours**

---

### 🗄️ [PostgreSQL Setup Guide](fixes.md#fix-5-document-postgresql-production-setup)
Included in the fixes document, this section covers:

- Why PostgreSQL vs SQLite for medical data
- Installation on Ubuntu/Debian/macOS/Docker
- Database setup and user creation
- Data migration from SQLite
- Security hardening (SSL, read-only users, connection pooling)
- Backup strategy with automated scripts
- Monitoring and performance tuning
- Encryption at rest options

---

## Scripts

All scripts are located in `/scripts/` directory.

### 🚀 [bootstrap.sh](../scripts/bootstrap.sh)
**Non-destructive environment setup and validation**

```bash
./scripts/bootstrap.sh
```

Checks:
- Python version (3.13+)
- Project structure
- Virtual environment
- Dependencies installed
- Environment variables configured
- Database and migrations
- Test configuration

**Run this first** to validate your development environment.

---

### 🩺 [simulate_bp.py](../scripts/simulate_bp.py)
**Blood pressure device simulator**

Generates realistic BP readings and posts them via:
- Alice webhook (voice interface)
- Django REST API (bot interface)

```bash
# Post to Alice webhook
python scripts/simulate_bp.py \
  --mode alice \
  --url http://localhost:8000/alice_webhook/ \
  --token YOUR_SECRET \
  --profile normal \
  --count 5

# Post to Django API
python scripts/simulate_bp.py \
  --mode api \
  --url http://localhost:8000/api/v1/measurements/ \
  --api-token YOUR_TOKEN \
  --user-id alice_user_123 \
  --profile high \
  --count 10

# Dry run (generate without sending)
python scripts/simulate_bp.py \
  --mode alice \
  --url http://localhost:8000/alice_webhook/ \
  --token SECRET \
  --dry-run
```

**Profiles:**
- `normal` - Healthy BP (110-130/70-85)
- `elevated` - Pre-hypertension (130-140/80-90)
- `high` - Hypertension (140-180/90-120)
- `low` - Hypotension (85-110/50-70)
- `mixed` - Random profile each reading

---

### 🧪 [test_yandex_webhook.sh](../scripts/test_yandex_webhook.sh)
**Comprehensive Yandex.Dialogs webhook test harness**

```bash
./scripts/test_yandex_webhook.sh [webhook_url] [secret_token]

# Example:
./scripts/test_yandex_webhook.sh http://localhost:8000/alice_webhook/ test-secret
```

Tests:
- Security (no token, wrong token)
- BP recording (standard format, with pulse, edge cases, invalid values)
- Last measurement retrieval
- Account linking
- NLU token processing (homoglyphs, case normalization)
- Session management
- Timezone handling

**35+ test cases** covering all Alice intents and error scenarios.

---

## Tests

### 🧬 [Integration Tests](../tests/test_integration.py)
**Example end-to-end test suite**

```bash
pytest tests/test_integration.py -v
```

Test classes:
- `AccountLinkingFlowTest` - Complete Telegram ↔ Alice linking
- `BloodPressureRecordingFlowTest` - Voice → DB → API retrieval
- `AuthorizationFlowTest` - Data scoping and access control
- `ErrorHandlingFlowTest` - Validation and security
- `TimezoneHandlingTest` - Timezone conversion

**Use as template** for writing additional integration tests.

---

## CI/CD

### ⚙️ [GitHub Actions Workflow](../.github/workflows/ci.yml)
**Automated testing and security scanning**

Triggers on:
- Push to `main`, `develop`, `api_security` branches
- Pull requests to `main`, `develop`

Jobs:
1. **test** - Run pytest with coverage
2. **security** - Bandit + Safety + secret scanning
3. **lint** - Ruff code quality checks
4. **deployment-check** - Production readiness validation
5. **bot-tests** - Telegram bot test suite
6. **integration-tests** - End-to-end flows
7. **summary** - Overall CI status

**Artifacts:**
- Coverage reports (HTML + XML)
- Bandit security report (JSON)
- Safety dependency report (JSON)

---

## Quick Start

### For First-Time Setup

```bash
# 1. Validate environment
./scripts/bootstrap.sh

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Generate secrets
python manage.py generate_secret_keys

# Copy output to .env file

# 4. Run migrations
python manage.py migrate

# 5. Run tests
pytest

# 6. Start development server
python manage.py runserver
```

### For Testing Alice Integration

```bash
# 1. Set webhook secret in .env
ALICE_WEBHOOK_SECRET=your-secret-here

# 2. Start server
python manage.py runserver

# 3. Test webhook (in another terminal)
./scripts/test_yandex_webhook.sh http://localhost:8000/alice_webhook/ your-secret-here

# 4. Simulate BP readings
python scripts/simulate_bp.py \
  --mode alice \
  --url http://localhost:8000/alice_webhook/ \
  --token your-secret-here \
  --count 5
```

### For Production Deployment

```bash
# 1. Read the inspection report
cat docs/inspection_report.md

# 2. Review critical fixes
cat docs/fixes.md

# 3. Implement fixes #1 and #2 (CRITICAL)
# See docs/fixes.md for exact code changes

# 4. Set up PostgreSQL
# Follow PostgreSQL Setup Guide in docs/fixes.md

# 5. Run production readiness check
python manage.py check_production_ready --strict

# 6. Run deployment checks
python manage.py check --deploy

# 7. Test webhook security
./scripts/test_yandex_webhook.sh https://yourdomain.com/alice_webhook/ $ALICE_WEBHOOK_SECRET
```

---

## Security Findings Summary

### Critical (Fix Before Production)

1. **Alice webhook secret is optional**
   - Risk: Unauthenticated data manipulation
   - Fix: Add `ImproperlyConfigured` check
   - Time: 2 minutes

2. **DEBUG defaults to True**
   - Risk: Information leakage
   - Fix: Change default to False
   - Time: 1 minute

### High (Week 1)

3. **No production readiness validation**
   - Fix: Add management command
   - Time: 15 minutes

4. **No CI/CD pipeline**
   - Fix: GitHub Actions workflow (provided)
   - Time: 30 minutes

5. **SQLite in production**
   - Fix: Migrate to PostgreSQL
   - Time: 20 minutes setup + migration time

### Medium (Month 1)

6. **No audit logging**
   - Fix: django-auditlog
   - Time: 2 hours

7. **Simple token authentication**
   - Fix: JWT tokens
   - Time: 4 hours

---

## Test Coverage

| Component | Files | Lines | Tests |
|-----------|-------|-------|-------|
| Django App (alice_skill) | 13 | 2,110 | 87+ |
| Telegram Bot (tgbot_bp) | 8 | 777 | 40+ |
| **TOTAL** | **21** | **2,887** | **127+** |

**Coverage:** ~85% of core business logic

---

## Architecture at a Glance

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Yandex    │ HTTPS   │    Django    │ HTTPS   │  Telegram   │
│   Alice     ├────────►│   Backend    │◄────────┤    Bot      │
│  (Voice)    │ POST    │  (REST API)  │ Client  │  (Aiogram)  │
└─────────────┘         └──────┬───────┘         └─────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │  PostgreSQL  │
                        │   Database   │
                        └──────────────┘
```

**Data Models:**
- `AliceUser` - User accounts with hashed identifiers
- `BloodPressureMeasurement` - PHI data (systolic, diastolic, pulse)
- `AccountLinkToken` - Secure linking tokens (HMAC-hashed)

**Security:**
- HMAC-SHA256 hashing for user identifiers
- Token-based account linking (10-min expiry, one-time use)
- Rate limiting (60s cooldown, 100/day anon, 1000/min user)
- Comprehensive authorization (data scoped per user)

---

## Support

For questions or issues:
1. Check [inspection_report.md](inspection_report.md) for detailed analysis
2. Review [fixes.md](fixes.md) for implementation guidance
3. Run `./scripts/bootstrap.sh` to diagnose environment issues
4. Check test output: `pytest -v --tb=short`

---

**Generated:** 2025-11-12
**Inspection Method:** Multi-expert analysis (Django, Aiogram, Yandex.Dialogs, Security)
**Files Examined:** 87 files, ~15,000 lines of code
**Deliverables:** 7 documents + 3 scripts + 1 test suite + 1 CI/CD workflow
