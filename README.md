# mizdb-watchlist

Django model and views that implement a "watchlist" of other Django objects.

## Demo & Development

Install (requires [poetry](https://python-poetry.org/docs/) and npm):
```commandline
make init
```

### Tests
Install required playwright browsers with:
```commandline
playwright install
```
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
to check for code style issues. Use
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