# XSD to OpenAPI Schema Converter

A Python tool to convert XML Schema Definition (XSD) files to OpenAPI 3.0+ specifications, with proper handling of XSD choice elements and complex type hierarchies.

## Features

- **XSD Parsing**: Complete support for XSD files including imports and includes
- **Choice Handling**: Converts XSD `<xs:choice>` elements to OpenAPI `oneOf`/`anyOf` constructs
- **Complex Types**: Full support for complex types, sequences, and nested structures
- **Reference Resolution**: Proper handling of type references and circular dependencies
- **Multiple Formats**: Output in both YAML and JSON formats
- **CLI Interface**: Easy-to-use command-line tool

## Prerequisites

- Python 3.8+
- pip package manager

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install the package in development mode:**
   ```bash
   pip install -e .
   ```

   **Note:** After installation, you may need to add `~/.local/bin` to your PATH if the CLI command isn't found:
   ```bash
   export PATH="$HOME/.local/bin:$PATH"
   ```

For development with additional tools:
```bash
pip install -e ".[dev]"
```

## Usage

### Command Line

Convert a single XSD file:
```bash
xsd-to-openapi convert input.xsd output.yaml
```

Convert with JSON output:
```bash
xsd-to-openapi convert input.xsd output.json --format json
```

### Python API

```python
from xsd_to_openapi import XSDConverter

converter = XSDConverter()
openapi_spec = converter.convert_file("schema.xsd")
```

### Examples

See the `examples/` directory for usage examples:

```bash
# Run the demonstration example
python3 examples/demo.py
```

This example processes the included AF Command XSD files and shows the conversion process step-by-step.

## XSD Feature Support

- ✅ Simple types with restrictions (string, numeric, date, etc.)
- ✅ Complex types and sequences
- ✅ Choice elements (`xs:choice` → `oneOf`)
- ✅ Optional and required elements (`minOccurs`, `maxOccurs`)
- ✅ Enumerations
- ✅ String constraints (length, pattern)
- ✅ Numeric constraints (min/max values, decimal places)
- ✅ Schema imports and includes
- ✅ Type inheritance and extensions
- ✅ Attributes
- ✅ Documentation annotations

## Example

Given this XSD:
```xml
<xs:complexType name="Payment">
    <xs:sequence>
        <xs:element name="amount" type="xs:decimal"/>
        <xs:choice>
            <xs:element name="creditCard" type="CreditCard"/>
            <xs:element name="bankAccount" type="BankAccount"/>
        </xs:choice>
    </xs:sequence>
</xs:complexType>
```

Generates this OpenAPI schema:
```yaml
Payment:
  type: object
  required: [amount]
  properties:
    amount:
      type: number
  oneOf:
    - properties:
        creditCard:
          $ref: '#/components/schemas/CreditCard'
    - properties:
        bankAccount:
          $ref: '#/components/schemas/BankAccount'
```

## Development

1. Clone the repository
2. Install development dependencies: `pip install -e ".[dev]"`
3. Run tests: `pytest`
4. Format code: `black src tests`
5. Lint: `flake8 src tests`
6. Type check: `mypy src`

## License

MIT License - see LICENSE file for details.