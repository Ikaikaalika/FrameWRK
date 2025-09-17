.PHONY: up down logs ps test seed

up:
	docker compose up --build

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=100

ps:
	docker compose ps

test:
	docker compose exec backend pytest -q

seed:
	docker compose exec backend bash -lc "python scripts/ingest.py scripts/seed_docs"
