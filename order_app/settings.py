import os 
from flask import Flask

DATABASE = {
    'drivername': 'postgresql',
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'username': os.getenv('DB_USERNAME'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = "%s://%s:%s@%s:%s/%s" % (
	DATABASE['drivername'], DATABASE['username'], 
	DATABASE['password'], DATABASE['host'], 
	DATABASE['port'], DATABASE['database']
	)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

GMAP_TOKEN = os.getenv("GMAP_TOKEN")
GMAP_DISTANCE_MATRIX_API = os.getenv("GMAP_DISTANCE_MATRIX_API")

TEST_DIR = os.path.join(os.getenv("BASEDIR"), "tests")