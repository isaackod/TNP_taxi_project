from flask import render_template,flash, redirect, send_file, session, url_for, request
from app import app
from app.forms import TripForm
import ast


## Model and Data setup
## It's a bit out of place in routes but not sure where else to put it.

from .data_science_part.feature_utils import load_hdf
from .data_science_part.aggregations import bin_on_time_distance
from .data_science_part.model_utils import get_model_from_file, predict_fare
from .data_science_part.trips import Stop, Ride
from .data_science_part.api_interactions import price_estimate_from_lyft, get_current_time_in_chicago
from .data_science_part.top_level import run_Fair_Fare
from .data_science_part.folium_map import generate_map


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
    session['preds'] = {}
    if form.validate_on_submit():
        USER_PARAMS = {"pickup": chicagoize(form.pickup.data),
               "dropoff": chicagoize(form.dropoff.data),
               "forecast_hrs":1}

        res = run_Fair_Fare(USER_PARAMS,rideshare_binned,
                        taxi_binned,taxi_model,rideshare_model)

        ride_dict = res['ride_object'].info_dict()

        poly = res['ride_object'].poly

        generate_map(poly)

        return redirect(url_for('results', model_dict = res['model_estimates'], ride_dict = ride_dict))
    return render_template('index.html', form = form)


@app.route('/map.html')
def show_map():
    return send_file('map.html')


@app.route('/results')
def results():
    # probably a better way to pass dicts than literal_eval...
    model_vals = ast.literal_eval(request.args.get('model_dict'))
    ride_info = ast.literal_eval(request.args.get('ride_dict'))
    flash(model_vals)
    return render_template('results.html', ride_info = ride_info, model_vals = model_vals)

@app.route('/data')
def data_info():
    flash('under construction')
    return render_template('data.html')



@app.route('/details', methods=['GET'])
def details():
    flash('details page TBD')
    return render_template('data.html')