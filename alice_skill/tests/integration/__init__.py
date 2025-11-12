"""
Integration Tests for Alice BP Monitoring System

Integration tests focus on testing multiple components working together:
- API endpoints with authentication
- Webhook request/response cycles
- Database + API + handlers workflows
- End-to-end user flows (account linking, BP recording)
- Full CRUD operations with state verification

These tests typically:
- Use APITestCase or pytest client fixtures
- Make actual HTTP requests to endpoints
- Verify database state changes
- Test complete workflows
- May run slower than unit tests

Run integration tests only:
    pytest alice_skill/tests/integration/ -v
"""
