import xml.etree.ElementTree as ET



class XMLGeneratorClass:
    def __init__(self, logger):
        self.logger = logger
        self.logger.info("XML generator initialized")

    def create_frodo2_xml_head_instance():
        instance = ET.Element("instance", {
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "src/frodo2/algorithms/XCSPschemaJaCoP.xsd"
        })

        return instance

# Just an example from cap_factor_three_states -- to delete in the 1.0 version
def EXAMPLE(output_file):
    instance = ET.Element("instance", {
        "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        "xsi:noNamespaceSchemaLocation": "src/frodo2/algorithms/XCSPschemaJaCoP.xsd"
    })

    presentation = ET.SubElement(instance, "presentation", {
        "name": "three_states",
        "maxConstraintArity": "7",
        "maximize": "true",
        "format": "XCSP 2.1_FRODO"
    })

    agents = ET.SubElement(instance, "agents", {"nbAgents": "3"})
    for agent_name in ["a", "b", "c"]:
        ET.SubElement(agents, "agent", {"name": agent_name})

    domains = ET.SubElement(instance, "domains")
    domain_values = {
        "new_capacity": "0 1 2 3 4 5 6 7 8 9 10",
        "capacity_factor": "0 10 20 21 22 30 40 50 60 70 80 90 100",
        "transmission_capacity_AB": "0 500 1000 1500 2000",
        "transmission_capacity_BC": "0 500 1000 1500"
    }
    for name, values in domain_values.items():
        ET.SubElement(domains, "domain", {"name": name, "nbValues": str(len(values.split()))}).text = values

    variables = ET.SubElement(instance, "variables")
    variable_data = [
        ("solarCapacityA", "new_capacity", "a"),
        ("solarCapacityB", "new_capacity", "b"),
        ("solarCapacityC", "new_capacity", "c"),
        ("gasCapacityA", "new_capacity", "a"),
        ("gasCapacityB", "new_capacity", "b"),
        ("gasCapacityC", "new_capacity", "c"),
        ("gasFactorA", "capacity_factor", "a"),
        ("gasFactorB", "capacity_factor", "b"),
        ("gasFactorC", "capacity_factor", "c"),
        ("transmissionAB", "transmission_capacity_AB", "a"),
        ("transmissionBC", "transmission_capacity_BC", "b"),
        ("transmissionBA", "transmission_capacity_AB", "b"),
        ("transmissionCB", "transmission_capacity_BC", "c")
    ]
    for name, domain, agent in variable_data:
        ET.SubElement(variables, "variable", {"name": name, "domain": domain, "agent": agent})

    tree = ET.ElementTree(instance)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)