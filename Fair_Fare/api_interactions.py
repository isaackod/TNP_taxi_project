"""Includes any calls to external API's."""

import googlemaps
import json
import requests
from datetime import datetime
import pytz


def get_current_time_in_chicago():
    utc_now = pytz.utc.localize(datetime.utcnow())
    return utc_now.astimezone(pytz.timezone("America/Chicago"))


def gmaps_handler(start, end, time):
    """Runs the gmaps directions API and returns the info we want."""
    with open("./secrets.json.nogit") as fh:
        secrets = json.loads(fh.read())

    gmaps_client = googlemaps.Client(key=secrets['gmaps_api_key'])
    
    GMAPS_NAME_MAPPING = {'start_address':'start_geocoded',
                      'end_address':'end_geocoded',
                      'start_location':'start_latlong',
                      'end_location':'end_latlong',
                      'duration_in_traffic':'time_s',
                      'distance':'dist_m'}
    
    directions_result = gmaps_client.directions(start,end, departure_time = time)

    dr = directions_result[0]['legs'][0]
    out = {}
    for gname,newname in GMAPS_NAME_MAPPING.items():
        vals = dr[gname]
        if gname == 'start_address' or gname == 'end_address':
            out[newname] = vals
        elif gname == 'end_location' or gname =='start_location':
            out[newname] = tuple([float(val) for val in vals.values()])
        else:
            out[newname] = int(list(vals.values())[1])
    return out


def parse_lyft_api(json_response):
    out = {}
    for ride_type in json_response['cost_estimates']:
        min_c, max_c = ride_type['estimated_cost_cents_min'],ride_type['estimated_cost_cents_max']
        duration = ride_type['estimated_duration_seconds']
        if ride_type['ride_type'] == 'lyft_line':
            out['shared_min_p'] = min_c
            out['shared_max_p'] = max_c
        elif ride_type['ride_type'] == 'lyft':
            out['min_p'] = min_c
            out['max_p'] = max_c
            out['trip_time_s'] = duration
    return out

def price_estimate_from_lyft(start,end):
    """Calls lyft API for latlong tuples at start and end."""
    params = {'start_lat':start[0], 
            'start_lng': start[1], 
            'end_lat': end[0],
            'end_lng': end[1]
             }
    response = requests.get('https://www.lyft.com/api/costs?', params=params,timeout=5)
    try:
        return parse_lyft_api(response.json())
    except:
        raise ValueError('Unable to get result from Lyft API.')




        