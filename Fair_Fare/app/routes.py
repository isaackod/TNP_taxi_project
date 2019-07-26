from flask import render_template,flash, redirect
from app import app
from app.forms import TripForm


## Model and Data setup
## It's a bit out of place in routes but not sure where else to put it.

from .data_science_part.feature_utils import load_hdf
from .data_science_part.aggregations import bin_on_time_distance
from .data_science_part.model_utils import get_model_from_file, predict_fare
from .data_science_part.trips import Stop, Ride
from .data_science_part.api_interactions import price_estimate_from_lyft, get_current_time_in_chicago
from .data_science_part.top_level import run_Fair_Fare


models = {"path":"../models/", "taxi":"taxi_xgb_full_reduced_params", "rideshare":"tnp_xgb_full_reduced_params" }
data = {"path":"../data/","taxi":"taxi_test.h5", "rideshare":"tnp_test.h5" }

taxi_model = get_model_from_file(models['path']+models['taxi'])
taxi_data = load_hdf(data['path']+data['taxi'])

rideshare_model = get_model_from_file(models['path']+models['rideshare'])
rideshare_data = load_hdf(data['path']+data['rideshare'])

rideshare_binned = bin_on_time_distance(rideshare_data)
del(rideshare_data)
taxi_binned = bin_on_time_distance(taxi_data)
del(taxi_data)


# desperate and dumb hacks
def chicagoize(in_str):
    if ("chicago" in in_str) or ("Chicago" in in_str):
        return in_str
    else:
        return in_str + ' chicago'



@app.route('/', methods=['GET', 'POST'])
def index():
    form = TripForm()
    if form.validate_on_submit():
        USER_PARAMS = {"pickup": chicagoize(form.pickup.data),
               "dropoff": chicagoize(form.dropoff.data),
               "forecast_hrs":1}

        res = run_Fair_Fare(USER_PARAMS,rideshare_binned,
                        taxi_binned,taxi_model,rideshare_model)

        flash('Route: {}, {}, {}'.format(
            chicagoize(form.pickup.data), form.dropoff.data,res[0]['Taxi_price_estimate'][0]))
        return redirect('/')
    return render_template('index.html', form = form)