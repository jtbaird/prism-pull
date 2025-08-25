# prism-pull
prism-pull is a python package made to pull data from PRISM Group via web automation. Via the the [PRISM website](https://prism.nacse.org/):
```
The PRISM Group gathers weather observations from a wide range of monitoring networks, applies sophisticated quality control measures, and develops spatial datasets to reveal short- and long-term weather patterns. The resulting datasets incorporate a variety of modeling techniques and are available at multiple spatial/temporal resolutions, covering the period from 1895 to the present. 
```
The types of weather data consist of:
- precipitaion totals
- minimum temperatures
- mean temperatures
- maximum temperatures
- minimum vapor pressure deficit
- maximum vapor pressure deficit
- mean dewpoint temperature
- cloud transmittance
- horizontal surface solar radiation data
- sloped surface solar radiation data
- clear sky solar radiation data

These data are available across a variety of timescales for each cell of a 4km by 4km or 800m by 800m grid covering the entire continential United States. This makes it an especially great source for locations where weather stations may not be operating.
## Installation
Prerequisites:
- pip
- Google Chrome
- Python3.13
    - Working on finding lowest compatible python version at the moment.
Install with: `pip install prism-pull`
## Usage
Usage is simple, and will be familiar to anyone who has used the PRISM GUI in the past. The package consists of 
one class, and it's associated getter methods:
- PrismSession
    - get_30_year_monthly_normals
    - get_30_year_daily_normals
    - get_annual_values
    - get_single_month_values
    - get_monthly_values
    - get_daily_values
### PrismSession
Generate a new PrismSession:
```
import prism-pull as pp

session = pp.PrismSession()
```
Your PrismSession object can be initialized with two optional arguments:
- download_dir:
    - The directory where prism-pull will download the results of your PRISM queries.
    - default: your current working directory
- driver_wait:
    - The time (in seconds) prism-pull web driver will wait before moving onto the next step. Consider increasing if you have poor download speeds.
    - default: 5 seconds
Here's an example of setting up a session with these arguments:
```
import prism-pull as pp

session = pp.PrismSession(download_dir='absolute/path/to/download/to', driver_wait=10)
```
### get_30_year_monthly_normals
Returns the average monthly conditions over the previous three decades for the specified area or areas.
### get_30_year_daily_normals
Returns the average daily conditions over the previous three decades for the specified area or areas.
### get_annual_values
Returns data for selected measurements in the specified range of years.
### get_single_month_values
Returns data for selected measurements for a given month each year in the specified range of years.
### get_monthly_values
Returns monthly data for selected measurements for each month between the starting month and year, to ending month and year.
### get_daily_values
Returns daily data for selected measurements for each dat between the starting date, month, and year, to ending date, month, and year.
## Testing
## Contributing
## Contact