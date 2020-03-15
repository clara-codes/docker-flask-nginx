import unittest, os, json
from utilities.logger import get_logger
from order_app.settings import TEST_DIR
from order_app.models import create_db_if_not_exists, db_connect, create_tables, DeclarativeBase, BaseModel, Order

logger = get_logger('test')

class DataBaseInitilizationTestCase(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		"""
		Define integration test DB connection string, and the databaes for test.
		"""
		cls.db_test_name = 'TestDB'
		cls.global_db_config = {
		    'drivername': 'postgresql',
		    'host': os.getenv('DB_HOST'),
		    'port': os.getenv('DB_PORT'),
		    'username': os.getenv('DB_USERNAME'),
		    'password': os.getenv('DB_PASSWORD'),
		    'database': cls.db_test_name
		}

		cls.table_names = DeclarativeBase.metadata.tables.keys()
		with open(os.path.join(TEST_DIR, 'support', 'tests_db_schema.json')) as f:
			cls.test_db_schema = json.loads(f.read())
			cls.test_db_schema = {table_name: cls.test_db_schema[table_name] for table_name in cls.table_names}

	@classmethod
	def tearDownClass(cls):
		"""
		Tear down database after testcase finish.
		"""
		db_config = cls.global_db_config.copy()
		#connect to postgres to drop table TestDB.
		db_config['database'] = 'postgres'
		engine = db_connect(db_config=db_config)
		conn = engine.connect()
		#prevent fulture connection to TestDB
		conn.execute("""REVOKE CONNECT ON DATABASE "%s" FROM public;""" % (cls.db_test_name,))
		#terminal all connections to TestDB
		conn.execute("""SELECT pid, pg_terminate_backend(pid) FROM pg_stat_activity \
			WHERE datname = '%s' AND pid <> pg_backend_pid();""" % (cls.db_test_name,))
		conn.execute("commit")
		conn.execute("""DROP DATABASE IF EXISTS "%s";""" % (cls.db_test_name,)) #run outside of transaction block
		conn.close()
		engine.dispose()
		logger.info('End of %s , database: %s has been torn down.' % (cls.__name__, cls.db_test_name))

	def _test_create_db_if_not_exists(self):
		"""
		Test if create_db_if_not_exists can successfully create db if it does not exists.
		"""
		create_db_if_not_exists(db_config=self.global_db_config)
		engine = db_connect(db_config=self.global_db_config)
		conn = engine.connect()
		result = conn.execute("""SELECT datname FROM pg_database;""")
		db_names = [dict(i)['datname'] for i in result]
		result.close()
		conn.close()
		created_db = self.db_test_name in db_names
		self.assertEqual(created_db, True)

	def _test_create_db_if_exists(self):
		"""
		Test if create_db_if_not_exists can skip creating db if exists already.
		This runs after self.test_create_db_if_not_exists.
		"""
		create_db_if_not_exists(db_config=self.global_db_config)
		engine = db_connect(db_config=self.global_db_config)
		conn = engine.connect()
		result = conn.execute("""SELECT datname FROM pg_database;""")
		db_names = [dict(i)['datname'] for i in result]
		result.close()
		conn.close()
		created_db = self.db_test_name in db_names
		self.assertEqual(created_db, True)

	def test_create_db(self):
		self._test_create_db_if_not_exists()
		self._test_create_db_if_exists()

	def test_create_tables(self):
		"""
		Create tables according to DeclarativeBase definition in models.py,
		and validate the schema retrieved from DB of the tables that have just been created.
		(Schema definition to validate against is defined in tests_db_schema.json,
		update accordingly to testing for any changes in schema.)
		"""
		engine = db_connect(db_config=self.global_db_config)
		create_tables(engine)
		conn = engine.connect()
		for table_name in self.table_names:
			result = conn.execute("""SELECT * FROM information_schema.columns WHERE table_name = '%s';""" % (table_name,))
			schema = [dict(item) for item in result]
			result.close()
			#a and b have the same elements in the same number, regardless of their order.
			self.assertCountEqual(schema, self.test_db_schema[table_name])
		conn.close()


if __name__ == '__main__':
    unittest.main()