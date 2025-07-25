#!/usr/bin/env python3
"""Debug script to understand xmlschema API."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from xmlschema import XMLSchema

def debug_schema():
    """Debug the xmlschema parsing."""
    schema = XMLSchema('schemas/afcommand/xsd/AFCommand.xsd')
    
    print("=== Schema Debug Info ===")
    print(f"Target namespace: {schema.target_namespace}")
    
    # Look at global elements
    print(f"\n=== Global Elements ({len(schema.elements)}) ===")
    for name, element in schema.elements.items():
        print(f"Element: {name}")
        print(f"  Type: {type(element)}")
        print(f"  Element type: {type(element.type) if element.type else None}")
        if hasattr(element.type, 'content_type'):
            print(f"  Content type: {type(element.type.content_type)}")
            if element.type.content_type:
                print(f"  Content model: {getattr(element.type.content_type, 'model', 'no model')}")
                if hasattr(element.type.content_type, '__iter__'):
                    print(f"  Content children: {len(list(element.type.content_type))}")
                    for i, child in enumerate(element.type.content_type):
                        print(f"    {i}: {type(child)} - {getattr(child, 'name', 'no name')}")
                        if hasattr(child, 'model'):
                            print(f"      Model: {child.model}")
        print()
    
    # Look at types
    print(f"\n=== Types ({len(schema.types)}) ===")
    for name, type_def in list(schema.types.items())[:5]:  # First 5
        print(f"Type: {name}")
        print(f"  Type class: {type(type_def)}")
        print(f"  Has content_type: {hasattr(type_def, 'content_type')}")
        if hasattr(type_def, 'content_type') and type_def.content_type:
            print(f"  Content type class: {type(type_def.content_type)}")
            print(f"  Content model: {getattr(type_def.content_type, 'model', 'no model')}")
            if hasattr(type_def.content_type, '__iter__'):
                print(f"  Content children: {len(list(type_def.content_type))}")
                for i, child in enumerate(type_def.content_type):
                    print(f"    {i}: {type(child)} - {getattr(child, 'name', 'no name')}")
                    if hasattr(child, 'model'):
                        print(f"      Model: {child.model}")
        print()

if __name__ == "__main__":
    debug_schema()