# Prioritized Security & Reliability Fixes

This document provides **7 actionable fixes** with code diffs, shell commands, and validation steps to make the Alice BP system production-ready.

---

## Priority 1: CRITICAL (Before Production)

### Fix #1: Enforce Alice Webhook Secret

**Severity:** 🔴 CRITICAL
**Time to Implement:** 2 minutes
**Risk if Not Fixed:** Unauthenticated attackers can submit fake BP data and extract PHI

**Current Code:**
`config/components/base.py:20`
```python
ALICE_WEBHOOK_SECRET = os.environ.get("ALICE_WEBHOOK_SECRET")  # ❌ Optional
```

**Problem:** Application starts even if `ALICE_WEBHOOK_SECRET` is not set, allowing insecure deployments.

**Fix:**

```diff
--- a/config/components/base.py
+++ b/config/components/base.py
@@ -19,6 +19,7 @@

 ALICE_WEBHOOK_SECRET = os.environ.get("ALICE_WEBHOOK_SECRET")
 TELEGRAM_ID_HMAC_KEY = os.environ.get("TELEGRAM_ID_HMAC_KEY")
 LINK_SECRET = os.environ.get("LINK_SECRET")

+if not ALICE_WEBHOOK_SECRET:
+    raise ImproperlyConfigured("ALICE_WEBHOOK_SECRET must be set in the environment.")
+
 if not TELEGRAM_ID_HMAC_KEY:
     raise ImproperlyConfigured("TELEGRAM_ID_HMAC_KEY must be set in the environment.")
```

**Implementation Steps:**

1. Edit `config/components/base.py` and add the validation:
   ```bash
   # Add these lines after line 22
   if not ALICE_WEBHOOK_SECRET:
       raise ImproperlyConfigured("ALICE_WEBHOOK_SECRET must be set in the environment.")
   ```

2. Ensure `.env` has the secret set:
   ```bash
   # Check if set
   grep "^ALICE_WEBHOOK_SECRET=" .env

   # If not set, generate one
   python manage.py generate_secret_keys | grep ALICE_WEBHOOK_SECRET >> .env
   ```

**Validation:**

```bash
# Test 1: Unset the secret temporarily
export ALICE_WEBHOOK_SECRET=""
python manage.py check
# Expected: ImproperlyConfigured exception

# Test 2: Set the secret
export ALICE_WEBHOOK_SECRET="your-secret-here"
python manage.py check
# Expected: System check identified no issues.

# Test 3: Run tests
pytest alice_skill/tests/test_webhook.py -v
# Expected: All webhook security tests pass
```

---

### Fix #2: Change DEBUG Default to False

**Severity:** 🔴 CRITICAL
**Time to Implement:** 1 minute
**Risk if Not Fixed:** Production deployments leak stack traces, SQL queries, and environment info

**Current Code:**
`config/components/base.py:11`
```python
DEBUG = os.environ.get("DEBUG", "True") == "True"  # ❌ Defaults to True
```

**Problem:** Default is `True`, requiring explicit opt-out. Should be `False` for security.

**Fix:**

```diff
--- a/config/components/base.py
+++ b/config/components/base.py
@@ -8,7 +8,7 @@
 )

 # SECURITY WARNING: don't run with debug turned on in production!
-DEBUG = os.environ.get("DEBUG", "True") == "True"
+DEBUG = os.environ.get("DEBUG", "False") == "True"

 ALLOWED_HOSTS = os.getenv(key="ALLOWED_HOSTS", default="127.0.0.1,localhost").split(",")
```

**Alternative (More Explicit):**

```python
# Even better: require explicit "True" to enable debug mode
DEBUG = os.environ.get("DEBUG", "").lower() == "true"
```

**Implementation Steps:**

1. Edit `config/components/base.py:11`:
   ```python
   DEBUG = os.environ.get("DEBUG", "False") == "True"
   ```

2. Update `.env.dist` template:
   ```bash
   # Change line 18 from DEBUG=True to:
   DEBUG=False
   ```

3. For development, explicitly set in `.env`:
   ```bash
   echo "DEBUG=True" >> .env
   ```

**Validation:**

```bash
# Test 1: Check default behavior
unset DEBUG
python -c "from config.settings import DEBUG; print('DEBUG =', DEBUG)"
# Expected: DEBUG = False

# Test 2: Enable for development
export DEBUG=True
python -c "from config.settings import DEBUG; print('DEBUG =', DEBUG)"
# Expected: DEBUG = True

# Test 3: Run deployment checks
export DEBUG=False
python manage.py check --deploy
# Expected: Should pass (or show non-DEBUG-related warnings)
```

