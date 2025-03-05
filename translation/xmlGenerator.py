import xml.etree.ElementTree as ET

class XMLGeneratorClass:
    def __init__(self, logger):
        self.logger = logger
        self.logger.info("XML generator initialized")

        self.instance = self.create_frodo2_xml_head_instance()

    def create_frodo2_xml_head_instance(self):
        instance = ET.Element("instance", {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "src/frodo2/algorithms/XCSPschemaJaCoP.xsd"
        })

        return instance
    
    def add_presentation(self, name, maxConstraintArity, maximize, format):
        ET.SubElement(self.instance, "presentation", {
            "name": name,
            "maxConstraintArity": maxConstraintArity,
            "maximize": maximize,
            "format": format
        })
    
    def add_agents(self, agent_names):
        """Adds multiple agents inside a single <agents> element."""
        agents_element = self.instance.find("agents")
        if agents_element is None:
            agents_element = ET.SubElement(self.instance, "agents")

        for agent_name in agent_names:
            ET.SubElement(agents_element, "agent", {"name": agent_name})


    def add_domains(self, domain_values):
        """Adds multiple domains inside a single <domains> element."""
        domains_element = self.instance.find("domains")
        if domains_element is None:
            domains_element = ET.SubElement(self.instance, "domains")
              
        for name, values in domain_values.items():
            ET.SubElement(domains_element, "domain", {"name": name, "nbValues": str(len(values))}).text = " ".join(map(str, values))

    def add_variables(self, technologies, agent_names):
        """Adds multiple variables inside a single <variables> element."""
        variables_element = self.instance.find("variables")
        if variables_element is None:
            variables_element = ET.SubElement(self.instance, "variables")

        for technology in technologies:
            for agent in agent_names:
                formatted_agent = agent.capitalize()
                ET.SubElement(variables_element, "variable", {
                    "name": f"{technology}{formatted_agent}capacity", 
                    "domain": "capacity_installed", 
                    "agent": agent
                })
                ET.SubElement(variables_element, "variable", {
                    "name": f"{technology}{formatted_agent}capFactor", 
                    "domain": "capacity_factor", 
                    "agent": agent
                })

        # TODO: change once the agent_names are not only neighboring
        for agent in agent_names:
            for agent2 in agent_names:
                if agent != agent2:
                    formatted_agent1 = agent.capitalize()
                    formatted_agent2 = agent2.capitalize()
                    ET.SubElement(variables_element, "variable", {
                        "name": f"transmission{formatted_agent1}{formatted_agent2}",
                        "domain": "transmission_capacity",
                        "agent": agent
                    })
    
    def add_predicate(self, name, parameters, functional):
        """Adds a single predicate element with parameters and functional expression."""
        predicates_element = self.instance.find("predicates")
        if (predicates_element is None):
            predicates_element = ET.SubElement(self.instance, "predicates")
        
        predicate_element = ET.SubElement(predicates_element, "predicate", {"name": name})
        ET.SubElement(predicate_element, "parameters").text = parameters
        expression_element = ET.SubElement(predicate_element, "expression")
        ET.SubElement(expression_element, "functional").text = functional

    def add_function(self, name, parameters, functional):
        """Adds a single function element with parameters and functional expression."""
        functions_element = self.instance.find("functions")
        if (functions_element is None):
            functions_element = ET.SubElement(self.instance, "functions")
        
        function_element = ET.SubElement(functions_element, "function", {"name": name, "return": "int"})
        ET.SubElement(function_element, "parameters").text = parameters
        ET.SubElement(function_element, "expression").text = functional

    def add_constraint(self, name, arity, scope, reference, parameters):
        """Adds a single constraint element with arity, scope and reference."""
        constraints_element = self.instance.find("constraints")
        if (constraints_element is None):
            constraints_element = ET.SubElement(self.instance, "constraints")
        
        constraint_element = ET.SubElement(constraints_element, "constraint", {"name": name, "arity": arity, "scope": scope, "reference": reference})
        ET.SubElement(constraint_element, "parameters").text = parameters

    def find_predicate(self, name):
        """Finds a predicate element by name."""
        predicates_element = self.instance.find("predicates")
        if predicates_element is None:
            predicates_element = ET.SubElement(self.instance, "predicates")
            return False
        else:
            for predicate in predicates_element.findall("predicate"):
                if predicate.attrib["name"] == name:
                    return True
            return False
        
    def find_function(self, name):
        """Finds a function element by name."""
        functions_element = self.instance.find("functions")
        if functions_element is None:
            functions_element = ET.SubElement(self.instance, "functions")
            return False
        else:
            for function in functions_element.findall("function"):
                if function.attrib["name"] == name:
                    return True
            return False

    def add_minimum_capacity_constraint(self, variable_name, min_capacity):
        """Adds an hard constraint to the XML instance that enforces minimum installed capacity."""

        if not isinstance(min_capacity, int):
            raise ValueError("min_capacity must be an integer")
        
        if not self.find_predicate("alreadyInstalledCapacity"):
            self.add_predicate(
                name="alreadyInstalledCapacity", 
                parameters="int capacity int min_capacity", 
                functional=boolean_ge("capacity", "min_capacity")
            )
        
        self.add_constraint(
            name=f"alreadyInstalledCapacity_{variable_name}", 
            arity="1", 
            scope=variable_name, 
            reference="alreadyInstalledCapacity",
            parameters=f"{variable_name} {min_capacity}"
        )

    def add_maximum_capacity_constraint(self, variable_name, max_capacity):
        """Adds an hard constraint to the XML instance that enforces maximum installed capacity."""

        if not isinstance(max_capacity, int):
            raise ValueError("max_capacity must be an integer")
        
        if not self.find_predicate("withinMaxCapacity"):
            self.add_predicate(
                name="withinMaxCapacity", 
                parameters="int capacity int max_capacity", 
                functional=boolean_le("capacity", "max_capacity")
            )
        
        self.add_constraint(
            name=f"withinMaxCapacity_{variable_name}", 
            arity="1", 
            scope=variable_name, 
            reference="withinMaxCapacity",
            parameters=f"{variable_name} {max_capacity}"
        )
    
    def add_minimum_capacity_factor_constraint(self, variable_name, min_capacity_factor):
        """Adds an hard constraint to the XML instance that enforces minimum capacity factor."""

        if not isinstance(min_capacity_factor, int):
            raise ValueError("min_capacity_factor must be an integer")
        
        if not self.find_predicate("minimumCapacityFactor"):
            self.add_predicate(
                name="minimumCapacityFactor", 
                parameters="int capacity_factor int min_capacity_factor", 
                functional=boolean_ge("capacity_factor", "min_capacity_factor")
            )
        
        self.add_constraint(
            name=f"minimumCapacityFactor_{variable_name}", 
            arity="1", 
            scope=variable_name, 
            reference="minimumCapacityFactor",
            parameters=f"{variable_name} {min_capacity_factor}"
        )
        
    def add_maximum_capacity_factor_constraint(self, variable_name, max_capacity_factor):
        """Adds an hard constraint to the XML instance that enforces maximum capacity factor."""

        if not isinstance(max_capacity_factor, int):
            raise ValueError("max_capacity_factor must be an integer")
        
        if not self.find_predicate("maximumCapacityFactor"):
            self.add_predicate(
                name="maximumCapacityFactor", 
                parameters="int capacity_factor int max_capacity_factor", 
                functional=boolean_le("capacity_factor", "max_capacity_factor")
            )
        
        self.add_constraint(
            name=f"maximumCapacityFactor_{variable_name}", 
            arity="1", 
            scope=variable_name, 
            reference="maximumCapacityFactor",
            parameters=f"{variable_name} {max_capacity_factor}"
        )
    
    def add_min_transmission_capacity_constraint(self, transmission_variable_name, min_transmission_capacity):
        """Adds an hard constraint to the XML instance that enforces minimum transmission capacity."""

        if not isinstance(min_transmission_capacity, int):
            raise ValueError("min_transmission_capacity must be an integer")
        
        if not self.find_predicate("minimumTransmissionCapacity"):
            self.add_predicate(
                name="minimumTransmissionCapacity", 
                parameters="int transmission int min_transmission_capacity",
                functional=boolean_ge("transmission", "min_transmission_capacity")
            )
        
        self.add_constraint(
            name=f"minimumTransmissionCapacity_{transmission_variable_name}",
            arity="1",
            scope=transmission_variable_name,
            reference="minimumTransmissionCapacity",
            parameters=f"{transmission_variable_name} {min_transmission_capacity}"
        )
    
    def add_max_transmission_capacity_constraint(self, transmission_variable_name, max_transmission_capacity):
        """Adds an hard constraint to the XML instance that enforces maximum transmission capacity."""
        
        if not isinstance(max_transmission_capacity, int):
            raise ValueError("max_transmission_capacity must be an integer")

        if not self.find_predicate("maximumTransmissionCapacity"):
            self.add_predicate(
                name="maximumTransmissionCapacity", 
                parameters="int transmission int max_transmission_capacity",
                functional=boolean_le("transmission", "max_transmission_capacity")
            )
        
        self.add_constraint(
            name=f"maximumTransmissionCapacity_{transmission_variable_name}",
            arity="1",
            scope=transmission_variable_name,
            reference="maximumTransmissionCapacity",
            parameters=f"{transmission_variable_name} {max_transmission_capacity}"
        )
    
    def add_emission_cap_constraint(self, agents, technolgies_emission_costs, max_emission):
        """Adds an hard constraint to the XML instance that enforces maximum emission."""
        def build_recursive_expression(technolgies_emission_costs):
            technologies = technolgies_emission_costs.keys()
            # Base case: If only one technology remains, return its multiplication
            if len(technologies) == 1:
                tech = technologies[0]
                return f"mul({tech}Capacity, {tech}CapFactor)"

            # Recursive case: Take the first technology, multiply its capacity and factor, then add to the rest
            return add(mul(mul(f"{technologies[0]}Capacity", f"{technologies[0]}CapFactor"), mul(8760, technolgies_emission_costs[technologies[0]])), build_recursive_expression(technologies[1:]))
        
        if not isinstance(max_emission, int):
            raise ValueError("max_emission must be an integer")

        technologies = technolgies_emission_costs.keys()
        variables = [f"{technology}{agent_name}capacity" for technology in technologies for agent_name in agents]
        variables += [f"{technology}{agent_name}capFactor" for technology in technologies for agent_name in agents]
        variables.sort()

        if not self.find_predicate(f"withinMaxEmission_{len(agents)*len(technolgies_emission_costs)}"):
            self.add_predicate(
                name=f"withinMaxEmission_{len(agents)*len(technolgies_emission_costs)}", 
                parameters=" ".join([f"int {variable}" for variable in variables]) + " int max_emission",
                functional=boolean_le(build_recursive_expression(technolgies_emission_costs), "max_emission")
            )

        self.add_constraint(
            name=f"withinMaxEmission_{len(agents)*len(technolgies_emission_costs)}", 
            arity=str(len(variables)), 
            scope=" ".join(variables), 
            reference=f"withinMaxEmission_{len(agents)*len(technolgies_emission_costs)}",
            parameters=f"{' '.join(variables)} {max_emission}"
        )

    def add_demand_constraint_per_agent(self, agent_name, max_demand, technologies):
        """Adds an hard constraint to the XML instance that enforces maximum demand."""
        def build_recursive_expression(technologies):
            """Recursively builds the expression: 
            add(add(mul(tech1Capacity, tech1CapFactor), mul(tech2Capacity, tech2CapFactor)), mul(tech3Capacity, tech3CapFactor))"""
            
            # Base case: If only one technology remains, return its multiplication
            if len(technologies) == 1:
                tech = technologies[0]
                return f"mul({tech}Capacity, {tech}CapFactor)"

            # Recursive case: Take the first technology, multiply its capacity and factor, then add to the rest
            return add(mul(f"{technologies[0]}Capacity", f"{technologies[0]}CapFactor"), build_recursive_expression(technologies[1:]))
            
        if not isinstance(max_demand, int):
            raise ValueError("max_demand must be an integer")
        
        variables = [f"{technology}{agent_name}capacity" for technology in technologies]
        variables += [f"{technology}{agent_name}capFactor" for technology in technologies]

        variables.sort()
        
        if not self.find_predicate("withinMaxDemand"):
            self.add_predicate(
                name="minDemandPerAgent", 
                parameters=" ".join([f"int {variable}" for variable in variables]) + " int max_demand",
                functional=boolean_ge(build_recursive_expression(technologies), "max_demand")
            )
        
        self.add_constraint(
            name=f"minDemandPerAgent_{agent_name}", 
            arity=str(len(variables)), 
            scope=" ".join(variables), 
            reference="minDemandPerAgent",
            parameters=f"{' '.join(variables)} {max_demand}"
        )
    
    def add_operating_cost_minimization_constraint(self, weight, variable_capacity_name, variable_capFactor_name, cost_per_MWh):
        """Adds a soft constraint to the XML instance that enforces maximum operating cost."""

        if not isinstance(weight, int) or not isinstance(cost_per_MWh, int):
            raise ValueError("weight and cost_per_MW must be integers")

        if not self.find_function(f"minimize_operatingCost_{variable_capacity_name.replace('capacity', '')}"):
            self.add_function(
                name=f"minimize_operatingCost_{variable_capacity_name.replace('capacity', '')}", 
                parameters="int weight int capacity int capFactor int hours_per_year int cost_per_MWh",
                # Note: it is negative since the problem wants to minimize the cost and the problem scope is to maximize
                functional= neg(div(mul(mul("capacity", "capFactor"), mul("hours_per_year", "cost_per_MWh")), "weight"))
            )

        self.add_constraint(
            name=f"minimize_operatingCost_{variable_capacity_name.replace('capacity', '')}",
            arity="2",
            scope=f"{variable_capacity_name} {variable_capFactor_name}",
            reference=f"minimize_operatingCost_{variable_capacity_name.replace('capacity', '')}",
            parameters=f"{weight} {variable_capacity_name} {variable_capFactor_name} 8760 {cost_per_MWh}"
        )

    def add_installing_cost_minimization_constraint(self, weight, variable_capacity_name, previous_installed_capacity, cost_per_MW):
        """Adds a soft constraint to the XML instance that enforces maximum installing cost."""

        if not isinstance(weight, int) or not isinstance(cost_per_MW, int):
            raise ValueError("weight and cost_per_MW must be integers")

        if not self.find_function(f"minimize_installingCost_{variable_capacity_name.replace('capacity', '')}"):
            self.add_function(
                name=f"minimize_installingCost_{variable_capacity_name.replace('capacity', '')}", 
                parameters="int weight int capacity int oldCapacity int cost_per_MW",
                # Note: it is negative since the problem wants to minimize the cost and the problem scope is to maximize
                functional= neg(div(mul(sub("capacity", "oldCapacity"), "cost_per_MW"), "weight"))
            )

        self.add_constraint(
            name=f"minimize_installingCost_{variable_capacity_name.replace('capacity', '')}",
            arity="1",
            scope=f"{variable_capacity_name}",
            reference=f"minimize_installingCost_{variable_capacity_name.replace('capacity', '')}",
            parameters=f"{str(weight)} {variable_capacity_name} {previous_installed_capacity} {str(cost_per_MW)}"
        )
    
    def frame_xml(
        self, 
        name="defaultName", 
        max_constraint_arity=1,
        agent_names=None,
        technologies=None
    ):
        
        self.instance = self.create_frodo2_xml_head_instance()
        self.instance = self.add_presentation(self.instance, name, max_constraint_arity, "True", "XCSP 2.1_FRODO")

        self.instance = self.add_agents(self.instance, agent_names)
        self.instance = self.add_domains(self.instance)
        self.instance = self.add_variables(self.instance, technologies, agent_names)

    def print_xml(self, output_file = "defaultName_problem.xml"):
        tree = ET.ElementTre(self.instance)
        tree.write(output_file, encoding="utf-8", xml_declaration=True)

        self.logger.info(f"XML generated and saved to {output_file}")
    def change_max_arity_contraints(self, max_arity):
        self.instance.attrib["maxConstraintArity"] = max_arity

