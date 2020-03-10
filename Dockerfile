#python 3.7.5
FROM python:3.7.5

WORKDIR /home

RUN apt-get update && apt-get install -y vim \
	&& apt-get install -y nginx

RUN rm -rf /var/lib/apt/list/*

COPY nginx.conf /etc/nginx
COPY uwsgi.ini .
COPY start.sh .
RUN chmod +x start.sh

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

COPY wsgi.py .
COPY app ./app

CMD bash start.sh