"""
CNC Settings view
"""
from flask import render_template, redirect, url_for, flash, current_app
from flask.views import MethodView
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Regexp, ValidationError

from ....models.cncsettings import CNCSettings
from ....db import ksql, db


class CNCSettingsForm(FlaskForm):
    """
    CNC Settings form
    """
    cnc_port = StringField('USB Connection Port',
                           description='Port on which the CNC is connected',
                           validators=[DataRequired(),
                                       Regexp(r"^/dev/.+", message="Not a valid port (e.g., /dev/ttyUSB0)")])
    cnc_uuid = StringField('OpenFactory CNC UUID',
                           description='OpenFactory UUID of the CNC',
                           validators=[DataRequired()])
    cnc_sup_uuid = StringField('OpenFactory CNC Supervisor UUID',
                               description='OpenFactory UUID of the CNC supervisor',
                               validators=[DataRequired()])
    submit = SubmitField('Save')

    def validate_cnc_uuid(form, field):
        """ Validate if UUID exists """
        query = f"SELECT AVAILABILITY FROM ASSETS_AVAIL WHERE ASSET_UUID='{field.data}';"
        res = ksql.query(query)
        if not res:
            raise ValidationError('This UUID does not exist in OpenFactory')


class CNCSettingsView(MethodView):
    """
    CNC settings view
    """

    decorators = [login_required]
    methods = ["GET", "POST"]

    def get(self):
        # retrieve stored values from the database
        port = CNCSettings.query.filter_by(key="cnc_port").first()
        uuid = CNCSettings.query.filter_by(key="cnc_uuid").first()
        sup = CNCSettings.query.filter_by(key="sup_uuid").first()

        # populate the form with stored values
        form = CNCSettingsForm()
        if port:
            form.cnc_port.data = port.value
        if uuid:
            form.cnc_uuid.data = uuid.value
        if sup:
            form.cnc_sup_uuid.data = sup.value

        return render_template("settings/settings.html",
                               form=form,
                               title='CNC Settings')

    def post(self):

        form = CNCSettingsForm()
        if form.validate_on_submit():
            port = CNCSettings.query.filter_by(key="cnc_port").first()
            uuid = CNCSettings.query.filter_by(key="cnc_uuid").first()
            sup = CNCSettings.query.filter_by(key="sup_uuid").first()

            # Update or create the database entries
            if port:
                port.value = form.cnc_port.data
            else:
                port = CNCSettings(key="cnc_port", value=form.cnc_port.data, description="USB Connection Port")
                db.session.add(port)

            if uuid:
                uuid.value = form.cnc_uuid.data
            else:
                uuid = CNCSettings(key="cnc_uuid", value=form.cnc_uuid.data, description="OpenFactory UUID")
                db.session.add(uuid)

            if sup:
                sup.value = form.cnc_sup_uuid.data
            else:
                sup = CNCSettings(key="sup_uuid", value=form.cnc_sup_uuid.data, description="OpenFactory Supvervisor UUID")
                db.session.add(sup)

            # Commit changes to the database
            db.session.commit()

            flash('CNC settings saved successfully', "success")
            current_app.cnc_uuid = form.cnc_uuid.data
            return redirect(url_for('settings.index'))
        else:
            flash('Errors in your settings', "danger")
            return render_template("settings/settings.html",
                                   form=form,
                                   title='CNC Settings')
