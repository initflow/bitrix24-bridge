FROM python:3.7-stretch

ENV PYTHONUNBUFFERED 1

RUN apt-get update

RUN mkdir /usr/src/app
WORKDIR /usr/src/app

ADD requirements.txt /usr/src/app/

RUN pip install --no-cache -r requirements.txt

ADD . /usr/src/app/


