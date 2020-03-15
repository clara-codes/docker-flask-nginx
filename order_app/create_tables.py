from order_app.models import db_connect, create_tables, create_db_if_not_exists

if __name__ == '__main__':
	create_db_if_not_exists()
	create_tables(db_connect())