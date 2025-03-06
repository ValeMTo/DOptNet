from translation.parsers.configParser import ConfigParserClass
from translation.parsers.localDataParser import localDataParserClass
from translation.xmlGenerator import XMLGeneratorClass
from deprecated import deprecated
import logging
import os

class EnergyModelClass:
    def __init__(self):
        self.config_parser = ConfigParserClass(file_path='config.yaml')
        self.log_level, log_file = self.config_parser.get_log_info()
        self.logger = self.create_logger(self.log_level, log_file)
        self.config_parser.set_logger(self.logger)

        self.data_parser = localDataParserClass(logger = self.logger)
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

        powerplants_data = self.config_parser.get_powerplants_data()
        self.variables = self.xml_generator.add_variables(
            technologies=powerplants_data['Technology'].unique(),
            agent_names=self.countries
        )

        installed_powerplants = self.data_parser.get_already_installed_powerplants_data(self.countries)

        for index, row in installed_powerplants.iterrows():
            self.xml_generator.add_minimum_capacity_constraint(
                variable_name=f"{row['fueltype']}{row['country'].capitalize()}capacity", 
                min_capacity=round(row['already_installed_capacity'])
            )

        powerplants_data = powerplants_data.merge(
            installed_powerplants[['fueltype', 'country', 'already_installed_capacity']],
            left_on=['Technology', 'Country'],
            right_on=['fueltype', 'country'],
            how='left'
        ).drop(columns=['fueltype', 'country']).fillna({'already_installed_capacity': 0})
        for index, row in powerplants_data.iterrows():
            self.xml_generator.add_maximum_capacity_constraint(
                variable_name=f"{row['Technology']}{row['Country'].capitalize()}capacity",
                max_capacity=round(row['Max Installable Capacity (MW)'])
            )
            self.xml_generator.add_maximum_capacity_factor_constraint(
                variable_name=f"{row['Technology']}{row['Country'].capitalize()}capacityfactor",
                max_capacity_factor=row['Mean Capacity Factor']
            )
            self.xml_generator.add_operating_cost_minimization_constraint(
                weight=1,
                variable_capacity_name=f"{row['Technology']}{row['Country'].capitalize()}capacity",
                variable_capFactor_name=f"{row['Technology']}{row['Country'].capitalize()}capacityfactor",
                cost_per_MWh=round(row['Operating Cost ($/MWh)'] + row['Fuel Cost ($/MWh)'])
            )
            self.xml_generator.add_installing_cost_minimization_constraint(
                weight=1,
                variable_capacity_name=f"{row['Technology']}{row['Country'].capitalize()}capacity",
                previous_installed_capacity=int(row["already_installed_capacity"]),
                cost_per_MW=round(row['Installation Cost ($/MW)'])
            )

        demand_data = self.data_parser.get_annual_demand_data(self.year, self.countries)
        for country in self.countries:
            self.xml_generator.add_demand_constraint_per_agent(
                agent_name=country,
                max_demand=round(demand_data.loc[demand_data['country'] == country][f'annual_demand_{int(self.year)}_GW'].values[0] * 1000), #GW to MW
                technologies=powerplants_data.loc[powerplants_data['Country'] == country]['Technology'].values
            )

        #TODO: add max emissions constraints

        self.xml_generator.print_xml(output_file=f'{self.name}_output.xml')
        self.logger.info("XML generated")
        
    def generate_domains(self):
        #TODO: Do not hard code this values
        self.logger.debug("Generating domains...")
        domains = {}
        domains["capacity_factors_domain"] = range(0, 101, 1)
        domains["installable_capacity_domain"] = range(0, 10000, 100) #MW
        domains["trasferable_capacity_domain"] = range(0, 3000, 50) #MW
        return domains
    
