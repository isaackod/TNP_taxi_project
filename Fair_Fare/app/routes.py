from flask import render_template,flash, redirect, send_file, session, url_for, request
from app import app
from app.forms import TripForm
import time
import ast
from datetime import timedelta


## Model and Data setup
## It's a bit out of place in routes but not sure where else to put it.

from .data_science_part.feature_utils import load_hdf
from .data_science_part.aggregations import bin_on_time_distance
from .data_science_part.model_utils import get_model_from_file, predict_fare
from .data_science_part.trips import Stop, Ride
from .data_science_part.api_interactions import price_estimate_from_lyft
from .data_science_part.top_level import run_Fair_Fare
from .data_science_part.folium_map import generate_map
from .data_science_part.plotting import build_hists_for_altair, build_preds_for_altair, show_viz

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

def price_trend(val_dict):
    res = {}
    for key, vals in val_dict.items():
        cur_price = vals[0]
        if len(vals) > 3:
            future_price = sum(vals[1:4])/3
            savings = future_price/cur_price-1
            if savings > .05:
                res[key] = f"Prices increasing ({int(savings*100)}%)"
            elif savings < -.05:
                res[key] = f"Prices decreasing ({-int(savings*100)}%"
            else:
                res[key]= "stable"
        else:
            res[key]= None
    return res


@app.route('/', methods=['GET', 'POST'])
def index():
    form = TripForm()
    session['preds'] = {}
    if form.validate_on_submit():
        USER_PARAMS = {"pickup": chicagoize(form.pickup.data),
               "dropoff": chicagoize(form.dropoff.data),
               "forecast_hrs":5, "time":form.date.data}


        res = run_Fair_Fare(USER_PARAMS,rideshare_binned,
                        taxi_binned,taxi_model,rideshare_model)

        # Add time info
        ride_dict = res['ride_object'].info_dict()
        ride_dict['departure_datetime']=str(form.date.data)
        ride_dict['arrival_datetime']=str(form.date.data + timedelta(seconds=ride_dict['Trip_Seconds']))

        poly = res['ride_object'].poly

        generate_map(poly)

    

        model_dict = res['model_estimates']

        # To indicate 'fairness'
        means = {}
        for name, agg in res['fare_aggs'].items():
            means[name+"_mean"] = f"{agg.mean():.2f}$"

        ride_dict.update(means)

        show_viz(res['fare_aggs'], res['model_estimates'])
        

        return redirect(url_for('results', model_dict = model_dict, ride_dict = ride_dict))
    return render_template('index.html', form = form)


@app.route('/map.html')
def show_map():
    return send_file('static/map.html')

@app.route('/hist.html')
def show_hist():
    return send_file('static/hist.html')


@app.route('/results')
def results():
    # probably a better way to pass dicts than literal_eval...
    model_vals = ast.literal_eval(request.args.get('model_dict'))
    ride_info = ast.literal_eval(request.args.get('ride_dict'))
    #flash(ride_info)
    prices = {k: f"{round(v[0]):.2f}$" for k, v in model_vals.items()}
    return render_template('results.html', ride_info = ride_info, prices = prices, price_trend = price_trend(model_vals))

@app.route('/splash')
def data_info():
    return render_template('splash.html')



@app.route('/details', methods=['GET'])
def details():
    return render_template('implementation.html')

## prevent caching for the map
@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r