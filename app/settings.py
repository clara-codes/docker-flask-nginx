import os

DATABASE = {
    'drivername': 'postgresql',
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'username': os.getenv('DB_USERNAME'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}