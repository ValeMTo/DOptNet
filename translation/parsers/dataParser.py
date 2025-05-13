import pandas as pd
from translation.retriever.transmissionRetriever import transmissionRetrieverClass

class dataParserClass:
    def __init__(self, logger):
        pass
    
    def get_country_data(self, country, year, timeslice):
        """
        Returns the data for a specific country, year and time slice.
        It returns a dataframe with technologies as indexes and columns as relevant data
        """
        raise NotImplementedError("This method will be implemented in child classes")
    
    def get_transmission_data(self, regions):
        retriever = transmissionRetrieverClass(self.logger, regions)
        return retriever.extract_cross_border_lines(regions)


    