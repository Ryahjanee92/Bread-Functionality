## Copilot Instructions for Module14_is601

This file helps AI code agents quickly become productive in this FastAPI + SQLAlchemy project.

Overview
- FastAPI app in `app/main.py` exposes HTML pages (Jinja2 templates) and REST APIs.
- Models: SQLAlchemy in `app/models/` (User, Calculation). `Calculation` uses single-table polymorphism with subclasses (Addition, Subtraction, Multiplication, Division).
- Schemas: Pydantic v2 in `app/schemas/`. Use `model_validator` & `field_validator` when working with input validation.
- Auth: JWT handled in `app/auth/jwt.py` and dependencies in `app/auth/dependencies.py` (two `get_current_user` wrappers exist — one returns `UserResponse`, the other returns `User` model). Use `get_current_active_user` for secured endpoints.
- Tests: Integration & e2e tests run in `tests/` with a local `uvicorn` server launched by `conftest.py`. Playwright is used for browser-based tests.

Key Files to Open First
- `app/main.py` — app routes, template mounts, and main REST endpoints.
- `app/models/*` — business logic for models and tokens.
- `app/schemas/*` — validation logic and examples.
- `tests/conftest.py` — database & server fixtures (important for test flow & port selection).

Patterns & Conventions
- Database: `app/database.py` provides `get_engine()` and `get_sessionmaker()` helpers used in tests to use a different engine.
- Tokens: Use `User.create_access_token`/`create_refresh_token` and `jwt.decode_token` helpers instead of direct `jose` calls.
- Calculations: Use `Calculation.create()` factory to create the proper subclass. Do not directly instantiate subclasses unless needed for model-level tests.
- Front-end: JS uses `localStorage` to store `access_token`. UI routes check for tokens and redirect to `/login` if missing.
- Test patterns: Integration tests use `requests` for direct API behavior; e2e/Playwright tests rely on browser UI flows and `page` fixture.

Playwright Tests
- UI-based tests in `tests/e2e/test_playwright_ui.py` cover register/login flows and BREAD operations via the UI.
- Use `fastapi_server` fixture (in `conftest.py`) to get the running server URL.
- When writing UI tests, prefer using CSS selectors found in templates (e.g., `#calcInputs`, `#calculationForm`, `#calculationsTable`, `#errorAlert`) and `page.wait_for_selector()` to synchronize.

Development & Run Commands
- Local dev server (fast reload): `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`.
- Run all tests: `pytest` (coverage is enabled in `pytest.ini`).
- Run only e2e tests: `pytest -m e2e`.
- Docker compose: `docker-compose up --build` starts Postgres, pgadmin and the app.

Auto-commit / Sync
- The repository includes a small watcher script to auto-stage, commit and push changes during local development: `scripts/autocommit.py`.
- Run it with `python3 scripts/autocommit.py --interval 2` or use `scripts/run_autocommit.sh` to background it.
- It's a convenience tool and not intended for CI or production; review the script before enabling in a shared environment.

Notes for AI Agents (Do's)
- When adding API endpoints, follow the patterns in `app/main.py`: use `Depends(get_db)` for DB sessions and `get_current_active_user` for auth.
- When editing models, ensure you add migrations or `Base.metadata.create_all()` usage in `app/database_init.py` if needed for testing.
- Use `conftest.py` for tests: `TestingSessionLocal` and `get_engine()` to isolate DB for tests.
- Prefer using the Pydantic schemas for validation and rely on existing `model_validator` or `field_validator` for business rules.
- For UI changes, update `templates/*` and the scripts embedded in those templates; some JS logic is repeated across templates — adjust carefully.

Notes for AI Agents (Don'ts)
- Don't bypass authentication in endpoint changes — use consistent token checks and `get_current_active_user`.
- Don't directly modify session and engine behavior in `conftest.py` — if needed, use `get_engine()` factory.

Testing & Troubleshooting
- When tests fail with server not starting, check `conftest.py` port selection logic and `/health` endpoint. The `wait_for_server()` helper waits up to 30s.
- If Playwright tests fail, ensure `playwright` is installed and up-to-date. The project uses `playwright` shared in `requirements.txt`.
- If tests need DB changes, add DB setup / teardown under `tests/conftest.py` and ensure fixtures call `Base.metadata.create_all`.

Example Quick Tasks
- Add a new calculation type:
  - Add new subclass in `app/models/calculation.py` and a new enum value/validation in `app/schemas/calculation.py`.
  - Add unit tests under `tests/unit` for `get_result()` and integration tests under `tests/integration` for API behavior.
  - Update front-end: add option to `#calcType` selects and ensure preview/calculation logic supports it.

If you need more details on how to implement a specific change, say which component (API, UI, tests) and I'll provide a focused plan and patch.
