from translation.parsers.configParser import ConfigParserClass
from translation.parsers.osemosysDataParser import localDataParserClass
from translation.xmlGenerator import XMLGeneratorClass
from deprecated import deprecated
import pandas as pd
import logging
import os
from itertools import product

class TransmissionModelClass:
    def __init__(self, countries, data, logger, xml_file_path):
        self.countries = countries
        self.data = data
        self.logger = logger
        self.xml_file_path = xml_file_path
        self.xml_generator = XMLGeneratorClass(logger=self.logger)

   
    def generate_xml(self):
        raise NotImplementedError("generate_xml method not implemented yet")
    
    def print_xml(self, name):
        self.logger.debug(f"Printing XML for {self.name}")
        self.xml_generator.print_xml(output_file=os.path.join(self.xml_file_path, name))
        self.logger.debug(f"XML generated for {self.name} at {os.path.join(self.xml_file_path, name)}")
    