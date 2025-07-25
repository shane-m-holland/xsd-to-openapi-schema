# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **XSD to OpenAPI Schema Converter** - a Python tool that converts XML Schema Definition (XSD) files to OpenAPI 3.0+ specifications. The primary focus is on properly handling XSD choice elements and converting them to OpenAPI `oneOf` constructs.

## Key Architecture

### Core Components

1. **`src/xsd_to_openapi/converter.py`** - Main conversion engine using xmlschema library
2. **`src/xsd_to_openapi/models.py`** - Data models for OpenAPI schemas and conversion results  
3. **`src/xsd_to_openapi/cli.py`** - Command-line interface
4. **`src/xsd_to_openapi/simple_parser.py`** - Simplified parser using built-in XML library (backup implementation)

### Critical Feature: Choice Element Handling

The core innovation is converting XSD `<xs:choice>` elements to OpenAPI `oneOf`:

```xml
<!-- XSD Choice -->
<xs:choice>
    <xs:element name="creditCard" type="CreditCard"/>
    <xs:element name="bankAccount" type="BankAccount"/>
</xs:choice>
```

Becomes:
```yaml
# OpenAPI oneOf
oneOf:
  - type: object
    properties:
      creditCard:
        $ref: '#/components/schemas/CreditCard'
  - type: object
    properties:
      bankAccount:
        $ref: '#/components/schemas/BankAccount'
```

## Common Development Commands

### Setup and Installation
```bash
# Install dependencies (requires pip)
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Running the Tool

**CLI Usage (when xmlschema is available):**
```bash
# Basic conversion
xsd-to-openapi convert schemas/afcommand/xsd/AFCommand.xsd output.yaml

# JSON output
xsd-to-openapi convert input.xsd output.json --format json

# Validate XSD
xsd-to-openapi validate schemas/afcommand/xsd/AFCommand.xsd

# Analyze schema
xsd-to-openapi info schemas/afcommand/xsd/AFCommand.xsd
```

**Examples and Testing:**
```bash
# Run comprehensive demonstration
python3 examples/demo.py

# Run tests
python3 tests/test_converter.py
```

### Testing and Development
```bash
# Run tests
python3 tests/test_converter.py

# Format code (when available)
black src tests
isort src tests

# Type checking (when available)
mypy src
```

## Schema Structure Understanding

### Domain Context
The test schemas (`schemas/afcommand/xsd/`) represent an insurance/claims domain with:
- **AFCommand.xsd** - Main command schema with extensive choice elements
- **AFCommon.xsd** - Common types and structures  
- **AFTypes.xsd** - Basic type definitions

### Choice Element Patterns
The XSD contains ~20 choice elements representing:
- Command selection (SubrogationCommand vs ArbitrationCommand)
- Payment methods (AutoDamages vs Comprehensive)
- Identity choices (PersonName vs Company)
- Data format choices (BinaryContent vs FileName)

## File Structure

```
├── src/xsd_to_openapi/          # Main package
│   ├── __init__.py
│   ├── converter.py             # Core conversion logic
│   ├── models.py                # Data models
│   ├── cli.py                   # Command-line interface
│   └── simple_parser.py         # Simplified parser (backup)
├── examples/                    # Usage examples
│   └── demo.py                  # Comprehensive demonstration
├── schemas/afcommand/xsd/       # Test XSD files
├── tests/                       # Test files
├── pyproject.toml               # Project configuration
├── requirements.txt             # Dependencies
└── LICENSE                      # MIT license
```

## Key Design Decisions

1. **Dual Implementation**: Both full-featured (xmlschema) and simple (built-in XML) parsers
2. **Choice Priority**: XSD choice elements are the primary conversion target
3. **Reference Handling**: Complex types generate schema references (`$ref`)
4. **Type Mapping**: Comprehensive XSD built-in type to OpenAPI mapping
5. **Validation**: Input XSD validation and output OpenAPI schema validation

## Testing Strategy

Tests focus on:
- Choice element conversion (the key feature)
- Simple type restrictions (length, pattern, min/max)
- Built-in type mappings
- Reference resolution
- Complex type sequences

## Dependencies

**Required:**
- `xmlschema>=2.5.0` - XSD parsing (main implementation)
- `pyyaml>=6.0` - YAML output
- `click>=8.0.0` - CLI framework

**Development:**
- `pytest>=7.0.0` - Testing
- `black>=22.0.0` - Code formatting
- `mypy>=1.0.0` - Type checking

**Note:** The `simple_test.py` implementation works with only Python standard library.