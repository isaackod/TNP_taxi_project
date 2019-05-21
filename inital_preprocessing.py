"""This script loades and saves the CSV files as h5 files with reasonable
pandas formats. See https://www.dataquest.io/blog/pandas-big-data/ for 
a discussion on big-ish data loading in pandas.
"""

from path import Path
import pandas as pd

datap = Path('data')
taxi_in_path = datap/'Taxi_Trips.csv'
tnp_in_path = datap/'Transportation_Network_Providers_-_Trips.csv'

taxi_out_path = datap/'taxi.h5'
tnp_out_path = datap/'tnp.h5'


taxi_cols = ['Trip Start Timestamp',
       'Trip Seconds', 'Trip Miles', 'Pickup Community Area','Dropoff Community Area',
       'Fare', 'Tips', 'Tolls', 'Extras','Trip Total',
       'Pickup Centroid Latitude','Pickup Centroid Longitude',
       'Dropoff Centroid Latitude', 'Dropoff Centroid Longitude']

taxi_dtypes = ['float32','float32','float32','float32',
               'float32','float32','float32','float32','float32',
               'float64','float64','float64','float64']

tnp_cols = ['Trip Start Timestamp', 
       'Trip Seconds','Trip Miles','Pickup Community Area', 'Dropoff Community Area', 
       'Fare', 'Tip', 'Additional Charges', 'Trip Total', 'Shared Trip Authorized',
       'Pickup Centroid Latitude', 'Pickup Centroid Longitude', 
       'Dropoff Centroid Latitude', 'Dropoff Centroid Longitude']

tnp_dtypes = ['float32','float32','float32','float32',
               'float32','float32','float32','float32','bool',
               'float64','float64','float64','float64']

def load_and_clean(cols, dtypes, fname):
    """Load csv with specified dtypes and column subset, assumes a time axis is in the frist column elt."""
    column_types = dict(zip(cols[1:], dtypes)) # skip the date

    return pd.read_csv(
             fname, usecols =cols,
             dtype = column_types,parse_dates=[cols[0]],infer_datetime_format=True)

if not taxi_out_path.isfile():
    print("No h5 file found, generating from csv")
    taxi = load_and_clean(taxi_cols, taxi_dtypes, taxi_in_path)
    # Save as hdf for much faster loading in the future.
    taxi.to_hdf(taxi_out_path, key='df', mode='w',format='table')
    print(taxi.info(memory_usage='deep')) # 1.8 GB
    del(taxi)

elif not tnp_out_path.isfile():
    print("No h5 file found, generating from csv")
    tnp = load_and_clean(tnp_cols, tnp_dtypes, tnp_in_path)
    tnp.to_hdf(tnp_out_path, key='df', mode='w',format='table')
    print(tnp.info(memory_usage='deep'))
    del(tnp)

else:
    print("Nothing to be done, h5 files exist.")


