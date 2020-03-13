cd /home && python app/create_tables.py
touch error_rotate.log && touch info_rotate.log
chmod 666 error_rotate.log && chmod 666 info_rotate.log
service nginx start
uwsgi --ini uwsgi.ini