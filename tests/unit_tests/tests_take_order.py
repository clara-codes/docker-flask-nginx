import unittest
from unittest.mock import Mock, patch
from utilities.logger import get_logger
from app.take_order import TakeOrder

logger = get_logger('test')

class TakeOrderTestCase(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		"""
		Start all mocking necessary for testing.
		"""
		#mock orm db_connect before any reference to app.place_order
		#start mocking create_engine behavior in app.place_order.engine
		cls.mock_engine_patcher = patch('app.take_order.db_connect')
		cls.mock_engine = cls.mock_engine_patcher.start()

		#start mocking sessionmaker behavior in apps.place_order
		cls.mock_sessionmaker_patcher = patch('app.take_order.sessionmaker')
		cls.mock_sessionmaker = cls.mock_sessionmaker_patcher.start()

		#start mocking the request object of PlceOrder
		cls.mock_request_patcher = patch('app.take_order.request')
		cls.mock_request = cls.mock_request_patcher.start()

	@classmethod
	def tearDownClass(cls):
		"""
		Terminal all mocking.
		"""
		cls.mock_engine.stop()
		cls.mock_sessionmaker.stop()
		cls.mock_request.stop()

	def test_take_order_input_validation(self):
		"""
		Test input validation.
		"""
		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'status': 'TAKEN'
		}
		order = TakeOrder(order_id=1, request=self.mock_request)
		validated, err_msg = order.validate_json()
		self.assertEqual(validated, True)
		self.assertEqual(err_msg is None, True)
		
		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'status': 'SOMETHING ELSE'
		}
		order = TakeOrder(order_id=1, request=self.mock_request)
		validated, err_msg = order.validate_json()
		self.assertEqual(validated, False)
		self.assertEqual(err_msg is None, False)

		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'status': 'TAKEN',
			'test': 'xyz'
		}
		order = TakeOrder(order_id=1, request=self.mock_request)
		validated, err_msg = order.validate_json()
		self.assertEqual(validated, False)
		self.assertEqual(err_msg is None, False)
		
if __name__ == '__main__':
    unittest.main()