import unittest, os
from unittest.mock import Mock, patch
from sqlalchemy.orm import sessionmaker
from utilities.logger import get_logger
from app.take_order import TakeOrder
from app.models import create_db_if_not_exists, db_connect, create_tables, Order

logger = get_logger('test')

class TakeOrderDBTestCase(unittest.TestCase):

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

		#start mocking db_connect bahavior to connect to TestDB in app.place_order
		cls.mock_db_connect_patcher = patch('app.place_order.db_connect')
		cls.mock_db_connect = cls.mock_db_connect_patcher.start()
		cls.mock_db_connect.return_value = cls.engine

		#start mocking the request object of PlceOrder
		cls.mock_request_patcher = patch('app.place_order.request')
		cls.mock_request = cls.mock_request_patcher.start()

	@classmethod
	def tearDownClass(cls):
		"""
		Stop all mocking.
		Tear down database after testcase finish.
		"""
		#stop mocking
		cls.mock_db_connect.stop()
		cls.mock_request.stop()

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

	def tests_update_order_status(self):
		"""
		Test if order status can be updated to TAKEN.
		"""
		Session = sessionmaker(bind=self.engine)
		session = Session()
		new_order = Order({'distance':111})
		try:
			session.add(new_order)
			session.commit()
			new_order_id = new_order.id
			logger.info("Added new order with id: %s for integration test." % (new_order.id,))
		except Exception as e: 
			session.rollback()
			logger.error(e)
		finally:
			session.close()

		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'status': 'TAKEN'
		}
		order = TakeOrder(order_id=new_order_id, request=self.mock_request)
		success, err_msg = order.update_order_status()
		self.assertEqual(success, True)
		self.assertEqual(err_msg is None, True)

	def tests_update_order_status(self):
		"""
		Test if error message is thrown if trying to update an already taken order.
		"""
		Session = sessionmaker(bind=self.engine)
		session = Session()
		new_order = Order(**{'distance':111, 'status': 'TAKEN'})
		try:
			session.add(new_order)
			session.commit()
			new_order_id = new_order.id
			#new_order = session.query(Order).filter(Order.id==new_order_id).one()
			#new_order.status = "TALEN"  #force the status to be TAKEN already.
			#new_order.commit()
			logger.info("Added new order with id: %s for integration test." % (new_order.id,))
		except Exception as e: 
			session.rollback()
			logger.error(e)
		finally:
			session.close()

		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'status': 'TAKEN'
		}
		order = TakeOrder(order_id=new_order_id, request=self.mock_request)
		success, err_msg = order.update_order_status()
		self.assertEqual(success, False)
		self.assertEqual(err_msg is None, False)

if __name__ == '__main__':
    unittest.main()

