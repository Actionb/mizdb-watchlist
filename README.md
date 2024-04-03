# mizdb-watchlist

Django model and views that implement a "watchlist" of other Django objects.

## Installation

Install using pip:
```commandline
pip install -U mizdb-watchlist
```

Then add to your `INSTALLED_APPS` settings:
```python
INSTALLED_APPS = [
    ...,
    "mizdb_watchlist"
]
```
NOTE: ensure that Django's SessionMiddleware is [enabled](https://docs.djangoproject.com/en/5.0/topics/http/sessions/).


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