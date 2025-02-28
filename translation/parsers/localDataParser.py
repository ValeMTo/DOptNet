import pandas as pd

class localDataParserClass:
    def __init__(self, logger):
        self.logger = logger
        self.logger.info("Local Data parser initialized")
    
    def get_powerplants_data(self):
        self.logger.debug("Getting powerplants data")

        data = pd.read_csv('../data/custom_powerplants_ssp126_2050.csv')

        filtered_data = data[data['DateIn'] <= 2020]
        filtered_data = filtered_data[filtered_data['DateOut'] >= 2030]
        filtered_data = filtered_data[filtered_data['Country'].isin(['ZM', 'ZW', 'MZ'])]
        
        grouped_data = filtered_data.groupby(['Fueltype', 'Technology', 'Country'])['Capacity'].sum().reset_index()
        grouped_data = grouped_data.rename(columns={'Fueltype': 'fueltype', 'Technology': 'technology', 'Country': 'country', 'Capacity': 'capacity'})

        return grouped_data
    
    def get_annual_demand_data(self, year, countries):
        self.logger.debug("Getting demand data")

        if not isinstance(year, str) or len(year) != 4 or not year.isdigit():
            raise ValueError("Year must be a string of 4 digits")

        if not isinstance(countries, list) or not all(isinstance(country, str) and len(country) == 2 for country in countries):
            raise ValueError("Countries must be a list of strings with exactly 2 characters each")

        df = pd.read_csv('../data/demand_TEMBA_SSP1-2.6.csv')

        df = df.map(lambda x: round((x/(365*24*60*60))*10**6, 3)) # Convert from PJ/year to GW

        df['country'] = df.index.map(lambda x: x[:2])
        filtered_data = df[df['Country'].isin(countries)]
        filtered_data = filtered_data[[str(year), 'country']]
        filtered_data.reset_index(drop=True, inplace=True)
        filtered_data = filtered_data.rename(columns={str(year): 'annual_demand_{year}_GW'})

        return filtered_data

    