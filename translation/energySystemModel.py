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
import numpy as np
import subprocess
from concurrent.futures import ThreadPoolExecutor

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
        self.delta_marginal_cost = self.config_parser.get_delta_marginal_cost()

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

        for t in range(self.time_resolution):
            k = 0
            self.solve_internal_DCOP(t)
            for _ in range(self.max_iteration):
                self.solve_transmission_problem()
                self.solve_internal_DCOP(t)
                if self.check_convergence():
                    break
                k += 1         

    def solve_internal_DCOP(self, t, year):
        self.logger.info(f"Calculating marginal costs for time {t} and year {year}")

        for country in self.countries:
            self.create_internal_DCOP(country, t, year, self.delta_marginal_cost)
        self.solve_folder(os.path.join(self.config_parser.get_output_file_path(), f"DCOP/internal/{t}"))
        self.calculate_marginal_costs(t, year)
    
    def calculate_marginal_costs(self, t, year):
        raise NotImplementedError("Marginal cost calculation not implemented yet")

    def solve_transmission_problem(self, time):
        raise NotImplementedError("Transmission problem solving not implemented yet")

    def check_convergence(self):
        raise NotImplementedError("Convergence check not implemented yet")
    
    def create_internal_DCOP(self, country, time, year, delta_marginal_cost):
            self.logger.debug(f"Creating internal DCOP for {country} at time {time} and year {year}")
            if not os.path.exists(os.path.join(self.config_parser.get_output_file_path(), f"DCOP/internal/{time}/problems")):
                os.makedirs(os.path.join(self.config_parser.get_output_file_path(), f"DCOP/internal/{time}/problems"))

            energy_country_class = EnergyAgentClass(
                country=country,
                logger=self.logger,
                data=self.data_parser.get_country_data(country, time, year),
                output_file_path=os.path.join(self.config_parser.get_output_file_path(), f"DCOP/internal/{time}/problems")
            )
            energy_country_class.generate_xml(
                domains=self.data_parser.get_domains(),
                technologies=self.data_parser.get_technologies(),
                delta_marginal_cost_percentage=0
            )
            energy_country_class.print_xml(f"{country}.xml")
            energy_country_class.change_demand(delta_marginal_cost_percentage=delta_marginal_cost)
            energy_country_class.print_xml(f"{country}_+{delta_marginal_cost}.xml")
            energy_country_class.change_demand(delta_marginal_cost_percentage=-delta_marginal_cost)
            energy_country_class.print_xml(f"{country}_-{delta_marginal_cost}.xml")

    def solve_DCOP(self, input_path, output_path):
        java_command = [
            'java', 
            '-Xmx2G', 
            '-cp', 
            'frodo2.18.1.jar:junit-4.13.2.jar:hamcrest-core-1.3.jar', 
            'frodo2.algorithms.AgentFactory', 
            '-timeout', 
            '60000', 
            input_path, 
            'agents/DPOP/DPOPagentJaCoP.xml', 
            '-o', 
            output_path,
        ]
        java_process = subprocess.Popen(java_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = java_process.communicate()
        if java_process.returncode == 0:
            self.logger.info(f"Java program finished successfully for {input_path}.")
        else:
            self.logger.error(f"Java program encountered an error for {input_path}:\n{stderr.decode()}")

    def solve_folder(self, folder):
        problem_folder = os.path.join(folder, f"problems")
        output_folder = os.path.join(folder, f"outputs")

        if not os.path.exists(problem_folder):
            self.logger.error(f"Problem folder {problem_folder} does not exist.")
            raise FileNotFoundError(f"Problem folder {problem_folder} does not exist.")

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        def process_file(file_name):
            if file_name.endswith(".xml"):
                input_path = os.path.join(problem_folder, file_name)
                output_path = os.path.join(output_folder, f"{file_name}_output.xml")
                self.solve_DCOP(input_path, output_path)

        with ThreadPoolExecutor() as executor:
            executor.map(process_file, os.listdir(problem_folder))

