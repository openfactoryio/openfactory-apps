import os


class Config:
    APPLICATION_ROOT = os.environ.get("OPENFACTORY_ROOT_PATH", "")
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    FLASK_ADMIN_SWATCH = 'cerulean'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///hmi.db'
    KSQL_HOST = os.environ.get('KSQLDB_URL') or 'http://localhost:8088'
    KAFKA_BROKER = os.environ.get('KAFKA_BROKER') or 'localhost:9092'
    NC_FILES_FOLDER = None
