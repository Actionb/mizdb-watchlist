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


## How to use

This library provides a toggle button for adding individual items, as well as a list action for adding
multiple items, and a default template for rendering the watchlist. 

### Toggle button

The toggle button adds an item to your watchlist if it is not already on it, or
removes it from the watchlist if the item is already on it. 
If the item is on the watchlist, the button is rendered with the `on-watchlist` CSS class.

The `toggle_button` template tag adds a button to your page:
```html
{% load static mizdb_watchlist %}
{% block extrahead %}
    <script src="{% static 'mizdb_watchlist/js/watchlist.js' %}"></script>
{% endblock extrahead %}

{% block content %}
    <h5>{{ object }} {% toggle_button view.request object %}</h5>
    ...
{% endblock content %}
```
The template tag takes the following arguments:

| Argument     | Default value | Description                                                                               |
|--------------|---------------|-------------------------------------------------------------------------------------------|
| request      | **required**  | the view's request                                                                        |
| obj          | **required**  | the model object to add or remove                                                         |
| text         | ""            | optional text for the button                                                              |
| url          | None          | the URL for the view that handles the toggling. Defaults to `reverse("watchlist:toggle")` |
| on_watchlist | None          | an optional boolean that indicates whether the item is on the watchlist                   |


### ListViews and the `on_watchlist` QuerySet annotation

Note that if a value for the `on_watchlist` argument is not provided to the toggle button tag (i.e. the value is `None`),
the tag will make a query to check if the item is on the watchlist. This is acceptable if you are only rendering
one toggle button per page. But if you are rendering multiple toggle buttons (for example one for each
item in a list view), then this will create a query and a database hit for each button, slowing down the page.

To easily provide a `on_watchlist` value for each object in a queryset in a single query, call the 
`annotate_queryset` method on a watchlist manager with the queryset. For example:
```python
from mizdb_watchlist.manager import get_manager

class MyListView(ListView):
    
    def get_queryset(self):
        queryset = super().get_queryset()
        manager = get_manager(self.request)
        queryset = manager.annotate_queryset(queryset)
        return queryset
```

This adds a `on_watchlist` annotation to each object in the queryset. You can then use the annotation like this:
```html
{% for object in object_list %}
  ...
  {% toggle_button view.request object on_watchlist=object.on_watchlist %}
{% endfor %}
```

You can also use the `ListViewMixin` to add annotations to your ListViews:
```python
from mizdb_watchlist.views import ListViewMixin

class MyListView(ListViewMixin, ListView):
    pass
```

### Displaying the watchlist

Add `WatchlistViewMixin` to a template view:
```python
from mizdb_watchlist.views import WatchlistViewMixin

class MyWatchlistView(WatchlistViewMixin, TemplateView):
    template_name = "watchlist.html"
```

Include the view in your URL conf:
```python
urlpatterns = [
    ...,
    path("watchlist/", MyWatchlistView.as_view(), name="my_watchlist"),
]
```

Render the HTML for the watchlist in your template, for example:
```html
<!-- template for MyWatchlistView -->
{% extends "base.html" %}
{% load static %}

{% block extrahead %}
    <script src="{% static 'mizdb_watchlist/js/watchlist.js' %}"></script>
{% endblock %}

{% block content %}
    {% include "mizdb_watchlist/watchlist.html" %}
{% endblock content %}
```

#### Link to the watchlist

The template tag `watchlist_link` renders a hyperlink to the watchlist overview.
You can add this to your site navigation:
```html
<nav>
  <ul>
    ...
    <li class="nav-item">{% watchlist_link 'my_watchlist' %}</li>
  </ul>
</nav>
```
The tag takes two arguments:

| Argument   | Default value | Description                                                                         |
|------------|---------------|-------------------------------------------------------------------------------------|
| view_name  | **required**  | the view name of the watchlist as declared in the URL conf                          |
| icon       | True          | an optional boolean indicating whether an icon should be included in the link HTML  |

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