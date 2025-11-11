# Implementation Tasks

This document breaks down the implementation of the secure Telegram ID storage mechanism into a series of smaller, manageable tasks. Each task is designed to be the size of a single pull request.

## Phase 1: Preparation and Initial Setup

1.  **Task**: Create a new feature branch for the project.
    *   **Description**: Create a new git branch to isolate the changes for this feature.
    *   **Effort**: Small

2.  **Task**: Add a new secret key to the environment.
    *   **Description**: Add a new environment variable `TELEGRAM_ID_HMAC_KEY` to the `.env.dist` files in both `alice_bp` and `tgbot_bp`. Generate a strong secret key and add it to the local `.env` files.
    *   **Effort**: Small

## Phase 2: Backend Changes (`alice_bp`)

3.  **Task**: Create a data migration script for existing Telegram IDs.
    *   **Description**: Create a Django management command to migrate the existing plaintext `telegram_user_id`s to their HMAC-SHA256 hashed equivalents. The script must be idempotent, resumable, and have a `--dry-run` mode.
    *   **TDD**: Write unit tests for the migration script's logic.
    *   **Effort**: Medium

4.  **Task**: Create a database schema migration.
    *   **Description**: Create a Django schema migration to change the `telegram_user_id` field in the `AliceUser` model. The field should be a `CharField` with a length of 64 and should be indexed.
    *   **TDD**: The migration itself is the implementation.
    *   **Effort**: Small

5.  **Task**: Update the `AliceUser` model and related queries.
    *   **Description**: Update the `AliceUser` model to reflect the new `telegram_user_id` field type. Update all queries that use the `telegram_user_id` field to work with the hashed ID.
    *   **TDD**: Write unit tests to verify that the queries work as expected.
    *   **Effort**: Medium

6.  **Task**: Update the `UserByTelegramView` API endpoint.
    *   **Description**: Update the `UserByTelegramView` to expect a hashed Telegram ID in the URL.
    *   **TDD**: Write integration tests for the updated API endpoint.
    *   **Effort**: Small

## Phase 3: Telegram Bot Changes (`tgbot_bp`)

7.  **Task**: Implement the Telegram ID hashing logic.
    *   **Description**: In the `tgbot_bp` service, create a utility function to hash the Telegram ID using HMAC-SHA256 and the `TELEGRAM_ID_HMAC_KEY`.
    *   **TDD**: Write unit tests for the hashing function.
    *   **Effort**: Small

8.  **Task**: Update the `bp_api` client.
    *   **Description**: Update the `bp_api` client to use the new hashing function before sending the Telegram ID to the `alice_bp` API.
    *   **TDD**: Write unit tests for the updated API client.
    *   **Effort**: Medium

9.  **Task**: Update the bot handlers.
    *   **Description**: Update the bot handlers in `tgbot/handlers/user.py` to use the updated `bp_api` client.
    *   **TDD**: Write integration tests for the bot handlers.
    *   **Effort**: Medium

## Phase 4: Testing and CI/CD

10. **Task**: Create end-to-end tests.
    *   **Description**: Create at least one end-to-end test that simulates the entire flow, from a user interacting with the bot to the data being stored securely in the database.
    *   **Effort**: Medium

11. **Task**: Update the CI/CD pipeline.
    *   **Description**: Update the CI/CD pipeline to run the new tests. Create a `ci/README.md` file to document the changes.
    *   **Effort**: Small

## Phase 5: Deployment and Rollout

12. **Task**: Create a security verification checklist.
    *   **Description**: Create a markdown file with a checklist of security verifications to be performed before deployment.
    *   **Effort**: Small

13. **Task**: Document the rollout and rollback plan.
    *   **Description**: Add a section to the `design.md` file detailing the steps for rolling out the new feature and for rolling it back in case of issues.
    *   **Effort**: Small
