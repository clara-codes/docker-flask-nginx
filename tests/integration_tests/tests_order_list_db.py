import unittest, os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from unittest.mock import Mock, patch
from sqlalchemy.orm import sessionmaker
from utilities.logger import get_logger
from order_app.order_list import OrderList
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

		#Create test data
		cls.engine.execute("""INSERT INTO "Order" (id, distance, status) VALUES (100, 111, 'UNASSIGNED');""")

		#Mock flask-sqlalchemy db connection
		cls.mock_flask_db_patcher = patch("order_app.models.db")
		cls.mock_flask_db = cls.mock_flask_db_patcher.start()
		cls.test_app = Flask("test_order_list")
		cls.test_app.config['SQLALCHEMY_DATABASE_URI'] = "%s://%s:%s@%s:%s/%s" % (
			cls.global_db_config['drivername'], cls.global_db_config['username'], 
			cls.global_db_config['password'], cls.global_db_config['host'], 
			cls.global_db_config['port'], cls.global_db_config['database']
			)
		cls.test_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
		cls.test_db = SQLAlchemy(cls.test_app)
		cls.mock_flask_db.return_value = cls.test_db
		

	@classmethod
	def tearDownClass(cls):
		"""
		Stop all mocking.
		Tear down database after testcase finish.
		"""
		#stop mocking
		cls.mock_flask_db_patcher.stop()

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

	def tests_order_list(self):
		order_list = OrderList(page=1, limit=1)
		order_items, err_msg = order_list.query_paginated_orders()
		self.assertEqual(order_items is not None, True)
		self.assertEqual(err_msg is not None, False)

if __name__ == '__main__':
    unittest.main()

