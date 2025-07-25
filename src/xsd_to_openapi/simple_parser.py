#!/usr/bin/env python3
"""Simple test to verify basic functionality without external dependencies."""

import json
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_xsd_simple(xsd_file: Path) -> dict:
    """Simple XSD parser using built-in XML library."""
    tree = ET.parse(xsd_file)
    root = tree.getroot()
    
    # Extract namespace
    ns = {"xs": "http://www.w3.org/2001/XMLSchema"}
    
    # Find all complex types
    complex_types = {}
    for ct in root.findall(".//xs:complexType", ns):
        name = ct.get("name")
        if name:
            complex_types[name] = analyze_complex_type(ct, ns)
    
    # Find all simple types
    simple_types = {}
    for st in root.findall(".//xs:simpleType", ns):
        name = st.get("name")
        if name:
            simple_types[name] = analyze_simple_type(st, ns)
    
    # Find choice elements
    choices = []
    for choice in root.findall(".//xs:choice", ns):
        choices.append(analyze_choice(choice, ns))
    
    return {
        "complex_types": complex_types,
        "simple_types": simple_types, 
        "choices": choices,
        "target_namespace": root.get("targetNamespace"),
    }


def analyze_complex_type(ct, ns):
    """Analyze a complex type element."""
    info = {
        "name": ct.get("name"),
        "elements": [],
        "choices": [],
        "sequences": [],
    }
    
    # Find sequences
    for seq in ct.findall(".//xs:sequence", ns):
        elements = []
        for elem in seq.findall("xs:element", ns):
            elements.append({
                "name": elem.get("name"),
                "type": elem.get("type"),
                "minOccurs": elem.get("minOccurs", "1"),
                "maxOccurs": elem.get("maxOccurs", "1"),
            })
        info["sequences"].append(elements)
    
    # Find choices
    for choice in ct.findall(".//xs:choice", ns):
        info["choices"].append(analyze_choice(choice, ns))
    
    return info


def analyze_simple_type(st, ns):
    """Analyze a simple type element."""
    info = {
        "name": st.get("name"),
        "base": None,
        "restrictions": [],
        "enumerations": [],
    }
    
    # Find restriction
    restriction = st.find("xs:restriction", ns)
    if restriction is not None:
        info["base"] = restriction.get("base")
        
        # Find enumerations
        for enum in restriction.findall("xs:enumeration", ns):
            info["enumerations"].append(enum.get("value"))
        
        # Find other restrictions
        for facet in restriction:
            if facet.tag.endswith("}enumeration"):
                continue  # Already handled
            facet_name = facet.tag.split("}")[-1]
            info["restrictions"].append({
                "type": facet_name,
                "value": facet.get("value")
            })
    
    return info


def analyze_choice(choice, ns):
    """Analyze a choice element.""" 
    elements = []
    for elem in choice.findall("xs:element", ns):
        elements.append({
            "name": elem.get("name"),
            "type": elem.get("type"),
            "minOccurs": elem.get("minOccurs", "1"),
            "maxOccurs": elem.get("maxOccurs", "1"),
        })
    
    return {
        "minOccurs": choice.get("minOccurs", "1"),
        "maxOccurs": choice.get("maxOccurs", "1"),
        "elements": elements,
    }


def convert_to_openapi(xsd_data: dict) -> dict:
    """Convert parsed XSD data to basic OpenAPI schema."""
    openapi = {
        "openapi": "3.0.3",
        "info": {
            "title": "Generated API",
            "version": "1.0.0",
            "description": f"Generated from XSD: {xsd_data.get('target_namespace', 'Unknown')}"
        },
        "paths": {},
        "components": {
            "schemas": {}
        }
    }
    
    # Convert complex types
    for name, ct in xsd_data["complex_types"].items():
        schema = {
            "type": "object",
            "properties": {}
        }
        
        # Handle sequences
        for seq in ct["sequences"]:
            for elem in seq:
                prop_schema = convert_element_to_schema(elem)
                schema["properties"][elem["name"]] = prop_schema
        
        # Handle choices - this is the key feature!
        if ct["choices"]:
            choice_schemas = []
            for choice in ct["choices"]:
                choice_options = []
                for elem in choice["elements"]:
                    option = {
                        "type": "object",
                        "properties": {
                            elem["name"]: convert_element_to_schema(elem)
                        }
                    }
                    choice_options.append(option)
                
                if choice_options:
                    if len(choice_options) == 1:
                        # Single option - merge into parent
                        schema["properties"].update(choice_options[0]["properties"])
                    else:
                        # Multiple options - use oneOf
                        schema["oneOf"] = choice_options
        
        openapi["components"]["schemas"][name] = schema
    
    # Convert simple types  
    for name, st in xsd_data["simple_types"].items():
        schema = convert_simple_type_to_schema(st)
        openapi["components"]["schemas"][name] = schema
    
    return openapi


