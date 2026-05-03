.PHONY: dev up down backend frontend test migrate revision

dev:
	docker compose up --build

up:
	docker compose up -d --build

down:
	docker compose down

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest -q

migrate:
	cd backend && alembic upgrade head

revision:
	cd backend && alembic revision --autogenerate -m "$(m)"


seed-demo:
	cd backend && python scripts/seed_demo.py

smoke:
	cd backend && python scripts/smoke_test.py http://localhost:8000
