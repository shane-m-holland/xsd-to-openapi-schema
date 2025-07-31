# 🔄 XSD to OpenAPI Schema Converter

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.0%2B-green)](https://swagger.io/specification/)

A powerful Python tool to convert XML Schema Definition (XSD) files to OpenAPI 3.0+ specifications, with robust handling of XSD choice elements, complex type hierarchies, and built-in type mappings.

## ✨ Features

- **Complete XSD Support**: Full support for XSD files including imports, includes, and complex nested structures
- **Choice Element Conversion**: Converts XSD `<xs:choice>` elements to OpenAPI `oneOf` constructs
- **Built-in Type Handling**: Proper conversion of all XSD built-in types (boolean, date, decimal, etc.)
- **Complex Type Support**: Full support for complex types, sequences, attributes, and inheritance
- **Reference Resolution**: Intelligent handling of type references to generate clean, reusable schemas
- **Constraint Mapping**: Converts XSD restrictions (length, pattern, min/max) to OpenAPI constraints
- **Multiple Formats**: Output in both YAML and JSON formats
- **CLI Interface**: Easy-to-use command-line tool
- **Robust Error Handling**: Graceful handling of edge cases and malformed schemas

## 📋 Prerequisites

- Python 3.8+
- pip package manager

## 🚀 Installation

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

## 💻 Usage

### 🖥️ Command Line

Convert a single XSD file:
```bash
xsd-to-openapi convert input.xsd output.yaml
```

Convert with JSON output:
```bash
xsd-to-openapi convert input.xsd output.json --format json
```

### 🐍 Python API

```python
from xsd_to_openapi import XSDConverter

converter = XSDConverter()
openapi_spec = converter.convert_file("schema.xsd")
```

### 📝 Examples

See the `examples/` directory for usage examples:

```bash
# Run the demonstration example with your own XSD files
python3 examples/demo.py your_schema.xsd
```

The example demonstrates the conversion process step-by-step. You'll need to provide your own XSD files to test with.

## 🎯 XSD Feature Support

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

## 🔍 Conversion Example

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

## 🛠️ Development

### 🔧 Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/user/xsd-to-openapi.git
   cd xsd-to-openapi
   ```

2. **Install development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

### 🧪 Testing

```bash
# Run tests
python3 tests/test_converter.py
# or with pytest if available
pytest
```

### 🎨 Code Quality

```bash
# Format code
black src tests examples

# Sort imports
isort src tests examples

# Type checking (if mypy available)
mypy src
```

### 🏗️ Project Structure

```
src/xsd_to_openapi/     # Main package
├── __init__.py         # Package exports
├── converter.py        # Core conversion logic
├── models.py           # Data models
└── cli.py             # Command-line interface

examples/              # Usage examples
tests/                 # Test files
pyproject.toml         # Project configuration
requirements.txt       # Dependencies
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🐛 Issues

If you encounter any problems or have feature requests, please [open an issue](https://github.com/user/xsd-to-openapi/issues) on GitHub.

## ⭐ Star History

If you find this project useful, please consider giving it a star! ⭐