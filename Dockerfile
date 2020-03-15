#python 3.7.5
FROM python:3.7.5 as base_builder

WORKDIR /home

RUN apt-get update && apt-get install -y vim \
	&& apt-get install -y nginx

RUN rm -rf /var/lib/apt/list/*

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

COPY nginx.conf /etc/nginx
COPY uwsgi.ini .
COPY start.sh .

ENV PYTHONPATH "/home:${PYTHONPATH}"
ENV BASEDIR "/home"

COPY wsgi.py .
COPY Makefile .
COPY utilities ./utilities
COPY order_app ./order_app


FROM base_builder as builder
CMD bash start.sh

FROM base_builder as test_builder
COPY tests ./tests
COPY unit_test.env .
COPY start_test.sh start.sh
CMD bash start.sh
