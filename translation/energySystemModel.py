from translation.parsers.configParser import ConfigParserClass
from translation.parsers.osemosysDataParser import localDataParserClass
from translation.xmlGenerator import XMLGeneratorClass
from translation.energyAgentModel import EnergyAgentClass
from deprecated import deprecated
import pandas as pd
import logging
import os
from itertools import product
from tqdm import tqdm



class EnergyModelClass:
    def __init__(self):
        self.config_parser = ConfigParserClass(file_path='config.yaml')
        self.logger = self.create_logger(**self.config_parser.get_log_info())
        self.config_parser.set_logger(self.logger)

        self.data_parser = localDataParserClass(logger = self.logger, file_path=self.config_parser.get_file_path())
        self.xml_generator = XMLGeneratorClass(logger = self.logger)

        self.name = self.config_parser.get_problem_name()
        self.time_resolution = self.config_parser.get_annual_time_resolution()
        self.years = self.config_parser.get_years()

        self.countries = self.config_parser.get_countries()
        self.logger.info("Energy model initialized")
        self.max_iteration = self.config_parser.get_max_iteration()

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
    
    def solve(self):
        self.logger.info("Solving the energy model")
        for year in tqdm(self.years, desc="Solving energy model"):
            self.solve_year(year)
        self.logger.info("Energy model solved")
    
    def solve_year(self, year):
        self.logger.info(f"Solving the energy model for {self.year}")

        k = 0
        self.calculate_marginal_costs()
        for _ in tqdm(range(self.max_iteration), desc=f"Solving iterations per {year}"):
            self.solve_transmission_problem()
            self.calculate_marginal_costs()
            if self.check_convergence():
                break
            k += 1

    def calculate_marginal_costs(self):
        raise NotImplementedError("Marginal cost calculation not implemented yet")
            
    def solve_transmission_problem(self):
        raise NotImplementedError("Transmission problem solving not implemented yet")

    def check_convergence(self):
        raise NotImplementedError("Convergence check not implemented yet")