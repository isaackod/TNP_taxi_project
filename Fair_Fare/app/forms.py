from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired


class TripForm(FlaskForm):
    pickup = StringField('Pickup', validators=[DataRequired()])
    dropoff = StringField('Dropoff', validators=[DataRequired()])
    show_pooled = BooleanField('Show pooled trips')
    submit = SubmitField('Go!')