cd /home && python app/create_tables.py
service nginx start
uwsgi --ini uwsgi.ini