---

## Priority 2: HIGH (Week 1)

### Fix #3: Add Production Readiness Checks

**Severity:** 🟠 HIGH
**Time to Implement:** 15 minutes
**Risk if Not Fixed:** Insecure configurations deployed to production

**Objective:** Create startup validation script that ensures all security requirements are met.

**Implementation:**

Create `alice_skill/management/commands/check_production_ready.py`:

```python
"""
Django management command: check_production_ready
Validates production security requirements

Usage: python manage.py check_production_ready
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import sys


class Command(BaseCommand):
    help = 'Check if application is configured for production deployment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--strict',
            action='store_true',
            help='Exit with error code if any check fails'
        )

    def handle(self, *args, **options):
        strict_mode = options.get('strict', False)
        errors = []
        warnings = []

        self.stdout.write(self.style.MIGRATE_HEADING("Production Readiness Check"))
        self.stdout.write("")

        # Check 1: DEBUG must be False
        if settings.DEBUG:
            errors.append("DEBUG is True (must be False in production)")
            self.stdout.write(self.style.ERROR("✗ DEBUG=True"))
        else:
            self.stdout.write(self.style.SUCCESS("✓ DEBUG=False"))

        # Check 2: SECRET_KEY must not be default insecure value
        insecure_key = "django-insecure-g!vb&)u#oa-zlerg68nyo(esv4^j(_=rtwd9ktf14=ken0#q_("
        if settings.SECRET_KEY == insecure_key:
            errors.append("SECRET_KEY is using default insecure value")
            self.stdout.write(self.style.ERROR("✗ SECRET_KEY is insecure default"))
        else:
            self.stdout.write(self.style.SUCCESS("✓ SECRET_KEY is custom"))

        # Check 3: Required secrets are set
        required_secrets = [
            'ALICE_WEBHOOK_SECRET',
            'TELEGRAM_ID_HMAC_KEY',
            'LINK_SECRET',
            'API_TOKEN'
        ]

        for secret in required_secrets:
            value = getattr(settings, secret, None)
            if not value:
                errors.append(f"{secret} is not set")
                self.stdout.write(self.style.ERROR(f"✗ {secret} not set"))
            else:
                self.stdout.write(self.style.SUCCESS(f"✓ {secret} is set"))

        # Check 4: ALLOWED_HOSTS should not be ['*']
        if '*' in settings.ALLOWED_HOSTS:
            warnings.append("ALLOWED_HOSTS contains '*' (should be specific domains)")
            self.stdout.write(self.style.WARNING("⚠ ALLOWED_HOSTS = ['*']"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✓ ALLOWED_HOSTS = {settings.ALLOWED_HOSTS}"))

        # Check 5: Database should not be SQLite in production
        db_engine = settings.DATABASES['default']['ENGINE']
        if 'sqlite' in db_engine.lower():
            warnings.append("Using SQLite database (not recommended for production)")
            self.stdout.write(self.style.WARNING("⚠ Database: SQLite"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✓ Database: {db_engine}"))

        # Check 6: CSRF_TRUSTED_ORIGINS should use HTTPS
        insecure_origins = [o for o in settings.CSRF_TRUSTED_ORIGINS if o.startswith('http://')]
        if insecure_origins and not settings.DEBUG:
            warnings.append("CSRF_TRUSTED_ORIGINS contains HTTP URLs (should be HTTPS)")
            self.stdout.write(self.style.WARNING(f"⚠ HTTP origins: {insecure_origins}"))
        else:
            self.stdout.write(self.style.SUCCESS("✓ CSRF_TRUSTED_ORIGINS configured"))

        # Summary
        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("Summary"))
        self.stdout.write(f"Errors: {len(errors)}")
        self.stdout.write(f"Warnings: {len(warnings)}")

        if errors:
            self.stdout.write("")
            self.stdout.write(self.style.ERROR("CRITICAL ISSUES:"))
            for error in errors:
                self.stdout.write(f"  • {error}")

        if warnings:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING("WARNINGS:"))
            for warning in warnings:
                self.stdout.write(f"  • {warning}")

        if not errors and not warnings:
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("✓ All checks passed!"))
            return

        if errors and strict_mode:
            raise CommandError("Production readiness check failed")
```

**Usage:**

```bash
# Development mode (informational)
python manage.py check_production_ready

# CI/CD mode (exit with error if issues found)
python manage.py check_production_ready --strict
```

