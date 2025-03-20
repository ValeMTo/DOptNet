from translation.parsers.configParser import ConfigParserClass
from translation.parsers.osemosysDataParser import localDataParserClass
from translation.xmlGenerator import XMLGeneratorClass
from deprecated import deprecated
import pandas as pd
import logging
import os

class EnergyModelClass:
    def __init__(self):
        self.config_parser = ConfigParserClass(file_path='config.yaml')
        self.log_level, log_file = self.config_parser.get_log_info()
        self.logger = self.create_logger(self.log_level, log_file)
        self.config_parser.set_logger(self.logger)

        self.data_parser = localDataParserClass(logger = self.logger, file_path=self.config_parser.get_file_path())
        self.xml_generator = XMLGeneratorClass(logger = self.logger)

        self.name = self.config_parser.get_problem_name()
        self.countries = self.config_parser.get_countries()
        self.year = self.config_parser.get_year()

        self.logger.info("Energy model initialized")

    def create_logger(self, log_level, log_file):
        log_dir = os.path.dirname(log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        logging.basicConfig(
            filename=log_file,
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        return logging.getLogger(__name__)
    
    def filter_based_on_countries(self, data):
        if 'COUNTRY' not in data.columns: 
            raise ValueError("Data does not have a 'COUNTRY' column")
        return data.loc[data['COUNTRY'].isin(self.countries)]
    
    @deprecated(reason="Data directly connected in generate_xml function")
    def collect_data(self):
        self.logger.debug("Collecting data...")
        self.already = self.data_parser.get_already_installed_powerplants_data(self.countries)
        self.logger.debug("Powerplants data collected")

        self.demand_data = self.data_parser.get_annual_demand_data(self.year, self.countries)
        self.logger.debug("Annual demand data collected")

    def generate_xml(self):
        self.logger.debug("Generating XML...")
        
        self.xml_generator.add_presentation(name=self.name, maximize='true')
        self.xml_generator.add_agents(self.countries)

        domains = self.generate_domains()
        self.xml_generator.add_domains(domains)

        self.variables = self.xml_generator.add_variable_from_name(
            technologies=self.filter_based_on_countries(self.data_parser.extract_technologies_per_country())['TECHNOLOGY'].values, 
            agents=self.countries
        )

        residual_capacity_df = self.filter_based_on_countries(self.data_parser.extract_minimum_installed_capacity(year=self.year, unit='MW'))
        residual_capacity_df = residual_capacity_df[residual_capacity_df['MIN_INSTALLED_CAPACITY'] > 0]

        for index, row in residual_capacity_df.iterrows():
            self.xml_generator.add_minimum_capacity_constraint(
                variable_name=f"{row['COUNTRY']}{row['TECH']}_capacity", 
                min_capacity=round(row['MIN_INSTALLED_CAPACITY'])
            )
        
        capacity_factor_df = self.filter_based_on_countries(self.data_parser.extract_capacity_factors(year=self.year))
        availability_factor_df = self.filter_based_on_countries(self.data_parser.extract_availability_factors(year=self.year))
        conversion_factor_df = self.data_parser.extract_capacity_to_activity_unit()
        merged_factors_df = capacity_factor_df.merge(
            availability_factor_df, on=['COUNTRY', 'TECH'], how='outer'
        ).merge(
            conversion_factor_df, on=['COUNTRY', 'TECH'], how='outer'
        )

        #TODO: how should i treat the NaN values?
        for index, row in merged_factors_df.iterrows():
            factor = row['CAPACITY_FACTOR'] * row['AVAILABILITY_FACTOR'] * row['CAPACITY_TO_ACTIVITY_UNIT']
            if not pd.isna(factor):
                self.xml_generator.add_maximum_rate_of_activity_constraint(agent_technology = f"{row['COUNTRY']}{row['TECH']}", factor=factor)


        



        # for index, row in powerplants_data.iterrows():
        #     self.xml_generator.add_maximum_capacity_constraint(
        #         variable_name=f"{row['Technology']}{row['Country'].capitalize()}capacity",
        #         max_capacity=round(row['Max Installable Capacity (MW)'])
        #     )
        #     self.xml_generator.add_maximum_capacity_factor_constraint(
        #         variable_name=f"{row['Technology']}{row['Country'].capitalize()}capFactor",
        #         max_capacity_factor=row['Mean Capacity Factor']
        #     )
        #     self.xml_generator.add_operating_cost_minimization_constraint(
        #         weight=10**3,
        #         variable_capacity_name=f"{row['Technology']}{row['Country'].capitalize()}capacity",
        #         variable_capFactor_name=f"{row['Technology']}{row['Country'].capitalize()}capFactor",
        #         cost_per_MWh=round(row['Operating Cost ($/MWh)'] + row['Fuel Cost ($/MWh)'])
        #     )
        #     self.xml_generator.add_installing_cost_minimization_constraint(
        #         weight=10**3,
        #         variable_capacity_name=f"{row['Technology']}{row['Country'].capitalize()}capacity",
        #         previous_installed_capacity=int(row["already_installed_capacity"]),
        #         cost_per_MW=round(row['Installation Cost ($/MW)'])
        #     )
        #     continue

        # demand_data = self.data_parser.get_annual_demand_data(self.year, self.countries)
        # for country in self.countries:
        #     self.xml_generator.add_demand_constraint_per_agent(
        #         agent_name=country,
        #         min_demand=round(demand_data.loc[demand_data['country'] == country][f'annual_demand_{int(self.year)}_GW'].values[0] * 1000), #GW to MW
        #         technologies=powerplants_data['Technology'].unique(),
        #         neighbor_agents=self.countries #TODO: remove self and create a function to find only the neighbors
        #     )
        #     self.xml_generator.add_emission_cap_constraint_per_agent(
        #     agent_name=country, 
        #     technolgies_emission_costs=powerplants_data[['Technology', 'CO2 Emissions (tCO2/MWh yearly)']].drop_duplicates().set_index('Technology').to_dict()['CO2 Emissions (tCO2/MWh yearly)'], 
        #     max_emission=10**8
        # )
        #     continue

        # self.xml_generator.add_emission_cap_constraint(
        #     agents=self.countries, 
        #     technolgies_emission_costs=powerplants_data[['Technology', 'CO2 Emissions (tCO2/MWh yearly)']].drop_duplicates().set_index('Technology').to_dict()['CO2 Emissions (tCO2/MWh yearly)'], 
        #     max_emission=10**8
        # )

        self.xml_generator.print_xml(output_file=f'{self.name}_output.xml')
        self.logger.info("XML generated")
        
    def generate_domains(self):
        #TODO: Do not hard code this values
        self.logger.debug("Generating domains...")
        domains = {}
        domains["rate_activity_domain"] = range(0, 100000, 1000) #PJ/year
        domains["installable_capacity_domain"] = range(0, 250000, 100) #MW 
        domains["trasferable_capacity_domain"] = range(0, 3000, 500) #PJ/year
        return domains
    
