# Setting up Packages
import json
import country_converter as coco
from datetime import datetime, timedelta
import requests
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
# Getting the data
PAYLOAD = {'code': 'ALL'}
URL = 'https://api.statworx.com/covid'
RESPONSE = requests.post(url=URL, data=json.dumps(PAYLOAD))
# Convert the response to a data frame
covid_df = pd.DataFrame.from_dict(json.loads(RESPONSE.text))
covid_df.head(3)

# Setting the path to the shapefile
SHAPEFILE = 'data/shapefiles/worldmap/ne_10m_admin_0_countries.shp'
# Read shapefile using Geopandas
geo_df = gpd.read_file(SHAPEFILE)[['ADMIN', 'ADM0_A3', 'geometry']]
# Rename columns.
geo_df.columns = ['country', 'country_code', 'geometry']
geo_df.head(3)

# Drop row for 'Antarctica'. It takes a lot of space in the map and is not of much use
geo_df = geo_df.drop(geo_df.loc[geo_df['country'] == 'Antarctica'].index)
# Print the map
geo_df.plot(figsize=(20, 20), edgecolor='white', linewidth=1, color='lightblue')

# Next, we need to ensure that our data matches with the country codes. 
iso3_codes = geo_df['country'].to_list()
# Convert to iso3_codes
iso2_codes_list = coco.convert(names=iso3_codes, to='ISO2', not_found='NULL')
# Add the list with iso2 codes to the dataframe
geo_df['iso2_code'] = iso2_codes_list
# There are some countries for which the converter could not find a country code. 
# We will drop these countries.
geo_df = geo_df.drop(geo_df.loc[geo_df['iso2_code'] == 'NULL'].index)

# We want to drop the history and only get the data from the last day
d = datetime.today()-timedelta(days=1)
date_yesterday = d.strftime("%Y-%m-%d")
# Preparing the data
covid_df = covid_df[covid_df['date'] == date_yesterday]
# Merge the two dataframes
merged_df = pd.merge(left=geo_df, right=covid_df, how='left', left_on='iso2_code', right_on='code')
# Delete some columns that we won't use
df = merged_df.drop(['day', 'month', 'year', 'country_y', 'code'], axis=1)
#Create the indicator values
df['case_growth_rate'] = round(df['cases']/df['cases_cum'], 2)
df['case_growth_rate'].fillna(0, inplace=True) 
df.head(3)

# Print the map
# Set the range for the choropleth
title = 'Daily COVID-19 Growth Rates'
col = 'case_growth_rate'
source = 'Source: relataly.com \nGrowth Rate = New cases / All previous cases'
vmin = df[col].min()
vmax = df[col].max()
cmap = 'viridis'
# Create figure and axes for Matplotlib
fig, ax = plt.subplots(1, figsize=(20, 8))
# Remove the axis
ax.axis('off')
df.plot(column=col, ax=ax, edgecolor='0.8', linewidth=1, cmap=cmap)
# Add a title
ax.set_title(title, fontdict={'fontsize': '25', 'fontweight': '3'})
# Create an annotation for the data source
ax.annotate(source, xy=(0.1, .08), xycoords='figure fraction', horizontalalignment='left', 
            verticalalignment='bottom', fontsize=10)
            
# Create colorbar as a legend
sm = plt.cm.ScalarMappable(norm=plt.Normalize(vmin=vmin, vmax=vmax), cmap=cmap)
# Empty array for the data range
sm._A = []
# Add the colorbar to the figure
cbaxes = fig.add_axes([0.15, 0.25, 0.01, 0.4])
cbar = fig.colorbar(sm, cax=cbaxes)