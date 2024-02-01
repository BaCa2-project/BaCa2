.PHONY: install
install:
	poetry intall

.PHONY: update
update:
	poetry update

.PHONY: migrations
migrations:
	poetry run python BaCa2/manage.py makemigrations

.PHONY: migrate
migrate:
	poetry run python BaCa2/manage.py migrate

#tests:
#	poetry run python BaCa2/manage.py test

.PHONY: update-all
update-all: update migrations migrate;
