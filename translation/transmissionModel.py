from translation.xmlGenerator import XMLGeneratorClass
from deprecated import deprecated
import pandas as pd
import logging
import os
from itertools import product

class TransmissionModelClass:
    def __init__(self, countries, data, delta_demand_map, marginal_costs_df, cost_transmission_line, logger, xml_file_path, expansion_enabled):
        self.countries = countries
        self.data = data
        self.delta_demand_map = delta_demand_map
        self.year_split = self.delta_demand_map['year_split']
        self.marginal_costs_df = marginal_costs_df
        self.cost_transmission_line = cost_transmission_line
        self.logger = logger
        self.xml_file_path = xml_file_path
        self.xml_generator = XMLGeneratorClass(logger=self.logger)
        self.expansion_enabled = expansion_enabled
   
    def generate_xml(self, domains):
        self.logger.debug("Generating XML for transmission model")

        self.xml_generator.add_presentation(name="TransmissionModel", maximize='True')
        self.xml_generator.add_agents(self.countries)
        self.xml_generator.add_domains(domains)

        for idx, row in self.data.iterrows():
            self.xml_generator.add_variable(name=f"transmission_{row['start_country']}_{row['end_country']}", domain='capacity_domain', agent=row['start_country'])
        
        already_inside = {}
        for idx, row in self.data.iterrows():   
            if f"{row['end_country']}_{row['start_country']}" not in already_inside:
                self.xml_generator.add_symmetry_constraint(
                    extra_name=f"{row['start_country']}_{row['end_country']}",
                    var1=f"transmission_{row['start_country']}_{row['end_country']}",
                    var2=f"transmission_{row['end_country']}_{row['start_country']}"
                )
                already_inside[f"{row['start_country']}_{row['end_country']}"] = True

        # Constraint: Power balance per country
        for country in self.countries:
            transmission_variables = [f"transmission_{row['start_country']}_{row['end_country']}" for idx, row in self.data.iterrows() if row['start_country'] == country]
            self.xml_generator.add_power_balance_constraint(
                extra_name = f"{country}",
                flow_variables = transmission_variables,
                delta=round(self.delta_demand_map[country]['marginal_demand'])
            )

        # Constraint: Transmission capacity should be less than or equal to the maximum capacity & Utility function
        for idx, row in self.data.iterrows():
            self.xml_generator.add_maximum_capacity_constraint(
                variable_name=f"transmission_{row['start_country']}_{row['end_country']}",
                max_capacity=round(row['capacity']*(8760*self.year_split)),
            )

            self.xml_generator.add_utility_function_constaint(
                extra_name=f"{row['start_country']}_{row['end_country']}",
                variable=f"transmission_{row['start_country']}_{row['end_country']}",
                import_marginal_cost = round(self.marginal_costs_df.loc[row['end_country'], 'MC_import']),
                export_marginal_cost = round(self.marginal_costs_df.loc[row['start_country'], 'MC_export']),
                cost = round(self.cost_transmission_line),
            )
    
    def print_xml(self, name):
        self.logger.debug(f"Printing XML for {name}")

        if not os.path.exists(self.xml_file_path):
            os.makedirs(self.xml_file_path)

        self.xml_generator.print_xml(output_file=os.path.join(self.xml_file_path, name))
        self.logger.debug(f"XML generated for at {os.path.join(self.xml_file_path, name)}")
    