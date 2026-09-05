build:
	docker compose -f local.yml up --build -d --remove-orphans

up:
	docker compose -f local.yml up -d

down-v:
	docker compose -f local.yml down -v

down:
	docker compose -f local.yml down

config:
	docker compose -f local.yml config

make-migrations:
	docker compose -f local.yml exec -it api alembic revision --autogenerate -m "$(name)"

migrate:
	docker compose -f local.yml exec api alembic upgrade head

history:
	docker compose -f local.yml exec api alembic history

current-migration:
	docker compose -f local.yml exec api alembic current

downgrade:
	docker compose -f local.yml exec -it api alembic downgrade $(version)

inspect-network:
	docker network inspect bankfraud_local_nw

psql:
	docker compose -f local.yml exec -it postgres psql -U alphaogilo -d bank