
from translation.xmlGenerator import XMLGeneratorClass
from deprecated import deprecated
import pandas as pd
import logging
import os
from itertools import product

class EnergyAgentClass:
    def __init__(self, country, logger, data, year_split, demand, xml_file_path):
        self.name = country
        self.logger = logger
        self.data = data
        self.year_split = year_split
        self.demand = demand / year_split
        self.demand_constraint = None
        self.xml_generator = XMLGeneratorClass(logger = self.logger)
        self.logger.debug(f"EnergyAgentClass initialized for {country}")
        self.xml_file_path = xml_file_path
    
    def generate_xml(self, domains):
        self.logger.debug(f"Generating XML for {self.name}")
        
        self.xml_generator.add_presentation(name=self.name, maximize='False')
        self.xml_generator.add_agents([self.name])
        self.xml_generator.add_domains(domains)
        
        self.tech_df = self.data.copy().drop_duplicates(subset=['TECHNOLOGY'], keep='first').set_index('TECHNOLOGY')
        self.tech_df['FACTOR'] = self.tech_df['CAPACITY_FACTOR'] * self.tech_df['AVAILABILITY_FACTOR'] * self.tech_df['CAPACITY_TO_ACTIVITY_UNIT']
        self.tech_df['FACTOR'] = self.tech_df['FACTOR'].fillna(0)  # Replace NaN factors with zero
        self.tech_df = self.tech_df[self.tech_df['FACTOR'] > 0]

        for var in self.tech_df.index:
            self.xml_generator.add_variable(name=f"{var}_capacity", domain='capacity_domain', agent=self.name)
            self.xml_generator.add_variable(name=f"{var}_rateActivity", domain='rateActivity_domain', agent=self.name)

        
        for technology, row in self.tech_df.iterrows():
            if pd.notna(row['MIN_INSTALLED_CAPACITY']) and row['MIN_INSTALLED_CAPACITY'] > 0:
                self.xml_generator.add_minimum_capacity_constraint(
                    variable_name=f"{technology}_capacity",
                    min_capacity=round(row['MIN_INSTALLED_CAPACITY'])
                )
            if row['CAPITAL_COST'] > 0:
                self.xml_generator.add_installing_cost_minimization_constraint(
                    variable_capacity_name=f"{technology}_capacity",
                    previous_installed_capacity=round(row['MIN_INSTALLED_CAPACITY']) if pd.notna(row['MIN_INSTALLED_CAPACITY']) else 0,
                    cost_per_MW=round(row['CAPITAL_COST']),
                    extra_name=f"capital_cost"
                )
            self.xml_generator.add_maximum_activity_rate_constraint(
                cap_variable=f"{technology}_capacity",
                capActivity_variable=f"{technology}_rateActivity",
                factor=row['FACTOR'],
            )
            # Add constraint on fixed cost
            # Add constraint on variable costF

        self.demand_constraint = self.xml_generator.add_minimum_demand_constraint(
            variables = [f"{var}_rateActivity" for var in self.tech_df.index],
            demand = round(self.demand),
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

            new_demand = round(self.demand * (1 + demand_variation_percentage))

            # Add the updated demand constraint
            self.demand_constraint = self.xml_generator.add_minimum_demand_constraint(
                variables=[f"{var}_rateActivity" for var in self.tech_df.index],
                demand=new_demand,
                extra_name=f"{demand_variation_percentage}"
            )
        else:
            raise NotImplementedError("XML instance missing")