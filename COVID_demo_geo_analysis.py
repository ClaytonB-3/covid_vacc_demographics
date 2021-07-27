import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.style as style
import seaborn as sns
import geopandas as gpd
import swifter
from shapely import wkt
style.use(style='fivethirtyeight')

#Read in CDC dataset as dataframe
df_cdc = pd.read_csv('Vaccine_Hesitancy_for_COVID-19__County_and_local_estimates_523.csv')
df_cdc.head()

#Update county name column name
column_mapper_1 = {'County Name':'County_Name'}
df_cdc.rename(columns=column_mapper_1, inplace=True)

#Inspect data for nulls
df_cdc.info()

#Describe and inspect as we start the outlier removal process
df_cdc.describe()

#Use boxplots to look for outliers
fig, ax = plt.subplots(1, figsize=(24,12))
df_cdc.boxplot(['Percent adults fully vaccinated against COVID-19','Estimated hesitant or unsure','Estimated hesitant','Estimated strongly hesitant'])
plt.grid(b=False, which='both', axis='x')
plt.xticks(fontsize=18)
plt.yticks(fontsize=18)
plt.show()

#View outlier
df_cdc[df_cdc['Percent adults fully vaccinated against COVID-19']>0.8]

#remove outlier
df_cdc_2 = df_cdc[df_cdc['FIPS Code']!=13053]

#View SVI null value
df_cdc_2[df_cdc_2['Social Vulnerability Index (SVI)'].isnull()]

#Update null value based on internet search
df_cdc_2.loc[df_cdc_2.County_Name == 'Rio Arriba County, New Mexico', 'Social Vulnerability Index (SVI)'] = .89
df_cdc_2.loc[df_cdc_2.County_Name == 'Rio Arriba County, New Mexico', 'SVI Category'] = 'Very High Vulnerability'

#View County Boundary null
df_cdc_2[df_cdc_2['County Boundary'].isnull()]

#View State Boundary null
df_cdc_2[df_cdc_2['State Boundary'].isnull()]

#Remove the one null county boundary row
clean_geo_county = df_cdc_2[df_cdc_2['County Boundary'].notnull()]
clean_geo_county.info()

#Convert County geomteries into a geometry GeoSeries in geopandas.
clean_geo_county['geometry'] = clean_geo_county['County Boundary'].swifter.apply(lambda x: wkt.loads(x))
clean_geo_county['geometry'].iloc[0]

'''We'll finish converting the dataframe into a GeoDataFrame with geopandas and will remove the
two now unnecessary State and County Boundary columns.'''

#Convert entire DataFrame into a GeoDataFrame with the counties as the geometries
county_geoframe = gpd.GeoDataFrame(clean_geo_county, crs='epsg:4326', geometry='geometry')
county_geoframe.drop(['County Boundary','State Boundary'], axis=1, inplace=True)
county_geoframe.info()

#Visualize vaccination data on a map to look for geographic areas with missing data
fig, ax = plt.subplots(1, figsize=(24,12))
ax = county_geoframe.plot(axes=ax, column='Percent adults fully vaccinated against COVID-19')
plt.grid(b=False, which='both')
plt.title("Counties with Vaccination Data", fontsize=24, fontweight=750)
ax.axes.get_xaxis().set_ticks([])
ax.axes.get_yaxis().set_ticks([])
plt.xlim([-200,-50])
plt.show()

#Count the number of times each state appears in the dataframe. This is the number of counties in the state
df_cdc['State Code'].value_counts(dropna=False)

'''Create dataframe of counties with missing vaccination data. Count the number of missing counties per state.'''

null_vacc = df_cdc[df_cdc['Percent adults fully vaccinated against COVID-19'].isnull()]
null_vacc['State Code'].value_counts()

#Removing Hawaii data because vaccination data is not included
county_geoframe = county_geoframe[~county_geoframe['State'].isin(['HAWAII'])]

'''Texas makes their data available through their state gov website, so we will read it in, clean it, and incorporate it.'''
df_texas = pd.read_csv('Texas COVID-19 Vaccine Data by County - By County.csv')
print(len(df_texas.index))
df_texas.head()

df_texas.info()

#Look at the null row
df_texas[df_texas['Population, Phase 1A Healthcare Workers'].isnull()]

#Remove 'Other' row
df_texas = df_texas[~(df_texas['County Name']=='Other')]

