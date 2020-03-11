import logging.config
import logging, json, os


def get_logger(name):
	# get logging config file
	with open(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logger.json')) as log_json:
	    logging_config = json.load(log_json)
	logging.config.dictConfig(logging_config)
	return logging.getLogger(name)