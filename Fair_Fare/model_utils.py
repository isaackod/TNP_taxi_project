import xgboost as xgb
import pandas as pd

def get_model_from_file(fname):
    bst = xgb.Booster()
    bst.load_model(fname)
    # restore feature names
    if bst.attr('feature_names') is not None: bst.feature_names = bst.attr('feature_names').split('|')
    return bst

def predict_fare(Ride, model):
    pred = pd.Series(Ride.as_row)
    feature_names = list(pred.keys())
    vals = pred.values.reshape(1,-1)
    dm = xgb.DMatrix(vals,feature_names=feature_names)
    return model.predict(dm)


# this is a bad way to do this as we would want to also update the time/distance from google
def predict_fare_future_times(Ride, model):
    single_row = ride.as_row
    # extend 24 hours into the future
    single_row['hour'] = [(single_row['hour'] + i)%24 for i in range(24)]
    pred = pd.DataFrame(single_row)
    feature_names = list(pred.keys())
    #vals = pred.values.reshape(1,-1)
    dm = xgb.DMatrix(pred,feature_names=feature_names)
    return model.predict(dm)