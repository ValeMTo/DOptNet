import os
import xml.etree.ElementTree as ET

input_folder = "solutions/SAPP-single-country-limited-technology-2030-ssp5/outputs"
output_file = "solutions/SAPP-single-country-limited-technology-2030-ssp5/combined_solution.xml"

combined_root = ET.Element("solution")

total_valuation = 0
for filename in os.listdir(input_folder):
    if filename.endswith(".xml"):
        file_path = os.path.join(input_folder, filename)
        tree = ET.parse(file_path)
        root = tree.getroot()

        valuation = int(root.attrib.get("valuation", 0))
        total_valuation += valuation

        for assignment in root.findall("assignment"):
            combined_root.append(assignment)

combined_root.set("valuation", str(total_valuation))  # or use "combined"

tree = ET.ElementTree(combined_root)
tree.write(output_file, encoding="utf-8", xml_declaration=True)

print(f"Combined XML saved to: {output_file}")
