serve-api:
	uv run uvicorn events_poller.api.app:app --host localhost --port 8000

serve-poller:
	uv run python -m events_poller.poller.run

tests:
	uv run pytest tests

alembic-up:
	uv run alembic upgrade head

alembic-down:
	uv run alembic downgrade -1
