from translation.parsers.configParser import ConfigParserClass
from translation.parsers.osemosysDataParser import osemosysDataParserClass
from translation.xmlGenerator import XMLGeneratorClass
from translation.energyAgentModel import EnergyAgentClass
from translation.transmissionModel import TransmissionModelClass
from deprecated import deprecated
import pandas as pd
import logging
import os
from itertools import product
from tqdm import tqdm
import numpy as np
import subprocess
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET

class EnergyModelClass:
    def __init__(self):
        self.config_parser = ConfigParserClass(file_path='config.yaml')
        self.logger = self.create_logger(**self.config_parser.get_log_info())
        self.config_parser.set_logger(self.logger)

        self.data_parser = osemosysDataParserClass(logger = self.logger, file_path=self.config_parser.get_file_path())
        self.xml_generator = XMLGeneratorClass(logger = self.logger)

        self.name = self.config_parser.get_problem_name()
        self.time_resolution = self.config_parser.get_annual_time_resolution()
        self.years = self.config_parser.get_years()

        self.countries = self.config_parser.get_countries()
        self.logger.info("Energy model initialized")
        self.max_iteration = self.config_parser.get_max_iteration()
        self.delta_marginal_cost = self.config_parser.get_delta_marginal_cost()
        self.marginal_cost_tolerance = self.config_parser.get_marginal_cost_tolerance()
        self.marginal_costs_df = None

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
            self.data_parser.load_data(year)
            self.solve_year(year)
            self.update_data(year)
        self.logger.info("Energy model solved")
    
    def solve_year(self, year):
        self.logger.info(f"Solving the energy model for {year}")

        for t in range(self.time_resolution):
            marginal_costs_df = self.solve_internal_DCOP(t)
            for k in range(self.max_iteration):
                if self.check_convergence(marginal_costs_df):
                    self.logger.info(f"Convergence reached for time {t} and year {year}")
                    break
                self.solve_transmission_problem(t, year)
                marginal_costs_df = self.solve_internal_DCOP(t)
        if k == self.max_iteration:
            self.logger.warning(f"Maximum iterations reached for time {t} and year {year}")

    def solve_internal_DCOP(self, t, year):
        self.logger.info(f"Calculating marginal costs for time {t} and year {year}")

        for country in self.countries:
            self.create_internal_DCOP(country, t, year)
        output_folder_path = self.solve_folder(os.path.join(self.config_parser.get_output_file_path(), f"DCOP/internal/{year}/{t}"))
        marginal_costs_df = self.calculate_marginal_costs(t, year, output_folder_path)

        self.logger.info(f"Marginal costs calculated for time {t} and year {year}")
        return marginal_costs_df
    
    def calculate_marginal_costs(self, t, year, output_folder_path):
        self.logger.info(f"Calculating marginal costs for time {t} and year {year} at {output_folder_path}")
        data = {
            country: {
            f"-{self.delta_marginal_cost}": None,
            "0": None,
            f"+{self.delta_marginal_cost}": None
            }
            for country in self.countries
        }
        df = pd.DataFrame.from_dict(data, orient='index')
        
        for file_name in os.listdir(output_folder_path):
            if file_name.endswith(".xml"):
                file_path = os.path.join(output_folder_path, file_name)
                country = file_name.split("_")[0]
                demand = file_name.split("_")[1]
                tree = ET.parse(file_path)
                root = tree.getroot()
                valuation = root.attrib.get("valuation")

                self.logger.debug(f"Processing file {file_name} with valuation {valuation}")
                df.at[country, demand] = int(valuation)

        df['MC_import'] = (df["0"] - df[f"-{self.delta_marginal_cost}"]) / self.delta_marginal_cost
        df['MC_export'] = (df[f"+{self.delta_marginal_cost}"] - df["0"]) / self.delta_marginal_cost
        return df

    def solve_transmission_problem(self, time, year):
        self.logger.info(f"Solving transmission problem for time {time}")

        transmission_solver = TransmissionModelClass(
            countries=self.countries,
            data=self.data_parser.get_transmission_data(self.countries),
            logger=self.logger,
            xml_file_path=os.path.join(self.config_parser.get_output_file_path(), f"DCOP/transmission/{year}/problems")
        )

        transmission_solver.generate_xml()
        transmission_solver.print_xml(
            name=f"transmission_problem_{time}.xml",
            output_file_path=os.path.join(self.config_parser.get_output_file_path(), f"DCOP/transmission/{year}/outputs")
        )

    def check_convergence(self, marginal_costs_df):
        self.logger.info("Checking convergence of marginal costs")
        if self.marginal_costs_df is None:
            self.marginal_costs_df = marginal_costs_df
            return False
        distance = (self.marginal_costs_df[['MC_import', 'MC_export']] - marginal_costs_df[['MC_import', 'MC_export']]).abs().max().max() 
        self.logger.debug(f"Maximum Distance between marginal costs: {distance}")
        if distance < self.marginal_cost_tolerance:
            return True
        self.marginal_costs_df = marginal_costs_df
        return False
    
    def update_data(self, year):
        raise NotImplementedError("Data update not implemented yet")
    
    def create_internal_DCOP(self, country, time, year):
        self.logger.debug(f"Creating internal DCOP for {country} at time {time} and year {year}")
        if not os.path.exists(os.path.join(self.config_parser.get_output_file_path(), f"DCOP/internal/{year}/{time}/problems")):
            os.makedirs(os.path.join(self.config_parser.get_output_file_path(), f"DCOP/internal/{year}/{time}/problems"))

        energy_country_class = EnergyAgentClass(
            country=country,
            logger=self.logger,
            data=self.data_parser.get_country_data(country, time),
            output_file_path=os.path.join(self.config_parser.get_output_file_path(), f"DCOP/internal/{year}/{time}/problems")
        )
        energy_country_class.generate_xml(
            domains=self.data_parser.get_domains(),
            delta_marginal_cost_percentage=self.delta_marginal_cost,
        )
        energy_country_class.print_xml(f"{country}_0.xml")
        energy_country_class.change_demand(delta_marginal_cost_percentage=self.delta_marginal_cost)
        energy_country_class.print_xml(f"{country}_+{self.delta_marginal_cost}.xml")
        energy_country_class.change_demand(delta_marginal_cost_percentage=-self.delta_marginal_cost)
        energy_country_class.print_xml(f"{country}_-{self.delta_marginal_cost}.xml")

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

        return output_folder

