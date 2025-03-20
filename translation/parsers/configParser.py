import yaml
import pandas as pd
from deprecated import deprecated

class ConfigParserClass:
    def __init__(self, file_path='config.yaml'):

        try:
            with open(file_path, 'r') as file:
                self.config = yaml.safe_load(file)
                self.config = self.config['config']
        except FileNotFoundError:
            raise FileNotFoundError(f"File {file_path} not found")
        
    def get_file_path(self):
        return self.config['outline']['data_file_path']
    
        
    def get_problem_name(self):
        return self.config['name']
    
    def get_log_info(self):
        return self.config['logging']['level'], self.config['logging']['file']
    
    def set_logger(self, logger):
        self.logger = logger
        self.logger.info("Logger set in config parser")

    def get_countries(self):
        return self.config['outline']['countries']
    
    def get_year(self):
        return self.config['outline']['year']
    
    @deprecated(reason="Data extracted by dataParser class")
    def get_powerplants_data(self):
        powerplants = []
        for plant, details in self.powerplants_config.items():
            for country, capacity in details["max_installable_capacity_MW"].items():
                powerplants.append({
                    "Technology": plant,
                    "Installation Cost ($/MW)": details["installation_cost_per_MW"],
                    "Operating Cost ($/MWh)": details["operating_cost_per_MWh"],
                    "Fuel Cost ($/MWh)": details["fuel_cost_per_MWh"],
                    "CO2 Emissions (tCO2/MWh yearly)": round(details["emissions"]["CO2"] * 87.60),
                    "N2O Emissions (tN2O/MWh yearly)": round(details["emissions"]["N2O"] * 87.60),
                    "CH4 Emissions (tCH4/MWh yearly)": round(details["emissions"]["CH4"] * 87.60),
                    "CFC Emissions (tCFC/MWh yearly)": round(details["emissions"]["CFCs"] * 87.60),
                    "Mean Capacity Factor": details["capacity_factor"]["mean"],
                    "Country": country,
                    "Max Installable Capacity (MW)": capacity
                })

        df = pd.DataFrame(powerplants)
        return df
    

