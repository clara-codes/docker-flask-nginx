from sqlalchemy import create_engine, Column, Integer, String, DateTime, VARCHAR
from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import DateTime
from sqlalchemy.exc import OperationalError
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine

import datetime
from app import settings
from utilities.logger import get_logger

DeclarativeBase = declarative_base()

logger = get_logger('database')

global_db_config = settings.DATABASE

def create_db_if_not_exists(db_config=None):
	"""
	Create Database if not exists, using postgres default user. 
	"""
	try: #Test if connects to app-specific database successfully
		if not db_config:
			db_config = global_db_config.copy()
		engine = create_engine(URL(**db_config))
		conn = engine.connect()
		conn.close()
		logger.info('Database connection to database: %s successfully made.' % db_config['database'])
	except OperationalError as e:
		logger.info('OperationalError exception caught in database connection - %s.' % e)
		if not db_config:
			db_config = global_db_config.copy()
		db_to_create = db_config['database']
		default_db_config = db_config.copy()
		default_db_config['database'] = 'postgres' #Connects to default database for database creation
		engine = create_engine(URL(**default_db_config))
		conn = engine.connect()
		conn.execute("commit")
		conn.execute("""CREATE DATABASE "%s";""" % db_to_create) #execute outside of transaction block.
		conn.close()
		logger.info("Database created: %s" % db_to_create)
		engine.dispose()
		logger.info("Disposed engine of 'postgres' db, expects to no longer be connected to it.")
	return

def db_connect(db_config=None):
	"""
	Performs database connection using database settings from settings.py.
	Returns sqlalchemy engine instance
	"""
	if not db_config:
		db_config = global_db_config.copy()
	engine = create_engine(URL(**db_config))
	logger.info("Created db engine to database: %s." % db_config['database'])
	return engine


def create_tables(engine):
    """
	Take the meta data of the table to create the tables. 
    """
    DeclarativeBase.metadata.create_all(engine)
    logger.info('Created tables if not exist.')

class utcnow(expression.FunctionElement):
	type = DateTime()

@compiles(utcnow, 'postgresql')
def pg_utcnow(element, compiler, **kw):
	return "TIMEZONE('utc', CURRENT_TIMESTAMP)"


class BaseModel(object):
	"""
	Define base attributes and columns for DeclarativeBase class.
	"""
	@declared_attr
	def __tablename__(cls):
		return cls.__name__

	created_at = Column('created_at', DateTime, server_default=utcnow(), nullable=False)
	updated_at = Column('updated_at', DateTime, server_default=utcnow(),
		server_onupdate=utcnow(), nullable=False)


class Order(BaseModel, DeclarativeBase):
	"""Schema logic for Order table."""
	id = Column(Integer, primary_key=True)
	distance = Column('distance', Integer, nullable=False)
	status = Column('status', VARCHAR(32), server_default="UNASSIGNED", nullable=False)
	