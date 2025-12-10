# Day 03 — Settings API + Minimal UI

## Goal
Ability to save a test subscription; bare-minimum UI.

## Deliverables
- Subscription CRUD endpoints (save/fetch)
- Ultra-simple settings form (topics, RSS URL, frequency)

## TODO
- [x] POST /subscriptions (create with topics[], sources[], frequency, item_count)
- [x] GET /subscriptions (list for current user)
- [x] Form validation (topics non-empty, RSS URL format check)
- [x] React form component: topics input, RSS URL, frequency dropdown
- [x] "Save subscription" wires to API
- [x] In-memory storage: subscriptions keyed by user_id
- [x] Unit tests for models, storage, and API endpoints (44 tests total)

## Acceptance checks
- [x] POST returns subscription ID
- [x] GET returns saved subscription
- [x] Form values persist in local state
- [x] No styling needed; function first
- [x] All tests passing (44/44)

## Implementation Summary

### Backend (API)
1. **Enhanced Models** (`apps/api/app/models.py`)
   - Added `EmailStr` validation for user emails
   - Added `SourceSpec` validation with RSS URL format checking
   - Added `SubscriptionIn` validation:
     - Topics: non-empty, whitespace trimming
     - Item count: 1-50 range validation
     - Whitespace handling for all string inputs

2. **API Endpoints** (`apps/api/app/routes/api.py`)
   - ✅ POST `/v1/users/{user_id}/subscriptions` - Create subscription
   - ✅ GET `/v1/users/{user_id}/subscriptions` - List subscriptions
   - ✅ PUT `/v1/users/{user_id}/subscriptions/{id}` - Update subscription
   - All endpoints include proper validation and error handling

3. **Storage Layer** (`apps/api/app/storage/memory.py`)
   - In-memory storage implementation
   - User management with case-insensitive email lookup
   - Subscription CRUD operations
   - Proper isolation per user

4. **Comprehensive Test Suite** (44 tests, all passing)
   - `tests/test_models.py` - 21 tests for Pydantic model validation
   - `tests/test_storage.py` - 9 tests for storage layer
   - `tests/test_api.py` - 14 tests for API endpoints + integration flow
   - Test fixtures for isolated test runs
   - Full coverage of validation edge cases

### Frontend (Web)
1. **Settings Page** (`apps/web/app/settings/page.tsx`)
   - Tabbed interface (Content, Sources, Delivery)
   - Form validation with real-time error messages
   - Email validation
   - Topics input with comma-separated values
   - RSS URL validation
   - Item count validation (1-50)
   - Error handling for API responses
   - Visual feedback for validation errors

2. **UI Components** (`components/ui/badge.tsx`)
   - Enhanced Badge component with variant support
   - Variants: default, secondary, destructive, outline

### Dependencies Added
- `pytest>=7.4` - Testing framework
- `pytest-asyncio>=0.21` - Async test support
- `email-validator` - Email validation for Pydantic

### Test Results
```
44 passed in 0.11s
- 21 model validation tests
- 9 storage layer tests  
- 14 API endpoint tests
```
