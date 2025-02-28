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
    config_parser = ConfigParserClass(file_path='config.yaml')
    log_level, log_file = config_parser.get_log_info()
    logger = create_logger(log_level, log_file)
    config_parser.set_logger(logger)

    zenodo_parser = localDataParserClass(logger = logger)
    model = EnergyModelClass(name = config_parser.get_problem_name(),logger = logger)
    xml_generator = XMLGeneratorClass(logger = logger)
    logger.debug("All classes initialized")
    logger.debug("Program started...")

    

    
    
