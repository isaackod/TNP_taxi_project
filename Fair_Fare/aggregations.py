"""Utilities for transforming a cleaned dataset 
into aggregations over trips"""

import numpy as np
import pandas as pd



class agg_on_trips(object):
    """Takes a cleaned taxi or TNP dataframe and generates trips by binning
    (lat, long) coordinates."""
    def __init__(self, dataframe):
        self.df = dataframe
        self.geo_cols = ['Pickup_Centroid_Latitude','Dropoff_Centroid_Latitude','Pickup_Centroid_Longitude','Dropoff_Centroid_Longitude']
        self.n_bins = 20
        self.total_unique_paths = None


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
        lat_axis = np.linspace(bottomright[0],topleft[0],self.n_bins)
        long_axis = np.linspace(topleft[1],bottomright[1],self.n_bins)
        return lat_axis, long_axis
    

    def cut_along_lat_long(self):
        """Add a _b binned column foreach lat and long, also a tuple of all the bins"""
        locs = self.geo_cols
        labels = np.arange(self.n_bins-1)
        new_colname = {loc:loc + "_b" for loc in locs}
        lat_axis, long_axis = self.coord_bins()
        
        for lat in locs[0:2]:
            self.df[new_colname[lat]] = pd.cut(self.df[lat], bins = lat_axis,labels = labels, retbins=False)

        for long in locs[2:]:
            self.df[new_colname[long]] = pd.cut(self.df[long], bins = long_axis,labels = labels, retbins=False)
            
        # path is a list 
        self.df['path'] = list(zip(
            zip(self.df.Pickup_Centroid_Latitude_b,self.df.Pickup_Centroid_Longitude_b),
            zip(self.df.Dropoff_Centroid_Latitude_b,self.df.Dropoff_Centroid_Longitude_b))
                              )
        self.total_unique_paths = self.df.groupby('path').Trip_Miles.count().count()
        