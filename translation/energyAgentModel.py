from translation.parsers.configParser import ConfigParserClass
from translation.parsers.osemosysDataParser import osemosysDataParserClass
from translation.xmlGenerator import XMLGeneratorClass
from deprecated import deprecated
import pandas as pd
import logging
import os
from itertools import product

class EnergyAgentClass:
    def __init__(self, country, logger, data, demand, xml_file_path):
        self.name = country
        self.logger = logger
        self.data = data
        self.demand = demand
        self.demand_constraint = None
        self.xml_generator = XMLGeneratorClass(logger = self.logger)
        self.logger.debug(f"EnergyAgentClass initialized for {country}")
        self.xml_file_path = xml_file_path
    
    def generate_xml(self, domains):
        self.logger.debug(f"Generating XML for {self.name}")
        
        self.xml_generator.add_presentation(name=self.name, maximize='False')
        self.xml_generator.add_agents([self.name])
        self.xml_generator.add_domains(domains)
        
        for var in self.data.index:
            self.xml_generator.add_variable(name=f"{var}_capacity", domain='capacity_domain', agent=self.name)
            self.xml_generator.add_variable(name=f"{var}_rateActivity", domain='rateActivity_domain', agent=self.name)

        # Add constraints here
        for technology, row in self.data.iterrows():
            if pd.notna(row['MIN_INSTALLED_CAPACITY']) and row['MIN_INSTALLED_CAPACITY'] > 0:
                self.xml_generator.add_maximum_capacity_constraint(
                    variable_name=f"{technology}_capacity",
                    max_capacity=round(row['MIN_INSTALLED_CAPACITY'])
                )
                if row['CAPITAL_COST'] > 0:
                    self.xml_generator.add_installing_cost_minimization_constraint(
                        variable_name=f"{technology}_capacity",
                        previous_installed_capacity=round(row['MIN_INSTALLED_CAPACITY']),
                        cost_per_MW=round(row['CAPITAL_COST']),
                        extra_name=f"capital_cost"
                    )
            if pd.notna(row['CAPACITY_FACTOR']) and pd.notna(row['AVAILABILITY_FACTOR']) and pd.notna(row['CAPACITY_TO_ACTIVITY_UNIT']):
                self.xml_generator.add_maximum_activity_rate_constraint(
                    cap_variable=f"{technology}_capacity",
                    capActivity_variable=f"{technology}_rateActivity",
                    factor=round(row['CAPACITY_FACTOR']*row['AVAILABILITY_FACTOR']*row['CAPACITY_TO_ACTIVITY_UNIT'])
                )
            else:
                self.xml_generator.add_maximum_activity_rate_constraint(
                    cap_variable=f"{technology}_capacity",
                    capActivity_variable=f"{technology}_rateActivity",
                    factor=0
                )
            if pd.notna(row['TOTAL_ANNUAL_CAPACITY']):
                if row['TOTAL_ANNUAL_CAPACITY'] != 99999999:
                    self.xml_generator.add_maximum_capacity_constraint(
                        variable_name=f"{technology}_rateActivity",
                        max_capacity=round(row['TOTAL_ANNUAL_CAPACITY'])
                    )   
            else:
                self.xml_generator.add_maximum_capacity_constraint(
                    variable_name=f"{technology}_rateActivity",
                    max_capacity=0
                )
            # Add constraint on fixed cost
            # Add constraint on variable cost

        self.demand_constraint = self.xml_generator.add_minimum_respecting_demand(
            variables = [f"{var}_rateActivity" for var in self.data.index],
            demand = self.demand,
            extra_name = f"0"
        )

    def print_xml(self, name):
        self.logger.debug(f"Printing XML for {self.name}")
        self.xml_generator.print_xml(output_file=os.path.join(self.xml_file_path, name))
        self.logger.debug(f"XML generated for {self.name} at {os.path.join(self.xml_file_path, name)}")
    
    def change_demand(self, demand_variation_percentage):
        if self.demand_constraint is not None:
            self.logger.debug(f"Changing demand for {self.name} by {demand_variation_percentage}%")
            self.xml_generator.remove_constraint(self.demand_constraint)

            new_demand = self.demand * (1 + demand_variation_percentage / 100)

            # Add the updated demand constraint
            self.demand_constraint = self.xml_generator.add_minimum_respecting_demand(
                variables=[f"{var}_rateActivity" for var in self.data.index],
                demand=new_demand,
                extra_name=f"{self.demand_variation_percentage}"
            )
        
        raise NotImplementedError("XML")