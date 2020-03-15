import json, requests
from flask import request
from utilities.logger import get_logger
from werkzeug import exceptions
from order_app.models import Order

logger = get_logger('flask_order_app')

class OrderList():

	def __init__(self, page, limit):
		self.page = page
		self.limit = limit

	def query_paginated_orders(self):
		order_items = None
		err_msg = None
		try:
			#only get columns: id, distance, status, and order by id descending.
			order_paged = Order.query.with_entities(Order.id, Order.distance, Order.status).order_by(Order.id.desc()).paginate(self.page, self.limit)
			order_items = [{'id': order[0], 'distance': order[1], 'status': order[2]} for order in order_paged.items]
			logger.info("Successfully retrieved orders with pagination %s on page %s." % (self.limit, self.page))
			logger.info("Has previous page: %s, and has next page: %s." % (order_paged.has_prev, order_paged.has_next))
		except exceptions.NotFound:
			order_items = []
			logger.info("Number of pages exceeded.")
		except Exception as e: 
			err_msg = "Orders cannot be queried."
			logger.error("Orders cannot be queried.: %s." % (e,))
		return order_items, err_msg