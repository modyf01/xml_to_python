# README: XML to Python Code Generator

## Overview
This project is a Python-based tool that dynamically generates Python classes, instances, and dependency graphs from a given XML file. The tool analyzes the structure of the XML document and creates Python code that can:

1. Define classes based on the XML structure.
2. Generate instances for each XML element.
3. Export instances to CSV files.
4. Visualize class dependencies as a PDF graph using Graphviz.

## Features
- **Automatic Class Generation**: Generates Python classes with attributes and relationships derived from XML tags and attributes.
- **Instance Creation**: Creates instances for each XML element.
- **CSV Export**: Automatically saves instances to CSV files.
- **Dependency Graph**: Generates a PDF graph of class dependencies using Graphviz.

## Prerequisites

### Python Libraries
This project requires the following Python libraries:
- `os`
- `xml.etree.ElementTree`
- `uuid`
- `collections`
- `keyword`
- `pandas`
- `graphviz`

Install the required libraries using:
```bash
pip install pandas graphviz
```

### Graphviz
The `graphviz` library must be installed on your system for generating dependency graphs. Follow the installation guide for your platform:
- **Ubuntu/Debian**: `sudo apt-get install graphviz`
- **MacOS**: `brew install graphviz`
- **Windows**: Download and install from [Graphviz Download Page](https://graphviz.org/download/).

## Usage

### Example
1. Place your XML file (e.g., `drugbank_partial.xml`) in the project directory.
2. Run the script using:
   ```bash
   python your_script_name.py
   ```

### Main Function
Call the `generate_python_code` function with the path to your XML file:
```python
from your_script_name import generate_python_code

generate_python_code("path_to_your_xml.xml")
```

### Output
The script will generate the following in the `generated_code` directory:
1. **Class Files**: Individual Python files for each class.
2. **Main Script**: A `generated_main.py` file to initialize instances and export them to CSV.
3. **Dependency Graph**: A `class_dependencies.pdf` file visualizing class relationships.

## Functions Explained

### Key Functions

#### `escape_string(value: str) -> str`
Escapes problematic characters (e.g., `\`, `'`, `\n`) in strings.

#### `sanitize(name: str) -> str`
Sanitizes XML tag/attribute names by:
- Removing namespaces.
- Replacing invalid characters with underscores.
- Adding underscores if the name conflicts with Python keywords.

#### `analyze_structure(root: ET.Element)`
Analyzes the XML structure to:
- Count child elements and attributes.
- Identify potential fields for class definitions.

#### `define_class(class_name: str, potential_fields: dict, element_counts: dict) -> str`
Generates Python class code for a given class name based on the XML structure.

#### `generate_instance(...)`
Creates an instance of a class and recursively handles its child elements.

#### `parse_element(...)`
Parses an XML element and generates corresponding Python code dynamically.

#### `generate_python_code(xml_file: str, output_dir: str = "generated_code", generate_graph: bool = True)`
Main function to generate Python code and optional dependency graphs.

#### `generate_dependency_graph(output_dir: str, potential_fields: dict)`
Generates a dependency graph of classes and their relationships, saved as a PDF file.

## Directory Structure
```
project_directory/
|-- your_script_name.py       # Main script
|-- drugbank_partial.xml      # Example XML file
|-- generated_code/           # Output directory
    |-- base_model.py         # Base model class
    |-- generated_main.py     # Main script to initialize instances
    |-- *.py                  # Generated class files
    |-- class_dependencies.pdf # Dependency graph
```

## Customization
You can customize the behavior of the script by modifying:
- **BaseModel Class**: Extend the base model functionality in `base_model.py`.
- **Dependency Graph**: Adjust graph attributes in the `generate_dependency_graph` function.

## Error Handling
If an error occurs, the script prints a detailed error message. Ensure the input XML file is well-formed and adheres to XML standards.

## License
This project is licensed under the MIT License. Feel free to use and modify it as needed.

---

Happy coding!

