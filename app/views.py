from flask import Flask, escape, request, jsonify
from app.place_order import PlaceOrder
from utilities.logger import get_logger

app = Flask('flask_main_app')
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

logger = get_logger('flask_order_app')

# To test if flask application works
@app.route('/hello')
def hello():
	return jsonify({'data': 'hello world.'})

@app.route('/orders', methods = ['POST'])
def place_order_view():
	logger.info('Requested form data: (%s, %s).' % (request.get_json()['origin'], request.get_json()['destination']))
	order = PlaceOrder(request=request)
	new_order_item, err_msg = order.run_place_order()
	if err_msg:
		return jsonify({'error': err_msg})
	return jsonify(new_order_item)