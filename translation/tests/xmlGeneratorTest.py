import unittest
from translation.xmlGenerator import XMLGeneratorClass
from unittest.mock import MagicMock

import xml.etree.ElementTree as ET
from xml.dom import minidom

PRINT_INTERMIDIATE_XML = True

def to_pretty_xml(element):
    """Returns a pretty-formatted XML string."""
    rough_string = ET.tostring(element, 'utf-8')
    parsed = minidom.parseString(rough_string)
    return parsed.toprettyxml(indent="  ")

class TestXMLGeneratorClass(unittest.TestCase):

    def setUp(self):
        self.logger = MagicMock()
        self.xml_generator = XMLGeneratorClass(self.logger)

    def test_create_frodo2_xml_head_instance(self):
        instance = self.xml_generator.create_frodo2_xml_head_instance()
        self.assertEqual(instance.tag, "instance")
        self.assertEqual(instance.attrib["xmlns:xsi"], "http://www.w3.org/2001/XMLSchema-instance")
        self.assertEqual(instance.attrib["xsi:noNamespaceSchemaLocation"], "src/frodo2/algorithms/XCSPschemaJaCoP.xsd")
        
        if PRINT_INTERMIDIATE_XML:
            print(to_pretty_xml(instance))

    def test_add_presentation(self):
        """Test if <presentation> is correctly added inside <instance>."""
        self.xml_generator.add_presentation("testName", '2', 'true', "XCSP 2.1_FRODO")

        presentation = self.xml_generator.instance.find("presentation")
        self.assertIsNotNone(presentation, "Missing <presentation> element in XML structure")

        self.assertEqual(presentation.attrib["name"], "testName")
        self.assertTrue(presentation.attrib["maxConstraintArity"].isdigit(), "maxConstraintArity should be a numeric string")
        self.assertEqual(presentation.attrib["maximize"], "true")  # Should be lowercase
        self.assertEqual(presentation.attrib["format"], "XCSP 2.1_FRODO")

        if PRINT_INTERMIDIATE_XML:
            print(to_pretty_xml(self.xml_generator.instance))

    def test_add_agents(self):
        """Test if <agents> section is correctly added to the XML."""
        self.xml_generator.add_agents(["agent1", "agent2"])
        agents_element = self.xml_generator.instance.find("agents")
        self.assertIsNotNone(agents_element, "Missing <agents> section")
        
        agent_list = agents_element.findall("agent")
        self.assertEqual(len(agent_list), 2, "Incorrect number of <agent> elements")

        if PRINT_INTERMIDIATE_XML:
            print(to_pretty_xml(self.xml_generator.instance))

    def test_add_domains(self):
        """Test if <domains> section is correctly added to the XML."""
        self.xml_generator.add_domains({
            "domain1": range(1,10),
            "domain2": range(10,25,5),
        })

        domains_element = self.xml_generator.instance.find("domains")
        self.assertIsNotNone(domains_element, "Missing <domains> section")

        domain_list = domains_element.findall("domain")
        self.assertGreater(len(domain_list), 0, "No <domain> elements found")

        if PRINT_INTERMIDIATE_XML:
            print(to_pretty_xml(self.xml_generator.instance))

    def test_add_variables(self):
        """Test if <variables> structure is correctly formatted inside <instance>."""
        technologies = ["solar", "gas"] 
        agents = ["a", "b", "c"]

        self.xml_generator.add_variables(technologies, agents) 
        variables_element = self.xml_generator.instance.find("variables")
        self.assertIsNotNone(variables_element, "Missing <variables> section in XML structure")

        variable_list = variables_element.findall("variable")
        self.assertGreater(len(variable_list), 0, "No <variable> elements found")

        expected_variable_count = len(technologies) * len(agents) * 2 + len(agents) * (len(agents) - 1)
        self.assertEqual(len(variable_list), expected_variable_count, f"Expected {expected_variable_count} variables, found {len(variable_list)}")

        for variable in variable_list:
            name = variable.get("name")
            domain = variable.get("domain")
            agent = variable.get("agent")

            self.assertIsNotNone(name, "Variable is missing 'name' attribute")
            self.assertIsNotNone(domain, "Variable is missing 'domain' attribute")
            self.assertIsNotNone(agent, "Variable is missing 'agent' attribute")

            if "transmission" in name:
                self.assertTrue(domain.startswith("transmission_capacity"), f"Invalid domain for {name}: {domain}")
            elif "capacity" in name:
                self.assertEqual(domain, "capacity_installed", f"Expected 'capacity_installed' for {name}, got {domain}")
            elif "capFactor" in name:
                self.assertEqual(domain, "capacity_factor", f"Expected 'capacity_factor' for {name}, got {domain}")
            else:
                self.fail(f"Unknown variable name: {name}")

        if PRINT_INTERMIDIATE_XML:
            print(to_pretty_xml(self.xml_generator.instance))

    def test_add_predicate(self):
        """Test if <predicate> elements are correctly added inside <predicates>."""
        
        self.xml_generator.add_predicate(
            name="meetDemand",
            parameters="int solarCapacity int gasCapacity int gasFactor int inflow int outflow int demand",
            functional="ge(add(sub(add(mul(solarCapacity, 1000), mul(gasCapacity, mul(gasFactor, 88))), outflow), inflow), demand)"
        )

        predicates_element = self.xml_generator.instance.find("predicates")
        self.assertIsNotNone(predicates_element, "Missing <predicates> section in XML structure")

        predicate_list = predicates_element.findall("predicate")
        self.assertGreater(len(predicate_list), 0, "No <predicate> elements found")

        predicate = predicate_list[0]
        self.assertEqual(predicate.attrib["name"], "meetDemand")
        
        parameters = predicate.find("parameters")
        self.assertIsNotNone(parameters, "Missing <parameters> in <predicate>")
        self.assertEqual(parameters.text, "int solarCapacity int gasCapacity int gasFactor int inflow int outflow int demand")

        expression = predicate.find("expression")
        self.assertIsNotNone(expression, "Missing <expression> in <predicate>")
        
        functional = expression.find("functional")
        self.assertIsNotNone(functional, "Missing <functional> in <expression>")
        self.assertEqual(functional.text, "ge(add(sub(add(mul(solarCapacity, 1000), mul(gasCapacity, mul(gasFactor, 88))), outflow), inflow), demand)")

        if PRINT_INTERMIDIATE_XML:
            print(to_pretty_xml(self.xml_generator.instance))


    def test_add_function(self):
        """Test if <function> elements are correctly added inside <functions>."""
        
        self.xml_generator.add_function(
            name="total_cost",
            parameters="int capacity int factor int operatingCost",
            functional="neg(div(mul(mul(mul(capacity, factor), 8760), operatingCost), 10000))"
        )

        functions_element = self.xml_generator.instance.find("functions")
        self.assertIsNotNone(functions_element, "Missing <functions> section in XML structure")

        function_list = functions_element.findall("function")
        self.assertGreater(len(function_list), 0, "No <function> elements found")

        function = function_list[0]
        self.assertEqual(function.attrib["name"], "total_cost")
        self.assertEqual(function.attrib["return"], "int")

        parameters = function.find("parameters")
        self.assertIsNotNone(parameters, "Missing <parameters> in <function>")
        self.assertEqual(parameters.text, "int capacity int factor int operatingCost")

        expression = function.find("expression")
        self.assertIsNotNone(expression, "Missing <expression> in <function>")
        self.assertEqual(expression.text, "neg(div(mul(mul(mul(capacity, factor), 8760), operatingCost), 10000))")

        if PRINT_INTERMIDIATE_XML:
            print(to_pretty_xml(self.xml_generator.instance))

    def test_add_constraint(self):
        """Test if <constraint> elements are correctly added inside <constraints>."""

        self.xml_generator.add_constraint(
            name="withinInstalledCapacity",
            arity=2,
            scope="capacity max_capacity",
            reference="withinInstalledCapacity",
            parameters="capacity max_capacity"
        )

        constraints_element = self.xml_generator.instance.find("constraints")
        self.assertIsNotNone(constraints_element, "Missing <constraints> section in XML structure")

        constraint_list = constraints_element.findall("constraint")
        self.assertGreater(len(constraint_list), 0, "No <constraint> elements found")

        constraint = constraint_list[0]
        self.assertEqual(constraint.attrib["name"], "withinInstalledCapacity")
        self.assertEqual(constraint.attrib["arity"], "2")
        self.assertEqual(constraint.attrib["scope"], "capacity max_capacity")
        self.assertEqual(constraint.attrib["reference"], "withinInstalledCapacity")

        parameters = constraint.find("parameters")
        self.assertIsNotNone(parameters, "Missing <parameters> in <constraint>")
        self.assertEqual(parameters.text, "capacity max_capacity")

        if PRINT_INTERMIDIATE_XML:
            print(to_pretty_xml(self.xml_generator.instance))


    def test_find_predicate(self):
        """Test the find_predicate method to check if a predicate exists in the XML."""

        self.assertFalse(self.xml_generator.find_predicate("meetDemand"))

        self.xml_generator.add_predicate(
            name="meetDemand",
            parameters="int capacity int demand",
            functional="ge(capacity, demand)"
        )

        self.assertTrue(self.xml_generator.find_predicate("meetDemand"))


    def test_find_function(self):
        """Test the find_function method to check if a function exists in the XML."""

        self.assertFalse(self.xml_generator.find_function("total_cost"))

        self.xml_generator.add_function(
            name="total_cost",
            parameters="int capacity int cost",
            functional="mul(capacity, cost)"
        )

        self.assertTrue(self.xml_generator.find_function("total_cost"))


    def test_add_minimum_capacity_constraint(self):
        """Test if the minimum installed capacity constraint is correctly added."""

        self.xml_generator.add_minimum_capacity_constraint("solarCapacityA", 500)

        predicates_element = self.xml_generator.instance.find("predicates")
        self.assertIsNotNone(predicates_element, "Missing <predicates> section")
        self.assertTrue(self.xml_generator.find_predicate("alreadyInstalledCapacity"))

        constraints_element = self.xml_generator.instance.find("constraints")
        self.assertIsNotNone(constraints_element, "Missing <constraints> section")

        constraint = constraints_element.find("constraint")
        self.assertIsNotNone(constraint, "Missing <constraint> element for alreadyInstalledCapacity")
        self.assertEqual(constraint.attrib["name"], "alreadyInstalledCapacity_solarCapacityA")
        self.assertEqual(constraint.attrib["arity"], "1")
        self.assertEqual(constraint.attrib["scope"], "solarCapacityA")
        self.assertEqual(constraint.attrib["reference"], "alreadyInstalledCapacity")

        parameters = constraint.find("parameters")
        self.assertIsNotNone(parameters, "Missing <parameters> in constraint")
        self.assertEqual(parameters.text, "solarCapacityA 500")

        if PRINT_INTERMIDIATE_XML:
            print(to_pretty_xml(self.xml_generator.instance))

    def test_add_maximum_capacity_factor_constraint(self):
        """Test if the maximum capacity factor constraint is correctly added."""

        self.xml_generator.add_maximum_capacity_factor_constraint("gasFactorA", 90)

        predicates_element = self.xml_generator.instance.find("predicates")
        self.assertIsNotNone(predicates_element, "Missing <predicates> section")
        self.assertTrue(self.xml_generator.find_predicate("maximumCapacityFactor"))

        constraints_element = self.xml_generator.instance.find("constraints")
        self.assertIsNotNone(constraints_element, "Missing <constraints> section")

        constraint = constraints_element.find("constraint")
        self.assertIsNotNone(constraint, "Missing <constraint> element for maximumCapacityFactor")
        self.assertEqual(constraint.attrib["name"], "maximumCapacityFactor_gasFactorA")
        self.assertEqual(constraint.attrib["arity"], "1")
        self.assertEqual(constraint.attrib["scope"], "gasFactorA")
        self.assertEqual(constraint.attrib["reference"], "maximumCapacityFactor")

        parameters = constraint.find("parameters")
        self.assertIsNotNone(parameters, "Missing <parameters> in constraint")
        self.assertEqual(parameters.text, "gasFactorA 90")

        if PRINT_INTERMIDIATE_XML:
            print(to_pretty_xml(self.xml_generator.instance))


    def test_add_min_transmission_capacity_constraint(self):
        """Test if the minimum transmission capacity constraint is correctly added."""

        self.xml_generator.add_min_transmission_capacity_constraint("transmissionAB", 100)

        predicates_element = self.xml_generator.instance.find("predicates")
        self.assertIsNotNone(predicates_element, "Missing <predicates> section")
        self.assertTrue(self.xml_generator.find_predicate("minimumTransmissionCapacity"))

        constraints_element = self.xml_generator.instance.find("constraints")
        self.assertIsNotNone(constraints_element, "Missing <constraints> section")

        constraint = constraints_element.find("constraint")
        self.assertIsNotNone(constraint, "Missing <constraint> element for minimumTransmissionCapacity")
        self.assertEqual(constraint.attrib["name"], "minimumTransmissionCapacity_transmissionAB")
        self.assertEqual(constraint.attrib["arity"], "1")
        self.assertEqual(constraint.attrib["scope"], "transmissionAB")
        self.assertEqual(constraint.attrib["reference"], "minimumTransmissionCapacity")

        parameters = constraint.find("parameters")
        self.assertIsNotNone(parameters, "Missing <parameters> in constraint")
        self.assertEqual(parameters.text, "transmissionAB 100")

        if PRINT_INTERMIDIATE_XML:
            print(to_pretty_xml(self.xml_generator.instance))


    def test_add_max_transmission_capacity_constraint(self):
        """Test if the maximum transmission capacity constraint is correctly added."""

        self.xml_generator.add_max_transmission_capacity_constraint("transmissionBC", 500)

        predicates_element = self.xml_generator.instance.find("predicates")
        self.assertIsNotNone(predicates_element, "Missing <predicates> section")
        self.assertTrue(self.xml_generator.find_predicate("maximumTransmissionCapacity"))

        constraints_element = self.xml_generator.instance.find("constraints")
        self.assertIsNotNone(constraints_element, "Missing <constraints> section")

        constraint = constraints_element.find("constraint")
        self.assertIsNotNone(constraint, "Missing <constraint> element for maximumTransmissionCapacity")
        self.assertEqual(constraint.attrib["name"], "maximumTransmissionCapacity_transmissionBC")
        self.assertEqual(constraint.attrib["arity"], "1")
        self.assertEqual(constraint.attrib["scope"], "transmissionBC")
        self.assertEqual(constraint.attrib["reference"], "maximumTransmissionCapacity")

        parameters = constraint.find("parameters")
        self.assertIsNotNone(parameters, "Missing <parameters> in constraint")
        self.assertEqual(parameters.text, "transmissionBC 500")

        if PRINT_INTERMIDIATE_XML:
            print(to_pretty_xml(self.xml_generator.instance))

    def test_add_demand_constraint_per_agent(self):
        """Test if the demand constraint per agent is correctly added."""

        agent_name = "A"
        max_demand = 10000
        technologies = ["solar", "wind", "gas"]

        self.xml_generator.add_demand_constraint_per_agent(agent_name, max_demand, technologies)
        predicates_element = self.xml_generator.instance.find("predicates")
        self.assertIsNotNone(predicates_element, "Missing <predicates> section")
        self.assertTrue(self.xml_generator.find_predicate("minDemandPerAgent"))

        predicate = predicates_element.find("predicate")
        self.assertIsNotNone(predicate, "Missing <predicate> element for minDemandPerAgent")
        self.assertEqual(predicate.attrib["name"], "minDemandPerAgent")

        parameters = predicate.find("parameters")
        self.assertIsNotNone(parameters, "Missing <parameters> in <predicate>")

        variables = [f"{technology}{agent_name}capacity" for technology in technologies]
        variables += [f"{technology}{agent_name}capFactor" for technology in technologies]
        variables.sort()
        
        expected_parameters = " ".join([f"int {variable}" for variable in variables]) + " int max_demand"
        self.assertEqual(parameters.text, expected_parameters, "Incorrect <parameters> format in <predicate>")

        expression = predicate.find("expression")
        self.assertIsNotNone(expression, "Missing <expression> in <predicate>")

        functional = expression.find("functional")
        self.assertIsNotNone(functional, "Missing <functional> in <expression>")

        # # Build expected functional expression
        # expected_functional = f"ge({build_recursive_expression(technologies)}, max_demand)"
        # self.assertEqual(functional.text, expected_functional, "Incorrect <functional> format in <predicate>")

        constraints_element = self.xml_generator.instance.find("constraints")
        self.assertIsNotNone(constraints_element, "Missing <constraints> section")

        constraint = constraints_element.find("constraint")
        self.assertIsNotNone(constraint, "Missing <constraint> element for minDemandPerAgent")
        self.assertEqual(constraint.attrib["name"], f"minDemandPerAgent_{agent_name}")
        self.assertEqual(constraint.attrib["arity"], str(len(technologies) * 2))
        
        expected_scope = " ".join(variables)
        self.assertEqual(constraint.attrib["scope"], expected_scope, "Incorrect <scope> format in <constraint>")
        self.assertEqual(constraint.attrib["reference"], "minDemandPerAgent")

        parameters = constraint.find("parameters")
        self.assertIsNotNone(parameters, "Missing <parameters> in constraint")
        expected_parameters = f"{expected_scope} {max_demand}"
        self.assertEqual(parameters.text, expected_parameters, "Incorrect <parameters> format in <constraint>")

        if PRINT_INTERMIDIATE_XML:
            print(to_pretty_xml(self.xml_generator.instance))

    def test_add_operating_cost_constraint(self):
        """Test if the operating cost constraint is correctly added."""

        weight = 10000
        variable_capacity_name = "solarAcapacity"
        variable_capFactor_name = "solarAcapFactor"
        cost_per_MWh = 50

        # Add the operating cost constraint
        self.xml_generator.add_operating_cost_minimization_constraint(weight, variable_capacity_name, variable_capFactor_name, cost_per_MWh)

        # Ensure the function is created
        functions_element = self.xml_generator.instance.find("functions")
        self.assertIsNotNone(functions_element, "Missing <functions> section")
        function_name = f"minimize_operatingCost_solarA"
        self.assertTrue(self.xml_generator.find_function(function_name))

        # Find the function element
        function = functions_element.find(f"function[@name='{function_name}']")
        self.assertIsNotNone(function, f"Missing <function> element for {function_name}")

        # Check if parameters are correctly set
        parameters = function.find("parameters")
        self.assertIsNotNone(parameters, "Missing <parameters> in <function>")
        self.assertEqual(parameters.text, "int weight int capacity int capFactor int hours_per_year int cost_per_MWh")

        # Check if expression exists
        expression = function.find("expression")
        self.assertIsNotNone(expression, "Missing <expression> in <function>")
        self.assertEqual(expression.text, "neg(div(mul(mul(capacity, capFactor), mul(hours_per_year, cost_per_MWh)), mul(weight, 100)))")

        # Ensure the constraint is created
        constraints_element = self.xml_generator.instance.find("constraints")
        self.assertIsNotNone(constraints_element, "Missing <constraints> section")

        # Find the constraint element
        constraint = constraints_element.find(f"constraint[@name='{function_name}']")
        self.assertIsNotNone(constraint, f"Missing <constraint> element for {function_name}")
        self.assertEqual(constraint.attrib["arity"], "2")
        self.assertEqual(constraint.attrib["scope"], f"{variable_capacity_name} {variable_capFactor_name}")
        self.assertEqual(constraint.attrib["reference"], function_name)

        # Check if parameters are correctly set
        parameters = constraint.find("parameters")
        self.assertIsNotNone(parameters, "Missing <parameters> in constraint")
        self.assertEqual(parameters.text, f"{weight} {variable_capacity_name} {variable_capFactor_name} 8760 {cost_per_MWh}")

        # Print XML output if enabled
        if PRINT_INTERMIDIATE_XML:
            print(to_pretty_xml(self.xml_generator.instance))

    def test_add_installing_cost_constraint(self):
        """Test if the installing cost constraint is correctly added."""

        weight = 20000
        variable_capacity_name = "windBcapacity"
        previous_installed_capacity = "300"
        cost_per_MW = 1000

        # Add the installing cost constraint
        self.xml_generator.add_installing_cost_minimization_constraint(weight, variable_capacity_name, previous_installed_capacity, cost_per_MW)

        # Ensure the function is created
        functions_element = self.xml_generator.instance.find("functions")
        self.assertIsNotNone(functions_element, "Missing <functions> section")
        function_name = f"minimize_installingCost_windB"
        self.assertTrue(self.xml_generator.find_function(function_name))

        # Find the function element
        function = functions_element.find(f"function[@name='{function_name}']")
        self.assertIsNotNone(function, f"Missing <function> element for {function_name}")

        # Check if parameters are correctly set
        parameters = function.find("parameters")
        self.assertIsNotNone(parameters, "Missing <parameters> in <function>")
        self.assertEqual(parameters.text, "int weight int capacity int oldCapacity int cost_per_MW")

        # Check if expression exists
        expression = function.find("expression")
        self.assertIsNotNone(expression, "Missing <expression> in <function>")
        self.assertEqual(expression.text, "neg(div(mul(sub(capacity, oldCapacity), cost_per_MW), weight))")

        # Ensure the constraint is created
        constraints_element = self.xml_generator.instance.find("constraints")
        self.assertIsNotNone(constraints_element, "Missing <constraints> section")

        # Find the constraint element
        constraint = constraints_element.find(f"constraint[@name='{function_name}']")
        self.assertIsNotNone(constraint, f"Missing <constraint> element for {function_name}")
        self.assertEqual(constraint.attrib["arity"], "1")
        self.assertEqual(constraint.attrib["scope"], f"{variable_capacity_name}")
        self.assertEqual(constraint.attrib["reference"], function_name)

        # Check if parameters are correctly set
        parameters = constraint.find("parameters")
        self.assertIsNotNone(parameters, "Missing <parameters> in constraint")
        self.assertEqual(parameters.text, f"{weight} {variable_capacity_name} {previous_installed_capacity} {cost_per_MW}")

        # Print XML output if enabled
        if PRINT_INTERMIDIATE_XML:
            print(to_pretty_xml(self.xml_generator.instance))


    # def test_frame_xml(self):
    #     self.xml_generator.frame_xml(name="testName", max_constraint_arity=2, agent_names=["agent1", "agent2"], technologies=["tech1"])
    #     self.assertIsNotNone(self.xml_generator.instance)
    #     print(to_pretty_xml(self.xml_generator.instance))

    # def test_print_xml(self):
    #     self.xml_generator.frame_xml(name="testName", max_constraint_arity=2, agent_names=["agent1", "agent2"], technologies=["tech1"])
    #     self.xml_generator.print_xl(output_file="test_output.xml")
    #     self.logger.info.assert_called_with("XML generated and saved to test_output.xml")
    #     print(to_pretty_xml(self.xml_generator.instance))

if __name__ == '__main__':
    unittest.main()