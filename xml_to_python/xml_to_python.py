import keyword
import os
import uuid
import xml.etree.ElementTree as ET
from collections import defaultdict

import graphviz


def escape_string(value: str) -> str:
    """Escape problematic characters in strings."""
    if not value:
        return None
    return value.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")


def sanitize(name: str) -> str:
    """Sanitize names by removing namespaces and replacing invalid characters."""
    if "}" in name:
        name = name.split("}")[-1]  # Remove namespace
    sanitized_name = ''.join(char if char.isalnum() or char == '_' else '_' for char in name)
    if sanitized_name in keyword.kwlist:  # If sanitized name is a Python keyword
        sanitized_name += '_'  # Add an underscore to avoid conflict
    return sanitized_name


def analyze_structure(root: ET.Element):
    """Analyze the structure of the XML to determine element and attribute counts."""
    element_counts = defaultdict(int)
    potential_fields = defaultdict(set)

    def count_elements(element: ET.Element, parent_name: str = None):
        class_name = sanitize(element.tag).capitalize()

        # Count child elements
        for child in element:
            key = (class_name, sanitize(child.tag.lower()))
            element_counts[key] = max(element_counts[key], len(list(filter(lambda x: x.tag == child.tag, element))))
            potential_fields[class_name].add(sanitize(child.tag.lower()))

        # Count attributes
        for attr in element.attrib:
            key = (class_name, sanitize(attr))
            attr_count = sum(1 for _ in element.attrib if _ == attr)
            element_counts[key] = max(element_counts[key], attr_count)
            potential_fields[class_name].add(sanitize(attr))

        # Recurse into child elements
        for child in element:
            count_elements(child, class_name)

    count_elements(root)

    return element_counts, potential_fields


def has_only_text(class_name: str, element_counts: dict, potential_fields: dict) -> bool:
    """Check if a class has only text and no attributes or child elements."""
    if not potential_fields.get(class_name):
        return True  # No attributes or child elements
    return False


def has_no_attributes(class_name: str, potential_fields: dict) -> bool:
    """Check if a class has no attributes."""
    fields = potential_fields.get(class_name, set())
    return all(field.islower() for field in fields)  # Assuming attributes are lowercase


def is_single_instance(class_name: str, field: str, element_counts: dict) -> bool:
    """Check if a field always has a single instance or multiple instances."""
    key = (class_name, field)
    return element_counts[key] <= 1


def is_class_field(class_name: str, field: str, potential_fields: dict) -> bool:
    """Check if a field of a class represents another class."""
    return field.capitalize() in potential_fields


def define_class(class_name: str, potential_fields: dict, element_counts: dict) -> str:
    """Generate Python class code based on XML structure."""
    lines = [f"class {class_name}(BaseModel):"]
    lines.append("    instances = []  # List to track all instances of this class")
    lines.append("")
    lines.append("    def __init__(self):")
    lines.append("        super().__init__()")

    for field in potential_fields.get(class_name, []):
        if is_class_field(class_name, field, potential_fields):
            if not is_single_instance(class_name, field, element_counts):
                lines.append(f"        self.{field} = []  # List of instances")
            else:
                lines.append(f"        self.{field} = None  # Single instance")
        else:
            if not is_single_instance(class_name, field, element_counts):
                lines.append(f"        self.{field} = []  # List of texts or values")
            else:
                lines.append(f"        self.{field} = None  # Single value")

    lines.append("")
    lines.append("    @classmethod")
    lines.append("    def to_csv(cls):")
    lines.append("        data = [vars(instance) for instance in cls.instances]")
    lines.append(f"        pd.DataFrame(data).to_csv('{class_name}.csv', index=False)")
    lines.append("")
    return "\n".join(lines)


