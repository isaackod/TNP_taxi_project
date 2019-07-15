"""Utilities for transforming a cleaned dataset 
into aggregations over trips"""

import numpy as np
import pandas as pd



class agg_on_trips(object):
    """Takes a cleaned taxi or TNP dataframe and generates trips by binning
    (lat, long) coordinates."""
    def __init__(self, dataframe):
        self.df = dataframe
        self.n_bins = 50


    def rename_ll(self):
        """to make lat and long easier to type"""
        name_mapping = {'Pickup_Centroid_Latitude': 'latp',
                        'Dropoff_Centroid_Latitude': 'latd',
                        'Pickup_Centroid_Longitude': 'longp',
                        'Dropoff_Centroid_Longitude': 'longd'}
        self.df.rename(index=str, columns = name_mapping, inplace=True)


    def find_boundary(self, padding = 0.001):
        topleft = (max(self.df.latp.max(),self.df.latd.max())+padding,min(self.df.longp.min(),self.df.longd.min())-padding)
        bottomright = (min(self.df.latp.min(),self.df.latd.min())-padding,max(self.df.longp.max(),self.df.longd.max())+padding)
        return topleft, bottomright

    def coord_bins(self):
        """Generate the grid from the lat and long."""
        # TODO: consider non-rectangular grid
        topleft, bottomright = self.find_boundary(self.df)
        lat_axis = np.linspace(bottomright[0],topleft[0],n_bins)
        long_axis = np.linspace(topleft[1],bottomright[1],n_bins)
        return lat_axis, long_axis
    

    def cut_along_lat_long(self, locs):
        """Add a _b binned column foreach lat and long, also a tuple of all the bins"""
        labels = np.arange(self.n_bins-1)
        new_colname = {loc:loc + "_b" for loc in locs}
        lat_axis, long_axis = self.coord_bins()
        
        for lat in locs[0:2]:
            self.df[new_colname[lat]] = pd.cut(self.df[lat], bins = lat_axis,labels = labels, retbins=False)

        for long in locs[2:]:
            self.df[new_colname[long]] = pd.cut(self.df[long], bins = long_axis,labels = labels, retbins=False)
            
        self.df['path'] = list(zip(zip(self.df.latp_b,self.df.longp_b), zip(self.df.latd_b,self.df.longd_b)))
        