import googlemaps
import json

def gmaps_handler(start, end, time):
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
        