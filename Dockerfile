#python 3.7.5
FROM python:3.7.5

WORKDIR /home

RUN apt-get update && apt-get install -y vim \
	&& apt-get install -y nginx

RUN rm -rf /var/lib/apt/list/*

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

COPY nginx.conf /etc/nginx
COPY uwsgi.ini .
COPY start.sh .
RUN chmod +x start.sh

ENV PYTHONPATH "/home:${PYTHONPATH}"

COPY wsgi.py .
COPY Makefile .
COPY utilities ./utilities
COPY app ./app
COPY tests ./tests

CMD bash start.sh