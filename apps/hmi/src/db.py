import os
from openfactory.kafka import KSQLDBClient
from flask_sqlalchemy import SQLAlchemy
from .models import Base


ksql = KSQLDBClient(os.getenv("KSQLDB_URL", "http://localhost:8088"))
db = SQLAlchemy(model_class=Base)
