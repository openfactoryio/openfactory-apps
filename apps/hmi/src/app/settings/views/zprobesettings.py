"""
Z-Probe Settings view
"""
from flask import render_template, redirect, url_for, flash
from flask.views import MethodView
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

from ....models.cncsettings import CNCSettings
from ....db import db


class ZProbeSettingsForm(FlaskForm):
    """
    Z-Probe Settings form
    """
    probe_speed = StringField('Probe speed',
                              description='Probe speed in mm/min',
                              validators=[DataRequired()])
    probe_height = StringField('Probe height',
                               description='Probe height in mm',
                               validators=[DataRequired()])
    z_rise = StringField('Z rise rise',
                         description='Z rise height in mm',
                         validators=[DataRequired()])
    submit = SubmitField('Save')


class ZProbeSettingsView(MethodView):
    """
    Z-Probe settings view
    """

    decorators = [login_required]
    methods = ["GET", "POST"]

    def get(self):
        # retrieve stored values from the database
        probe_speed = CNCSettings.query.filter_by(key="probe_speed").first()
        probe_height = CNCSettings.query.filter_by(key="probe_height").first()
        z_rise = CNCSettings.query.filter_by(key="z_rise").first()

        # populate the form with stored values
        form = ZProbeSettingsForm()
        if probe_speed:
            form.probe_speed.data = probe_speed.value
        if probe_height:
            form.probe_height.data = probe_height.value
        if z_rise:
            form.z_rise.data = z_rise.value

        return render_template("settings/settings.html",
                               form=form,
                               title='Z-Probe Settings')

    def post(self):

        form = ZProbeSettingsForm()
        if form.validate_on_submit():
            probe_speed = CNCSettings.query.filter_by(key="probe_speed").first()
            probe_height = CNCSettings.query.filter_by(key="probe_height").first()
            z_rise = CNCSettings.query.filter_by(key="z_rise").first()

            # Update or create the database entries
            if probe_speed:
                probe_speed.value = form.probe_speed.data
            else:
                probe_speed = CNCSettings(key="probe_speed", value=form.probe_speed.data, description="Probe speed in mm/min")
                db.session.add(probe_speed)

            if probe_height:
                probe_height.value = form.probe_height.data
            else:
                probe_height = CNCSettings(key="probe_height", value=form.probe_speed.data, description="Probe height in mm")
                db.session.add(probe_height)

            if z_rise:
                z_rise.value = form.z_rise.data
            else:
                z_rise = CNCSettings(key="z_rise", value=form.z_rise.data, description="Z rise in mm")
                db.session.add(z_rise)

            # Commit changes to the database
            db.session.commit()

            flash('Z-probe settings saved successfully', "success")
            return redirect(url_for('settings.index'))
        else:
            flash('Errors in your settings', "danger")
            return render_template("settings/settings.html",
                                   form=form,
                                   title='Z-Probe Settings')
