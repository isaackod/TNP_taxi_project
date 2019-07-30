import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .aggregations import bin_on_time_distance
from .model_utils import get_model_from_file, predict_fare
from .trips import Stop, Ride
from .api_interactions import price_estimate_from_lyft, get_current_time_in_chicago


# TODO: Rethink Ride object to either not do the API call or have better public methods (currently using internal ones)
def run_model_and_gdirections_api(start, end, start_time,taxi_model,rideshare_model, forecast_hours = 1):
    assert(forecast_hours <10) # don't break the bank!
    model_estimate = {'Rideshare_pooled_price_estimate':[],'Rideshare_regular_price_estimate':[],'Taxi_price_estimate':[]}
    
    # forecast hours from start
    times = [start_time+timedelta(hours=i) for i in range(forecast_hours)] 
    rides = [Ride(start,end, time, bRideshare = True, bShared = False) for time in times]
        
    for ride in rides:
        model_estimate['Rideshare_regular_price_estimate'].append(predict_fare(ride, rideshare_model)[0])
        ride.bShared = True
        ride.build_row()
        model_estimate['Rideshare_pooled_price_estimate'].append(predict_fare(ride, rideshare_model)[0])
        
    for ride in rides:
        ride.bRideshare = False
        ride.build_row()
        model_estimate['Taxi_price_estimate'].append(predict_fare(ride, taxi_model)[0])
        
    # returing one ride for the geolocation etc.
    return model_estimate, ride


def text_to_fares(binned_rs,binned_tax, start, end, taxi_model,rideshare_model, forecast_hours = 1):
    curr_time = get_current_time_in_chicago()
    model_estimate, ride = run_model_and_gdirections_api(start, end,curr_time,taxi_model,rideshare_model, forecast_hours)

    lyft_estimates = price_estimate_from_lyft(ride.start.tuple,ride.end.tuple)

    # Lyft estimate is not time dependant
    td_tup = (ride.traveltime,ride.miles)
    
    group_rs,  group_tax = ride_subset_from_time_distance(td_tup,binned_tax,binned_rs)

    
    return model_estimate, lyft_estimates, group_tax, group_rs, ride

def ride_subset_from_time_distance(td_tup,binned_tax,binned_rs):
    """select only rides corresponding to bin containing td_tup = (time, distance)"""
    binned_pth_tax = binned_tax.time_distance_to_bin(td_tup)
    binned_pth_rs = binned_rs.time_distance_to_bin(td_tup)
    return binned_rs.df[binned_rs.df.td_bin == binned_pth_rs], binned_tax.df[binned_tax.df.td_bin == binned_pth_tax]
    
def run_Fair_Fare(USER_PARAMS,rideshare_binned,taxi_binned,taxi_model,rideshare_model):

    model_estimate, lyft_estimate,taxi_group, rideshare_group, ride = text_to_fares(rideshare_binned,taxi_binned,
                                                                                   USER_PARAMS['pickup'], USER_PARAMS['dropoff'],taxi_model,rideshare_model, 
                                                                                   USER_PARAMS['forecast_hrs'])

    rideshare_shared_fares = rideshare_group[rideshare_group["Shared_Trip_Authorized"] == True].Final_Fare
    rideshare_fares = rideshare_group[rideshare_group["Shared_Trip_Authorized"] == False].Final_Fare
    taxi_fares = taxi_group.Final_Fare

    ret_d = {'model_estimates': model_estimate, 
    'lyft_api_estimate':lyft_estimate, 
    'fare_aggs': {'Pooled_Rideshare':rideshare_shared_fares,'Regular_Rideshare':rideshare_fares,'Taxi':taxi_fares},
    'ride_object': ride}

    return ret_d