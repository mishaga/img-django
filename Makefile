build:
	docker-compose build

migrate:
	docker-compose run --rm web python manage.py migrate

collectstatic:
	docker-compose run --rm web python manage.py collectstatic

shell:
	docker-compose run --rm web bash

up:
	docker-compose up

up-d:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose down && docker-compose up -d

autotests:
	docker-compose run --rm web bash -c "coverage run --source='.' manage.py test && coverage report"

lint:
	docker-compose run --rm web bash -c "flake8 . --count && mypy ."

logs:
	docker logs img-web
