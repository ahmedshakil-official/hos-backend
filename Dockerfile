FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive 

RUN apt-get update 
RUN apt-get install -y apt-transport-https software-properties-common build-essential libssl-dev 
RUN apt-get install -y nano bash-completion wget curl git python3-pip python3-dev python3-venv
RUN apt-get install -y libmagic-dev libpangocairo-1.0-0

ENV VIRTUAL_ENV=/home/django/env
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy files to folder
ADD . /home/django/project

# Create folder for uwsgi logs
RUN mkdir -p /home/django/logs/uwsgi

WORKDIR /home/django/project

RUN pip install --upgrade pip
RUN pip install wheel
RUN pip install -r requirements/development.txt -r requirements/production.txt

EXPOSE 8000

CMD ["uwsgi", "--ini", "/home/django/project/conf/uwsgi/docker.ini"]