**Integration with Deployment:**

Add to your deployment script:
```bash
#!/bin/bash
# deploy.sh

set -e

echo "Running production readiness check..."
python manage.py check_production_ready --strict

echo "Running Django deployment checks..."
python manage.py check --deploy

echo "All checks passed. Proceeding with deployment..."
# ... rest of deployment
```

**Validation:**

```bash
# Test with insecure config
export DEBUG=True
python manage.py check_production_ready
# Expected: Shows errors

# Test with secure config
export DEBUG=False
export SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
python manage.py check_production_ready --strict
# Expected: Passes or shows only warnings
```

---

## Priority 3: MEDIUM (Week 1-2)

### Fix #4: Add CI/CD Pipeline with Security Scanning

**Severity:** 🟡 MEDIUM
**Time to Implement:** 30 minutes
**Risk if Not Fixed:** Vulnerabilities introduced without detection

**Objective:** Automate testing and security scanning on every commit/PR.

**Implementation:**

Create `.github/workflows/ci.yml`:

```yaml
name: CI Pipeline

on:
  push:
    branches: [ main, develop, api_security ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: ["3.13"]

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install uv
      run: |
        curl -LsSf https://astral.sh/uv/install.sh | sh
        echo "$HOME/.cargo/bin" >> $GITHUB_PATH

    - name: Install dependencies
      run: |
        uv pip install --system -r requirements.txt
        uv pip install --system pytest pytest-django pytest-cov bandit safety

    - name: Set up test environment
      run: |
        cp .env.dist .env
        python manage.py generate_secret_keys > /tmp/keys.txt
        # Extract and set secrets
        export SECRET_KEY=$(grep SECRET_KEY /tmp/keys.txt | cut -d= -f2)
        export ALICE_WEBHOOK_SECRET=$(grep ALICE_WEBHOOK_SECRET /tmp/keys.txt | cut -d= -f2)
        export TELEGRAM_ID_HMAC_KEY=$(grep TELEGRAM_ID_HMAC_KEY /tmp/keys.txt | cut -d= -f2)
        export LINK_SECRET=$(grep LINK_SECRET /tmp/keys.txt | cut -d= -f2)
        export API_TOKEN=$(grep API_TOKEN /tmp/keys.txt | cut -d= -f2)
        echo "DEBUG=False" >> .env

    - name: Run Django checks
      run: |
        python manage.py check
        python manage.py check --deploy

    - name: Run migrations (dry run)
      run: |
        python manage.py migrate --check

    - name: Run tests with coverage
      run: |
        pytest --cov=alice_skill --cov=pyanywhere_bg --cov-report=xml --cov-report=term

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
        fail_ci_if_error: false

  security:
    name: Security Scanning
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.13"

    - name: Install dependencies
      run: |
        pip install bandit safety

    - name: Run Bandit (Python security scanner)
      run: |
        bandit -r alice_skill/ pyanywhere_bg/ config/ -f json -o bandit-report.json || true
        bandit -r alice_skill/ pyanywhere_bg/ config/ -f screen

    - name: Run Safety (dependency vulnerability check)
      run: |
        safety check --json || true
        safety check

    - name: Check for secrets in code
      run: |
        # Simple check for common secret patterns
        ! grep -r "SECRET_KEY = " --include="*.py" alice_skill/ config/ || exit 1
        ! grep -r "password = " --include="*.py" alice_skill/ || exit 1
        echo "✓ No hardcoded secrets found"

  lint:
    name: Code Quality
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.13"

    - name: Install dependencies
      run: |
        pip install ruff

    - name: Run Ruff linter
      run: |
        ruff check alice_skill/ pyanywhere_bg/ config/ --output-format=github

  production-readiness:
    name: Production Readiness Check
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.13"

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Check environment template
      run: |
        # Verify .env.dist doesn't have insecure defaults in production mode
        if grep -q "DEBUG=True" .env.dist; then
          echo "WARNING: .env.dist has DEBUG=True"
        fi

    - name: Validate required files
      run: |
        test -f .env.dist || exit 1
        test -f requirements.txt || exit 1
        test -f manage.py || exit 1
        echo "✓ All required files present"
```

**Usage:**

1. Commit the workflow file:
   ```bash
   git add .github/workflows/ci.yml
   git commit -m "Add CI/CD pipeline with security scanning"
   git push
   ```

2. View results in GitHub Actions tab

3. Configure branch protection to require CI pass before merge

**Validation:**

