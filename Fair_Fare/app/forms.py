from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from wtforms.fields import DateTimeField
from .data_science_part.api_interactions import get_current_time_in_chicago




class TripForm(FlaskForm):
    pickup = StringField('Pickup', validators=[DataRequired()])
    dropoff = StringField('Dropoff', validators=[DataRequired()])
    #start = TimeField('start')
    date = DateTimeField('Departure Time (CDT)', default = get_current_time_in_chicago())
    submit = SubmitField('Go!')