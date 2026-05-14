from flask import Blueprint, redirect, url_for, flash
from flask_admin import Admin, AdminIndexView
from flask_login import current_user
from ...models.cncsettings import CNCSettings
from .cncsettings import CNCSettingsModelView


class AdminRestrictedIndexView(AdminIndexView):
    """
    Custom AdminIndexView with restricted access
    """
    def is_accessible(self):
        """ check permissions """
        return current_user.is_authenticated and current_user.role == 'admin'

    def inaccessible_callback(self, name, **kwargs):
        """ redirect for unauthorized users """
        flash("You do not have permission to access the admin panel.", "danger")
        return redirect(url_for('auth.login'))
    
    def get_url(self, endpoint, **kwargs):
        """
        Override get_url to customize where the admin.index link points to.
        """
        print(endpoint)
        if endpoint == 'admin.index':
            return url_for('cnc.index')
        return super().get_url(endpoint, **kwargs)


def create_bp(app, db):
    """ Blueprint factory """
    Blueprint('hmi_admin', __name__)

    # Initialize Flask-Admin with the custom AdminIndexView
    admin_app = Admin(app, name='OpenFactory GRBL HMI Admin',
                      index_view=AdminRestrictedIndexView(name='Back to HMI'))

    # Add views to the admin interface
    admin_app.add_view(CNCSettingsModelView(CNCSettings, db.session, name='CNC Settings'))

    return admin_app