#Format county names to match COVID Data
df_texas['County Name'] = df_texas['County Name'] + ' County, Texas'
#Convert vaccinated number and population 16+ to integer
df_texas['People Fully Vaccinated'] = df_texas['People Fully Vaccinated'].str.replace(',','').astype(int)
df_texas['Population, 16+'] = df_texas['Population, 16+'].str.replace(',','').astype(int)
#Create column for percent of adults (16+) fully vaccinated
df_texas['TX adults fully vaccinated against COVID-19'] = df_texas['People Fully Vaccinated'] / df_texas['Population, 16+']
#Change County Name column to match name in COVID data
df_texas = df_texas.rename(mapper={'County Name':'County_Name'}, axis=1)
#Make final dataframe with the two relevent columns, county_name and percent full vaccinated adults
final_df_texas = df_texas[['County_Name','TX adults fully vaccinated against COVID-19']]
final_df_texas.head()

#Merge Texas data with our GeoDataFrame
county_geoframe = county_geoframe.merge(right=final_df_texas, how='left', on = ['County_Name'])
county_geoframe.info()

#Fill nulls in the fully vaccinated column with values in the Texas vaccinated column (if applicable)
county_geoframe['Percent adults fully vaccinated against COVID-19'].fillna(county_geoframe['TX adults fully vaccinated against COVID-19'], inplace=True)
county_geoframe.info()

#Drop column with just TX data and confirm there are no null vaccination data points in Texas in the full vacc column
county_geoframe.drop(labels='TX adults fully vaccinated against COVID-19', axis=1, inplace=True)
vacc_missing = county_geoframe[county_geoframe['Percent adults fully vaccinated against COVID-19'].isnull()]
vacc_missing['State Code'].value_counts()

'''We are now incorporating population data from the census for each county. We start by reading in the data.'''
df_county_pops = pd.read_csv('census_county_pop_ann.csv')
df_county_pops.head()

'''Population Data - Data Cleaning'''

'''Changing the county name column so it matches our other dataset and changing the 2019 pop for clarity.
Dropping the United States row as it is unnecessary.'''
column_mapper_2 = {'Unnamed: 0':'County_Name', '2019':'2019_pop'}
df_county_pops.rename(columns=column_mapper_2, inplace=True)
df_county_pops.drop(df_county_pops[df_county_pops.County_Name=='United States'].index, inplace=True)
df_county_pops.head()

#Creating a new dataframe with only the relevant columns: County Name and 2019 Population.
df_county_pop_2019 = df_county_pops[['County_Name','2019_pop']].copy()
df_county_pop_2019.head()

#Stripping the period that was included before each county name.
df_county_pop_2019['County_Name'] = df_county_pops['County_Name'].str[1:]
df_county_pop_2019.head()

#Convert population to an integer by removing the commas and converting to integer
df_county_pop_2019['2019_pop'] = df_county_pop_2019['2019_pop'].str.replace(',','').astype(int)

#Confirming we have the same number of rows in the population dataframe as the COVID info dataframe
df_county_pop_2019.info()

#Create the combined dataframe by merging the population df with the COVID info GeoDataFrame.
final_df = county_geoframe.merge(right=df_county_pop_2019, how='left', on =['County_Name'])
final_df.info()

'''We see that there is one null county population,
so we'll take a look at them to see if we can fill them in manually.'''
final_df[final_df['2019_pop'].isnull()]

#Search the population dataframe for the missing counties
df_county_pops[df_county_pops['County_Name'].str.contains('Bottineau')]

#Updating null values and confirming there are no additional nulls
final_df.loc[final_df.County_Name == 'Bottineau County, North Dakota', '2019_pop'] = 6282
final_df.info()


'''Displaying number of counties per state with missing vaccination data (that we have not already removed)
for reference'''
county_geoframe['State'][county_geoframe[['Percent adults fully vaccinated against COVID-19','State Code']]['Percent adults fully vaccinated against COVID-19'].isnull()].value_counts()

#Calcualte the total population in each state in the counties that are missing vaccination data
va_counties = final_df[final_df['State']=='VIRGINIA']
va_pop = va_counties['2019_pop'].sum()
ca_counties = final_df[final_df['State']=='CALIFORNIA']
ca_pop = ca_counties['2019_pop'].sum()
ak_counties = final_df[final_df['State']=='ALASKA']
ak_pop = ak_counties['2019_pop'].sum()
print('Virginia Pop:',va_pop)
print('California Pop:',ca_pop)
print('Alaska Pop:',ak_pop)

