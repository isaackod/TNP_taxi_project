"""See the jupyter notebook 'RS_Taxi_Model_Feature_Eng' for justification and plots."""


import numpy as np
import pandas as pd

AVG_EARTH_RADIUS = 6371.009  # in km

def haversine_dist(lat1, lng1, lat2, lng2):
    lat1, lng1, lat2, lng2 = map(np.radians, (lat1, lng1, lat2, lng2))
    lat = lat2 - lat1
    lng = lng2 - lng1
    d = np.sin(lat * 0.5) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(lng * 0.5) ** 2
    km = 2 * AVG_EARTH_RADIUS * np.arcsin(np.sqrt(d))
    return km

def bearing(lat1, lng1, lat2, lng2):
    lng_delta_rad = np.radians(lng2 - lng1)
    lat1, lng1, lat2, lng2 = map(np.radians, (lat1, lng1, lat2, lng2))
    y = np.sin(lng_delta_rad) * np.cos(lat2)
    x = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(lng_delta_rad)
    return np.degrees(np.arctan2(y, x))

def manhattan_dist(lat1, lng1, lat2, lng2):
    x = haversine_dist(lat1,lng1,lat1,lng2)
    y = haversine_dist(lat1,lng1,lat2,lng1)
    return x,y

def add_dist_and_bearing(df):
    df["l2_dist_km"] = haversine_dist(df["Pickup_Centroid_Latitude"],
                                       df["Pickup_Centroid_Longitude"],
                                       df["Dropoff_Centroid_Latitude"],
                                       df["Dropoff_Centroid_Longitude"])
    df["x_dist_km"],df["y_dist_km"] = manhattan_dist(df["Pickup_Centroid_Latitude"],
                                       df["Pickup_Centroid_Longitude"],
                                       df["Dropoff_Centroid_Latitude"],
                                       df["Dropoff_Centroid_Longitude"])
    df["bearing"] = bearing(df["Pickup_Centroid_Latitude"],
                               df["Pickup_Centroid_Longitude"],
                               df["Dropoff_Centroid_Latitude"],
                               df["Dropoff_Centroid_Longitude"])


def add_airport_col(df,thresh_km = 1):
    midway = (41.7868, -87.7522)
    ohare = (41.9742, -87.9073)
    airport_flag = haversine_dist(df["Pickup_Centroid_Latitude"],
                   df["Pickup_Centroid_Longitude"],
                   midway[0],
                   midway[1]) < thresh_km
    airport_flag |= haversine_dist(df["Pickup_Centroid_Latitude"],
                   df["Pickup_Centroid_Longitude"],
                   ohare[0],
                   ohare[1]) < thresh_km
    print(f"Airport trips pecentage: {airport_flag.mean()*100}")
    df["bAirport"] = airport_flag

def add_datetime_vars(df):
    df['day_of_wk'] = df.Trip_Start_Timestamp.dt.dayofweek.astype('category')
    df['hour'] = df.Trip_Start_Timestamp.dt.hour.astype('category')
    df.drop('Trip_Start_Timestamp', axis = 1, inplace = True)

def add_all_features(df):
    add_dist_and_bearing(df)
    add_airport_col(df,thresh_km = 1)
    add_datetime_vars(df)


def load_hdf(path, percent = 100):
    if percent == 100:
        return pd.read_hdf(path, 'df')
    else:
        store = pd.HDFStore(path)
        nrows = store.get_storer('df').nrows
        r = np.random.randint(0,nrows,size=int(nrows*percent/100))
        store.close()
        return pd.read_hdf(path, 'df',where=pd.Index(r))

type_map = {"Trip_Seconds": "uint16",
            "Pickup_Community_Area": "category",
            "Dropoff_Community_Area": "category"}

def preprocess_trip_data(df,max_fare = 100, max_miles = 100, max_time = int(1e4),bTaxi = True):
    df.columns = df.columns.str.replace(' ', '_') # for dot notation
    df.columns = df.columns.str.replace('Tips', 'Tip')
    df.dropna(inplace = True)
    # Drop trips with outlier distances or times
    df.drop(df[(df.Trip_Miles <=0)|(df.Trip_Miles >max_miles)].index, inplace=True)
    df.drop(df[(df.Trip_Seconds <=0)|(df.Trip_Seconds >max_time)].index, inplace=True)
    # Add velocity column to further screen data
    df['vel_mph'] = df['Trip_Miles']/(df['Trip_Seconds']/3600) #in mi/hr
    #drop insane velocities
    df.drop(df[df.vel_mph >= 60].index,inplace = True)
    # define a final fare, includes every fee other than tip
    df['Final_Fare'] = df['Trip_Total'] -df['Tip']
    # drop unusually large or small fares
    df.drop(df[((df.Final_Fare <= 0)|(df.Final_Fare > max_fare))].index,inplace = True)

    if bTaxi:
        df.drop(['Fare', 'Tip', 'Tolls', 'Extras','Trip_Total'],axis =1, inplace = True)
    else:
        df.drop(['Fare', 'Tip', 'Additional_Charges','Trip_Total'],axis =1, inplace = True)

