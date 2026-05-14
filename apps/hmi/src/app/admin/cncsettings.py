from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, ValidationError
from ...models.cncsettings import CNCSettings
from ...db import db


# Custom validator for the key field
def unique_key_validator(form, field):
    if db.session.query(CNCSettings).filter_by(key=field.data).first():
        raise ValidationError("This key already exists. Please choose a different key.")


class CNCSettingsForm(FlaskForm):
    """
    Custom form class for Configuration
    """
    key = StringField('Key', validators=[DataRequired(), unique_key_validator])
    value = TextAreaField('Value', validators=[DataRequired()])
    description = TextAreaField('Description')


class CNCSettingsModelView(ModelView):
    """
    Admin View for Configuration Model
    """
    form = CNCSettingsForm
