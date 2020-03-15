from flask import Flask, escape, request, jsonify
from app.place_order import PlaceOrder
from app.take_order import TakeOrder
from utilities.logger import get_logger

app = Flask('flask_main_app')
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

logger = get_logger('flask_order_app')

# To test if flask application works
@app.route('/hello')
def hello():
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
		return jsonify({'error': 'id of order must be integer or string that contains only one integer.'})
	order = TakeOrder(order_id=order_id, request=request)
	success, err_msg = order.run_take_order()
	logger.info('Request order id %s.' % order_id)
	logger.info('Requested json data: %s' % request.json)
	if success:
		return jsonify({'status': "SUCCESS"})
	response = jsonify({'error': err_msg})
	response.status_code = 400
	return response