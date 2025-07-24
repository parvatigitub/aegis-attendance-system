from flask_wtf import FlaskForm
from wtforms import HiddenField
from wtforms import BooleanField, IntegerField
from wtforms.validators import NumberRange


class AttendanceForm(FlaskForm):
    """Empty form just for CSRF protection"""
    pass
