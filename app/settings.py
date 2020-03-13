import os

DATABASE = {
    'drivername': 'postgresql',
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'username': os.getenv('DB_USERNAME'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

GMAP_TOKEN = os.getenv("GMAP_TOKEN")
GMAP_DISTANCE_MATRIX_API = os.getenv("GMAP_DISTANCE_MATRIX_API")

TEST_DIR = os.path.join(os.getenv("BASEDIR"), "tests")