import numpy as np
from scipy.stats import gaussian_kde
import altair as alt


def kde(data, nbins = 500):
    data = data[~np.isnan(data)]
    gkde = gaussian_kde(data,bw_method = .5)
    grid = np.linspace(-10,150,nbins)
    kde_vals = gkde.evaluate(grid)
    lo, hi= np.min(data), np.max(data)
    loidx = np.argmin(abs(lo-grid))
    hiidx = np.argmin(abs(hi-grid))
    return {'x':grid, 'y':kde_vals,'valid_range':(loidx,hiidx)}


## todo build out a wide dataframe only in the valid_range
def build_df_for_altair(fare_dict):
    df = pd.DataFrame()
    for i, name, fares in enumerate(fare_dict.items()):
        kde_dict = kde(fares.values)
        df[name] = kde_dict['y']
    df['x'] = kde_dict['x']
    long_df = kde.melt(id_vars="x").rename(columns = {"variable":"parameter"})
    return long_df