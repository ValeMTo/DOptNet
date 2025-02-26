import yaml

class ConfigParserClass:
    def __init__(self, file_path='config.yaml'):

        try:
            with open(file_path, 'r') as file:
                self.config = yaml.safe_load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"File {file_path} not found")
        
    def get_problem_name(self):
        return self.config['name']
    
    def get_log_info(self):
        return self.config['logging']['level'], self.config['logging']['file']
    
    def set_logger(self, logger):
        self.logger = logger
        self.logger.info("Logger set in config parser")
    

