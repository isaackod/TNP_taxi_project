"""Utilities for transforming a cleaned dataset 
into aggregations over trips"""

import numpy as np
import pandas as pd

class bin_on_trips(object):
    """Takes a cleaned taxi or TNP dataframe and generates trips by binning
    (lat, long) coordinates. No grouping done in this class."""
    def __init__(self, dataframe):
        self.df = dataframe
        self.geo_cols = ['Pickup_Centroid_Latitude','Dropoff_Centroid_Latitude','Pickup_Centroid_Longitude','Dropoff_Centroid_Longitude']
        self.n_bins = 20
        self.total_unique_paths = None
        
        self.coord_bins()
       


    def find_boundary(self, padding = 0.001):
        topleft = (max(self.df.Pickup_Centroid_Latitude.max(),self.df.Dropoff_Centroid_Latitude.max())+padding,
                   min(self.df.Pickup_Centroid_Longitude.min(),self.df.Dropoff_Centroid_Longitude.min())-padding)
        bottomright = (min(self.df.Pickup_Centroid_Latitude.min(),self.df.Dropoff_Centroid_Latitude.min())-padding,
                       max(self.df.Pickup_Centroid_Longitude.max(),self.df.Dropoff_Centroid_Longitude.max())+padding)
        return topleft, bottomright

    def coord_bins(self):
        """Generate the grid from the lat and long."""
        # TODO: consider non-rectangular grid
        topleft, bottomright = self.find_boundary()
        self.lat_axis = np.linspace(bottomright[0],topleft[0],self.n_bins)
        self.long_axis = np.linspace(topleft[1],bottomright[1],self.n_bins)


    def check_oob(self, latlong_tup):
        if ((latlong_tup[0] < self.lat_axis[0]) or (latlong_tup[0] > self.lat_axis[-1]) or
            (latlong_tup[1] < self.long_axis[0]) or (latlong_tup[1] > self.long_axis[-1])):
            return True
        else:
            return False
            
    def lat_long_to_bin(self, latlong_tup):
        if self.check_oob(latlong_tup):
            raise ValueError("A given latitude or longitude is not within the grid.")
        else:
            # bin is the where the value just exceeds the axis.
            lat_b = np.where(self.lat_axis-latlong_tup[0]<0)[0][-1]
            long_b = np.where(self.long_axis-latlong_tup[1]<0)[0][-1]
            return (lat_b, long_b)
    
    def trip_to_path(self, trip):
        start, end  = trip[0], trip[1]
        start_bins = self.lat_long_to_bin(start)
        end_bins = self.lat_long_to_bin(end)
        return (start_bins, end_bins)
        

    def cut_along_lat_long(self):
        """Add a _b binned column foreach lat and long, also a tuple of all the bins"""
        locs = self.geo_cols
        labels = np.arange(self.n_bins-1)
        new_colname = {loc:loc + "_b" for loc in locs}
        
        for lat in locs[0:2]:
            self.df[new_colname[lat]] = pd.cut(self.df[lat], bins = self.lat_axis,labels = labels, retbins=False)

        for long in locs[2:]:
            self.df[new_colname[long]] = pd.cut(self.df[long], bins = self.long_axis,labels = labels, retbins=False)
            
        # path is a list 
        self.df['path'] = list(zip(
            zip(self.df.Pickup_Centroid_Latitude_b,self.df.Pickup_Centroid_Longitude_b),
            zip(self.df.Dropoff_Centroid_Latitude_b,self.df.Dropoff_Centroid_Longitude_b))
                              )
        self.total_unique_paths = self.df.groupby('path').Trip_Miles.count().count()
        