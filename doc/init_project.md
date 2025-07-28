Make sure to have the following on your host:

Python 3.12
PostgreSQL.
Cookiecutter


## install Cookiecutter

https://github.com/cookiecutter/cookiecutter-django

```
pip install "cookiecutter>=1.7.0"
```

```
cookiecutter https://github.com/cookiecutter/cookiecutter-django
```


## Getting Up and Running Locally

https://cookiecutter-django.readthedocs.io/en/latest/2-local-development/developing-locally.html

we can skip Generate a new cookiecutter-django project. we already create it at step 1

### install postgresql -- macos

use homebrew to install postgresql, then on macos the default user is: as my computer is keboom.

so create database: ```createdb <project_slug>```, and the password is default empty. just use navicat to connect local postgreSQL, not need other additional command.
