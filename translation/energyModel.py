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
    
    def filter_data(self, data, only_powerplants=True):
        if 'COUNTRY' not in data.columns: 
            raise ValueError("Data does not have a 'COUNTRY' column")
        data = data.loc[data['COUNTRY'].isin(self.countries)]

        if only_powerplants:
            if 'TECH' in data.columns:
                data = data.loc[data['TECH'].isin(self.power_tech)]
            
            if 'TECHNOLOGY' in data.columns:
                data = data.loc[data['TECHNOLOGY'].map(lambda x: str(x)[2:]).isin(self.power_tech)]
        return data
        
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

        power_technologies = pd.read_csv('data/input_data/power_tech.csv')
        self.power_tech = power_technologies['power_tech'].unique()

        input_data=self.filter_data(self.data_parser.extract_technologies_per_country())
        selected_technologies = input_data['TECHNOLOGY'].unique()
        timeslice_technologies_modes = input_data['VARIABLE'].values
        modes = input_data['MODE_OF_OPERATION'].unique()
        self.variables = self.xml_generator.add_variable_from_name(
            variables = timeslice_technologies_modes,
            technologies=selected_technologies, 
            agents=self.countries
        )

        # residual_capacity_df = self.filter_data(self.data_parser.extract_minimum_installed_capacity(year=self.year, unit='MW'))
        # residual_capacity_df = residual_capacity_df[(residual_capacity_df['MIN_INSTALLED_CAPACITY'] > 0) & (residual_capacity_df['TECHNOLOGY'].isin(selected_technologies))]
        # for index, row in residual_capacity_df.iterrows():
        #     self.xml_generator.add_minimum_capacity_constraint(
        #         variable_name=f"{row['TECHNOLOGY']}_capacity", 
        #         min_capacity=round(row['MIN_INSTALLED_CAPACITY'])
        #     )
        
        # factors_df = self.collect_factors(selected_technologies)
        # self.xml_generator.add_maximum_rate_of_activity_per_all_technology_constraint(modes=modes, factors_df=factors_df)

        
        input_output_activity_ratio_df, specified_annual_demand_df, specified_demand_profile_df, year_split_df = self.collect_ratio_annual_demand()

        self.xml_generator.add_minimum_rate_of_activity_constraint(
            input_output_activity_ratio_df=input_output_activity_ratio_df,
            specified_annual_demand_df=specified_annual_demand_df,
            specified_demand_profile_df=specified_demand_profile_df,
            year_split_df = year_split_df
        )

        # max_capacity_installable_df = self.filter_data(self.data_parser.extract_total_annual_max_capacity(year=self.year, unit='MW'))
        # for index, row in max_capacity_installable_df.iterrows():
        #     self.xml_generator.add_maximum_capacity_constraint(
        #         variable_name=f"{row['TECHNOLOGY']}_capacity", 
        #         max_capacity=round(row['TOTAL_ANNUAL_CAPACITY'])
        #     )

        # upper_limit_technological_demand_df = self.filter_data(self.data_parser.extract_total_technology_annual_activity_upper_limit(year=self.year, unit='TJ'))
        # lower_limit_technological_demand_df = self.filter_data(self.data_parser.extract_total_technology_annual_activity_lower_limit(year=self.year, unit='TJ'))
        # print(upper_limit_technological_demand_df)
        # print(lower_limit_technological_demand_df)
        # limit_technological_demand_df = upper_limit_technological_demand_df.merge(lower_limit_technological_demand_df, on=['COUNTRY', 'TECHNOLOGY'], how='outer')
        # for index, row in limit_technological_demand_df.iterrows():
        #     self.xml_generator.add_min_max_total_technology_annual_activity_constraint(
        #         modes=modes,
        #         year_split_df=year_split_df,
        #         technology=row['TECHNOLOGY'], 
        #         upper_limit=row['TOTAL_ANNUAL_ACTIVITY_UPPER_LIMIT'],
        #         lower_limit=row['TOTAL_ANNUAL_ACTIVITY_LOWER_LIMIT'] 
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
        #     
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
    
    def collect_factors(self, selected_technologies):
        capacity_factor_df = self.filter_data(self.data_parser.extract_capacity_factors(year=self.year, timeslices=True))
        availability_factor_df = self.filter_data(self.data_parser.extract_availability_factors(year=self.year))
        conversion_factor_df = self.data_parser.extract_capacity_to_activity_unit()
        year_split_df = self.data_parser.extract_year_split(year=self.year)
        factors_df = capacity_factor_df.set_index(['COUNTRY', 'TECHNOLOGY']).join(
            availability_factor_df.set_index(['COUNTRY', 'TECHNOLOGY']), how='outer'
        ).join(
            conversion_factor_df.set_index(['COUNTRY', 'TECHNOLOGY']), how='outer'
        ).reset_index()
        factors_df = factors_df[factors_df['TECHNOLOGY'].isin(selected_technologies)]
        factors_df = factors_df.merge(year_split_df, on='TIMESLICE', how='left')
        #TODO: how should i treat the NaN values? - At the moment filling them with 1
        factors_df['CAPACITY_FACTOR'] = factors_df['CAPACITY_FACTOR'].fillna(1)
        factors_df['AVAILABILITY_FACTOR'] = factors_df['AVAILABILITY_FACTOR'].fillna(0)
        factors_df = factors_df[~factors_df['TIMESLICE'].isna()]
        factors_df['YEAR_SPLIT'] = factors_df['YEAR_SPLIT'].map(lambda x: 1/round(1/x))

        return factors_df
    
    def collect_ratio_annual_demand(self):
        output_activity_ratio_df = self.filter_data(self.data_parser.extract_output_activity_ratio(year=self.year))
        input_activity_ratio_df = self.filter_data(self.data_parser.extract_input_activity_ratio(year=self.year))
        input_output_activity_ratio_df = input_activity_ratio_df.merge(output_activity_ratio_df, on=['COUNTRY', 'TECHNOLOGY', 'FUEL', 'MODE_OF_OPERATION'], how='outer')
        #input_output_activity_ratio_df = input_output_activity_ratio_df.dropna(subset=['INPUT_ACTIVITY_RATIO', 'OUTPUT_ACTIVITY_RATIO'])
        input_output_activity_ratio_df = input_output_activity_ratio_df.fillna(1)
        # input_output_activity_ratio_df['Input/Output-Egual'] = abs(input_output_activity_ratio_df['INPUT_ACTIVITY_RATIO'] - input_output_activity_ratio_df['OUTPUT_ACTIVITY_RATIO']) < 0.001
        # input_output_activity_ratio_df = input_output_activity_ratio_df[input_output_activity_ratio_df['Input/Output-Egual'] == False]
        # input_output_activity_ratio_df = input_output_activity_ratio_df.drop(columns=['Input/Output-Egual'])
        specified_annual_demand_df = self.filter_data(self.data_parser.extract_specified_annual_demand(year=self.year, unit='TJ'))
        specified_demand_profile_df = self.filter_data(self.data_parser.extract_specified_demand_profile(year=self.year, timeslices=True))
        year_split_df = self.data_parser.extract_year_split(year=self.year)
        print(input_output_activity_ratio_df)

        return input_output_activity_ratio_df, specified_annual_demand_df, specified_demand_profile_df, year_split_df
        
    def generate_domains(self):
        #TODO: Do not hard code this values
        self.logger.debug("Generating domains...")
        domains = {}
        domains["rate_activity_domain"] = range(0, 100000, 1000) #PJ/year
        domains["installable_capacity_domain"] = range(0, 250000, 100) #MW 
        domains["trasferable_capacity_domain"] = range(0, 3000, 500) #PJ/year
        return domains
    
