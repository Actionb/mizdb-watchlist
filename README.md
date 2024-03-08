# mizdb-watchlist

Django model and views that implement a "watchlist" of other Django objects.

## Demo & Development

Install using [poetry](https://python-poetry.org/docs/):
```commandline
poetry install
```

Install JavaScript Standard Style (for formatting/linting) and Bootstrap (for the demo):
```commandline
npm install
```

### Tests
Run tests with 
```commandline
make test
```
And
```commandline
make tox
```

### Linting & Formatting

Use 
```commandline
make lint
```
to check for code style issues and use
```commandline
make reformat
```
to fix the issues.

### Demo:

To start the demo server:

```commandline
make init-demo
python demo/manage.py runserver
```