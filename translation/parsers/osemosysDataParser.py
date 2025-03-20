import pandas as pd

class localDataParserClass:
    def __init__(self, logger, file_path):
        self.logger = logger
        self.logger.info("Local Data parser initialized")
        self.data_file_path = file_path
        #self.tech_file_path = tech_path
        #self.fuel_file_path = fuel_path

    def convert_fromGW_capacity_unit(self, data, unit):
        if unit == 'GW':
            data = data
        elif unit == 'MW':
            data = data * 1000
        else:
            raise ValueError("Unit must be 'GW' or 'MW'")
        return data

    def extract_minimum_installed_capacity(self, year, unit='GW'):
        residualCapacity_df = pd.read_excel(self.data_file_path, sheet_name="ResidualCapacity")
        residualCapacity_df['COUNTRY'] = residualCapacity_df['TECHNOLOGY'].map(lambda x: x[:2])
        residualCapacity_df['TECH'] = residualCapacity_df['TECHNOLOGY'].map(lambda x: x[2:])
        new_df = residualCapacity_df[['COUNTRY', 'TECH', year]].rename(columns={year: 'MIN_INSTALLED_CAPACITY'})
        new_df['MIN_INSTALLED_CAPACITY'] = pd.to_numeric(new_df['MIN_INSTALLED_CAPACITY'], errors='coerce')
        
        new_df['MIN_INSTALLED_CAPACITY'] = self.convert_fromGW_capacity_unit(new_df['MIN_INSTALLED_CAPACITY'], unit)

        return new_df
    
    def extract_capacity_factors(self, year, timeslices=False):
        capacity_factors_df = pd.read_excel(self.data_file_path, sheet_name="CapacityFactor")
        capacity_factors_df['COUNTRY'] = capacity_factors_df['TECHNOLOGY'].map(lambda x: x[:2])
        capacity_factors_df['TECH'] = capacity_factors_df['TECHNOLOGY'].map(lambda x: x[2:])

        new_df = capacity_factors_df[['COUNTRY', 'TECH', 'TIMESLICE', year]].rename(columns={year: 'CAPACITY_FACTOR'})
        new_df['CAPACITY_FACTOR'] = pd.to_numeric(new_df['CAPACITY_FACTOR'], errors='coerce')

        if not timeslices:
            # Select only numeric columns before applying mean
            numeric_cols = ['CAPACITY_FACTOR']
            new_df = new_df.groupby(['COUNTRY', 'TECH'], as_index=False)[numeric_cols].mean()

        return new_df
    
    def extract_availability_factors(self, year):
        availability_factors_df = pd.read_excel(self.data_file_path, sheet_name="AvailabilityFactor")
        availability_factors_df['COUNTRY'] = availability_factors_df['TECHNOLOGY'].map(lambda x: x[:2])
        availability_factors_df['TECH'] = availability_factors_df['TECHNOLOGY'].map(lambda x: x[2:])

        new_df = availability_factors_df[['COUNTRY', 'TECH', year]].rename(columns={year: 'AVAILABILITY_FACTOR'})
        new_df['AVAILABILITY_FACTOR'] = pd.to_numeric(new_df['AVAILABILITY_FACTOR'], errors='coerce')

        return new_df
    
    def extract_capacity_to_activity_unit(self):
        capacity_to_activity_unit_df = pd.read_excel(self.data_file_path, sheet_name="CapacityToActivityUnit")
        capacity_to_activity_unit_df['COUNTRY'] = capacity_to_activity_unit_df['TECHNOLOGY'].map(lambda x: x[:2])
        capacity_to_activity_unit_df['TECH'] = capacity_to_activity_unit_df['TECHNOLOGY'].map(lambda x: x[2:])

        new_df = capacity_to_activity_unit_df[['COUNTRY', 'TECH', 'Value']].rename(columns={'Value': 'CAPACITY_TO_ACTIVITY_UNIT'})
        new_df['CAPACITY_TO_ACTIVITY_UNIT'] = pd.to_numeric(new_df['CAPACITY_TO_ACTIVITY_UNIT'], errors='coerce')

        return new_df
    
    def extract_specified_annual_demand(self, year):
        specified_annual_demand_df = pd.read_excel(self.data_file_path, sheet_name="SpecifiedAnnualDemand")
        specified_annual_demand_df['COUNTRY'] = specified_annual_demand_df['FUEL'].map(lambda x: x[:2])
        specified_annual_demand_df['FUEL_NAME'] = specified_annual_demand_df['FUEL'].map(lambda x: x[2:])

        new_df = specified_annual_demand_df[['COUNTRY', 'FUEL_NAME', year]].rename(columns={year: 'SPECIFIED_ANNUAL_DEMAND'})
        new_df['SPECIFIED_ANNUAL_DEMAND'] = pd.to_numeric(new_df['SPECIFIED_ANNUAL_DEMAND'], errors='coerce')

        return new_df

    def extract_specified_demand_profile(self, year, timeslices=False):
        specifiedDemandProfile_df = pd.read_excel(self.data_file_path, sheet_name="SpecifiedDemandProfile")
        specifiedDemandProfile_df['COUNTRY'] = specifiedDemandProfile_df['FUEL'].map(lambda x: x[:2])
        specifiedDemandProfile_df['FUEL_NAME'] = specifiedDemandProfile_df['FUEL'].map(lambda x: x[2:])

        new_df = specifiedDemandProfile_df[['COUNTRY', 'FUEL_NAME', 'TIMESLICE', year]].rename(columns={year: 'SPECIFIED_DEMAND_PROFILE'})
        new_df['SPECIFIED_DEMAND_PROFILE'] = pd.to_numeric(new_df['SPECIFIED_DEMAND_PROFILE'], errors='coerce')

        if not timeslices:
            # Select only numeric columns before applying sum
            numeric_cols = ['SPECIFIED_DEMAND_PROFILE']
            new_df = new_df.groupby(['COUNTRY', 'FUEL_NAME'], as_index=False)[numeric_cols].sum()

        return new_df
    
    def extract_year_split(self, year):
        year_split_df = pd.read_excel(self.data_file_path, sheet_name="YearSplit")
        year_split_df.rename(columns={'Unnamed: 0': 'TIMESLICE'}, inplace=True)

        new_df = year_split_df[['TIMESLICE', year]].rename(columns={year: 'YEAR_SPLIT'})
        return new_df
    
    def extract_accumulated_annual_demand(self, year):
        accumulated_annual_demand_df = pd.read_excel(self.data_file_path, sheet_name="AccumulatedAnnualDemand")
        accumulated_annual_demand_df['COUNTRY'] = accumulated_annual_demand_df['FUEL'].map(lambda x: x[:2])
        accumulated_annual_demand_df['FUEL_NAME'] = accumulated_annual_demand_df['FUEL'].map(lambda x: x[2:])

        new_df = accumulated_annual_demand_df[['COUNTRY', 'FUEL_NAME', year]].rename(columns={year: 'ACCUMULATED_ANNUAL_DEMAND'})
        new_df['ACCUMULATED_ANNUAL_DEMAND'] = pd.to_numeric(new_df['ACCUMULATED_ANNUAL_DEMAND'], errors='coerce')

        return new_df
    
    def extract_capital_costs(self, year):
        capital_costs_df = pd.read_excel(self.data_file_path, sheet_name="CapitalCost")
        capital_costs_df['COUNTRY'] = capital_costs_df['TECHNOLOGY'].map(lambda x: x[:2])
        capital_costs_df['TECH'] = capital_costs_df['TECHNOLOGY'].map(lambda x: x[2:])

        new_df = capital_costs_df[['COUNTRY', 'TECH', year]].rename(columns={year: 'CAPITAL_COST'})
        new_df['CAPITAL_COST'] = pd.to_numeric(new_df['CAPITAL_COST'], errors='coerce')

        return new_df
    
    def extract_fixed_costs(self, year):
        fixed_costs_df = pd.read_excel(self.data_file_path, sheet_name="FixedCost")
        fixed_costs_df['COUNTRY'] = fixed_costs_df['TECHNOLOGY'].map(lambda x: x[:2])
        fixed_costs_df['TECH'] = fixed_costs_df['TECHNOLOGY'].map(lambda x: x[2:])

        new_df = fixed_costs_df[['COUNTRY', 'TECH', year]].rename(columns={year: 'FIXED_COST'})
        new_df['FIXED_COST'] = pd.to_numeric(new_df['FIXED_COST'], errors='coerce')

        return new_df
    
    def extract_variable_costs(self, year):
        variable_costs_df = pd.read_excel(self.data_file_path, sheet_name="VariableCost")
        variable_costs_df['COUNTRY'] = variable_costs_df['TECHNOLOGY'].map(lambda x: x[:2])
        variable_costs_df['TECH'] = variable_costs_df['TECHNOLOGY'].map(lambda x: x[2:])

        new_df = variable_costs_df[['COUNTRY', 'TECH','MODEOFOPERATION', year]].rename(columns={year: 'VARIABLE_COST'})
        new_df['VARIABLE_COST'] = pd.to_numeric(new_df['VARIABLE_COST'], errors='coerce')

        if len(new_df['MODEOFOPERATION'].unique()) == 1:
            new_df.drop(columns=['MODEOFOPERATION'], inplace=True)

        return new_df
    
    def extract_discount_rate(self):
        discount_rate_df = pd.read_excel(self.data_file_path, sheet_name="DiscountRate", header=None)
        return discount_rate_df.iloc[0, 0]
    
    def extract_technology_operational_life(self):
        operational_lifetime_df = pd.read_excel(self.data_file_path, sheet_name="OperationalLife")
        operational_lifetime_df['COUNTRY'] = operational_lifetime_df['TECHNOLOGY'].map(lambda x: x[:2])
        operational_lifetime_df['TECH'] = operational_lifetime_df['TECHNOLOGY'].map(lambda x: x[2:])

        new_df = operational_lifetime_df[['COUNTRY', 'TECH', 'VALUE']].rename(columns={'VALUE': 'OPERATIONAL_LIFETIME'})
        new_df['OPERATIONAL_LIFETIME'] = pd.to_numeric(new_df['OPERATIONAL_LIFETIME'], errors='coerce')

        return new_df
    
    def extract_total_annual_max_capacity(self, year):
        total_annual_capacity_df = pd.read_excel(self.data_file_path, sheet_name="TotalAnnualMaxCapacity")
        total_annual_capacity_df['COUNTRY'] = total_annual_capacity_df['TECHNOLOGY'].map(lambda x: x[:2])
        total_annual_capacity_df['TECH'] = total_annual_capacity_df['TECHNOLOGY'].map(lambda x: x[2:])

        new_df = total_annual_capacity_df[['COUNTRY', 'TECH', year]].rename(columns={year: 'TOTAL_ANNUAL_CAPACITY'})
        new_df['TOTAL_ANNUAL_CAPACITY'] = pd.to_numeric(new_df['TOTAL_ANNUAL_CAPACITY'], errors='coerce')

        return new_df
    
    def extract_total_technology_annual_activity_upper_limit(self, year):
        total_annual_activity_upper_limit_df = pd.read_excel(self.data_file_path, sheet_name="TotalTechnologyAnnualActivityUp")
        total_annual_activity_upper_limit_df['COUNTRY'] = total_annual_activity_upper_limit_df['TECHNOLOGY'].map(lambda x: x[:2])
        total_annual_activity_upper_limit_df['TECH'] = total_annual_activity_upper_limit_df['TECHNOLOGY'].map(lambda x: x[2:])

        new_df = total_annual_activity_upper_limit_df[['COUNTRY', 'TECH', year]].rename(columns={year: 'TOTAL_ANNUAL_ACTIVITY_UPPER_LIMIT'})
        new_df['TOTAL_ANNUAL_ACTIVITY_UPPER_LIMIT'] = pd.to_numeric(new_df['TOTAL_ANNUAL_ACTIVITY_UPPER_LIMIT'], errors='coerce')

        return new_df
    
    def extract_total_technology_annual_activity_lower_limit(self, year):
        total_annual_activity_upper_limit_df = pd.read_excel(self.data_file_path, sheet_name="TotalTechnologyAnnualActivityLo")
        total_annual_activity_upper_limit_df['COUNTRY'] = total_annual_activity_upper_limit_df['TECHNOLOGY'].map(lambda x: x[:2])
        total_annual_activity_upper_limit_df['TECH'] = total_annual_activity_upper_limit_df['TECHNOLOGY'].map(lambda x: x[2:])

        new_df = total_annual_activity_upper_limit_df[['COUNTRY', 'TECH', year]].rename(columns={year: 'TOTAL_ANNUAL_ACTIVITY_LOWER_LIMIT'})
        new_df['TOTAL_ANNUAL_ACTIVITY_LOWER_LIMIT'] = pd.to_numeric(new_df['TOTAL_ANNUAL_ACTIVITY_LOWER_LIMIT'], errors='coerce')

        return new_df
    
    def extract_emission_activity_ratio(self, year):
        emission_activity_ratio_df = pd.read_excel(self.data_file_path, sheet_name="EmissionActivityRatio")
        emission_activity_ratio_df['COUNTRY_TECH'] = emission_activity_ratio_df['TECHNOLOGY'].map(lambda x: x[:2])
        emission_activity_ratio_df['TECH'] = emission_activity_ratio_df['TECHNOLOGY'].map(lambda x: x[2:])
        emission_activity_ratio_df['COUNTRY_EMI'] = emission_activity_ratio_df['EMISSION'].map(lambda x: x[:2])
        emission_activity_ratio_df['EMISSION'] = emission_activity_ratio_df['EMISSION'].map(lambda x: x[2:])

        emission_activity_ratio_df = emission_activity_ratio_df[emission_activity_ratio_df['COUNTRY_TECH'] == emission_activity_ratio_df['COUNTRY_EMI']]

        new_df = emission_activity_ratio_df[['COUNTRY_TECH', 'TECH', 'EMISSION', 'MODEOFOPERATION', year]].rename(columns={year: 'EMISSION_ACTIVITY_RATIO'})
        new_df['EMISSION_ACTIVITY_RATIO'] = pd.to_numeric(new_df['EMISSION_ACTIVITY_RATIO'], errors='coerce')

        return new_df

    def extract_emissions_penalty(self, year):
        emissions_penalty_df = pd.read_excel(self.data_file_path, sheet_name="EmissionsPenalty")
        emissions_penalty_df['COUNTRY'] = emissions_penalty_df['EMISSION'].map(lambda x: x[:2])
        emissions_penalty_df['EMISSION'] = emissions_penalty_df['EMISSION'].map(lambda x: x[2:])

        new_df = emissions_penalty_df[['COUNTRY', 'EMISSION', year]].rename(columns={year: 'EMISSIONS_PENALTY'})
        new_df['EMISSIONS_PENALTY'] = pd.to_numeric(new_df['EMISSIONS_PENALTY'], errors='coerce')

        return new_df

    def extract_annual_emission_limit(self, year):
        annual_emission_limit_df = pd.read_excel(self.data_file_path, sheet_name="AnnualEmissionLimit")
        annual_emission_limit_df['COUNTRY'] = annual_emission_limit_df['EMISSION'].map(lambda x: x[:2])
        annual_emission_limit_df['EMISSION'] = annual_emission_limit_df['EMISSION'].map(lambda x: x[2:])

        new_df = annual_emission_limit_df[['COUNTRY', 'EMISSION', year]].rename(columns={year: 'ANNUAL_EMISSION_LIMIT'})
        new_df['ANNUAL_EMISSION_LIMIT'] = pd.to_numeric(new_df['ANNUAL_EMISSION_LIMIT'], errors='coerce')

        return new_df
    
    def extract_technologies_per_country(self):

        technologies_df = pd.read_excel(self.data_file_path, sheet_name="TECHNOLOGY", header=None)
        technologies_df['TECHNOLOGY'] = technologies_df[0]
        technologies_df['COUNTRY'] = technologies_df[0].map(lambda x: x[:2])

        return technologies_df[['COUNTRY', 'TECHNOLOGY']]