#Counties from each state with missing vaccination data
va_missing_vacc_counties = va_counties[va_counties['Percent adults fully vaccinated against COVID-19'].isnull()]
ca_missing_vacc_counties = ca_counties[ca_counties['Percent adults fully vaccinated against COVID-19'].isnull()]
ak_missing_vacc_counties = ak_counties[ak_counties['Percent adults fully vaccinated against COVID-19'].isnull()]
#Population in those counties from each state (missing vaccination data)
va_missing_pop = va_missing_vacc_counties['2019_pop'].sum()
ca_missing_pop = ca_missing_vacc_counties['2019_pop'].sum()
ak_missing_pop = ak_missing_vacc_counties['2019_pop'].sum()
#Percent of each states population that is missing vaccination data
percent_va_missing = round(100*(va_missing_pop/va_pop),2)
percent_ca_missing = round(100*(ca_missing_pop/ca_pop),2)
percent_ak_missing = round(100*(ak_missing_pop/ak_pop),2)
print('Percent of Virgina Population Missing Vaccine Data:',percent_va_missing)
print('Percent of California Population Missing Vaccine Data:',percent_ca_missing)
print('Percent of Alaska Population Missing Vaccine Data:',percent_ak_missing)


'''We are now adding in 2016 voting data as a proxy for county political leaning.
We start by reading in the data as a data frame.'''
df_politics = pd.read_csv('countypres_2000-2016.csv')
df_politics.head()

#Create a dataframe with just 2016 voting data
df_politics_2016 = df_politics[df_politics['year']==2016]
df_politics_2016.info()


'''We've trimmed the dataframe down to just the year 2016 as we want the most recent information.
We'll also need to create a number to represent their political leanings. We'll be planning on matching
using the FIPS column, so first we'll look at the null values in that column. We'll then look at the nulls
in the party and candidatevotes columns.'''

#Check null FIPS counties
null_fips = df_politics_2016[df_politics_2016['FIPS'].isnull()]
null_fips.head(10)

#Check values in the party column
df_politics_2016['party'].value_counts()

#Investigate what is going on with party column null values. We see they are write in candidate and can be dropped.
party_nulls = df_politics_2016[df_politics_2016['party'].isnull()]
party_nulls.head()

#View 6 null candidatevotes rows
null_votes = df_politics_2016[df_politics_2016['candidatevotes'].isnull()]
null_votes.head(10)


'''Handling Voting Data Null Values'''
#Dropping all rows with nulls in either the FIPS, party, or candidatevotes column.
df_politics_2016 = df_politics_2016.dropna(axis=0, subset=['FIPS', 'party', 'candidatevotes'])
df_politics_2016.info()

# Converting the FIPS column to an integer before we can match it to our other dataset's FIPS column.
df_politics_2016['FIPS'] = df_politics_2016['FIPS'].astype(int)
df_politics_2016.head(10)

'''Measureing political leaning of counties. Group the 2016 Democratic and Republican
votes on the FIPS Code and sum the group leaving us with a dataframe with a column for
the total votes for the two parties in each county (among others) with the FIPS code as the index.'''
grouper_fips = df_politics_2016.groupby('FIPS').sum('candidatevotes')
grouper_fips

'''Save just the candidatevotes column as a series and rename to more accurately reflect that
it contains the combined votes for the two main parties. Convert to a dataframe, with the index
as a column, so we will have a column with the FIPS code for the county and the total votes cast
for the two major policatal parties.'''
all_major_party_votes = grouper_fips['candidatevotes']
all_major_party_votes.rename('combined_votes', inplace=True)
major_votes_df = all_major_party_votes.to_frame()
major_votes_df = major_votes_df.reset_index()
major_votes_df.head()

#Merge dataframe back to full voting data frame and confirm there are no nulls in combined votes
full_df_politics_2016 = df_politics_2016.merge(right=major_votes_df, how='left', on=['FIPS'])
full_df_politics_2016.info()
full_df_politics_2016.head()

'''Each row represents votes for a politacal party, so this will create a column with the proportion of
votes cast for the two main parties cast for the party represented by each row.'''
full_df_politics_2016['proportion_party_votes'] = (full_df_politics_2016['candidatevotes']/
                                                   full_df_politics_2016['combined_votes'])

'''Create a final dataframe with just the rows with the Republican votes. We will merge this with our
full GeoDataFrame of COVID data. Therefore the voting proportion we will be working with moving
forward will represent the proportion of votes cast for either the Dem or Rep candidate in that
county that was cast for the Rep candidate. We will also trim our merge dataframe down to just our
two relevant columns and rename them in prepartion for merging.
We also check the length to confirm we have around the right number of counties.'''

