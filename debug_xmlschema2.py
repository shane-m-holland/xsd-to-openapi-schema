#!/usr/bin/env python3
"""Debug script to understand xmlschema complex type structure."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from xmlschema import XMLSchema

def debug_complex_type():
    """Debug the complex type structure."""
    schema = XMLSchema('schemas/afcommand/xsd/AFCommand.xsd')
    
    # Look at AFCommand specifically
    afcommand_type = schema.types['AFCommand']
    print("=== AFCommand Complex Type Debug ===")
    print(f"Type: {type(afcommand_type)}")
    print(f"Attributes: {[attr for attr in dir(afcommand_type) if not attr.startswith('_')]}")
    
    print(f"\nContent: {afcommand_type.content}")
    print(f"Model group: {afcommand_type.model_group}")
    print(f"Content model: {getattr(afcommand_type.content, 'model', 'no model') if afcommand_type.content else 'no content'}")
    
    if afcommand_type.content:
        print(f"Content type class: {type(afcommand_type.content)}")
        print(f"Content iterable: {hasattr(afcommand_type.content, '__iter__')}")
        if hasattr(afcommand_type.content, '__iter__'):
            print(f"Content children:")
            for i, child in enumerate(afcommand_type.content):
                print(f"  {i}: {type(child)} - {getattr(child, 'name', 'no name')}")
                print(f"    Model: {getattr(child, 'model', 'no model')}")
                if hasattr(child, '__iter__'):
                    print(f"    Children:")
                    for j, grandchild in enumerate(child):
                        print(f"      {j}: {type(grandchild)} - {getattr(grandchild, 'name', 'no name')}")
                        print(f"        Type: {type(getattr(grandchild, 'type', None))}")

if __name__ == "__main__":
    debug_complex_type()