"""
File manager blueprint
"""
from pathlib import Path
from flask import Blueprint
from ...config import Config


file_manager_blueprint = Blueprint('files', __name__,
                                   template_folder='templates')

def create_bp(app):
    """ Blueprint factory """

    # Create NC files directory if missing
    Path(Config.NC_FILES_FOLDER).mkdir(parents=True, exist_ok=True)

    # register blueprint
    app.register_blueprint(file_manager_blueprint, url_prefix='/files')

from . import routes
