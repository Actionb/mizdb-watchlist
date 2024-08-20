# mizdb-watchlist

Django model and views that implement a watchlist of other Django objects.

This library provides a toggle button for adding individual items, a list view
action for adding multiple items, and a default template for rendering the
overview of what's on the watchlist.

The watchlist items are stored in a Watchlist model for authenticated users.
For unauthenticated users, the watchlist is stored in a Django session instead.

The styling was written with [Bootstrap](https://getbootstrap.com/) in mind.
Alternatively, some rudimentary styling is provided with `mizdb_watchlist/css/watchlist.css`
and `mizdb_watchlist/css/watchlist_toggle.css`.
You can use these for the admin site or if you don't want to use Bootstrap.

[comment]: <> (@formatter:off)
<!-- TOC -->
* [mizdb-watchlist](#mizdb-watchlist)
  * [Installation](#installation)
  * [Manipulating the watchlist](#manipulating-the-watchlist)
    * [Toggle button](#toggle-button)
    * [ListViews and the `on_watchlist` QuerySet annotation](#listviews-and-the-on_watchlist-queryset-annotation)
    * [views.WatchlistMixin](#viewswatchlistmixin)
  * [Displaying the watchlist](#displaying-the-watchlist)
    * [Link to the watchlist](#link-to-the-watchlist)
  * [Admin integration](#admin-integration)
    * [Admin toggle button & watchlist link](#admin-toggle-button--watchlist-link)
    * [admin.WatchlistMixin](#adminwatchlistmixin)
    * [Admin action](#admin-action)
  * [Initializing buttons](#initializing-buttons)
  * [Demo & Development](#demo--development)
    * [Tests](#tests)
    * [Linting & Formatting](#linting--formatting)
    * [Demo](#demo)
<!-- TOC -->
[comment]: <> (@formatter:on)

## Installation

Install using pip:

```commandline
pip install -U mizdb-watchlist
```

Then add to your `INSTALLED_APPS` settings:

```python
INSTALLED_APPS = [
    ...,
    "mizdb_watchlist",
]
```

Include the watchlist URLs in your URL conf:

```python
urlpatterns = [
    ...,
    path("mizdb_watchlist/", include("mizdb_watchlist.urls")),
]
```

Finally, run the migration to add the Watchlist model:

```commandline
python manage.py migrate mizdb_watchlist
```

> ⚠️️ **Note**:
>
> Django's SessionMiddleware must be [enabled](https://docs.djangoproject.com/en/5.0/topics/http/sessions/).

## Manipulating the watchlist

### Toggle button

The toggle button adds an item to your watchlist if it is not already on it,
otherwise it removes the item from the watchlist. If the item is on the watchlist,
the button is rendered with the `on-watchlist` CSS class.

Use the `toggle_button` template tag to a button to your page:

[comment]: <> (@formatter:off)
```html
{% load static mizdb_watchlist %}
{% block extrahead %}
  <script src="{% static 'mizdb_watchlist/js/watchlist.js' %}"></script>

  {# watchlist_init.js will initialize any watchlist buttons on the page #}
  <script src="{% static 'mizdb_watchlist/js/watchlist_init.js' %}"></script>

  {# Optional stylesheet, to make the button change color when toggled: #}
  <link rel="stylesheet" href="{% static 'mizdb_watchlist/css/watchlist_toggle.css' %}">

{% endblock extrahead %}

{% block content %}
  <h5>{{ object }} {% toggle_button view.request object classes='foo bar' %}</h5>
  ...
{% endblock content %}
```
[comment]: <> (@formatter:on)

> ℹ️ **Note**:
>
> The `mizdb_watchlist/js/watchlist.js` javascript drives the toggle button and the
> buttons that remove items on the watchlist overview. Make sure you include it.

The template tag takes the following arguments:

| Argument     | Default value | Description                                                                               |
|--------------|---------------|-------------------------------------------------------------------------------------------|
| request      | **required**  | the view's request                                                                        |
| obj          | **required**  | the model object to add or remove                                                         |
| text         | `""`          | optional text for the button                                                              |
| url          | `None`        | the URL for the view that handles the toggling. Defaults to `reverse("watchlist:toggle")` |
| on_watchlist | `None`        | an optional boolean that indicates whether the item is on the watchlist                   |
| classes      | `""`          | additional CSS classes for the button                                                     |

### ListViews and the `on_watchlist` QuerySet annotation

Note that if a value for the `on_watchlist` argument is not provided to the toggle
button tag (i.e. the value is `None`), the tag will make a query to check if the
item is on the watchlist. This is acceptable if you are only rendering one toggle
button per page. But if you are rendering multiple toggle buttons per page, for
example one for each item in a list view, then this will create a query and a
database hit for each button, slowing down the page.

To provide a `on_watchlist` value for each object in a queryset in a single
query, call the watchlist manager method `annotate_queryset` on the queryset:

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

[comment]: <> (@formatter:off)
```html
{% for object in object_list %}
  ...
  {% toggle_button view.request object on_watchlist=object.on_watchlist %}
{% endfor %}
```
[comment]: <> (@formatter:on)

### views.WatchlistMixin

The `WatchlistMixin` modifies a ListView's queryset to add the above annotations.
Additionally, if the right GET query parameter is present, `WatchlistMixin` filters
the queryset to only include items on the watchlist.
This is utilized, for example, by the changelist links on the watchlist overview.

Add the `WatchlistMixin` to your ListViews like this:

```python
from mizdb_watchlist.views import WatchlistMixin


class MyListView(WatchlistMixin, ListView):
    pass
```

## Displaying the watchlist

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

[comment]: <> (@formatter:off)
```html
<!-- template for MyWatchlistView -->
{% extends "base.html" %}
{% load static %}

{% block extrahead %}
  <script src="{% static 'mizdb_watchlist/js/watchlist.js' %}"></script>
  <script src="{% static 'mizdb_watchlist/js/watchlist_init.js' %}"></script>
{% endblock %}

{% block content %}
  {% include "mizdb_watchlist/watchlist.html" %}
{% endblock content %}
```
[comment]: <> (@formatter:on)

The watchlist overview groups the watchlist items by model. Each watchlist item
includes a link to the item's change page, and each group includes a link to the
changelist for the group's model. The changelist URL includes a query parameter
to filter the changelist to only show the model objects that are currently on the
watchlist (this requires [WatchlistMixin](#viewswatchlistmixin) on the changelist
view).

By default, the URLs for the links are reversed with URL names that follow the
Django admin URL naming
scheme ([see Reversing Admin URLs](https://docs.djangoproject.com/en/5.0/ref/contrib/admin/#reversing-admin-urls)),
i.e. `{{app_label}}_{{model_name}}_changelist`.
If you are using a different URL naming scheme, you can override the `get_object_url`
and `get_changelist_url` methods provided by `WatchlistViewMixin`. For example:

```python
class MyListView(WatchlistMixin, ListView):

    def get_object_url(self, request, model, pk):
        return reverse(
            f"{model._meta.model_name}_detail",
            args=[pk],
            current_app=request.resolver_match.namespace
        )
```

### Link to the watchlist

The template tag `watchlist_link` renders a hyperlink to the watchlist overview.
You can add this to your site navigation:

[comment]: <> (@formatter:off)
```html
{% load mizdb_watchlist %}

<nav>
  <ul>
    ...
    <li class="nav-item">{% watchlist_link 'my_watchlist' %}</li>
  </ul>
</nav>
```
[comment]: <> (@formatter:on)

The tag takes two arguments:

| Argument  | Default value | Description                                                                        |
|-----------|---------------|------------------------------------------------------------------------------------|
| view_name | **required**  | the view name of the watchlist as declared in the URL conf                         |
| icon      | `True`        | an optional boolean indicating whether an icon should be included in the link HTML |

## Admin integration

This library comes with a ModelAdmin for the Watchlist model.
The ModelAdmin provides an admin view for the watchlist overview and adds it
to the ModelAdmin's URLs with the view name `watchlist`. The URL of the overview
can be reversed with `reverse(f"{your_admin_site.name}:watchlist")`.

The ModelAdmin itself lets admins inspect and modify the (model) watchlists of
other users, while the overview displays the watchlist items of the current admin user.

The ModelAdmin is hooked up to Django's default admin site.
If you are not using the default admin site, make sure to register the ModelAdmin
with your site:

```python
from mizdb_watchlist.admin import WatchlistAdmin
from mizdb_watchlist.models import Watchlist

my_admin_site.register(Watchlist, WatchlistAdmin)
```

### Admin toggle button & watchlist link

To include the toggle button on admin change pages, you can override the
`admin/change_form.html` template. For example like this:

[comment]: <> (@formatter:off)
```html
{% extends "admin/change_form.html" %}
{% load static mizdb_watchlist %}

{% block extrahead %}
  {{ block.super }}
  <link rel="stylesheet" href="{% static 'mizdb_watchlist/css/watchlist.css' %}">
  <script src="{% static 'mizdb_watchlist/js/watchlist.js' %}"></script>
  <script src="{% static 'mizdb_watchlist/js/watchlist_init.js' %}"></script>
{% endblock extrahead %}

{% block content_subtitle %}
  {% if subtitle %}
    <h2>{{ subtitle }} {% toggle_button request original %}</h2>
  {% endif %}
{% endblock %}
``` 
[comment]: <> (@formatter:on)

To add a link to the watchlist overview to the admin user links, overwrite
`admin/base.html` like this:

[comment]: <> (@formatter:off)
```html
{% extends "admin/base.html" %}
{% load mizdb_watchlist %}

{% block userlinks %}
  {% watchlist_link '<name of your admin site>:watchlist' icon=False %} / {{ block.super }}
{% endblock %}
```
[comment]: <> (@formatter:on)

> ℹ️ **Note**:
>
> See [Overriding admin templates](https://docs.djangoproject.com/en/5.0/ref/contrib/admin/#admin-overriding-templates)
> for more details on how to override admin templates.

### admin.WatchlistMixin

`admin.WatchlistMixin` is the admin version of `views.WatchlistMixin`. The mixin
adds annotations and filtering (see [WatchlistMixin](#viewswatchlistmixin)) to
the ModelAdmin's queryset.

```python
from mizdb_watchlist.admin import WatchlistMixin


@admin.register(MyModel)
class MyModelAdmin(WatchlistMixin, admin.ModelAdmin):
    pass
```

### Admin action

You can use the `add_to_watchlist` action to add multiple items at once from the
admin changelist. To make the action available in your application, either
[add the action to your ModelAdmin](https://docs.djangoproject.com/en/5.0/ref/contrib/admin/actions/#adding-actions-to-the-modeladmin)
or [add it to your admin site](https://docs.djangoproject.com/en/5.0/ref/contrib/admin/actions/#making-actions-available-site-wide)
to make it globally available. For example:

```python
from mizdb_watchlist.actions import add_to_watchlist
from mizdb_watchlist.admin import WatchlistMixin

my_admin_site = admin.AdminSite(name="admin")


# for a single ModelAdmin:
@admin.register(MyModel, site=my_admin_site)
class MyModelAdmin(WatchlistMixin, admin.ModelAdmin):
    actions = [add_to_watchlist, ...]


# or for the entire admin site:
my_admin_site.add_action(add_to_watchlist)
```

## Initializing watchlist buttons

In the above examples, `watchlist_init.js` was used to initialize any button
that interacts with the watchlist.
However, you can initialize the buttons yourself by using the `initToggleButton`,
`initRemoveButton` and `initRemoveAllButton` functions provided by the global
attribute `WatchlistButton`.

For example like this:

```javascript
document.addEventListener('DOMContentLoaded', () => {
  const myToggleButton = document.querySelector('.my-toggle-button')
  WatchlistButton.initToggleButton(myToggleButton)
})
```

This also lets you provide a callback function that is called after the button
was pressed and the response from the server was handled.  
The callback will be called with the button that was pressed and the response
data.

```javascript
document.addEventListener('DOMContentLoaded', () => {
  const myToggleButton = document.querySelector('.my-toggle-button')
  const myCallback = (btn, data) => {
    if (data.on_watchlist) {
      btn.classList.remove('btn-primary')
      btn.classList.add('btn-success')
    } else {
      btn.classList.add('btn-primary')
      btn.classList.remove('btn-success')
    }
  }
  WatchlistButton.initToggleButton(myToggleButton, myCallback)
})
```

## Settings

### Overriding a watchlist manager class

The managers are responsible for managing the items on the watchlist (for example, they add or remove items).
There are two types of manager:

- a model manager that manages a watchlist based on a Django model (by default: `mizdb_watchlist.models.Watchlist`) and
  stored in the database
- a session manager that manages a watchlist stored in a Django session

To override a manager class, declare the path to your class in the settings:

```python
# foo/bar.py
from mizdb_watchlist.manager import ModelManager, SessionManager


class MyModelManager(ModelManager):
  ...


class MySessionManager(SessionManager):
  ...


# settings.py
MIZDB_WATCHLIST = {
  "manager": {
    "model": "foo.bar.MyModelManager",
    "session": "foo.bar.MySessionManager",
  }
}
```

## Demo & Development

Install (requires [poetry](https://python-poetry.org/docs/) and npm):

```commandline
make init
```

Install pre-commit hooks:
```commandline
pre-commit install
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

### Demo

To start the demo server, do:

```commandline
make init-demo
python demo/manage.py runserver
```
