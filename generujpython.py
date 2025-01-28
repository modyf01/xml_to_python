import xml.etree.ElementTree as ET
import uuid


def escape_string(value):
    """Escape problematic characters in strings."""
    if value is None:
        return None
    return value.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")


def generate_python_code(xml_file):
    """
    Parses an XML file and generates Python code with UUID-based relationships and CSV export.
    Each class has a `to_csv` method to save all instances to a CSV file.
    """
    def strip_namespace(tag):
        return tag.split("}")[-1] if "}" in tag else tag

    def is_repeated(element, parent):
        """Check if an element appears multiple times in its parent."""
        return sum(1 for e in parent if e.tag == element.tag) > 1

    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        python_code = []
        defined_classes = set()
        instances = []
        save_to_csv_code = []  # To store CSV saving code for each class

        def parse_element(element, parent=None):
            class_name = strip_namespace(element.tag).capitalize()
            attributes = element.attrib
            sub_elements = list(element)
            element_text = element.text.strip() if element.text and element.text.strip() else None

            # Define class if not already defined
            if class_name not in defined_classes:
                defined_classes.add(class_name)

                python_code.append(f"class {class_name}(BaseModel):")
                python_code.append("    instances = []  # List to track all instances of this class")
                python_code.append("")
                python_code.append("    def __init__(self):")
                python_code.append("        super().__init__()")

                # Add attributes (single values)
                for attr in attributes.keys():
                    python_code.append(f"        self.{attr.lower()} = None")

                # Add text as a single attribute, if present
                if element_text:
                    python_code.append(f"        self.text = None")

                # Add nested elements
                added_attributes = set()
                for sub_elem in sub_elements:
                    sub_elem_name = strip_namespace(sub_elem.tag).lower()
                    if is_repeated(sub_elem, element):
                        if sub_elem_name not in added_attributes:
                            python_code.append(f"        self.{sub_elem_name}_ids = []  # List of UUIDs")
                            added_attributes.add(sub_elem_name)
                    else:
                        if sub_elem_name not in added_attributes:
                            python_code.append(f"        self.{sub_elem_name}_id = None  # UUID reference")
                            added_attributes.add(sub_elem_name)

                python_code.append("")  # Blank line for readability

                # Add CSV export method
                python_code.append("    @classmethod")
                python_code.append("    def to_csv(cls):")
                python_code.append("        data = [vars(instance) for instance in cls.instances]")
                python_code.append(f"        pd.DataFrame(data).to_csv('{class_name}.csv', index=False)")
                python_code.append("")

                # Add CSV saving code for this class
                save_to_csv_code.append(f"{class_name}.to_csv()")

            # Generate instance creation
            instance_name = f"{class_name.lower()}_{uuid.uuid4().hex[:8]}"
            instance_creation = f"{instance_name} = {class_name}()"
            instances.append(instance_creation)

            # Add attributes to the instance
            for attr, value in attributes.items():
                escaped_value = escape_string(value)
                instances.append(f"{instance_name}.{attr.lower()} = '{escaped_value}'")

            # Add text to the instance, if present
            if element_text:
                escaped_text = escape_string(element_text)
                instances.append(f"{instance_name}.text = '{escaped_text}'")

            # Parse sub-elements recursively and add UUIDs to parent
            for sub_elem in sub_elements:
                sub_instance_name = parse_element(sub_elem, element)
                if is_repeated(sub_elem, element):
                    instances.append(f"{instance_name}.{strip_namespace(sub_elem.tag).lower()}_ids.append({sub_instance_name}.uuid)")
                else:
                    instances.append(f"{instance_name}.{strip_namespace(sub_elem.tag).lower()}_id = {sub_instance_name}.uuid")

            return instance_name

        # Parse root element
        parse_element(root)

        # Combine class definitions, instances, and CSV export
        return "\n".join(
            [
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
            ]
            + python_code
            + ["\n# Instances"]
            + instances
            + ["\n# Save all instances to CSV"]
            + save_to_csv_code
        )

    except Exception as e:
        return f"Error: {e}"

# Example usage
xml_file_path = "test_xml.xml"  # Replace with the path to your XML file
generated_code = generate_python_code(xml_file_path)

# Save the generated code to a file or print it
output_file_path = "generated_code.py"  # Replace with the desired output path
with open(output_file_path, "w") as file:
    file.write(generated_code)

print("Python code has been generated and saved to", output_file_path)
