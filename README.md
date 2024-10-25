# HealthOS E-commerce Backend #

A Django 1.11 skeleton project

**Comes out of the box with**

* REST Login
* JWT Authentication
* Redis Caching
* Redis Session Caching
* Register / Activation flow

**TODOs**

* Add tests for user creation and activation flow
* Add Locust scripts for load testing
* Add placeholder for Sentry
* Add bacman scripts for DB backup

---

## Getting started with the frontend ##

Its easy to get started with frontend development in this project.

### Redis ###

Install Redis on Ubuntu 22.04 LTS

```
    sudo apt-get update
    sudo apt-get install redis-stack-server
```

### Celery ###

**Running Celery**

    python projectile/manage.py celery worker --loglevel=info

**Running Celery in developer mode**

    python projectile/manage.py celery worker --loglevel=info --autoreload

**NOTE:** The trailing slash

---

## Deployment Procedures ##

---

## The 'django' user ##

The `django` user is the owner of the django project. It resides in `/home/django` and the project resides in `/home/django/project`

## Managing uWSGi ##

    sudo /etc/init.d/uwsgi start|stop|restart

The logs are located in `/home/django/logs/uwsgi/...`

    sudo su django
    tail -f ~/logs/nginx/uwsgi.log

## Managing Nginx ##

    sudo service nginx start|stop|restart

The logs are located in `/home/django/logs/nginx/...`

    sudo su django
    tail -f ~/logs/nginx/access.log

## Server configuration files ##

The config files should be checked into the repo whenever tweaks or changes are made.

* Nginx: `repo/conf/nginx/...`
* uWSGi: `repo/conf/uwsgi/...`
* WSGi: `repo/conf/wsgi/...`

They are located at `/home/django/project/conf/...` on the server

## Environment variables ##

If you need to add environment vars. You can do it by changing `/etc/environment`

    sudo nano `/etc/environment` for system wide env vars
    nano `/home/django/.env` for project wide env vars

## Deployment ##

    sudo su django
    git pull

---

## Development server ##

---

**SSH Login**

**TIP:** Ask Faisal (@faisalmahmud) to give you access to the development server.

**TIP:** Paste the snippet below in your ~/.ssh/config file, but remember to change to your user and the path to your identityfile (SSH private key)

	Host *
	IdentitiesOnly yes
	ServerAliveInterval 60

	host examplehost
      hostname test.example.com
	  user johndoe
      port 1919


**Cloning your fork**

	cd ~
	git clone bitbucket.com:johndoe/projectile.git project


**Setting up a virtualenv**

virtualenv is a nifty tool for creating virtual environments for Python projects

	cd ~
	virtualenv env
	source ~/env/bin/activate

If you find it tedious to do the above everytime you log in you can copy the snippet below in to a file named *~/.bash_profile* and You will automatically land in the project folder everytime you log in with the virtualenv activated.

	source ~/env/bin/activate
	cd ~/project

Try logging out from your ssh session and log in to see if the snippet above works.


**Install the Python dependencies for the project**

Make sure your virtualenv is active, the name of the env wrapped in round brackets should appear next to your username@hostname in the terminal.

```
	(env)johndoe@uduntu:~$
```

And then run

```
	pip install -r ~/project/requirements.txt
```

**Add your IP to internal IPs**

Add your IP to the variable INTERNAL_IPS in projectile\projectile\settings.py. You can find your IP address with http://www.whatsmyip.org/

**Run the test server**

The ports are often free 8111, 8222, 8333, 8444, 8555, 8777

	cd ~/project
	python projectile/manage.py runserver_plus 0:8111

---

## JWT Authentication ##

---

**Authenticate and get a token**

	$ curl -X POST -d "email=john@dough.com&password=abcdef123456" http://<BASE_URL>/api-token-auth/

or as json

	$ curl -X POST -H "Content-Type: application/json" -d '{"email":"john@dough.com", "password":"abcdef123456"}' http://<BASE_URL>/api-token-auth/

**Fetching data from protected URLs**

	$ curl -H "Authorization: Bearer <YOUR_TOKEN>" http://<BASE_URL>/api/v1/me/stream

**Refresh token**

	$ curl -X POST -H "Content-Type: application/json" -d '{"token":"<EXISTING_TOKEN>"}' http://<BASE_URL>/api-token-refresh/

Read more at http://getblimp.github.io/django-rest-framework-jwt/


**Additional Requirement**

* Elasticsearch 1.7.5

https://download.elastic.co/elasticsearch/elasticsearch/elasticsearch-1.7.5.deb

Additional info to install the environment: https://gist.github.com/faisalmahmud/e4c44c0dacacf01515dea1643929fcdb

## Running with Docker ##

Docker is implemented in this project so it can be run on DEBUG mode anytime like this:

```bash
docker-compose build
docker-compose up -d django
```
You need to have docker, docker-machine, docker-compose installed on your machine.  

## Running Tests ##

The project contains following tests:

- Django Test Cases
- Frontend Tests
- High Traffic Load Tests

**Running Django Tests**

```bash
python projectile/manage.py test -n projectile
```

or

```bash
./run-test.sh
```

if you omit the `-n`, all the migrations will be applied while starting the tests, so it will take a long time to start the tests. 

**Running the Frontend Tests**

To run the casperjs frontend tests:

```bash
cd client/tests
./run_tests.sh
```

To run the Django Frontend tests:

```bash
python projectile/manage.py test -n frontend
```

**Running the Load Tests**

After running the project locally on port 8000:

```bash
./locust.sh http://localhost:8000
```

Then go to `localhost:8089` and fill the needed fields to start the test.
