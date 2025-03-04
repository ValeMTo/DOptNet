from parsers.configParser import ConfigParserClass
from translation.parsers.localDataParser import localDataParserClass
from xmlGenerator import XMLGeneratorClass
import logging


class EnergyModelClass:
    def __init__(self, logger):
        self.config_parser = ConfigParserClass(file_path='config.yaml')
        self.log_level, log_file = self.config_parser.get_log_info()
        self.logger = self.create_logger(self.log_level, log_file)
        self.config_parser.set_logger(logger)

        self.logger = logger
        self.data_parser = localDataParserClass(logger = self.logger)
        self.xml_generator = XMLGeneratorClass(logger = self.logger)

        self.name = self.config_parser.get_problem_name()
        self.countries = self.config_parser.get_countries()
        self.year = self.config_parser.get_year()

        self.logger.info("Energy model initialized")

    def create_logger(log_level, log_file):
        logging.basicConfig(
            filename=log_file,
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        return logging.getLogger(__name__)
    
    def collect_data(self):
        self.logger.debug("Collecting data...")
        self.powerplants_data = self.data_parser.get_powerplants_data(self.countries)
        self.logger.debug("Powerplants data collected")

        self.demand_data = self.data_parser.get_annual_demand_data(self.year, self.countries)
        self.logger.debug("Annual demand data collected")

    def generate_xml(self):
        self.logger.debug("Generating XML...")
        technologies = self.powerplants_data['Fueltype-Technology'] = self.powerplants_data['Fueltype'] + '-' + self.powerplants_data['Technology']
        technologies = technologies.unique()

        self.xml_generator.frame_xml(
            name=self.name, 
            agent_names=self.countries, 
            technologies=technologies
        )
