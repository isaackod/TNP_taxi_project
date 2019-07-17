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