from flask import escape, request, jsonify
from order_app.place_order import PlaceOrder
from order_app.take_order import TakeOrder
from order_app.order_list import OrderList
from utilities.logger import get_logger
from order_app.settings import app

logger = get_logger('flask_order_app')

# Healthcheck
@app.route('/healthcheck')
def healthcheck():
	return jsonify({'data': 'hello world.'})

@app.route('/orders', methods=['POST'])
def place_order_view():
	logger.info('Requested json data: (%s, %s).' % (request.json['origin'], request.json['destination']))
	order = PlaceOrder(request=request)
	new_order_item, err_msg = order.run_place_order()
	if new_order_item:
		return jsonify(new_order_item)
	response = jsonify({'error': err_msg})
	response.status_code = 400
	return response


@app.route('/orders/<order_id>', methods=['PATCH'])
def take_order_view(order_id):
	try:
		order_id = int(order_id)
	except:
		response = jsonify({'error': 'id of order must be integer or string that contains only one integer.'})
		response.status_code = 400
		return response
	order = TakeOrder(order_id=order_id, request=request)
	success, err_msg = order.run_take_order()
	logger.info('Request order id %s.' % order_id)
	logger.info('Requested json data: %s' % request.json)
	if success:
		return jsonify({'status': "SUCCESS"})
	response = jsonify({'error': err_msg})
	response.status_code = 400
	return response

@app.route('/orders', methods=['GET'])
def order_list_view():
	page = request.args.get('page')
	limit = request.args.get('limit')
	try:
		page = int(page)
		limit = int(limit)
	except:
		response = jsonify({'error': 'Both arguments page and limit are required, and must be integer or string of integers only.'})
		response.status_code = 400
		return response
	order_list = OrderList(page=page, limit=limit)
	order_items, err_msg = order_list.query_paginated_orders()
	if order_items is not None: #order_items can be []
		return jsonify(order_items)
	response = jsonify({'error': err_msg})
	response.status_code = 400
	return response



