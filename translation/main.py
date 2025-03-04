from energyModel import EnergyModelClass
from parsers.configParser import ConfigParserClass
from translation.parsers.localDataParser import localDataParserClass
from xmlGenerator import XMLGeneratorClass
import logging

def create_logger(log_level, log_file):
    logging.basicConfig(
        filename=log_file,
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


if __name__ == "__main__":
    model = EnergyModelClass()

    model.collect_data()

    

    
    
