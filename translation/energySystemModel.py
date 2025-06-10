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
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import xml.etree.ElementTree as ET
from collections import defaultdict


class EnergyModelClass:
    def __init__(self):
        self.config_parser = ConfigParserClass(file_path='config.yaml')
        self.logger = self.create_logger(*self.config_parser.get_log_info())
        self.config_parser.set_logger(self.logger)
        self.countries = self.config_parser.get_countries()
        self.name = self.config_parser.get_problem_name()
        self.time_resolution = self.config_parser.get_annual_time_resolution()
        self.years = self.config_parser.get_years()

        self.data_parser = osemosysDataParserClass(logger = self.logger, file_path=self.config_parser.get_file_path())
        self.transmission_data = self.data_parser.get_transmission_data(self.countries)
        self.xml_generator = XMLGeneratorClass(logger = self.logger)


        self.logger.info("Energy model initialized")
        self.max_iteration = self.config_parser.get_max_iteration()
        self.delta_marginal_cost = self.config_parser.get_delta_marginal_cost()
        self.marginal_cost_tolerance = self.config_parser.get_marginal_cost_tolerance()
        self.marginal_costs_df = None
        self.results_df = None
        self.demand_map = {}
        self.data = {}

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
    
    def build_demand_map(self, year, t): 
        self.logger.info(f"Building demand map for year {year}")
        self.demand_map[t] = {}
        for country in self.countries:
            year_split, demand = self.data_parser.load_demand(year, country, t)
            self.demand_map[t][country] = {
                        'demand': demand,
                        'marginal_demand': demand * self.delta_marginal_cost,
                    }
        self.demand_map[t]['year_split'] = year_split # year_split is the same for all countries for timeslice t

    def solve(self):
        self.logger.info("Solving the energy model")
        for year in tqdm(self.years, desc="Solving energy model"):
            self.data_parser.load_data(year=year, countries=self.countries, new_installable_capacity_df=self.results_df)
            self.solve_year(year)
            self.update_data(year)
        self.logger.info("Energy model solved")
    
    def solve_year(self, year):
        self.logger.info(f"Solving the energy model for {year}")
        self.data[year] = {}
        
        for t in tqdm(self.time_resolution, desc=f"Solving year {year}"):
            self.data[year][t] = {}
            self.build_demand_map(year, t)
            marginal_costs_df = self.solve_internal_DCOP(t, year)
            for k in tqdm(range(self.max_iteration), desc=f"Solving time {t} for year {year}"):
                if self.check_convergence(marginal_costs_df):
                    self.logger.info(f"Convergence reached for time {t} and year {year}")
                    break
                self.solve_transmission_problem(t, year)
                marginal_costs_df = self.solve_internal_DCOP(t, year)
        if k == self.max_iteration:
            self.logger.warning(f"Maximum iterations reached for time {t} and year {year}")

    def solve_internal_DCOP(self, t, year):
        self.logger.info(f"Calculating marginal costs for time {t} and year {year}")

        for country in self.countries:
            self.create_internal_DCOP(country, t, year)
        output_folder_path = self.solve_folder(os.path.join(self.config_parser.get_output_file_path(), f"DCOP/{year}/{t}/internal"))
        marginal_costs_df = self.calculate_marginal_costs(t, year, output_folder_path)

        self.logger.info(f"Marginal costs calculated for time {t} and year {year}")
        return marginal_costs_df
    
    def calculate_marginal_costs(self, t, year, output_folder_path):
        self.logger.info(f"Calculating marginal costs for time {t} and year {year} at {output_folder_path}")
        data = {
            country: {
            f"-{self.delta_marginal_cost}": None,
            "0": None,
            f"+{self.delta_marginal_cost}": None,
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

                costs = 0
                for assignment in root.findall("assignment"):
                    var = assignment.attrib["variable"]
                    value = int(assignment.attrib["value"])
                    tech, attr = var.split("_")

                    if attr == "capacity":
                        costs += value * (self.data[year][t][tech]['capital_cost'] - self.data[year][t][tech]['min_installed_capacity']) 
                        costs += value * self.data[year][t][tech]['fixed_cost'] * self.demand_map[t]['year_split']
                    elif attr == "rateActivity":
                        costs += value * self.data[year][t][tech]['variable_cost']


                self.logger.debug(f"Processing file {file_name} with valuation {valuation}")
                df.at[country, demand] = costs
                df.at[country, "marginal_demand"] = self.demand_map[t][country]['marginal_demand']
        df['MC_import'] = (df["0"] - df[f"-{self.delta_marginal_cost}"]) / (df['marginal_demand'])
        df['MC_export'] = (df[f"+{self.delta_marginal_cost}"] - df["0"]) / (df['marginal_demand'])
        return df

    def solve_transmission_problem(self, time, year):
        self.logger.info(f"Solving transmission problem for time {time}")

        transmission_solver = TransmissionModelClass(
            countries=self.countries,
            data=self.transmission_data,
            delta_demand_map=self.demand_map[time],
            year_split=self.demand_map[time]['year_split'],
            marginal_costs_df=self.marginal_costs_df,
            cost_transmission_line=self.config_parser.get_cost_transmission_line(),
            logger=self.logger,
            xml_file_path=os.path.join(self.config_parser.get_output_file_path(), f"DCOP/{year}/{time}/transmission/problems"),
            expansion_enabled=self.config_parser.get_expansion_enabled(),
        )

        transmission_solver.generate_xml(domains=self.create_domains(country=None, time=None, problem_type='transmission'))
        transmission_solver.print_xml(
            name=f"transmission_problem_{time}.xml",
        )

        output_folder = self.solve_folder(os.path.join(self.config_parser.get_output_file_path(), f"DCOP/{year}/{time}/transmission"))
        self.update_demand(time, output_folder)
        self.logger.debug(f"Transmission problem solved for time {time}")

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
    
    def update_demand(self, time, output_folder):
        self.logger.info("Updating demand based on transmission problem results")
        file = os.listdir(output_folder)[0]
        
        file_path = os.path.join(output_folder, file)
        tree = ET.parse(file_path)
        root = tree.getroot()

        for assignment in root.findall("assignment"):
            variable = assignment.attrib["variable"]
            value = int(assignment.attrib["value"])
            if variable.startswith("transmission_"):
                _, country1, country2 = variable.split("_")
                self.demand_map[time][country1]['demand'] += value

        for c in self.countries:    
            self.demand_map[time][c]['marginal_demand'] = self.demand_map[time][c]['demand'] * self.delta_marginal_cost

    def update_data(self, year):
        self.logger.debug(f"Updating data for year {year}")

        base_folder = os.path.join(self.config_parser.get_output_file_path(), f"DCOP/{year}")
        
        # Store max capacities and rate activities
        max_capacities = defaultdict(int)
        rate_activities = defaultdict(dict)  # tech -> {timeslice: value}

        for t in self.time_resolution:
            for problem_type in ["internal"]:
                output_folder = os.path.join(base_folder, str(t), problem_type, "outputs")
                if not os.path.exists(output_folder):
                    continue

                for file_name in os.listdir(output_folder):
                    if file_name.endswith("_output.xml"):
                        file_path = os.path.join(output_folder, file_name)
                        root = ET.parse(file_path).getroot()
                        for assignment in root.findall("assignment"):
                            var = assignment.attrib["variable"]
                            value = int(assignment.attrib["value"])
                            tech, attr = var.split("_")

                            if attr == "capacity":
                                max_capacities[tech] = max(max_capacities[tech], value)
                            elif attr == "rateActivity":
                                rate_activities[tech][t] = value

        # Build the final result DataFrame
        all_techs = set(max_capacities) | set(rate_activities)
        result_df = pd.DataFrame(index=sorted(all_techs))

        # Add capacity column
        result_df[f"capacity_{year}"] = result_df.index.map(lambda tech: max_capacities.get(tech, 0))

        # Add rateActivity per timeslice
        for t in self.time_resolution:
            result_df[f"rateActivity_{year}_{t}"] = result_df.index.map(
                lambda tech: rate_activities.get(tech, {}).get(t, 0)
            )
        if self.results_df is None:
            self.results_df = result_df
        else:
            # Combine with previous results, aligning on index and columns
            self.results_df = pd.concat([self.results_df, result_df], axis=0, sort=False)
            self.results_df = self.results_df[~self.results_df.index.duplicated(keep='last')]
        self.results_df['TECHNOLOGY'] = self.results_df.index
        self.results_df['COUNTRY'] = self.results_df['TECHNOLOGY'].apply(lambda x: x[:2])
        self.results_df.to_csv(self.config_parser.get_output_file_path() + f"/results.csv")

        if self.config_parser.get_expansion_enabled():
            raise NotImplementedError("Expansion is not implemented yet.")
        
    def extract_costs(self, data, year, time):
        self.logger.debug("Extracting costs from the data")
        for tech, row in data.iterrows():
            self.data[year][time][tech] = {
                'capital_cost': row['CAPITAL_COST'],
                'variable_cost': row['VARIABLE_COST'],
                'fixed_cost': row['FIXED_COST'],
                'min_installed_capacity': row['MIN_INSTALLED_CAPACITY'] if pd.notna(row['MIN_INSTALLED_CAPACITY']) else 0,
                'operational_lifetime': row['OPERATIONAL_LIFETIME'],
            }
    
    def create_internal_DCOP(self, country, time, year):
        self.logger.debug(f"Creating internal DCOP for {country} at time {time} and year {year}")
        if not os.path.exists(os.path.join(self.config_parser.get_output_file_path(), f"DCOP/{year}/{time}/internal/problems")):
            os.makedirs(os.path.join(self.config_parser.get_output_file_path(), f"DCOP/{year}/{time}/internal/problems"))

        data = self.data_parser.get_country_data(country, time)
        self.extract_costs(data, year, time)
        energy_country_class = EnergyAgentClass(
            country=country,
            logger=self.logger,
            data=data,
            year_split=self.demand_map[time]['year_split'],
            demand=self.demand_map[time][country]['demand'],
            xml_file_path=os.path.join(self.config_parser.get_output_file_path(), f"DCOP/{year}/{time}/internal/problems")
        )
        energy_country_class.generate_xml(
            domains=self.create_domains(country=country, time=time, problem_type='internal')
        )
        energy_country_class.print_xml(f"{country}_0.xml")
        energy_country_class.change_demand(demand_variation_percentage=self.delta_marginal_cost)
        energy_country_class.print_xml(f"{country}_+{self.delta_marginal_cost}.xml")
        energy_country_class.change_demand(demand_variation_percentage=-self.delta_marginal_cost)
        energy_country_class.print_xml(f"{country}_-{self.delta_marginal_cost}.xml")

    def solve_DCOP(self, input_path, output_path):
        self.logger.debug(f"Solving DCOP for {input_path} and saving to {output_path}")
        java_command = [
            'java', 
            '-Xmx1G', 
            '-cp', 
            'frodo2.18.1.jar:junit-4.13.2.jar:hamcrest-core-1.3.jar', 
            'frodo2.algorithms.AgentFactory', 
            '-timeout', 
            str(self.config_parser.get_timeout_time_steps()*1000), 
            input_path, 
            'agents/DPOP/DPOPagentJaCoP.xml', 
            '-o', 
            output_path,
        ]
        java_process = subprocess.Popen(java_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = java_process.communicate()
        
        # Log both stdout and stderr from the Java process
        if stdout:
            self.logger.info(f"Java stdout for {input_path}:\n{stdout.decode()}")
        if stderr:
            self.logger.error(f"Java stderr for {input_path}:\n{stderr.decode()}")
        if java_process.returncode == 0:
            self.logger.info(f"Java program finished successfully for {input_path}.")
        else:
            self.logger.error(f"Java program encountered an error for {input_path}.")

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
                output_path = os.path.join(output_folder, f"{file_name.replace('.xml', '')}_output.xml")
                self.solve_DCOP(input_path, output_path)

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(process_file, file_name) for file_name in os.listdir(problem_folder)]
            for future in as_completed(futures):
                future.result()  # Wait for each thread to complete

        # Check that each output file in the folder contains a "valuation" parameter, so the run was successful
        for file_name in os.listdir(output_folder):
            if file_name.endswith("_output.xml"):
                file_path = os.path.join(output_folder, file_name)
                try:
                    tree = ET.parse(file_path)
                    root = tree.getroot()
                    if "valuation" not in root.attrib:
                        self.logger.error(f"File {file_name} is missing the 'valuation' parameter.")
                        raise ValueError(f"File {file_name} is missing the 'valuation' parameter.")
                    if not root.attrib["valuation"].isdigit():
                        self.logger.error(f"File {file_name} has an invalid 'valuation' parameter: {root.attrib['valuation']}")
                        raise ValueError(f"File {file_name} as infinity as 'valuation' parameter: {root.attrib['valuation']}")
                except ET.ParseError as e:
                    self.logger.error(f"Error parsing XML file {file_name}: {e}")
                    raise ValueError(f"Error parsing XML file {file_name}: {e}")

        return output_folder
    
    def create_domains(self, country, time, problem_type='internal'):
        self.logger.debug(f"Creating domains for {problem_type} problem in the model")
        domains = self.config_parser.get_domains()

        if problem_type == 'internal':
            if country is None or time is None:
                self.logger.error("Country and year must be provided for internal problem type.")
                raise ValueError("Country and year must be provided for internal problem type.")
            
            domains_mapping = {
                'capacity_domain': range(
                    domains['capacity']['min'],
                    domains['capacity']['max'] + 1,
                    domains['capacity']['step']
                ),
                'rateActivity_domain': range(
                    0,
                    round(self.demand_map[time][country]['demand'] + self.demand_map[time][country]['demand']/100),
                    round(self.demand_map[time][country]['demand']/100)
                )
            }
            return domains_mapping
        elif problem_type == 'transmission':
            domains_mapping = {
                'capacity_domain': range(
                    domains['transmission']['min'],
                    domains['transmission']['max'] + 1,
                    domains['transmission']['step']
                )
            }
            return domains_mapping

        self.logger.warning(f"Problem type {problem_type} not recognized. Returning empty domains.")
        raise ValueError(f"Problem type {problem_type} in create_domains method not recognized.")

