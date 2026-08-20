# .revy/rules/backend.md

# Backend

Python 3.12, FastAPI, SQLAlchemy 2.0 async, Pydantic v2, PostgreSQL. Enums: `snake_case` keys **and** values.

- Models `*ORM`; enums in `app.constants.enums` — not on the model, not PascalCase.
- No SQLModel. All DB I/O async.
- API errors: `app.core.exceptions` (`NotFoundError`, `ValidationError`, `ForbiddenError`). Envelope `{"success": false, "error": {"code", "message"}}`.
- JSON the frontend consumes: `float`, not `Decimal` (ORM may keep Decimal).
- List endpoints: cursor pagination `(created_at DESC, id DESC)` — not offset for data-heavy lists.
- JSONB arrays: `jsonb_array_or_empty_sql` / `jsonb_array_elements_safe_sql` — never bare `jsonb_array_elements(col)` or `jsonb_array_elements(COALESCE(...))`.
- Logging: `logging.getLogger(__name__)` + `extra={}`; no `print()`.
- Migrations: handwritten only — never `alembic revision --autogenerate`.
- Tests: `tests/unit/` default; `tests/api/` only for route/schema/auth, max 3 new HTTP tests per wave; do not add `tests/service/`.
