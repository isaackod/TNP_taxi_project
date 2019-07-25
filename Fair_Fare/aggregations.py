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
        
        
class bin_on_time_distance(object):
    """Takes a cleaned taxi or TNP dataframe and bins on time and distance"""
    def __init__(self, dataframe, nbins = (50,0),seconds_cutoff = 1600,miles_cutoff = 10, bUseCutoff = False):
        self.df = dataframe
        
        self.nbins = nbins[0]
        self.nbins_after_cutoff = nbins[1]
        # cutoffs were just chosen based on a histogram of the values the parameter takes
        self.seconds_cutoff = seconds_cutoff
        self.miles_cutoff = miles_cutoff

        self.seconds_b= None
        self.miles_b = None
        
        self.seconds_interval = ()
        self.miles_interval = ()
        
        self.cut_along_time_distance(bUseCutoff)
        
        
    def check_oob(self, td_tup):
        if ((td_tup[0]<self.seconds_interval[0]) or (td_tup[0]>self.seconds_interval[1]) or
            (td_tup[1]<self.miles_interval[0]) or (td_tup[1]>self.miles_interval[1])):
            return True
        else:
            return False
       
    def time_distance_to_bin(self, td_tup):
        if self.check_oob(td_tup):
            raise ValueError("Exceeded the maximum or minimum length trip.")
        else:
            # bin is the where the value just exceeds the axis.
            sec_b = np.where(self.seconds_b-td_tup[0]<0)[0][-1]
            mi_b = np.where(self.miles_b-td_tup[1]<0)[0][-1]
            return (sec_b, mi_b)

    def bin_on_counts_linmix(self, arr, cutoff):
        """adaptive bins based on bin size up until a cutoff, then linearly spaced."""
        start, end = np.min(arr), np.max(arr)
        # add small noise to allow sorting to be essentially unique if input data is discrete:
        arr += np.random.uniform(0,1e-6,len(arr))
        arr = np.sort(arr)
        n_below_cutoff = np.sum(arr <cutoff)
        lowarr = arr[:n_below_cutoff]
        spacing = int(n_below_cutoff/self.nbins)
        locs= np.arange(0,n_below_cutoff,spacing)
        low_idxs = lowarr[locs]
        cutoff_spacing = (end-cutoff)/self.nbins_after_cutoff 
        high_idxs = np.arange(cutoff, end, cutoff_spacing)
        return np.hstack((low_idxs, high_idxs)), (start,end)
    
    def bin_on_counts(self, arr):
        """adaptive bins no cutoff."""
        start, end = np.min(arr), np.max(arr)
        # add small noise to allow sorting to be essentially unique if input data is discrete:
        # This is sort of a disaster becasuse it indroduces the possibility of random failure... hopefully highly improbable
        arr += np.random.uniform(-1e-3,1e-3,len(arr))
        arr = np.sort(arr)
        spacing = int(len(arr)/self.nbins)
        locs= np.arange(0,len(arr),spacing)
        idxs = arr[locs]
        return idxs, (start,end)
    
    def cut_along_time_distance(self, bUseCutoff):
        """Add a _b binned column foreach lat and long, also a tuple of all the bins"""
        seconds = self.df.Trip_Seconds.values
        miles = self.df.Trip_Miles.values
        
        if bUseCutoff:
            self.seconds_b, self.seconds_interval = self.bin_on_counts_linmix(seconds,self.seconds_cutoff)
            self.miles_b, self.miles_interval = self.bin_on_counts_linmix(miles,self.miles_cutoff)
            
        else:
            self.seconds_b, self.seconds_interval = self.bin_on_counts(seconds)
            self.miles_b, self.miles_interval = self.bin_on_counts(miles)
        
        self.df["seconds_b"] = pd.cut(self.df["Trip_Seconds"],
                                             bins = self.seconds_b, labels = np.arange(len(self.seconds_b)-1), retbins=False)
        
        self.df["miles_b"]  = pd.cut(self.df["Trip_Miles"],
                                             bins = self.miles_b, labels = np.arange(len(self.miles_b)-1), retbins=False)
        self.df["td_bin"] = list(zip(self.df["seconds_b"],self.df["miles_b"]))
        
        