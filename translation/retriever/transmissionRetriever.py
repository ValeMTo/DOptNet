import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd

class transmissionRetrieverClass():
    def __init__(self, logger, regions):
        self.logger = logger
        self.regions = regions

    def get_power_lines(self):
        tags = {"power": "line", "voltage": True}
        gdf = ox.geometries_from_place("Southern Africa", tags=tags)

        # Filter high voltage lines (e.g. >110kV)
        gdf = gdf[gdf['voltage'].astype(str).str.extract('(\d+)').astype(float) > 110]

    def get_borders(self, countries_array):
        world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
        filtered_countries = world[world['name'].isin(countries_array)]
        return filtered_countries
    
    def get_line_countries(self, line, countries):
        start = Point(line.coords[0])
        end = Point(line.coords[-1])
        
        start_country = countries[countries.contains(start)]
        end_country = countries[countries.contains(end)]

        if start_country.empty or end_country.empty:
            return None, None  # skip if unknown
        return start_country.iloc[0]['NAME'], end_country.iloc[0]['NAME']
    
    def extract_cross_border_lines(self):
        self.logger.info("Extracting cross-border lines")

        countries = self.get_borders(self.regions)
        lines = self.get_power_lines()
        cross_border_lines = []
        for line in lines.geometry:
            start_country, end_country = self.get_line_countries(line, countries)
            if start_country != end_country:
                cross_border_lines.append((start_country, end_country))
                self.logger.info(f"Found {len(cross_border_lines)} cross-border lines")
                tension = line.get('voltage', None)
                circuit = line.get('circuit', None)
                cables = line.get('cables', None)
                cross_border_lines.append({
                    "start_country": start_country,
                    "end_country": end_country,
                    "tension": tension,
                    "circuit": circuit, #TODO: it might be also the number of cables
                    "cables": cables,
                })
        df = pd.DataFrame(cross_border_lines)
        self.logger.info(f"Extracted {len(df)} cross-border lines")

        return df