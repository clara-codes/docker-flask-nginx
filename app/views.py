from flask import Flask, escape, request, jsonify

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# To test if flask application works
@app.route('/hello')
def hello():
	return jsonify({'data': 'hello world.'})
