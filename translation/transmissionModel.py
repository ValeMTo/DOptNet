from translation.parsers.configParser import ConfigParserClass
from translation.parsers.osemosysDataParser import localDataParserClass
from translation.xmlGenerator import XMLGeneratorClass
from deprecated import deprecated
import pandas as pd
import logging
import os
from itertools import product

class TransmissionModelClass:
    def __init__(self, countries, neighbor_pairs, data, logger, xml_file_path, expansion_enabled):
        self.countries = countries
        self.neighbor_pairs = neighbor_pairs
        self.data = data
        self.logger = logger
        self.xml_file_path = xml_file_path
        self.xml_generator = XMLGeneratorClass(logger=self.logger)
        self.expansion_enabled = expansion_enabled
   
    def generate_xml(self):
        self.logger.debug("Generating XML for transmission model")

        self.xml_generator.add_presentation(name="TransmissionModel", maximize='False')
        self.xml_generator.add_agents(self.countries)
        self.xml_generator.add_domains(self.generate_domains())

        for n in self.neighbor_pairs:
            self.xml_generator.add_variable(name=f"transmission_{n[0]}_{n[1]}", domain='capacity_domain', agent=n[0])
            self.xml_generator.add_variable(name=f"transmission_{n[1]}_{n[0]}", domain='capacity_domain', agent=n[1])
            self.xml_generator.add_symmetry_constraint(
                extra_name=f"{n[0]}_{n[1]}",
                var1=f"transmission_{n[0]}_{n[1]}",
                var2=f"transmission_{n[1]}_{n[0]}"
            )
        
        # Constraint: Transmission capacity should be less than or equal to the maximum capacity
        for n in self.neighbor_pairs:
            self.xml_generator.add_maximum_capacity_constraint(
                variable_name=f"transmission_{n[0]}_{n[1]}",
                max_capacity=self.data.get_max_capacity(n[0], n[1])
            )
            self.xml_generator.add_maximum_capacity_constraint(
                variable_name=f"transmission_{n[1]}_{n[0]}",
                max_capacity=self.data.get_max_capacity(n[0], n[1])
            )

        # Constraint: Power balance per country
        for country in self.countries:
            transmission_variables = [f"transmission_{n[0]}_{n[1]}" for n in self.neighbor_pairs if n[0] == country]
            self.xml_generator.add_power_balance_constraint(
                extra_name = f"{country}",
                flow_variables = transmission_variables,
                delta=self.data.get_marginal_demand(country)
            )

        # Constraint: Utility function
        for n in self.neighbor_pairs:
            self.xml_generator.add_utility_function_constaint(
                extra_name=f"{n[0]}_{n[1]}",
                variable=f"transmission_{n[0]}_{n[1]}",
                import_marginal_cost = self.data.get_import_marginal_cost(n[1]),
                export_marginal_cost = self.data.get_export_marginal_cost(n[0]),
                cost_unit_transmission_line = self.data.get_cost_unit_transmission_line(origin=n[0], destination=n[1]),
            )
            self.xml_generator.add_utility_function_constaint(
                extra_name=f"{n[1]}_{n[0]}",
                variable=f"transmission_{n[1]}_{n[0]}",
                import_marginal_cost = self.data.get_import_marginal_cost(n[0]),
                export_marginal_cost = self.data.get_export_marginal_cost(n[1]),
                cost = self.data.get_cost_unit_transmission_line(origin=n[1], destination=n[0]),
            )
    
    def print_xml(self, name):
        self.logger.debug(f"Printing XML for {self.name}")
        self.xml_generator.print_xml(output_file=os.path.join(self.xml_file_path, name))
        self.logger.debug(f"XML generated for {self.name} at {os.path.join(self.xml_file_path, name)}")
    
    def generate_domains(self):
        raise NotImplementedError("This method has not been implemented yet")