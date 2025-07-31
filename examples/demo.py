#!/usr/bin/env python3
"""Example usage of the XSD to OpenAPI converter."""

import json
import sys
from pathlib import Path

import yaml

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from xsd_to_openapi import XSDConverter


def demonstrate_conversion():
    """Demonstrate the XSD to OpenAPI conversion process."""
    print("🚀 XSD to OpenAPI Converter Demo")
    print("=" * 50)

    # Check for command line argument
    if len(sys.argv) < 2:
        print("❌ Please provide an XSD file as an argument")
        print("Usage: python3 examples/demo.py your_schema.xsd")
        print("\nExample:")
        print("  python3 examples/demo.py /path/to/your/schema.xsd")
        return 1

    xsd_file = Path(sys.argv[1])
    if not xsd_file.exists():
        print(f"❌ XSD file not found: {xsd_file}")
        return 1

    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    print(f"📄 Processing: {xsd_file}")
    print(f"📁 Output directory: {output_dir}")

    try:
        # Step 1: Initialize the converter
        print(f"\n📊 Step 1: Initializing XSD Converter")
        print("-" * 40)

        converter = XSDConverter(
            title=f"Generated API from {xsd_file.stem}",
            version="1.0.0",
            description=f"API generated from XSD: {xsd_file.name}",
        )

        print("✅ Converter initialized")

        # Step 2: Convert XSD to OpenAPI
        print(f"\n🔄 Step 2: Converting XSD to OpenAPI")
        print("-" * 40)

        openapi_spec = converter.convert_file(xsd_file)

        # Analyze the results
        schemas = openapi_spec["components"]["schemas"]
        print(f"✅ Conversion completed!")
        print(f"📊 Generated {len(schemas)} schemas")

        # Count schemas with different features
        choice_schemas = []
        enum_schemas = []
        ref_schemas = []

        for name, schema in schemas.items():
            if "oneOf" in schema:
                choice_schemas.append(name)
            if "enum" in schema:
                enum_schemas.append(name)
            if isinstance(schema, dict) and any(
                "$ref" in str(prop) for prop in schema.get("properties", {}).values()
            ):
                ref_schemas.append(name)

        print(f"  - Schemas with choices (oneOf): {len(choice_schemas)}")
        print(f"  - Schemas with enumerations: {len(enum_schemas)}")
        print(f"  - Schemas with references: {len(ref_schemas)}")

        # Step 3: Save outputs
        print(f"\n💾 Step 3: Saving Results")
        print("-" * 30)

        # Generate output filename based on input
        base_name = xsd_file.stem

        # Save JSON version
        json_file = output_dir / f"{base_name}_openapi.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(openapi_spec, f, indent=2, ensure_ascii=False)
        print(f"📄 OpenAPI JSON: {json_file}")

        # Save YAML version
        yaml_file = output_dir / f"{base_name}_openapi.yaml"
        with open(yaml_file, "w", encoding="utf-8") as f:
            yaml.dump(openapi_spec, f, default_flow_style=False, sort_keys=False)
        print(f"📄 OpenAPI YAML: {yaml_file}")

        # Save analysis report
        report_file = output_dir / f"{base_name}_report.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("XSD to OpenAPI Conversion Report\n")
            f.write("=" * 35 + "\n\n")
            f.write(f"Source XSD: {xsd_file}\n")
            f.write(
                f"Target Namespace: {openapi_spec['info'].get('description', 'N/A')}\n"
            )
            f.write(f"Conversion Date: {__import__('datetime').datetime.now()}\n\n")

            f.write(f"OpenAPI Output:\n")
            f.write(f"  Total Schemas: {len(schemas)}\n")
            f.write(f"  Schemas with oneOf: {len(choice_schemas)}\n")
            f.write(f"  Schemas with enums: {len(enum_schemas)}\n")
            f.write(f"  Schemas with references: {len(ref_schemas)}\n\n")

            if choice_schemas:
                f.write("Schemas with Choice Elements (oneOf):\n")
                for name in choice_schemas:
                    schema = schemas[name]
                    if "oneOf" in schema:
                        f.write(f"  - {name}: {len(schema['oneOf'])} options\n")
                f.write("\n")

            if enum_schemas:
                f.write("Enumeration Schemas:\n")
                for name in enum_schemas:
                    schema = schemas[name]
                    if "enum" in schema:
                        enum_values = schema["enum"][:5]  # Show first 5
                        f.write(f"  - {name}: {enum_values}")
                        if len(schema["enum"]) > 5:
                            f.write(f" (and {len(schema['enum']) - 5} more)")
                        f.write("\n")

        print(f"📄 Analysis report: {report_file}")

        # Step 4: Show key examples
        print(f"\n🎯 Step 4: Key Schema Examples")
        print("-" * 35)

        # Show schemas with complex features first
        example_schemas = []

        # Prioritize schemas with choices
        if choice_schemas:
            example_schemas.extend(choice_schemas[:2])

        # Add enum schemas
        if enum_schemas:
            example_schemas.extend(
                [name for name in enum_schemas[:2] if name not in example_schemas]
            )

        # Add other interesting schemas
        if not example_schemas:
            example_schemas = list(schemas.keys())[:3]

        for schema_name in example_schemas[:3]:  # Show max 3 examples
            schema = schemas[schema_name]
            print(f"\n📋 {schema_name}:")
            print(f"  Type: {schema.get('type', 'N/A')}")

            if "properties" in schema:
                prop_count = len(schema["properties"])
                print(f"  Properties: {prop_count}")
                if prop_count <= 5:
                    for prop_name in schema["properties"]:
                        print(f"    - {prop_name}")
                else:
                    prop_names = list(schema["properties"].keys())[:3]
                    print(f"    - {', '.join(prop_names)} (and {prop_count - 3} more)")

            if "oneOf" in schema:
                print(f"  Choice options: {len(schema['oneOf'])}")

            if "enum" in schema:
                enum_values = schema["enum"][:3]
                print(f"  Enum values: {enum_values}")
                if len(schema["enum"]) > 3:
                    print(f"    (and {len(schema['enum']) - 3} more)")

        print(f"\n✅ Conversion completed successfully!")
        print(f"🎉 Key achievements:")
        print(f"  - XSD schemas converted to OpenAPI format")
        if choice_schemas:
            print(f"  - XSD choice elements converted to OpenAPI oneOf")
        if enum_schemas:
            print(f"  - XSD enumerations preserved")
        print(f"  - {len(ref_schemas)} schemas use references for clean structure")
        print(f"📁 All outputs saved to: {output_dir}/")

        return 0

    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(demonstrate_conversion())
