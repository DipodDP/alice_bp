# CI/CD Changes

This document outlines the changes to the CI/CD pipeline to support the new secure Telegram ID storage mechanism.

## 1. New Environment Variable

A new environment variable, `TELEGRAM_ID_HMAC_KEY`, must be added to the CI/CD environment for both the `alice_bp` and `tgbot_bp` services. This variable should contain a high-entropy secret key used for hashing the Telegram IDs.

## 2. New Tests

The following new tests have been added and must be included in the CI/CD pipeline:

*   `alice_skill/tests/test_telegram_id_migration.py`: Tests the data migration script for hashing existing Telegram IDs.
*   `tgbot_bp/tests/test_hashing.py`: Tests the hashing logic in the Telegram bot.

The existing test suites for both `alice_bp` and `tgbot_bp` should be run as part of the CI pipeline.

## 3. Gated Checks

The following checks should be gated and must pass before any pull request is merged:

*   All unit and integration tests for both `alice_bp` and `tgbot_bp` must pass.
*   The `migrate_telegram_ids` management command must be run in `--dry-run` mode to ensure that it executes without errors.

## 4. Deployment Pipeline

The deployment pipeline should be updated with the following steps:

1.  **Deploy `alice_bp` backend**:
    *   Deploy the new version of the `alice_bp` application.
    *   Run the `migrate` command to apply the new database schema migration.
    *   Run the `migrate_telegram_ids` management command to hash the existing Telegram IDs. This should be done **before** deploying the new `tgbot_bp` service.

2.  **Deploy `tgbot_bp` service**:
    *   Deploy the new version of the `tgbot_bp` application with the `TELEGRAM_ID_HMAC_KEY` environment variable set.

## 5. Rollback Plan

In case of any issues, the following rollback plan should be followed:

1.  **Rollback `tgbot_bp`**: Re-deploy the previous version of the `tgbot_bp` service.
2.  **Rollback `alice_bp`**:
    *   Re-deploy the previous version of the `alice_bp` application.
    *   Run the previous database migration to revert the schema changes.
    *   Restore the `telegram_user_id` column from a database backup taken before the migration.