```bash
# Test locally with act (GitHub Actions local runner)
act -j test

# Or manually run the same commands:
python manage.py check
pytest --cov=alice_skill
bandit -r alice_skill/
safety check
```

---

### Fix #5: Document PostgreSQL Production Setup

**Severity:** 🟡 MEDIUM
**Time to Implement:** 20 minutes
**Risk if Not Fixed:** Production uses SQLite, leading to data corruption

**Objective:** Provide clear PostgreSQL migration path for production.

**Implementation:**

Create `docs/postgresql_setup.md`:

```markdown
# PostgreSQL Production Setup Guide

## Why PostgreSQL?

SQLite is unsuitable for production medical data because:
- ❌ No concurrent write support (locking issues)
- ❌ File corruption risk under load
- ❌ No built-in replication/backup
- ❌ Difficult to encrypt at rest
- ❌ No audit logging support

PostgreSQL provides:
- ✅ Concurrent multi-user access
- ✅ ACID compliance
- ✅ Built-in replication
- ✅ Encryption support (pgcrypto)
- ✅ Audit logging

## Installation

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib libpq-dev
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### macOS
```bash
brew install postgresql@16
brew services start postgresql@16
```

### Docker
```bash
docker run --name alice-bp-postgres \
  -e POSTGRES_DB=alice_bp \
  -e POSTGRES_USER=alice_bp_user \
  -e POSTGRES_PASSWORD=CHANGE_ME \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  -d postgres:16
```

## Database Setup

1. Create database and user:
```bash
sudo -u postgres psql

postgres=# CREATE DATABASE alice_bp;
postgres=# CREATE USER alice_bp_user WITH PASSWORD 'STRONG_PASSWORD_HERE';
postgres=# GRANT ALL PRIVILEGES ON DATABASE alice_bp TO alice_bp_user;
postgres=# ALTER DATABASE alice_bp OWNER TO alice_bp_user;
postgres=# \q
```

2. Set environment variable:
```bash
# Add to .env
DATABASE_URL=postgresql://alice_bp_user:STRONG_PASSWORD_HERE@localhost:5432/alice_bp
```

3. Install Python PostgreSQL adapter:
```bash
uv pip install psycopg2-binary
```

4. Run migrations:
```bash
python manage.py migrate
```

## Data Migration from SQLite

```bash
# 1. Backup SQLite database
cp db.sqlite3 db.sqlite3.backup

# 2. Install django-extensions
uv pip install django-extensions

# 3. Dump data from SQLite
python manage.py dumpdata --natural-foreign --natural-primary \
  -e contenttypes -e auth.Permission \
  --indent 2 -o dump.json

# 4. Switch to PostgreSQL
export DATABASE_URL=postgresql://alice_bp_user:PASSWORD@localhost:5432/alice_bp

# 5. Run migrations
python manage.py migrate

# 6. Load data into PostgreSQL
python manage.py loaddata dump.json

# 7. Verify data
python manage.py shell
>>> from alice_skill.models import BloodPressureMeasurement
>>> BloodPressureMeasurement.objects.count()
```

## Security Hardening

### 1. SSL/TLS Connection
```python
# config/components/database.py
DATABASES = {
    'default': {
        **dj_database_url.config(conn_max_age=600),
        'OPTIONS': {
            'sslmode': 'require',  # Enforce SSL
        }
    }
}
```

### 2. Read-Only User for Analytics
```sql
CREATE USER alice_bp_readonly WITH PASSWORD 'readonly_password';
GRANT CONNECT ON DATABASE alice_bp TO alice_bp_readonly;
GRANT USAGE ON SCHEMA public TO alice_bp_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO alice_bp_readonly;
```

### 3. Connection Pooling
```bash
uv pip install psycopg2-pool
```

```python
# config/components/database.py
DATABASES['default']['CONN_MAX_AGE'] = 600  # 10 minutes
```

## Backup Strategy

### Automated Daily Backup
```bash
#!/bin/bash
# /usr/local/bin/backup-alice-bp.sh

BACKUP_DIR="/var/backups/alice_bp"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/alice_bp_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

pg_dump -U alice_bp_user -h localhost alice_bp | gzip > $BACKUP_FILE

# Keep last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_FILE"
```

Add to crontab:
```bash
0 2 * * * /usr/local/bin/backup-alice-bp.sh
```

### Restore from Backup
```bash
gunzip -c /var/backups/alice_bp/alice_bp_20251112.sql.gz | psql -U alice_bp_user alice_bp
```

## Monitoring

### Query Performance
```sql
-- Enable pg_stat_statements
CREATE EXTENSION pg_stat_statements;

