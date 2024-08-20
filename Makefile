.PHONY: tox
tox:
	rm -rf .tox
	tox -p auto

.PHONY: test
test:
	pytest --cov --cov-config=./tests/.coveragerc --cov-report=term-missing -n auto tests

.PHONY: reformat
reformat:
	-ruff check . --fix
	-ruff format .
	-npx standard . --fix

.PHONY: lint
lint:
	-ruff . --no-fix
	-ruff format --check .
	-npx standard .

.PHONY: build
build:
	python3 -m build

.PHONY: init
init:
	poetry install
	npm install

.PHONY: init-demo
init-demo:
	-rm demo/db.sqlite3
	python demo/manage.py migrate
	DJANGO_SUPERUSER_PASSWORD="admin" python demo/manage.py createsuperuser  --username=admin --email=foo@bar.com --noinput

.PHONY: compilemessages
compilemessages:
	django-admin compilemessages --ignore .tox
