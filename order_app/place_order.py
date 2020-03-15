import json, requests
from flask import request
from flask_inputs import Inputs
from flask_inputs.validators import JsonSchema
from sqlalchemy.orm import sessionmaker
from utilities.logger import get_logger
from order_app.settings import GMAP_TOKEN, GMAP_DISTANCE_MATRIX_API
from order_app.models import db_connect, Order

logger = get_logger('flask_order_app')

coorindate_schema = {
	'type': 'object',
	'properties': {
		'origin': {
			'type': 'array',
			'items':[
				{
					'type': 'string',
					'pattern': '^\d+(?:\.\d+)?$'
				},
				{
					'type': 'string',
					'pattern': '^\d+(?:\.\d+)?$'
				}
			],
			"minItems": 2,
			"additionalItems": False
		},
		'destination' : {
			'type': 'array',
			'items':[
				{
					'type': 'string',
					'pattern': '^\d+(?:\.\d+)?$'
				},
				{
					'type': 'string',
					'pattern': '^\d+(?:\.\d+)?$'
				}
			],
			"minItems": 2,
			"additionalItems": False
		}
	},
	'required': ['origin', 'destination'],
	'additionalProperties': False
}

class CoordinateInputs(Inputs):
   json = [JsonSchema(schema=coorindate_schema)]

class PlaceOrder():

	def __init__(self, request):
		self.request = request
		self.inputs = CoordinateInputs(self.request)
		self.origin_lat = None
		self.origin_lng = None
		self.destination_lat = None
		self.destination_lng = None
		self.gmap_unit = 'metric'
		self.gmap_key = GMAP_TOKEN
		self.gmap_url = GMAP_DISTANCE_MATRIX_API


	def validate_latlng_range(self):
		"""
		Validate the origins' and destinations' (lat, lng). 
		-90 <= lat <= 90
		-180 <= lng <= 180
		Return error message if any lat or lng validation fails 
		and display all lat and lng values that do not fall within the range.
		"""
		validated = True
		errors = []
		err_msg = None
		if self.origin_lat >= 90 or self.origin_lat <= -90:
			validated = False
			errors.append('origin latitude: %s' % (self.origin_lat,))
		if self.destination_lat >= 90 or self.destination_lat <= -90:
			validated = False
			errors.append('destination latitude: %s' % (self.destination_lat,))
		if self.origin_lng >= 180 or self.origin_lng <= -180:
			validated = False
			errors.append('origin longitude: %s' % (self.origin_lng,))
		if self.destination_lng >= 180 or self.destination_lng <= -180:
			validated = False
			errors.append('destination longitude: %s' % (self.destination_lng,))
		if not validated:
			logger.info("Validation fail, %s not withint range." % (', '.join(errors),))
			err_msg = "Wrong input, %s must be within range. -90<=latitude<=90, -180<=longitude<= 180." % (', '.join(errors),)
		return validated, err_msg

	def get_distance(self):
		"""
		Get distance between the origins and destions using Google Map Distance Matrix API.
		Return distance in meters (integer).
		Catch exception during requestiong Google Map Distance Matrix API, 
		return distance = None for failure to retrieve distance from API.
		"""
		distance = None
		err_msg = None
		gmap_params = {
			'origins': '%s, %s' % (self.origin_lat, self.origin_lng),
			'destinations': '%s, %s' % (self.destination_lat, self. destination_lng),
			'units': self.gmap_unit,
			'key': self.gmap_key
		}
		try:
			resp = requests.get(
					self.gmap_url, params=gmap_params
				)
			resp = resp.json()
			logger.info("Number of gmap API response rows returned: %s." % (len(resp['rows'], )))
			distance = int(resp['rows'][0]['elements'][0]['distance']['value']) #in meters
			logger.info("Distance: %s." % (distance,))
		except Exception as e: 
			logger.error(e)
			err_msg = "Distance cannot be retrieved with Google Maps Distance Matrix."
		return distance, err_msg

	def insert_new_order(self, distance):
		"""
		Insert new order into Order table. Return dict of the newly inserted order.
		Roll back if exception caught.
		"""
		engine = db_connect()
		Session = sessionmaker(bind=engine)
		item = {
			'distance': distance
		}
		session = Session() # invokes sessionmaker.__call__()
		logger.info("Created database session.")
		new_order = Order(**item)
		new_order_item = {}
		err_msg = None
		try:
			session.add(new_order)
			session.commit()
			new_order_item['id'] = new_order.id
			new_order_item['distance'] = new_order.distance
			new_order_item['status'] = new_order.status
			logger.info("Inserted new order with id %s, distance %s and status %s." % (new_order.id, new_order.distance, new_order.status))
		except Exception as e:
			session.rollback()
			logger.error("Roll back insert new order.")
			logger.error(e)
			err_msg = "New order cannot be created."
		finally: 
			session.close()
			logger.info("Closed database session.")
		engine.dispose() # Prevent OperationalError: (psycopg2.OperationalError) FATAL:  sorry, too many clients already
		return new_order_item, err_msg

	def run_place_order(self):
		"""
		Run all class functions of PlaceOrder.
		Return error message immediately if any error message been returned from any class functions,
		with newly inserted order being None.
		otherwise returns newly inserted order with None error message.
		"""
		new_order_item = None
		err_msg = None
		if self.inputs.validate():
			self.origin_lat = float(self.request.json['origin'][0])
			self.origin_lng = float(self.request.json['origin'][1])
			self.destination_lat = float(self.request.json['destination'][0])
			self.destination_lng = float(self.request.json['destination'][1])
			validated, err_msg = self.validate_latlng_range()
			if validated:
				distance, err_msg = self.get_distance()
				if distance:
					new_order_item, err_msg = self.insert_new_order(distance)
		else:
			err_msg = '. '.join(self.inputs.errors)
		return new_order_item, err_msg

