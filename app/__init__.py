import logging
import os
from flask import Flask
from flask_appbuilder import AppBuilder, SQLA
from .register import *
from .index import MyIndexView

"""
 Logging configuration
"""

logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
logging.getLogger().setLevel(logging.DEBUG)

app = Flask(__name__)
app.config.from_object("config")

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
if not os.path.exists(app.config['FILE_FOLDER']):
    os.makedirs(app.config['FILE_FOLDER'])

"""
    Register
"""
db = SQLA(app)
appbuilder = AppBuilder(
        app,
        db.session,
        security_manager_class=MySecurityManager,
        indexview=MyIndexView
    )

"""
from sqlalchemy.engine import Engine
from sqlalchemy import event

#Only include this for SQLLite constraints
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # Will force sqllite contraint foreign keys
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
"""

from . import views
