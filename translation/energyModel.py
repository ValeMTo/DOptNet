class EnergyModelClass:
    def __init__(self, name, logger):
        self.name = name
        self.logger = logger
        self.logger.info("Energy model initialized")
