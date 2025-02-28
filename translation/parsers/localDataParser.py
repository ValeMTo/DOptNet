import pandas as pd

class ZenodoParserClass:
    def __init__(self, logger):
        self.logger = logger
        self.logger.info("Zenodo parser initialized")
    
    def get_powerplants_data(self):
        self.logger.debug("Getting powerplants data")

        data = pd.read_csv('../data/custom_powerplants_ssp126_2050.csv')

        filtered_data = data[data['DateIn'] <= 2020]
        filtered_data = filtered_data[filtered_data['DateOut'] >= 2030]
        filtered_data = filtered_data[filtered_data['Country'].isin(['ZM', 'ZW', 'MZ'])]
        
        grouped_data = filtered_data.groupby(['Fueltype', 'Technology', 'Country'])['Capacity'].sum().reset_index()
        grouped_data = grouped_data.rename(columns={'Fueltype': 'fueltype', 'Technology': 'technology', 'Country': 'country', 'Capacity': 'capacity'})

        return grouped_data
    

