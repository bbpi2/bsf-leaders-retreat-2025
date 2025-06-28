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
import time
import requests
from dotenv import load_dotenv

from dotenv import load_dotenv
import os

load_dotenv()

DEST_LAT = -38.45956579986424
DEST_LON = 145.2472955709111
ORS_API_KEY = os.getenv("ORS_API_KEY")

if ORS_API_KEY:
    print(f"The secret value is FOUND")
else:
    print("Secret key not found.")

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

def ors_get_route(lat, lon):
    headers = {
        'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
    }
    call = requests.get(f'https://api.openrouteservice.org/v2/directions/driving-car?api_key={ORS_API_KEY}&start={lon},{lat}&end={DEST_LON},{DEST_LAT}', headers=headers)

    try:
        outputs = call.json()['features'][0]['properties']['summary']
        distance = outputs['distance']
        duration = outputs['duration']
    except:
        distance = "Unknown"
        duration = "Unknown"

    return distance, duration

def calculate_road_dist(df):
    # df = df[:10]
    # Purposely did NOT vectorise since API requires sleep
    df['distance'] = ""
    df['duration'] = ""
    for index, row in df.iterrows():
        lat = row['Lat_precise']
        lon = row['Long_precise']
        distance, duration = ors_get_route(lat, lon)
        df.loc[index, 'distance'] = distance
        df.loc[index, 'duration'] = duration
        time.sleep(2)
    
    return df
    
if __name__ == "__main__":
    metro_df = get_metro_suburbs()
    metro_suburbs = get_unique_suburbs(metro_df)
    metro_df_dist = calculate_road_dist(metro_df)
    vic_poly = get_vic_polygon()
    metro_poly = get_metro_polygon(vic_poly, metro_suburbs)

    metro_df_dist.to_csv("../data/metro_vic_suburbs.csv")
    # Write to a file
    with open('../data/metro_vic.json', 'w') as f:
        json.dump(metro_poly, f)