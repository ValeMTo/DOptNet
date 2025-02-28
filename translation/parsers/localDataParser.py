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
    
    def get_annual_demand_data(self):
        self.logger.debug("Getting demand data")

        df = pd.read_csv('../data/demand_TEMBA_SSP1-2.6.csv')

        df = df.map(lambda x: round((x/(365*24*60*60))*10**6, 3)) # Convert from PJ/year to GW

        df['country'] = df.index.map(lambda x: x[:2])
        filtered_data = df[df['Country'].isin(['ZM', 'ZW', 'MZ'])]
        filtered_data = filtered_data[['2030', 'country']]
        filtered_data.reset_index(drop=True, inplace=True)
        filtered_data = filtered_data.rename(columns={'2030': 'annual_demand_2030_GW'})

        return filtered_data

    