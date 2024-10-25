# How to run iPython Notebooks with Django

```
$ pip install jupyter ipython django-extensions
```

Add django_extensions under INSTALLED_APPS in your settings.py

```
INSTALLED_APPS = [
    ...
    'django_extensions',
]
```

And then start Jupyter Notebook

```
$ python manage.py shell_plus --notebook
```
