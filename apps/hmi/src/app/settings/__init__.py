"""
Settings blueprint
"""
from flask import Blueprint


settings_blueprint = Blueprint('settings', __name__,
                               template_folder='templates')

def create_bp(app):
    """ Blueprint factory """

    # register blueprint
    app.register_blueprint(settings_blueprint, url_prefix='/settings')

from . import routes