def convert_element_to_schema(elem: dict) -> dict:
    """Convert an XSD element to OpenAPI schema."""
    schema = {"type": "string"}  # Default
    
    elem_type = elem.get("type", "")
    if elem_type:
        if elem_type.startswith("xs:"):
            schema = convert_builtin_type(elem_type[3:])
        else:
            # Reference to custom type
            schema = {"$ref": f"#/components/schemas/{elem_type}"}
    
    # Handle arrays
    if elem.get("maxOccurs") and elem["maxOccurs"] not in ["1", "0"]:
        schema = {
            "type": "array",
            "items": schema
        }
        if elem["maxOccurs"] != "unbounded":
            schema["maxItems"] = int(elem["maxOccurs"])
    
    return schema


def convert_simple_type_to_schema(st: dict) -> dict:
    """Convert a simple type to OpenAPI schema."""
    schema = {"type": "string"}  # Default
    
    if st["base"]:
        if st["base"].startswith("xs:"):
            schema = convert_builtin_type(st["base"][3:])
    
    # Handle enumerations
    if st["enumerations"]:
        schema["enum"] = st["enumerations"]
    
    # Handle restrictions
    for restriction in st["restrictions"]:
        if restriction["type"] == "maxLength":
            schema["maxLength"] = int(restriction["value"])
        elif restriction["type"] == "minLength":
            schema["minLength"] = int(restriction["value"])
        elif restriction["type"] == "pattern":
            schema["pattern"] = restriction["value"]
        elif restriction["type"] == "maxInclusive":
            schema["maximum"] = float(restriction["value"])
        elif restriction["type"] == "minInclusive":
            schema["minimum"] = float(restriction["value"])
    
    return schema


def convert_builtin_type(xsd_type: str) -> dict:
    """Convert XSD built-in types to OpenAPI."""
    mappings = {
        "string": {"type": "string"},
        "int": {"type": "integer", "format": "int32"},
        "long": {"type": "integer", "format": "int64"},
        "decimal": {"type": "number"},
        "double": {"type": "number", "format": "double"},
        "float": {"type": "number", "format": "float"},
        "boolean": {"type": "boolean"},
        "date": {"type": "string", "format": "date"},
        "dateTime": {"type": "string", "format": "date-time"},
        "base64Binary": {"type": "string", "format": "byte"},
    }
    return mappings.get(xsd_type, {"type": "string"})


def main():
    """Test the simple conversion."""
    xsd_file = Path("schemas/afcommand/xsd/AFCommand.xsd")
    
    if not xsd_file.exists():
        print(f"Error: {xsd_file} not found")
        return 1
    
    print(f"Testing simple conversion of {xsd_file}")
    
    try:
        # Parse XSD
        print("📄 Parsing XSD...")
        xsd_data = parse_xsd_simple(xsd_file)
        
        print(f"  Found {len(xsd_data['complex_types'])} complex types")
        print(f"  Found {len(xsd_data['simple_types'])} simple types")
        print(f"  Found {len(xsd_data['choices'])} choice elements")
        print(f"  Target namespace: {xsd_data['target_namespace']}")
        
        # Convert to OpenAPI
        print("\n🔄 Converting to OpenAPI...")
        openapi_spec = convert_to_openapi(xsd_data)
        
        # Save result
        output_file = Path("af_command_simple.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(openapi_spec, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Simple conversion successful! Output saved to {output_file}")
        
        # Show some stats
        schemas = openapi_spec["components"]["schemas"]
        print(f"📈 Generated {len(schemas)} OpenAPI schemas")
        
        # Show schemas with choices
        print("\n📋 Schemas with choices (oneOf):")
        for name, schema in schemas.items():
            if "oneOf" in schema:
                print(f"  - {name}: oneOf with {len(schema['oneOf'])} options")
                for i, option in enumerate(schema['oneOf']):
                    props = list(option.get('properties', {}).keys())
                    print(f"    {i+1}. {', '.join(props)}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())