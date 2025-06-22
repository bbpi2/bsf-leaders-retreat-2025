"""
This script takes in two datasets:
* australian_postcodes.csv from https://www.matthewproctor.com/australian_postcodes#downloadlinks
* vic_suburbs.json from https://data.gov.au/data/dataset/vic-suburb-locality-boundaries-geoscape-administrative-boundaries

And has the following outputs:
1. `metro_vic_suburbs.csv`: csv of postcode, suburb, lat, long in metro VIC (filter by SA4s)
2. `metro_vic.geojson`: filtered version of the input shape file to show only metro VIC

"""
import pandas as pd
import numpy as np
import json

METRO_SA4 = ['Melbourne - Inner', 'Melbourne - Inner East',
       'Melbourne - Inner South', 'Melbourne - North East',
       'Melbourne - North West', 'Melbourne - Outer East',
       'Melbourne - South East', 'Melbourne - West']

def get_metro_suburbs():
    # This was downloaded from https://www.matthewproctor.com/australian_postcodes#downloadlinks
    suburbs_df = pd.read_csv("australian_postcodes.csv")
    metro_df = suburbs_df.query('state == "VIC" & type == "Delivery Area" & sa4name in @METRO_SA4')
    return metro_df[['postcode', 'locality', 'Long_precise', 'Lat_precise']]

def get_vic_polygon():
    # This was downloaded from https://data.gov.au/data/dataset/vic-suburb-locality-boundaries-geoscape-administrative-boundaries
    with open("vic_suburbs.json") as f:
        vic_poly = json.load(f)
    return vic_poly

def get_unique_suburbs(df):
    return list(np.unique(df['locality']))

def get_metro_polygon(poly, metro_suburbs):
    metro_features = []
    
    for row in poly['features']:
        suburb = row['properties']['vic_loca_2']
        if suburb in metro_suburbs:
            metro_features.append(row)

    poly.update({'features': metro_features})
    return poly

    
if __name__ == "__main__":
    metro_df = get_metro_suburbs()
    metro_suburbs = get_unique_suburbs(metro_df)
    vic_poly = get_vic_polygon()
    metro_poly = get_metro_polygon(vic_poly, metro_suburbs)

    metro_df.to_csv("../data/metro_vic_suburbs.csv")
    # Write to a file
    with open('../data/metro_vic.json', 'w') as f:
        json.dump(metro_poly, f)