import unittest, os, json
from unittest.mock import Mock, patch
from order_app.settings import TEST_DIR
from sqlalchemy.orm import sessionmaker
from utilities.logger import get_logger
from order_app.place_order import PlaceOrder
from order_app.models import create_db_if_not_exists, db_connect, create_tables

logger = get_logger('test')

class PlaceOrderDBTestCase(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		"""
		Define integration test DB connection string, and the databaes for test,
		followed by creating the TestDB and the related tables.
		Initialize args for PlaceOrder, with predefinitions in json file.
		Start all mocking necessary for testing.
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

		create_db_if_not_exists(db_config=cls.global_db_config)
		cls.engine = db_connect(db_config=cls.global_db_config)
		create_tables(cls.engine)

		with open(os.path.join(TEST_DIR, 'support','gmap_distance_matrix_api_resp.json')) as f:
			cls.predefined_gmap_resp = json.loads(f.read())
		cls.origins = cls.predefined_gmap_resp['success']['request_body']['origins']
		cls.destinations = cls.predefined_gmap_resp['success']['request_body']['destinations']
		cls.distance = cls.predefined_gmap_resp['success']['response_body']['rows'][0]['elements'][0]['distance']['value']

		#start mocking db_connect bahavior to connect to TestDB in order_app.place_order
		cls.mock_db_connect_patcher = patch('order_app.place_order.db_connect')
		cls.mock_db_connect = cls.mock_db_connect_patcher.start()
		cls.mock_db_connect.return_value = cls.engine

		#start mocking the request object of PlceOrder
		cls.mock_request_patcher = patch('order_app.place_order.request')
		cls.mock_request = cls.mock_request_patcher.start()

		#start mocking requests.get behavior in app.place_order
		cls.mock_get_patcher = patch('order_app.place_order.requests.get')
		cls.mock_get = cls.mock_get_patcher.start()

	@classmethod
	def tearDownClass(cls):
		"""
		Stop all mocking.
		Tear down database after testcase finish.
		"""
		#stop mocking
		cls.mock_db_connect_patcher.stop()
		cls.mock_request_patcher.stop()
		cls.mock_get_patcher.stop()

		db_config = cls.global_db_config.copy()
		#connect to postgres DB to drop DB TestDB.
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

	def test_insert_new_order(self):
		"""
		Test if insert_new_order can successfully insert into Order table given valid args.
		The id of the newly inserted order should be 1, given it is the 1st testcase to run.
		"""
		status = 'UNASSIGNED'
		test_err_msg = None
		test_new_order_item = {
			'id': 1,
			'distance': self.distance,
			'status': status
		}

		order = PlaceOrder(request=self.mock_request)
		#reinitiate PlceOrder class object with the TestDB Engine and Session
		order.engine = self.engine
		order.Session = sessionmaker(bind=self.engine)

		new_order_item, err_msg = order.insert_new_order(self.distance)
		self.assertEqual(new_order_item, test_new_order_item)

		conn = self.engine.connect()
		result = conn.execute("""SELECT id, distance, status FROM "Order" ORDER BY created_at DESC LIMIT(1);""")
		test_new_order = [dict(i) for i in result][0]
		result.close()
		conn.close()
		self.assertEqual(test_new_order['id'], 1)
		self.assertEqual(test_new_order['distance'], self.distance)
		self.assertEqual(test_new_order['status'], status)
		self.assertEqual(err_msg, None)

	def test_run_place_order(self):
		"""
		Test if the run_place_order can successfuly run all PlaceOrder class functions,
		and insert new order into Order table given valid args.
		The id of the newly inserted order should be 2, given it is the 2nd testcase to run.
		(with mock request to external api - gmap distance matrix)
		"""
		#success case
		status = 'UNASSIGNED'
		test_new_order_item = {
			'id': 2,
			'distance': self.distance,
			'status': status
		}

		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'origin': self.origins,
			'destination': self.destinations
		}

		order = PlaceOrder(request=self.mock_request)

		self.mock_get.return_value = Mock()
		self.mock_get.return_value.json.return_value = self.predefined_gmap_resp['success']['response_body']
		new_order_item, err_msg = order.run_place_order()
		self.assertEqual(new_order_item, test_new_order_item)
		self.assertEqual(err_msg, None)

	def test_run_place_order_fail(self):
		"""
		Test if the run_place_order can return correct error_message,
		and skip insert invalid order.
		(with mock request to external api - gmap distance matrix)
		"""
		#fail case
		test_new_order_item = None

		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'origin': ["1","2","3"],
			'destination': ["2","3"]
		}

		order = PlaceOrder(request=self.mock_request)

		self.mock_get.return_value = Mock()
		self.mock_get.return_value.json.return_value = self.predefined_gmap_resp['fail']['response_body']
		new_order_item, err_msg = order.run_place_order()
		self.assertEqual(new_order_item, test_new_order_item)
		self.assertEqual(err_msg is not None, True)


if __name__ == '__main__':
    unittest.main()