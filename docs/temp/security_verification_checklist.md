# Security Verification Checklist

This checklist should be used to verify the security of the new Telegram ID storage mechanism before and after deployment.

## Pre-Deployment

- [ ] **Code Review**:
    - [ ] The `TELEGRAM_ID_HMAC_KEY` is not hardcoded in the source code.
    - [ ] The `get_hashed_telegram_id` function uses a strong, vetted HMAC algorithm (HMAC-SHA256).
    - [ ] The `migrate_telegram_ids` management command correctly hashes the Telegram IDs.
    - [ ] The `bp_api` client in `tgbot_bp` is sending hashed IDs to the `alice_bp` API.
    - [ ] The `alice_bp` API endpoints are expecting and handling hashed IDs.
- [ ] **Configuration**:
    - [ ] A strong, high-entropy secret key has been generated for `TELEGRAM_ID_HMAC_KEY`.
    - [ ] The `TELEGRAM_ID_HMAC_KEY` is securely stored and managed (e.g., in a secret management system or as a secure environment variable).
- [ ] **Testing**:
    - [ ] All new and existing tests pass in the CI/CD pipeline.
    - [ ] The `migrate_telegram_ids` management command has been tested in a staging environment with a copy of the production database.

## Post-Deployment

- [ ] **Verification**:
    - [ ] The `alice_skill_aliceuser` table in the production database contains only hashed Telegram IDs (64-character hex strings).
    - [ ] The application is functioning correctly. Users can link their accounts, and the bot can retrieve user data.
- [ ] **Monitoring**:
    - [ ] Monitor the application logs for any errors related to the new hashing mechanism.
    - [ ] Monitor the database for any plaintext Telegram IDs being written to the `alice_skill_aliceuser` table.
- [ ] **Incident Response**:
    - [ ] The rollback plan has been reviewed and is ready to be executed if needed.
    - [ ] The team is aware of the changes and knows how to respond to any issues.
