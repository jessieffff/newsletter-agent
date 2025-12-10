# API Tests

This directory contains comprehensive tests for the Newsletter Agent API.

## Test Structure

- `test_models.py` - Pydantic model validation tests (21 tests)
- `test_storage.py` - Storage layer tests (9 tests)
- `test_api.py` - API endpoint and integration tests (14 tests)
- `conftest.py` - Pytest fixtures and configuration

## Running Tests

### Install Dependencies

```bash
cd apps/api
pip install -r requirements.txt
```

### Run All Tests

```bash
# From the apps/api directory
PYTHONPATH=/path/to/newsletter-agent/packages/agent/src:$PYTHONPATH python3 -m pytest tests/ -v

# Or use the simplified command if newsletter-agent package is installed
python3 -m pytest tests/ -v
```

### Run Specific Test Files

```bash
# Run only model tests
python3 -m pytest tests/test_models.py -v

# Run only storage tests
python3 -m pytest tests/test_storage.py -v

# Run only API tests
python3 -m pytest tests/test_api.py -v
```

### Run with Coverage

```bash
pip install pytest-cov
python3 -m pytest tests/ --cov=app --cov-report=html
```

## Test Coverage

### Model Validation Tests (21)
- UserIn: email validation
- SourceSpec: RSS URL validation, whitespace handling, different source types
- SubscriptionIn: topics validation, item count bounds, frequency options, defaults

### Storage Layer Tests (9)
- User creation and retrieval
- Case-insensitive email lookup
- Subscription CRUD operations
- Multi-user isolation
- Due subscriptions filtering

### API Endpoint Tests (14)
- Health check
- User creation and upsert
- Subscription creation with validation
- Subscription listing and updates
- Full integration flow
- Error handling

## Current Test Results

```
44 passed in 0.09s
```

All tests are passing with proper validation, error handling, and edge case coverage.
