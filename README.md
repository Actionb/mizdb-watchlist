# mizdb-watchlist

Django model and views that implement a "watchlist" of other Django objects.

<!-- TOC -->
* [mizdb-watchlist](#mizdb-watchlist)
  * [Installation](#installation)
  * [How to use](#how-to-use)
    * [Manipulating the watchlist](#manipulating-the-watchlist)
      * [Toggle button](#toggle-button)
      * [ListViews and the `on_watchlist` QuerySet annotation](#listviews-and-the-on_watchlist-queryset-annotation)
      * [ListViewMixin](#listviewmixin)
    * [Displaying the watchlist](#displaying-the-watchlist)
      * [Link to the watchlist](#link-to-the-watchlist)
    * [Admin integration](#admin-integration)
      * [Admin toggle button & watchlist link](#admin-toggle-button--watchlist-link)
      * [ModelAdminMixin](#modeladminmixin)
  * [Demo & Development](#demo--development)
    * [Tests](#tests)
    * [Linting & Formatting](#linting--formatting)
    * [Demo:](#demo)
<!-- TOC -->

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

This library provides a toggle button for adding individual items, as well as a 
list action for adding multiple items, and a default template for rendering the 
overview over what's on the watchlist. 

The watchlist items are stored in a Watchlist model for authenticated users. 
For unauthenticated users, the watchlist is stored in a local Django session instead.

The `mizdb_watchlist/js/watchlist.js` javascript drives the toggle button and the
buttons on the watchlist overview.

The styling was written with Bootstrap in mind. Alternatively, some rudimentary
styling is provided with `mizdb_watchlist/css/watchlist.css`. 
You can use this for the admin site or if you don't want to use Bootstrap.

### Manipulating the watchlist

#### Toggle button

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
| text         | `""`          | optional text for the button                                                              |
| url          | `None`        | the URL for the view that handles the toggling. Defaults to `reverse("watchlist:toggle")` |
| on_watchlist | `None`        | an optional boolean that indicates whether the item is on the watchlist                   |


#### ListViews and the `on_watchlist` QuerySet annotation

Note that if a value for the `on_watchlist` argument is not provided to the toggle 
button tag (i.e. the value is `None`), the tag will make a query to check if the 
item is on the watchlist. This is acceptable if you are only rendering one toggle 
button per page. But if you are rendering multiple toggle buttons per page, for 
example one for each item in a list view, then this will create a query and a 
database hit for each button, slowing down the page.

To easily provide a `on_watchlist` value for each object in a queryset in a single 
query, call the `annotate_queryset` method on a watchlist manager on the queryset.
For example:
```python
from mizdb_watchlist.manager import get_manager

class MyListView(ListView):
    
    def get_queryset(self):
        queryset = super().get_queryset()
        manager = get_manager(self.request)
        queryset = manager.annotate_queryset(queryset)
        return queryset
```

This adds a `on_watchlist` annotation to each object in the queryset. 
You can then use the annotation as an argument for the tag like this:
```html
{% for object in object_list %}
  ...
  {% toggle_button view.request object on_watchlist=object.on_watchlist %}
{% endfor %}
```

#### ListViewMixin
To add the above annotations, you can add the `ListViewMixin` to your ListViews:
```python
from mizdb_watchlist.views import ListViewMixin

class MyListView(ListViewMixin, ListView):
    pass
```

Additionally, if the right GET query parameter is present, `ListViewMixin` filters 
the queryset to only include items on the watchlist. 
This is utilized, for example, by the changelist links on the watchlist overview.

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

| Argument   | Default value  | Description                                                                         |
|------------|----------------|-------------------------------------------------------------------------------------|
| view_name  | **required**   | the view name of the watchlist as declared in the URL conf                          |
| icon       | `True`         | an optional boolean indicating whether an icon should be included in the link HTML  |

### Admin integration

This library comes with a ModelAdmin for the Watchlist model. 
The ModelAdmin provides an admin view for the watchlist overview and adds it 
to the ModelAdmin's URLs with the view name `watchlist`. The URL of the overview 
can be reversed with `reverse(f"{your_admin_site.name}:watchlist")`.

The ModelAdmin itself lets admins inspect and modify the (model) watchlists of 
other users, while the overview displays the watchlist items of the current admin user.

The ModelAdmin adds the `add_to_watchlist` action that lets you select items on 
the changelist page and add them to your watchlist via admin actions.

The ModelAdmin is hooked up to Django's default admin site.
If you are not using the default admin site, make sure to register the ModelAdmin with your site:
```python
from django.contrib import admin
from mizdb_watchlist.admin import WatchlistAdmin
from mizdb_watchlist.models import Watchlist

@admin.register(Watchlist, site=my_admin_site)
class MyWatchlistAdmin(WatchlistAdmin):
    pass
```

#### Admin toggle button & watchlist link

To include the toggle button on admin change pages, you can override the 
`admin/change_form.html` template. For example like this:
```html
{% extends "admin/change_form.html" %}
{% load static mizdb_watchlist %}

{% block extrahead %}
  {{ block.super }}
  <link rel="stylesheet" href="{% static 'mizdb_watchlist/css/watchlist.css' %}">
  <script src="{% static 'mizdb_watchlist/js/watchlist.js' %}"></script>
{% endblock extrahead %}

{% block content_subtitle %}{% if subtitle %}<h2>{{ subtitle }} {% toggle_button request original %}</h2>{% endif %}{% endblock %}
``` 

To add a link to the watchlist overview to the admin user links, overwrite 
`admin/base.html` like this:
```html
{% extends "admin/base.html" %}
{% load mizdb_watchlist %}

{% block userlinks %}
  {% watchlist_link '<name of your admin site>:watchlist' icon=False %} /
  {{ block.super }}
{% endblock %}
```
**NOTE**: see [Overriding admin templates](https://docs.djangoproject.com/en/5.0/ref/contrib/admin/#admin-overriding-templates) 
for more details on how to override admin templates. 

#### ModelAdminMixin

The `ModelAdminMixin` is the admin version of the `ListViewMixin`. The mixin adds 
annotations and filtering (see [ListViewMixin](#listviewmixin)) to the ModelAdmin's 
queryset.
```python
from mizdb_watchlist.views import ModelAdminMixin

@admin.register(MyModel)
class MyModelAdmin(ModelAdminMixin, admin.ModelAdmin):
    pass
```


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