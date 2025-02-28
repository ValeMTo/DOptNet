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
    
    def add_presentation(name, maxConstraintArity, maximize, format):
        instance = ET.SubElement(instance, "presentation", {
            "name": name,
            "maxConstraintArity": maxConstraintArity,
            "maximize": maximize,
            "format": format
        })

        return instance
    
    def add_agents(instance, agent_names):
        instance = ET.SubElement(instance, "agents", {"nbAgents": len(agent_names)})
        for agent_name in agent_names:
            ET.SubElement(instance, "agent", {"name": agent_name})
        
        return instance
    
    def add_domains(instance):
        instance = ET.SubElement(instance, "domains")
        #TODO: change the domain values in a more dynamic way
        domain_values = {
            "installed_capacity": range(0, 10000, 100),
            "capacity_factor": range(0, 101, 10),
            "transmission_capacity": range(0, 5000, 50),
        }
        for name, values in domain_values.items():
            ET.SubElement(instance, "domain", {"name": name, "nbValues": str(len(values))}).text = " ".join(map(str, values))


    def add_variables(instance, technologies, countries):
        for technology in technologies:
            for country in countries:
                instance = ET.SubElement(instance, "variable", {"name": f"{technology}_{country}", "domain": "capacity", "agent": country})
                instance = ET.SubElement(instance, "variable", {"name": f"{technology}_{country}_factor", "domain": "capacity_factor", "agent": country})

        # TODO: change once the countries are not only neighboring
        for country in countries:
            for country2 in countries:
                if country != country2:
                    instance = ET.SubElement(instance, "variable", {"name": f"transmission_{country}_{country2}", "domain": "transmission_capacity", "agent": country})

        return instance
    
    def add_constraints(instance):
        raise NotImplementedError()
    
    def add_minimum_capacity_constraint(instance):
        raise NotImplementedError()

    def add_maximum_capacity_constraint(instance):
        raise NotImplementedError()
    
    def add_minimum_capacity_factor_constraint(instance):
        raise NotImplementedError()
    
    def add_maximum_capacity_factor_constraint(instance):
        raise NotImplementedError()
    
    def add_min_transmission_capacity_constraint(instance):
        raise NotImplementedError()
    
    def add_max_transmission_capacity_constraint(instance):
        raise NotImplementedError()
    
    def add_emission_cap_constraint(instance):
        raise NotImplementedError()
    
    def add_demand_constraint(instance):
        raise NotImplementedError()
    
    def add_cost_constraint(instance):
        raise NotImplementedError()
    
    def generate_xml(instance, output_file, xml_declaration=True):
        tree = ET.ElementTree(instance)
        tree.write(output_file, encoding="utf-8", xml_declaration=xml_declaration)



