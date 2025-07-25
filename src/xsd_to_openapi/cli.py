"""Command-line interface for XSD to OpenAPI converter."""

import json
import sys
from pathlib import Path
from typing import Optional

import click
import yaml

from .converter import XSDConverter


@click.group()
@click.version_option(version="0.1.0")
def main() -> None:
    """XSD to OpenAPI Schema Converter.
    
    Convert XML Schema Definition (XSD) files to OpenAPI 3.0+ specifications.
    """
    pass


@main.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.argument("output_file", type=click.Path(path_type=Path))
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["yaml", "json"], case_sensitive=False),
    default="yaml",
    help="Output format (default: yaml)",
)
@click.option(
    "--title",
    default=None,
    help="OpenAPI specification title (default: derived from XSD)",
)
@click.option(
    "--version",
    "api_version",
    default="1.0.0",
    help="API version (default: 1.0.0)",
)
@click.option(
    "--description",
    default=None,
    help="API description (default: derived from XSD)",
)
@click.option(
    "--validate/--no-validate",
    default=True,
    help="Validate generated OpenAPI schema (default: validate)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
def convert(
    input_file: Path,
    output_file: Path,
    output_format: str,
    title: Optional[str],
    api_version: str,
    description: Optional[str],
    validate: bool,
    verbose: bool,
) -> None:
    """Convert XSD file to OpenAPI specification.
    
    INPUT_FILE: Path to the XSD file to convert
    OUTPUT_FILE: Path for the generated OpenAPI specification
    """
    try:
        if verbose:
            click.echo(f"Converting {input_file} to {output_file}")
            click.echo(f"Output format: {output_format}")
        
        # Initialize converter
        converter = XSDConverter(
            title=title,
            version=api_version,
            description=description,
            validate_output=validate,
        )
        
        # Convert XSD to OpenAPI
        if verbose:
            click.echo("Parsing XSD schema...")
        
        openapi_spec = converter.convert_file(input_file)
        
        if verbose:
            click.echo("Generating OpenAPI specification...")
        
        # Write output file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            if output_format.lower() == "json":
                json.dump(openapi_spec, f, indent=2, ensure_ascii=False)
            else:
                yaml.dump(
                    openapi_spec,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )
        
        if verbose:
            click.echo(f"Successfully converted XSD to OpenAPI: {output_file}")
        else:
            click.echo(f"Conversion complete: {output_file}")
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
def validate(input_file: Path) -> None:
    """Validate an XSD file for conversion compatibility.
    
    INPUT_FILE: Path to the XSD file to validate
    """
    try:
        click.echo(f"Validating {input_file}...")
        
        converter = XSDConverter()
        validation_result = converter.validate_xsd(input_file)
        
        if validation_result.is_valid:
            click.echo("✅ XSD file is valid and ready for conversion")
            if validation_result.warnings:
                click.echo("\nWarnings:")
                for warning in validation_result.warnings:
                    click.echo(f"  ⚠️  {warning}")
        else:
            click.echo("❌ XSD file has validation errors:")
            for error in validation_result.errors:
                click.echo(f"  ❌ {error}")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error validating XSD: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
def info(input_file: Path) -> None:
    """Display information about an XSD file.
    
    INPUT_FILE: Path to the XSD file to analyze
    """
    try:
        click.echo(f"Analyzing {input_file}...")
        
        converter = XSDConverter()
        schema_info = converter.analyze_schema(input_file)
        
        click.echo(f"\n📊 Schema Information:")
        click.echo(f"  Target Namespace: {schema_info.target_namespace or 'None'}")
        click.echo(f"  Element Form Default: {schema_info.element_form_default}")
        click.echo(f"  Attribute Form Default: {schema_info.attribute_form_default}")
        
        click.echo(f"\n📈 Statistics:")
        click.echo(f"  Complex Types: {schema_info.complex_types_count}")
        click.echo(f"  Simple Types: {schema_info.simple_types_count}")
        click.echo(f"  Global Elements: {schema_info.global_elements_count}")
        click.echo(f"  Choice Elements: {schema_info.choice_elements_count}")
        click.echo(f"  Imports: {schema_info.imports_count}")
        click.echo(f"  Includes: {schema_info.includes_count}")
        
        if schema_info.imports:
            click.echo(f"\n📥 Imports:")
            for imp in schema_info.imports:
                click.echo(f"  - {imp}")
                
        if schema_info.includes:
            click.echo(f"\n📄 Includes:")
            for inc in schema_info.includes:
                click.echo(f"  - {inc}")
        
    except Exception as e:
        click.echo(f"Error analyzing XSD: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()