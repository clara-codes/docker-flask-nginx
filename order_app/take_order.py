import json
from flask import request
from flask_inputs import Inputs
from flask_inputs.validators import JsonSchema
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from utilities.logger import get_logger
from order_app.models import db_connect, Order

logger = get_logger('flask_order_app')

status_schema = {
	'type': 'object',
	'properties': {
		'status': {
			'type': 'string',
			'pattern': '^TAKEN$'
		}
	},
	'required': ['status'],
	'additionalProperties': False
}

class StatusSchema(Inputs):
   json = [JsonSchema(schema=status_schema)]

class TakeOrder():

	def __init__(self, order_id, request):
		self.order_id = order_id
		self.request = request
		self.inputs = StatusSchema(self.request)
		self.new_status = None
		self.engine = db_connect()
		self.Session = sessionmaker(bind=self.engine)

	def validate_json(self):
		"""
		Validate json input with jsonschema.
		Json should contain one field 'status' with value 'TAKEN'
		"""
		err_msg = None
		if self.inputs.validate():
			self.new_status = self.request.json['status']
		else:
			err_msg = '. '.join(self.inputs.errors)
			return False, err_msg
		return True, err_msg


	def update_order_status(self):
		"""
		1. query order
		2. check if order exists (.scalar() is not None), but if order locked --> OperationalError. 
			else obtain a lock on the row.
		3. take one, and does the update operation.
		4. if update or commit has errors occur, rollback and fail.
		"""
		success = False
		err_msg = None
		engine = db_connect()
		Session = sessionmaker(bind=engine)
		session = Session()
		logger.info("Created database session.")
		try:
			#Row level lock (FOR UPDATE clause: 
			#other transactions that attempt UPDATE, DELETE, or SELECT FOR UPDATE of these rows will be blocked until the current transaction ends.
			#With nowait=True, the statement reports an error, rather than waiting, if a selected row cannot be locked immediately.
			order_query = session.query(Order).filter(Order.id==self.order_id).with_for_update(nowait=True, of=Order)
			#row lock is only obatain when query executes.
			if order_query.scalar(): #check if exists and obtain lock 
				order = order_query.one()
				if not order.status == 'TAKEN':
					order.status = self.request.json['status']
					session.commit() #commit update, release row lock
					logger.info("Order (id: %s) status is sucessfully updated to %s." % (order.id, order.status))
					success = True
				else:
					err_msg = "Order is already taken."
					logger.info("Order is already taken.")
			else:
				err_msg = "Order does not exist."
				logger.info("Order with id %s does not exist." % (self.order_id,))
		except OperationalError as e: #catch exception of psycopg2.errors.LockNotAvailable
			session.rollback()
			err_msg = "Order is currently occupied. Update status to TAKEN fail."
			logger.info("Roll back update order with id %s." % (self.order_id,))
			logger.info("OperationalError caught: %s." % (e,))
		except Exception as e:
			session.rollback()
			err_msg = "Cannot update order status with id %s. " % (self.order_id,)
			logger.info("Roll back update order with id %s." % (self.order_id,))
			logger.error(e)
		finally:
			session.close() #release row lock
			logger.info("Closed database session.")
		engine.dispose() # Prevent OperationalError: (psycopg2.OperationalError) FATAL:  sorry, too many clients already
		return success, err_msg

	def run_take_order(self):
		"""
		Run all class functions of TakeOrder
		"""
		order_item = None
		err_msg = None
		validated, err_msg = self.validate_json()
		if validated:
			order_item, err_msg = self.update_order_status()
		return order_item, err_msg
		


