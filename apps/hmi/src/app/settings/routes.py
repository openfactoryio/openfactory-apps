"""
Routes for Settings Blueprint
"""
from flask_login import login_required
from flask import render_template
from . import settings_blueprint
from .views.cncsettings import CNCSettingsView
from .views.zprobesettings import ZProbeSettingsView


@settings_blueprint.route('/')
@login_required
def index():
    return render_template('settings/settingsBase.html',
                           title='Settings home')


settings_blueprint.add_url_rule("/cnc", view_func=CNCSettingsView.as_view("cnc"))
settings_blueprint.add_url_rule("/zprobe", view_func=ZProbeSettingsView.as_view("zprobe"))
