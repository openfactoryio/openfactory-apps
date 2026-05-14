"""
CNC blueprint
"""
from flask import Blueprint


cnc_blueprint = Blueprint('cnc', __name__,
                          template_folder='templates')

def create_bp(app):
    """ Blueprint factory """

    # register blueprint
    app.register_blueprint(cnc_blueprint, url_prefix='/cnc')

from . import routes
