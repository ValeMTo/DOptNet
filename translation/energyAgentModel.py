from translation.parsers.configParser import ConfigParserClass
from translation.parsers.osemosysDataParser import localDataParserClass
from translation.xmlGenerator import XMLGeneratorClass
from deprecated import deprecated
import pandas as pd
import logging
import os
from itertools import product

class EnergyAgentClass:
    def __init__(self, country, timeslices, logger, data, output_file_path):
        self.name = country
        self.timeslices = timeslices
        self.logger = logger
        self.data = data
        self.xml_generator = XMLGeneratorClass(logger = self.logger)
        self.logger.debug(f"EnergyAgentClass initialized for {country}")
        self.output_file_path = output_file_path
    
    def generate_xml(self, domains, technologies):
        self.logger.debug(f"Generating XML for {self.name}")
        
        self.xml_generator.add_presentation(name=self.name, maximize='False')
        self.xml_generator.add_agents([self.name])
        self.xml_generator.add_domains(domains)
        
        for var in technologies:
            self.xml_generator.add_variable(name=f"{var}_capacity", domain='capacity_domain', agent=self.name)
            self.xml_generator.add_variable(name=f"{var}_rateActivity", domain='rateActivity_domain', agent=self.name)

        # Add constraints here

        self.xml_generator.print_xml(output_file=self.output_file_path)
        self.logger.debug(f"XML generated for {self.name} at {self.output_file_path}")
        