def boolean_not(a):
    return f"not({a})"

def boolean_and(a, b):
    return f"and({a}, {b})"

def boolean_or(a, b):
    return f"or({a}, {b})"

def boolean_xor(a, b):
    return f"xor({a}, {b})"

def boolean_iff(a, b):
    return f"iff({a}, {b})"

def boolean_eq(a, b):
    return f"eq({a}, {b})"

def boolean_ne(a, b):
    return f"ne({a}, {b})"

def boolean_ge(a, b):
    return f"ge({a}, {b})"

def boolean_gt(a, b):
    return f"gt({a}, {b})"

def boolean_le(a, b):
    return f"le({a}, {b})"

def boolean_lt(a, b):
    return f"lt({a}, {b})"

# Integer Expressions
def neg(a):
    return f"neg({a})"

def abs_val(a):
    return f"abs({a})"

def add(a, b):
    return f"add({a}, {b})"

def sub(a, b):
    return f"sub({a}, {b})"

def mul(a, b):
    return f"mul({a}, {b})"

def div(a, b):
    return f"div({a}, {b})"

def mod(a, b):
    return f"mod({a}, {b})"

def pow_val(a, b):
    return f"pow({a}, {b})"

def min_val(a, b):
    return f"min({a}, {b})"

def max_val(a, b):
    return f"max({a}, {b})"

def conditional(if_expr, true_expr, false_expr):
    return f"if({if_expr}, {true_expr}, {false_expr})"

