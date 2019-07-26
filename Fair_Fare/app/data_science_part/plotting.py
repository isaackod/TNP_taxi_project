import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde
import altair as alt


def kde(data, nbins = 1000):
    data = data[~np.isnan(data)]
    lo, hi= np.min(data), np.max(data)
    gkde = gaussian_kde(data,bw_method = .5)
    grid = np.linspace(-10,150,nbins)
    kde_vals = gkde.evaluate(grid)
    lo, hi= np.min(data), np.max(data)
    return {'x':grid, 'y':kde_vals,'valid_range':(lo,hi)}


## todo build out a wide dataframe only in the valid_range
def build_hists_for_altair(fare_dict):
    df = pd.DataFrame()
    for name, fares in fare_dict.items():
        kde_dict = kde(fares.values)
        df[name] = kde_dict['y']
    df['x'] = kde_dict['x']
    long_df = df.melt(id_vars="x").rename(columns = {"variable":"parameter"})
    # filter to min/max of data
    return long_df[(long_df.x>kde_dict['valid_range'][0]) & (long_df.x<kde_dict['valid_range'][1])]


# TODO: May want to handle the hour differently (eg, pass in array of times)
def build_preds_for_altair(predictions):
    pred_df = pd.DataFrame(predictions)
    pred_df['hour'] = [i for i in range(len(pred_df))]
    return pred_df.melt(id_vars = "hour").rename(columns = {"variable":"parameter"})


def show_viz(results, fare_dict, predictions):
    """fare_dict needs to include pooled, rs, and taxi fare values. Predictions are from ML model"""

    long_df = build_hists_for_altair(fare_dict)
    pred_df = build_preds_for_altair(predictions)

    domain = list(fare_dict.keys())
    domain2 = list(predictions.keys())
    range_ = ['red', 'green', 'blue']
    #range2 = ['#a31818','#18a321','#184ea3']

    # A dropdown filter
    columns= domain
    column_dropdown = alt.binding_select(options=columns)
    column_select = alt.selection_single(
        fields=['parameter'],
        on='doubleclick',
        clear=False, 
        bind=column_dropdown,
        name="Ride Type",
        init={'parameter': "Rideshare_Dist"}
    )

    hist = alt.Chart(long_df).mark_area(point=False, size = 4).encode(
        alt.X('x',title='Ride Cost (Dollars)'),
        alt.Y('value',title='Density'),
        color=alt.Color('parameter', scale = alt.Scale(range = range_, domain = domain),legend=None)
    )


    filter_columns = hist.add_selection(
        column_select
    ).encode(
        opacity=alt.condition(column_select, alt.value(0.6), alt.value(0))
    )


    slider = alt.binding_range(min=0, max=9, step=1)
    select_hour = alt.selection_single(name=" ", fields=['hour'],
                                       bind=slider, init={'hour': 0})

    estimates = alt.Chart(pred_df).mark_rule(color='red').encode(
        x='value',
        size=alt.value(5),
        color = alt.Color('parameter',scale = alt.Scale(range = range_, domain = domain2))
    ).add_selection(select_hour).transform_filter(select_hour)



    layer = estimates +filter_columns
    layer.properties(
        height=300,
        width = 800,
        title='Ridesharing Averages and Estimates'
    ).configure_axis(
        labelFontSize=16,
        titleFontSize=16
    ).configure_title(
        fontSize=20,
        font='Courier',
    ).configure_legend(
        strokeColor='gray',
        fillColor='#EEEEEE',
        padding=10,
        cornerRadius=10,
        orient='top-right',
        symbolType = 'circle'
    )
    return layer