-- View slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### Connection Monitoring
```sql
SELECT count(*) FROM pg_stat_activity WHERE datname = 'alice_bp';
```

## Encryption at Rest

### Option 1: Full-Disk Encryption (Recommended)
Use LUKS (Linux) or FileVault (macOS) for database directory.

### Option 2: pgcrypto Extension
```sql
CREATE EXTENSION pgcrypto;

-- Example: encrypt sensitive columns
ALTER TABLE alice_skill_bloodpressuremeasurement
  ADD COLUMN notes_encrypted BYTEA;
```
```

**Validation:**

```bash
# Test PostgreSQL connection
python manage.py dbshell
# Should connect to PostgreSQL, not SQLite

# Run all migrations
python manage.py migrate

# Run tests against PostgreSQL
pytest

# Check performance
python manage.py shell
>>> from django.db import connection
>>> print(connection.vendor)
# Expected: postgresql
```

---

## Priority 4: LOW (Month 1-2)

### Fix #6: Add Audit Logging

**Severity:** 🟢 LOW
**Time to Implement:** 2 hours
**Risk if Not Fixed:** No compliance trail for PHI access

**Objective:** Log all access to Protected Health Information.

**Implementation Overview:**

1. Install django-auditlog:
   ```bash
   uv pip install django-auditlog
   ```

2. Add to `INSTALLED_APPS`:
   ```python
   INSTALLED_APPS = [
       # ...
       'auditlog',
   ]
   ```

3. Register models for auditing:
   ```python
   # alice_skill/apps.py
   from django.apps import AppConfig

   class AliceSkillConfig(AppConfig):
       name = 'alice_skill'

       def ready(self):
           from auditlog.registry import auditlog
           from .models import AliceUser, BloodPressureMeasurement, AccountLinkToken

           auditlog.register(AliceUser)
           auditlog.register(BloodPressureMeasurement)
           auditlog.register(AccountLinkToken)
   ```

4. Run migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. View audit logs in admin or via API

**See:** [django-auditlog documentation](https://django-auditlog.readthedocs.io/)

---

### Fix #7: Enhanced API Authentication (JWT)

**Severity:** 🟢 LOW
**Time to Implement:** 4 hours
**Risk if Not Fixed:** Token leakage has unlimited impact

**Objective:** Replace simple token auth with JWT tokens that expire and rotate.

**Implementation Overview:**

1. Install djangorestframework-simplejwt:
   ```bash
   uv pip install djangorestframework-simplejwt
   ```

2. Update DRF settings:
   ```python
   # config/components/drf.py
   REST_FRAMEWORK = {
       'DEFAULT_AUTHENTICATION_CLASSES': [
           'rest_framework_simplejwt.authentication.JWTAuthentication',
           'rest_framework.authentication.SessionAuthentication',
       ],
   }
   ```

3. Add token endpoints:
   ```python
   # config/urls.py
   from rest_framework_simplejwt.views import (
       TokenObtainPairView,
       TokenRefreshView,
   )

   urlpatterns = [
       path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
       path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
   ]
   ```

4. Update bot API client to use JWT

**See:** [djangorestframework-simplejwt documentation](https://django-rest-framework-simplejwt.readthedocs.io/)

---

## Validation Checklist

After implementing all fixes, run:

```bash
# 1. Production readiness check
python manage.py check_production_ready --strict

# 2. Django deployment checks
python manage.py check --deploy

# 3. Run all tests
pytest --cov

# 4. Security scan
bandit -r alice_skill/ config/

# 5. Dependency vulnerabilities
safety check

# 6. Manual security review
./scripts/test_yandex_webhook.sh http://localhost:8000/alice_webhook/ $ALICE_WEBHOOK_SECRET
```

## Deployment Order

1. **Immediate (before any production use):**
   - Fix #1: Enforce webhook secret ✅
   - Fix #2: DEBUG default to False ✅

2. **Week 1:**
   - Fix #3: Production readiness checks ✅
   - Fix #4: CI/CD pipeline ✅
   - Fix #5: PostgreSQL setup ✅

3. **Month 1:**
   - Fix #6: Audit logging ✅
   - Fix #7: Enhanced authentication ✅

---

**Total Time Investment:** ~8 hours
**Risk Reduction:** CRITICAL → LOW
**Compliance Improvement:** Minimal → HIPAA-ready baseline
