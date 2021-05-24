# covid_vacc_demographics

## Intro
The COVID pandemic has been an event unlike anything faced in recent history. For a year much of the world came to a crawl as people theorized when we might be able to return to "normal". Finally as vaccines became available it seemed like that might actually be a reality. However, a new, somewhat unforeseen, challenge soon emerged: getting the necessary amount of people to get fully vaccinated to reach herd immunity. So why, and where, are we having so much trouble getting the vaccine rolled out in the United States? Who is hesitent to get vaccinated? In this project we will look at the demographics of counties all across the country along with vaccine hesitency and political voting data to try and answer these questions.

This repository contains code cleaning and aggregating vaccination and demographic data from the CDC, vaccination data from Texas Health and Human Services, population data from the US Census, and 2016 election voting data from the MIT Election Lab. We will also look for correlations between vaccination rate and these variables as well as map them looking for trends geographically.

The packages used in this analysis are listed in the requirements file in this repository and are: pandas, numpy, matplotlib, seaborn, geopandas, swifter, and shapely.


## Data Sources
CDC 'Vaccine Hesitancy for COVID-19: County and local estimates' dataset found [here](https://data.cdc.gov/Vaccinations/Vaccine-Hesitancy-for-COVID-19-County-and-local-es/q9mh-h2tw)
US Census county population data found [here](https://www.census.gov/data/datasets/time-series/demo/popest/2010s-counties-total.html)
2010-2016 Presidential Election voting records from the MIT Election Lab found [here](https://electionlab.mit.edu/data)
Texas county vaccination data from the Texas Health and Human Services found [here](https://www.dshs.texas.gov/coronavirus/immunize/vaccine.aspx). 

All of these datasets are also availabilty in this repository, accurate as of May 23, 2021.
