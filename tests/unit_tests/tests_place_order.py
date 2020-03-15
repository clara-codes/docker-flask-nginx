import unittest, json, os
from unittest.mock import Mock, patch
from utilities.logger import get_logger
from app.settings import TEST_DIR
from app.place_order import PlaceOrder
from app import place_order

logger = get_logger('test')


class PlaceOrderTestCase(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		"""
		Initialize args for PlaceOrder, with predefinitions in json file.
		Start all mocking necessary for testing.
		"""

		with open(os.path.join(TEST_DIR, 'support', 'gmap_distance_matrix_api_resp.json')) as f:
			cls.predefined_gmap_resp = json.loads(f.read())

		cls.origins = cls.predefined_gmap_resp['success']['request_body']['origins']
		cls.destinations = cls.predefined_gmap_resp['success']['request_body']['destinations']

		#mock orm db_connect before any reference to app.place_order
		#start mocking create_engine behavior in app.place_order.engine
		cls.mock_engine_patcher = patch('app.place_order.db_connect')
		cls.mock_engine = cls.mock_engine_patcher.start()

		#start mocking sessionmaker behavior in apps.place_order
		cls.mock_sessionmaker_patcher = patch('app.place_order.sessionmaker')
		cls.mock_sessionmaker = cls.mock_sessionmaker_patcher.start()

		#start mocking the request object of PlceOrder
		cls.mock_request_patcher = patch('app.place_order.request')
		cls.mock_request = cls.mock_request_patcher.start()

		#start mocking requests.get behavior in app.place_order
		cls.mock_get_patcher = patch('app.place_order.requests.get')
		cls.mock_get = cls.mock_get_patcher.start()


	@classmethod
	def tearDownClass(cls):
		"""
		Terminal all mocking.
		"""
		cls.mock_engine.stop()
		cls.mock_sessionmaker.stop()
		cls.mock_request.stop()
		cls.mock_get.stop()

	def setUp(self):
		"""
		Initialize PlaceOrder class object with valid args for success cases,
		with invalid args for fail cases,
		and mock engine and Session.
		"""
		self.mock_engine.return_value = Mock()
		self.mock_sessionmaker.return_value = Mock()

	def test_place_order_input_validation(self):
		"""
		Test if CoordinateInputs jsonschema validation can correctly valid request.json.
		"""
		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'origin': self.origins,
			'destination': self.destinations
		}
		order = PlaceOrder(request=self.mock_request)
		logger.info('Order inputs validator returns error %s.' % (order.inputs.errors,))
		self.assertEqual(order.inputs.validate(), True)
		self.assertEqual(order.inputs.errors == [], True)

		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'origin': 'abcd'
		}
		order = PlaceOrder(request=self.mock_request)
		self.assertEqual(order.inputs.validate(), False)
		self.assertEqual(order.inputs.errors == [], False)
		logger.info('Order inputs validator returns error %s.' % (order.inputs.errors,))

		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'origin': ["1","1"]
		}
		order = PlaceOrder(request=self.mock_request)
		self.assertEqual(order.inputs.validate(), False)
		self.assertEqual(order.inputs.errors == [], False)
		logger.info('Order inputs validator returns error %s.' % (order.inputs.errors,))

		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'origin': ["1","1","1"],
			'destination': ["1","1"]
		}
		order = PlaceOrder(request=self.mock_request)
		self.assertEqual(order.inputs.validate(), False)
		self.assertEqual(order.inputs.errors == [], False)
		logger.info('Order inputs validator returns error %s.' % (order.inputs.errors,))

		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'origin': ["1"],
			'destination': ["1"]
		}
		order = PlaceOrder(request=self.mock_request)
		self.assertEqual(order.inputs.validate(), False)
		self.assertEqual(order.inputs.errors == [], False)
		logger.info('Order inputs validator returns error %s.' % (order.inputs.errors,))

		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'origin': ["1","1"],
			'destination': ["1","1"],
			'test': ["1","1"]
		}
		order = PlaceOrder(request=self.mock_request)
		self.assertEqual(order.inputs.validate(), False)
		self.assertEqual(order.inputs.errors == [], False)
		logger.info('Order inputs validator returns error %s.' % (order.inputs.errors,))

		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'origin': [1,1],
			'destination': [1,1]
		}
		order = PlaceOrder(request=self.mock_request)
		self.assertEqual(order.inputs.validate(), False)
		self.assertEqual(order.inputs.errors == [], False)
		logger.info('Order inputs validator returns error %s.' % (order.inputs.errors,))

		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'origin': [1,1],
			'destination': [1,1]
		}
		order = PlaceOrder(request=self.mock_request)
		self.assertEqual(order.inputs.validate(), False)
		self.assertEqual(order.inputs.errors == [], False)
		logger.info('Order inputs validator returns error %s.' % (order.inputs.errors,))

		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'origin': ["bbccds", "we.2343re"],
			'destination': ["12bbb", "23e.2344"]
		}
		order = PlaceOrder(request=self.mock_request)
		self.assertEqual(order.inputs.validate(), False)
		self.assertEqual(order.inputs.errors == [], False)
		logger.info('Order inputs validator returns error %s.' % (order.inputs.errors,))


	def test_validate_latlng_range(self):
		"""
		Test if validate_latlng_range can correctly validate args(float) ragne. 
		"""
		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'origin': self.origins,
			'destination': self.destinations
		}
		order = PlaceOrder(request=self.mock_request)
		order.origin_lat, order.origin_lng = float(self.origins[0]), float(self.origins[1])
		order.destination_lat, order.destination_lng = float(self.destinations[0]), float(self.destinations[1])
		validated, err_msg = order.validate_latlng_range()
		self.assertEqual(validated, True)
		self.assertEqual(err_msg, None)

		test_err_msg = "Wrong input, origin latitude: 33333.0, destination latitude: 99999.0 must be within range. -90<=latitude<=90, -180<=longitude<= 180."
		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'origin': [33333,12],
			'destination': [99999,-10]
		}
		false_order = PlaceOrder(request=self.mock_request)
		false_order.origins = [33333,12]
		false_order.destinations = [99999,-10]
		false_order.origin_lat, false_order.origin_lng = float(false_order.origins[0]), float(false_order.origins[1])
		false_order.destination_lat, false_order.destination_lng = float(false_order.destinations[0]), float(false_order.destinations[1])
		validated, err_msg = false_order.validate_latlng_range()
		self.assertEqual(validated, False)
		self.assertEqual(err_msg, test_err_msg)

	def test_get_distance(self):
		"""
		Test if get_distance can return distance given args.
		With mock request to external api - gmap distance matrix.
		"""
		#success case
		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'origin': self.origins,
			'destination': self.destinations
		}
		order = PlaceOrder(request=self.mock_request)
		test_distance = self.predefined_gmap_resp['success']['response_body']['rows'][0]['elements'][0]['distance']['value']
		self.mock_get.return_value = Mock()
		self.mock_get.return_value.json.return_value = self.predefined_gmap_resp['success']['response_body']
		order.origin_lat, order.origin_lng = float(self.origins[0]), float(self.origins[1])
		order.destination_lat, order.destination_lng = float(self.destinations[0]), float(self.destinations[1])
		distance, err_msg = order.get_distance()
		self.assertEqual(distance, test_distance)
		self.assertEqual(err_msg is None, True)
		#fail case
		self.mock_get.return_value.json.return_value = self.predefined_gmap_resp['fail']['response_body']
		self.mock_request.return_value = Mock()
		self.mock_request.json = {
			'origin': [33333,12],
			'destination': [99999,-10]
		}
		false_order = PlaceOrder(request=self.mock_request)
		false_order.origins = [33333,12]
		false_order.destinations = [99999,-10]
		false_order.origin_lat, false_order.origin_lng = float(false_order.origins[0]), float(false_order.origins[1])
		false_order.destination_lat, false_order.destination_lng = float(false_order.destinations[0]), float(false_order.destinations[1])
		distance, err_msg = false_order.get_distance()
		self.assertEqual(distance, None)
		self.assertEqual(err_msg is not None, True)


if __name__ == '__main__':
    unittest.main()