def generate_instance(
        element: ET.Element,
        parent: str,
        class_name: str,
        attributes: dict,
        element_text: str,
        element_counts: dict,
        potential_fields: dict,
        instances: list,
        defined_classes: set
):
    """Generate an instance of a class and recursively handle child elements."""
    # Handle elements with only text (no attributes or children)
    if not attributes and not list(element) and element_text:
        return f"'{escape_string(element_text)}'"

    # Handle elements with no attributes, text, or children
    if not attributes and not list(element) and not element_text:
        return "True"  # Indicate presence as a boolean

    # Define class if not already defined
    if class_name not in defined_classes:
        defined_classes.add(class_name)
        define_class_code = define_class(class_name, potential_fields, element_counts)
        with open(f"generated_code/{class_name.lower()}.py", "w", encoding="utf-8") as file:
            file.write(f"from base_model import BaseModel\nimport pandas as pd\n\n{define_class_code}")

    # Create instance
    instance_name = f"{class_name.lower()}_{uuid.uuid4().hex[:8]}"
    instances.append(f"{instance_name} = {class_name}()")

    # Add attributes to the instance
    for attr, value in attributes.items():
        escaped_value = escape_string(value)
        instances.append(f"{instance_name}.{attr} = '{escaped_value}'")

    # Add text if it exists
    if element_text:
        escaped_text = escape_string(element_text)
        instances.append(f"{instance_name}.text = '{escaped_text}'")

    # Process child elements
    for sub_elem in element:
        sub_instance_or_text, is_class = parse_element(
            sub_elem, element_counts, potential_fields, instances, defined_classes
        )
        sub_elem_name = sanitize(sub_elem.tag.lower())
        key = (class_name, sub_elem_name)
        if element_counts[key] > 1:
            instances.append(
                f"{instance_name}.{sub_elem_name}.append({sub_instance_or_text}{'.uuid' if is_class else ''})")
        else:
            instances.append(f"{instance_name}.{sub_elem_name} = {sub_instance_or_text}{'.uuid' if is_class else ''}")

    return instance_name


def parse_element(
        element: ET.Element,
        element_counts: dict,
        potential_fields: dict,
        instances: list,
        defined_classes: set
):
    """Parse an XML element and generate Python code dynamically."""
    class_name = sanitize(element.tag).capitalize()
    attributes = {sanitize(k): v for k, v in element.attrib.items()}
    sub_elements = list(element)
    element_text = element.text.strip() if element.text and element.text.strip() else None

    # Handle elements with only text
    if not attributes and not sub_elements and element_text:
        return f"'{escape_string(element_text)}'", False

    # Handle elements with no attributes, text, or children
    if not attributes and not sub_elements and not element_text:
        return "False", False  # Indicate absence as a boolean

    return generate_instance(
        element, None, class_name, attributes, element_text, element_counts, potential_fields, instances,
        defined_classes
    ), True


def generate_python_code(xml_file: str, output_dir: str = "generated_code", generate_graph: bool = True):
    """Generate Python classes and a main script from an XML file."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Analyze the XML structure
        element_counts, potential_fields = analyze_structure(root)

        os.makedirs(output_dir, exist_ok=True)

        # Define BaseModel class
        base_model_path = os.path.join(output_dir, "base_model.py")
        with open(base_model_path, "w", encoding="utf-8") as file:
            file.write(
                "\n".join([
                    "import pandas as pd",
                    "import uuid",
                    "",
                    "class BaseModel:",
                    "    instances = []",
                    "",
                    "    def __init__(self):",
                    "        self.uuid = str(uuid.uuid4())",
                    "        self.__class__.instances.append(self)",
                    "",
                ])
            )

        # Generate classes and main script
        defined_classes = set()
        instances = []
        parse_element(root, element_counts, potential_fields, instances, defined_classes)

        # Generate main script
        main_script_path = os.path.join(output_dir, "generated_main.py")
        with open(main_script_path, "w", encoding="utf-8") as file:
            imports = "\n".join([f"from {cls.lower()} import {cls}" for cls in defined_classes])
            file.write(f"{imports}\n\n# Instances\n")
            file.write("\n".join(instances))
            file.write("\n\n# Save all instances to CSV\n")
            file.write("\n".join([f"{cls}.to_csv()" for cls in defined_classes]))

        if generate_graph:
            generate_dependency_graph(output_dir, potential_fields)

        print("Python code has been generated and saved to", output_dir)

    except Exception as e:
        print(f"Error: {e}")


def generate_dependency_graph(output_dir: str, potential_fields: dict):
    """
    Generate a dependency graph of the classes and their relationships and export it as a PDF.
    """
    graph = graphviz.Digraph("Dependencies", format="pdf")  # Set format to PDF
    graph.attr(rankdir="LR")  # Layout from left to right

    # Add nodes and edges
    for class_name, fields in potential_fields.items():
        graph.node(class_name, class_name)  # Add class as a node
        for field in fields:
            # If the field is a reference to another class, add an edge
            if field.capitalize() in potential_fields:
                graph.edge(class_name, field.capitalize())

    # Save and render the graph
    graph_path = os.path.join(output_dir, "class_dependencies")
    graph.render(graph_path)
    print(f"Dependency graph saved as PDF at {graph_path}.pdf")
