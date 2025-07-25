#!/usr/bin/env python3
"""Example usage of the XSD to OpenAPI converter."""

import json
import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import our simple parser functions as a working implementation
from xsd_to_openapi.simple_parser import parse_xsd_simple, convert_to_openapi


def demonstrate_conversion():
    """Demonstrate the XSD to OpenAPI conversion process."""
    print("🚀 XSD to OpenAPI Converter Demo")
    print("=" * 50)
    
    # Define paths (relative to project root)
    project_root = Path(__file__).parent.parent
    xsd_file = project_root / "schemas/afcommand/xsd/AFCommand.xsd"
    output_dir = project_root / "output"
    output_dir.mkdir(exist_ok=True)
    
    if not xsd_file.exists():
        print(f"❌ XSD file not found: {xsd_file}")
        return 1
    
    print(f"📄 Processing: {xsd_file}")
    print(f"📁 Output directory: {output_dir}")
    
    try:
        # Step 1: Parse the XSD schema
        print("\n📊 Step 1: Analyzing XSD Schema")
        print("-" * 30)
        
        xsd_data = parse_xsd_simple(xsd_file)
        
        print(f"Target Namespace: {xsd_data['target_namespace']}")
        print(f"Complex Types Found: {len(xsd_data['complex_types'])}")
        print(f"Simple Types Found: {len(xsd_data['simple_types'])}")
        print(f"Choice Elements Found: {len(xsd_data['choices'])}")
        
        # Show some examples
        print(f"\nComplex Types (first 5):")
        for i, name in enumerate(list(xsd_data['complex_types'].keys())[:5]):
            ct = xsd_data['complex_types'][name]
            choice_count = len(ct['choices'])
            seq_count = len(ct['sequences'])
            print(f"  {i+1}. {name} (choices: {choice_count}, sequences: {seq_count})")
        
        print(f"\nSimple Types:")
        for name, st in xsd_data['simple_types'].items():
            enum_count = len(st['enumerations'])
            restriction_count = len(st['restrictions'])
            print(f"  - {name} (enums: {enum_count}, restrictions: {restriction_count})")
        
        # Step 2: Convert to OpenAPI
        print(f"\n🔄 Step 2: Converting to OpenAPI")
        print("-" * 30)
        
        openapi_spec = convert_to_openapi(xsd_data)
        
        schemas = openapi_spec['components']['schemas']
        print(f"Generated OpenAPI schemas: {len(schemas)}")
        
        # Count schemas with different features
        choice_schemas = []
        enum_schemas = []
        ref_schemas = []
        
        for name, schema in schemas.items():
            if 'oneOf' in schema:
                choice_schemas.append(name)
            if 'enum' in schema:
                enum_schemas.append(name)
            if any('$ref' in str(prop) for prop in schema.get('properties', {}).values()):
                ref_schemas.append(name)
        
        print(f"Schemas with choices (oneOf): {len(choice_schemas)}")
        print(f"Schemas with enumerations: {len(enum_schemas)}")
        print(f"Schemas with references: {len(ref_schemas)}")
        
        # Step 3: Save outputs
        print(f"\n💾 Step 3: Saving Results")
        print("-" * 30)
        
        # Save full OpenAPI spec
        openapi_file = output_dir / "af_command_openapi.json"
        with open(openapi_file, 'w', encoding='utf-8') as f:
            json.dump(openapi_spec, f, indent=2, ensure_ascii=False)
        print(f"📄 Full OpenAPI spec: {openapi_file}")
        
        # Save just the schemas section for easier viewing
        schemas_file = output_dir / "af_command_schemas.json"
        with open(schemas_file, 'w', encoding='utf-8') as f:
            json.dump(schemas, f, indent=2, ensure_ascii=False)
        print(f"📄 Schemas only: {schemas_file}")
        
        # Save analysis report
        report_file = output_dir / "conversion_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("XSD to OpenAPI Conversion Report\n")
            f.write("=" * 35 + "\n\n")
            f.write(f"Source XSD: {xsd_file}\n")
            f.write(f"Target Namespace: {xsd_data['target_namespace']}\n")
            f.write(f"Conversion Date: {__import__('datetime').datetime.now()}\n\n")
            
            f.write(f"XSD Analysis:\n")
            f.write(f"  Complex Types: {len(xsd_data['complex_types'])}\n")
            f.write(f"  Simple Types: {len(xsd_data['simple_types'])}\n")
            f.write(f"  Choice Elements: {len(xsd_data['choices'])}\n\n")
            
            f.write(f"OpenAPI Output:\n")
            f.write(f"  Total Schemas: {len(schemas)}\n")
            f.write(f"  Schemas with oneOf: {len(choice_schemas)}\n")
            f.write(f"  Schemas with enums: {len(enum_schemas)}\n")
            f.write(f"  Schemas with references: {len(ref_schemas)}\n\n")
            
            f.write("Schemas with Choice Elements (oneOf):\n")
            for name in choice_schemas:
                schema = schemas[name]
                f.write(f"  - {name}: {len(schema['oneOf'])} options\n")
            
            f.write("\nEnumeration Schemas:\n")
            for name in enum_schemas:
                schema = schemas[name]
                f.write(f"  - {name}: {schema['enum']}\n")
        
        print(f"📄 Analysis report: {report_file}")
        
        # Step 4: Show key examples
        print(f"\n🎯 Step 4: Key Examples")
        print("-" * 30)
        
        # Show the main AFCommand schema with its choice
        if 'AFCommand' in schemas:
            af_command = schemas['AFCommand']
            print(f"\n📋 AFCommand Schema (main entry point):")
            print(f"  Type: {af_command.get('type', 'object')}")
            if 'properties' in af_command:
                print(f"  Properties: {list(af_command['properties'].keys())}")
            if 'oneOf' in af_command:
                print(f"  Choice options: {len(af_command['oneOf'])}")
                for i, option in enumerate(af_command['oneOf']):
                    props = list(option.get('properties', {}).keys())
                    print(f"    {i+1}. {props}")
        
        # Show a complex choice example
        if 'SubrogationCommand' in schemas:
            subrogation = schemas['SubrogationCommand']
            print(f"\n📋 SubrogationCommand Schema (complex choice):")
            if 'oneOf' in subrogation:
                print(f"  Has {len(subrogation['oneOf'])} command options:")
                for i, option in enumerate(subrogation['oneOf'][:5]):  # Show first 5
                    props = list(option.get('properties', {}).keys())
                    print(f"    {i+1}. {props}")
                if len(subrogation['oneOf']) > 5:
                    print(f"    ... and {len(subrogation['oneOf']) - 5} more")
        
        print(f"\n✅ Conversion completed successfully!")
        print(f"🎉 Key achievement: XSD choice elements converted to OpenAPI oneOf")
        print(f"📁 All outputs saved to: {output_dir}/")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(demonstrate_conversion())