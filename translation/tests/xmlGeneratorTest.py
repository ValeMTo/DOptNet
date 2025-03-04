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
            elif "Capacity" in name:
                self.assertEqual(domain, "capacity_installed", f"Expected 'capacity_installed' for {name}, got {domain}")
            elif "CapFactor" in name:
                self.assertEqual(domain, "capacity_factor", f"Expected 'capacity_factor' for {name}, got {domain}")

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
            arity="2",
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

        self.xml_generator.add_minimum_capacity_constraint("solarCapacityA", "500")

        predicates_element = self.xml_generator.instance.find("predicates")
        self.assertIsNotNone(predicates_element, "Missing <predicates> section")
        self.assertTrue(self.xml_generator.find_predicate("alreadyInstalledCapacity"))

        constraints_element = self.xml_generator.instance.find("constraints")
        self.assertIsNotNone(constraints_element, "Missing <constraints> section")

        constraint = constraints_element.find("constraint")
        self.assertIsNotNone(constraint, "Missing <constraint> element for alreadyInstalledCapacity")
        self.assertEqual(constraint.attrib["name"], "alreadyInstalledCapacity")
        self.assertEqual(constraint.attrib["arity"], "1")
        self.assertEqual(constraint.attrib["scope"], "solarCapacityA")
        self.assertEqual(constraint.attrib["reference"], "alreadyInstalledCapacity")

        parameters = constraint.find("parameters")
        self.assertIsNotNone(parameters, "Missing <parameters> in constraint")
        self.assertEqual(parameters.text, "solarCapacityA 500")

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