final_df_politics_2016 = full_df_politics_2016[full_df_politics_2016['party']=='republican']
final_df_politics_2016 = final_df_politics_2016[['FIPS','proportion_party_votes']]
final_df_politics_2016 = final_df_politics_2016.rename(mapper={'FIPS':'FIPS Code', 'proportion_party_votes':'prop_repub_votes'}, axis=1)
len(final_df_politics_2016.index)

#Merge dataframes
final_df = final_df.merge(right=final_df_politics_2016, how='left', on=['FIPS Code'])
final_df.head()
final_df.info()

#Counties in which states that are missing voting data
missing_votes = final_df[final_df['prop_repub_votes'].isnull()]
missing_votes['State'].value_counts()


'''Data Analysis'''

vacc_pop_corr = final_df[['Estimated hesitant or unsure','Estimated hesitant','Estimated strongly hesitant','Social Vulnerability Index (SVI)','Percent Hispanic','Percent non-Hispanic American Indian/Alaska Native','Percent non-Hispanic Asian','Percent non-Hispanic Black','Percent non-Hispanic Native Hawaiian/Pacific Islander','Percent non-Hispanic White','2019_pop','prop_repub_votes','Percent adults fully vaccinated against COVID-19']].corr()

#Plot the correlations
fig, ax = plt.subplots(figsize=(8,6))
att_heatmap = sns.heatmap(vacc_pop_corr)
plt.title("Vaccination Correlations", fontsize=24, fontweight=750, pad=15)
plt.yticks(rotation = 45, fontsize = 14)
plt.xticks(fontsize = 14)
plt.show()

vacc_pop_corr

#Maps of these variables around the country
#Map of fully vaccinated percentage by county
fig, ax = plt.subplots(1, figsize=(16,8))
ax = final_df.plot(axes=ax, column='Percent adults fully vaccinated against COVID-19', legend = True)
plt.grid(b=False, which='both')
plt.xlim([-200,-50])
ax.axes.get_xaxis().set_ticks([])
ax.axes.get_yaxis().set_ticks([])
plt.title("Percent Adults Fully Vaccinated by County", fontsize=24, fontweight=750)
plt.show()

#Map of policatal leaning by county
fig, ax = plt.subplots(1, figsize=(16,8))
ax = final_df.plot(axes=ax, column='prop_repub_votes', legend = True)
plt.grid(b=False, which='both')
plt.xlim([-200,-50])
ax.axes.get_xaxis().set_ticks([])
ax.axes.get_yaxis().set_ticks([])
plt.title("Proportion of Votes Cast Republican(2016) by County", fontsize=24, fontweight=750)
plt.show()

#Map of Social Vulnerability Index by county
fig, ax = plt.subplots(1, figsize=(16,8))
ax = final_df.plot(axes=ax, column='Social Vulnerability Index (SVI)', legend = True)
plt.grid(b=False, which='both')
plt.xlim([-200,-50])
ax.axes.get_xaxis().set_ticks([])
ax.axes.get_yaxis().set_ticks([])
plt.title("Social Vulnerability Index by County", fontsize=24, fontweight=750)
plt.show()

#Map of vaccine hesitency by county
fig, ax = plt.subplots(1, figsize=(16,8))
ax = final_df.plot(axes=ax, column='Estimated hesitant or unsure', legend = True)
plt.grid(b=False, which='both')
plt.xlim([-200,-50])
ax.axes.get_xaxis().set_ticks([])
ax.axes.get_yaxis().set_ticks([])
plt.title("Residents Hesitent or Unsure about Vaccination by County", fontsize=24, fontweight=750)
plt.show()


#Top 500 counties by vacc rate
top_500_vacc = final_df.sort_values('Percent adults fully vaccinated against COVID-19', ascending=False).head(500)
fig, ax = plt.subplots(1, figsize=(16,8))
ax = top_500_vacc.plot(axes=ax, column='Percent adults fully vaccinated against COVID-19', legend = True)
plt.grid(b=False, which='both')
plt.xlim([-200,-50])
ax.axes.get_xaxis().set_ticks([])
ax.axes.get_yaxis().set_ticks([])
plt.title("Top 500 Counties by Vaccination Rate", fontsize=24, fontweight=750)

plt.show()
