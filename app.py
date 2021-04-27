import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from Collection_Aggregation import FirePrecipDataCollection, CaliforniaYearlyCounty, FireAggregations, MapCreator, ChartCreator

app = dash.Dash(__name__)
server = app.server

'''
Declaring the paths and start year
If you change start year it globally changes the amount of data seen in the plots
'''
FIREPATH = 'Code/all_usa_fires_cleaned.csv'
PRECIP_PATH = './data/precip_agg_series.csv'
startYear = 1992

'''
Creating a data collector object and obtaining the filtered fires, years,
precipitation, and daily precipitation datasets
'''
DataCollector = FirePrecipDataCollection(startYear, FIREPATH, PRECIP_PATH)
fires, years = DataCollector.getFiresData()
daily = DataCollector.mergeFirePrecipDataDaily()

'''
Creating a county data collector object and obtaining the yearly data by county,
and the cali geojson objects by year
'''
CountyDataCollector = CaliforniaYearlyCounty(startYear, fires, years)
yearlyData = CountyDataCollector.getYearlyDataDict()
fireCountsByYear = CountyDataCollector.getFireCountsByYear()
cali = CountyDataCollector.getCaliGeoJson()
caliCounties = CountyDataCollector.getCountyNames(cali)


'''
Creating a fire aggregator object that will be used to aggregate information for the different charts
'''
FireAggregator = FireAggregations(yearlyData, caliCounties, daily)
allsize = FireAggregator.getAllFireSizes()
description = (
    "Between " + str(startYear) + " and 2015, there were an estimated 1.88 Million"
    " wildfires across the US. This map explores the correlations"
    " between various catalysts, weather conditions, and the resulting damages of these wildfires."
 )

app.layout = html.Div(
    id="root",
    children=[
        html.Div(
            id="header",
            children=[
                html.Img(id="logo", src=app.get_asset_url("uva-sds-white.png")),
                html.H4(children="Visualizing US Wildfires ("+str(startYear)+"-2015)"),
                html.P(
                    id="description",
                    children=description,
                    ),
                ],
            ),
        html.Div(
            id="app-container",
            children=[
                html.Div(
                    id="left-column",
                    children=[
                        html.Div(
                            id="slider-container",
                            children=[
                                html.P(
                                    id="slider-text",
                                    children="Drag the slider to change the year:",
                                ),
                                dcc.Slider(
                                    id='year-slider',
                                    min=years.min(),
                                    max=years.max(),
                                    value=years.min(),
                                    marks={str(year): str(year) for year in years},
                                    step=None
                                ),
                            ],
                        ),
                    html.Div(
                        id="map-container",
                        children=[
                            html.P(id="map-selector", children="Select map:"),
                            dcc.Dropdown(
                                options=[
                                    {
                                        "label": "Chloropleth map of total fire counts in " + str(startYear) + ", split by county",
                                        "value": "show_full_year_map",
                                    },
                                    {
                                        "label": "Fire counts by month animation",
                                        "value": "show_fires_month",
                                    },
                                ],
                                value="show_full_year_map",
                                id="map-dropdown",
                            ),
                            dcc.Graph(id='cali-wildfires',
                                figure=dict(
                                    data=[dict(x=0, y=0)],
                                    layout=dict(
                                        paper_bgcolor="#3f3332", #F4F4F8
                                        plot_bgcolor="#3f3332",
                                        autofill=True,
                                        margin=dict(t=0, r=0, b=0, l=0),
            
                                ),
                            ),),
                    ],
                ),
                ],
                ),
                
                html.Div(
                    id="graph-container",
                    children=[
                        html.P(id="chart-selector", children="Select chart:"),
                        dcc.Dropdown(
                            options=[
                                {
                                    "label": "Histogram of fire catalysts count (single year)",
                                    "value": "show_fire_catalysts_single_year",
                                },
                                {
                                    "label": "Most destructive fires (single year)",
                                    "value": "show_largest_fires_table_single_year",
                                },
                                {
                                    "label": "Histogram of fire catalysts average (single year)",
                                    "value": "show_fire_catalysts_avg_single_year",
                                },
                                {
                                    "label": "Fire size over time (single year, Class A-C)",
                                    "value": "show_fire_over_time_single_year_C",
                                },
                                {
                                    "label": "Fire size over time (single year, Class D-G)",
                                    "value": "show_fire_over_time_single_year_D",
                                },
                                {
                                    "label": "Fire Size and Precipitation",
                                    "value": "show_firesize_v_precip",
                                },

                                {
                                    "label": "Average Fire Size (Weekly)",
                                    "value": "show_avg_firesize_counts_w",
                                },

                            ],
                            value="show_fire_catalysts_single_year",
                            id="chart-dropdown",
                        ),
                        dcc.Graph(
                            id="selected-data",
                            figure=dict(
                                data=[dict(x=0, y=0)],
                                layout=dict(
                                    paper_bgcolor="#3f3332", #F4F4F8
                                    plot_bgcolor="#3f3332",
                                    autofill=True,
                                    margin=dict(t=0, r=0, b=0, l=0),
            
                                ),
                            ),
                            ),
                        ],
                    ),
                ],
            ),
        ],
)



@app.callback(
    Output('cali-wildfires', 'figure'),
    [
    Input('year-slider', 'value'),
    Input('map-dropdown', 'value')
     ],
)
def update_figure(selected_year, map_dropdown):
    MapVisualizer = MapCreator(yearlyData, caliCounties, daily, selected_year, map_dropdown)
    if map_dropdown == "show_full_year_map":
        #filtered_fires_by_fips = FireAggregator.getFireCountsByYear(selected_year)
        filtered_fires_by_fips = fireCountsByYear.get(selected_year)
        fig = MapVisualizer.MakeWildfireMap(cali, filtered_fires_by_fips)
    elif map_dropdown == "show_fires_month":
        months = FireAggregator.getMonthlyCounts(selected_year)
        fig = MapVisualizer.MakeMonthlyMap(cali, months)
    return fig

@app.callback(
    Output("selected-data", "figure"),
    [
        Input('year-slider', 'value'),
        Input("chart-dropdown", "value"),
    ],
)
def update_chart(selected_year, chart_dropdown):
    ChartVisualizer = ChartCreator(yearlyData, caliCounties, daily, allsize, selected_year, chart_dropdown)
    fig = ChartVisualizer.DetermineWhichPlot()
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
