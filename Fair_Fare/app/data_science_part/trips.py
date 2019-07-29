from .feature_utils import haversine_dist
from .api_interactions import gmaps_handler



class Stop(object):
    """Keeps track of lat/long and geocode of a point on a map. Also checks if it's near a Chicago airport."""
    def __init__(self, location):
        self.bGeocoded= False
        self.bAirport = None
        self.tuple = None
        
        if isinstance(location, tuple):
            self.lat = location[0]
            self.long = location[1]
            self.tuple = location
            self.geocode = location
        elif isinstance(location, str):
            self.lat = None
            self.long = None
            self.geocode = location
        else:
            raise ValueError("Stop must be a string or a (lat,long) tuple.")
            
    def __repr__(self):
        if self.bGeocoded:
            return(f"Geocoded Location: {self.geocode}, Coordinates: {(self.lat,self.long)}")
        else:
            return(f"Coordinates: {(self.lat,self.long)}")
            
    
    # TODO: use properties and setters instead of just updating internal vars
    def update_params(self, lat,long,geocode):
        self.lat = lat
        self.long = long
        self.tuple = (self.lat,self.long)
        self.geocode = geocode
        self.bGeocoded= True
        self.update_airport()
        
    
    def update_airport(self,thresh_km = 3):
        midway = (41.7868, -87.7522)
        ohare = (41.9742, -87.9073)
        d1 = haversine_dist(self.lat, self.long,midway[0],midway[1])
        d2 = haversine_dist(self.lat, self.long,ohare[0],ohare[1])
        airport_flag = d1 < thresh_km
        airport_flag |= d2 < thresh_km
        self.bAirport = airport_flag
        
        


class Ride(object):
    """Defines a ride consisting of two 'Stop' classes. Pulls additional info and geocoding from 
    the google maps API for that route. Formats the ride in a way suitible to the ML model predictions."""
    def __init__(self, start, end,time, bRideshare = True, bShared = False):
        self.start = Stop(start)
        self.end = Stop(end)
        self.time = time
        self.path = (self.start.tuple,self.end.tuple)
        self.as_row = {}
        self.gm = None
        self.traveltime = None
        self.miles = None
        self.poly = None
        self.bShared = bShared
        self.bRideshare = bRideshare
   
        self.build_row()
        
    def __repr__(self):
        return f"Start: {self.start} \nEnd: {self.end} \nDetails: {self.as_row}"
        
    ### TODO: Add some protection to the gmaps call
    ### we let gmaps update the lat and long, it should put things on a street if not already
    def gmaps_call(self):
        self.gm = gmaps_handler(self.start.geocode,self.end.geocode, self.time)
        self.start.update_params(self.gm['start_latlong'][0],self.gm['start_latlong'][1],self.gm['start_geocoded'])
        self.end.update_params(self.gm['end_latlong'][0],self.gm['end_latlong'][1],self.gm['end_geocoded'])
        self.path = (self.start.tuple,self.end.tuple)
        self.poly = self.gm['poly']
   
    def build_row(self):
        if not self.gm:
            self.gmaps_call()
            
        self.miles = self.gm['dist_m']/1609.34
        self.traveltime = self.gm['time_s']
        self.as_row['Trip_Seconds'] = self.traveltime
        self.as_row['Trip_Miles'] = self.miles
        if self.bRideshare:
            self.as_row['Shared_Trip_Authorized'] = self.bShared
        elif 'Shared_Trip_Authorized' in self.as_row:
            del self.as_row['Shared_Trip_Authorized']
     
        self.as_row['Pickup_Centroid_Latitude'] = self.gm['start_latlong'][0]
        self.as_row['Pickup_Centroid_Longitude'] = self.gm['start_latlong'][1]
        self.as_row['Dropoff_Centroid_Latitude'] = self.gm['end_latlong'][0]
        self.as_row['Dropoff_Centroid_Longitude'] = self.gm['end_latlong'][1]
        self.as_row['vel_mph'] = self.as_row['Trip_Miles']/(self.as_row['Trip_Seconds']/3600)
        self.add_airport()
        self.add_time()
      
   
    def add_airport(self):
        if self.start.bAirport or self.end.bAirport:
            self.as_row['bAirport'] = True
        else:
            self.as_row['bAirport'] = False
    
    def add_time(self):
        self.as_row['day_of_wk'] = self.time.weekday()
        self.as_row['hour'] = self.time.hour

    def info_dict(self):
        ret = {}
        ret['start'] = self.start.geocode
        ret['end'] = self.end.geocode
        ret.update(self.as_row)
        return ret
        
    