"""Tests for the XSD to OpenAPI converter."""

import json
import tempfile
from pathlib import Path

# Basic test cases without external dependencies
def test_simple_xsd_parsing():
    """Test basic XSD parsing functionality."""
    # Simple XSD content
    xsd_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           targetNamespace="http://example.com/test"
           elementFormDefault="qualified">
    
    <xs:element name="TestElement" type="TestComplexType"/>
    
    <xs:complexType name="TestComplexType">
        <xs:sequence>
            <xs:element name="name" type="xs:string"/>
            <xs:choice>
                <xs:element name="email" type="xs:string"/>
                <xs:element name="phone" type="xs:string"/>
            </xs:choice>
        </xs:sequence>
    </xs:complexType>
    
    <xs:simpleType name="StatusType">
        <xs:restriction base="xs:string">
            <xs:enumeration value="active"/>
            <xs:enumeration value="inactive"/>
        </xs:restriction>
    </xs:simpleType>
    
</xs:schema>'''
    
    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xsd', delete=False) as f:
        f.write(xsd_content)
        xsd_file = Path(f.name)
    
    try:
        # Import the simple parser from our test script
        import sys
        sys.path.append(str(Path(__file__).parent.parent / "src"))
        from xsd_to_openapi.simple_parser import parse_xsd_simple, convert_to_openapi
        
        # Parse XSD
        xsd_data = parse_xsd_simple(xsd_file)
        
        # Verify parsing results
        assert xsd_data["target_namespace"] == "http://example.com/test"
        assert "TestComplexType" in xsd_data["complex_types"]
        assert "StatusType" in xsd_data["simple_types"]
        assert len(xsd_data["choices"]) > 0
        
        # Convert to OpenAPI
        openapi_spec = convert_to_openapi(xsd_data)
        
        # Verify OpenAPI structure
        assert openapi_spec["openapi"] == "3.0.3"
        assert "components" in openapi_spec
        assert "schemas" in openapi_spec["components"]
        
        schemas = openapi_spec["components"]["schemas"]
        assert "TestComplexType" in schemas
        assert "StatusType" in schemas
        
        # Verify choice handling
        test_type = schemas["TestComplexType"]
        assert "oneOf" in test_type
        assert len(test_type["oneOf"]) == 2
        
        # Verify enumeration handling
        status_type = schemas["StatusType"]
        assert "enum" in status_type
        assert "active" in status_type["enum"]
        assert "inactive" in status_type["enum"]
        
    finally:
        # Clean up
        xsd_file.unlink()


def test_choice_element_conversion():
    """Test that XSD choice elements are correctly converted to oneOf."""
    xsd_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:complexType name="PaymentMethod">
        <xs:choice>
            <xs:element name="creditCard" type="xs:string"/>
            <xs:element name="bankAccount" type="xs:string"/>
            <xs:element name="paypal" type="xs:string"/>
        </xs:choice>
    </xs:complexType>
</xs:schema>'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xsd', delete=False) as f:
        f.write(xsd_content)
        xsd_file = Path(f.name)
    
    try:
        import sys
        sys.path.append(str(Path(__file__).parent.parent / "src"))
        from xsd_to_openapi.simple_parser import parse_xsd_simple, convert_to_openapi
        
        xsd_data = parse_xsd_simple(xsd_file)
        openapi_spec = convert_to_openapi(xsd_data)
        
        payment_method = openapi_spec["components"]["schemas"]["PaymentMethod"]
        
        # Should have oneOf with 3 options
        assert "oneOf" in payment_method
        assert len(payment_method["oneOf"]) == 3
        
        # Each option should be an object with one property
        options = payment_method["oneOf"]
        option_names = []
        for option in options:
            assert option["type"] == "object"
            assert len(option["properties"]) == 1
            option_names.extend(option["properties"].keys())
        
        assert "creditCard" in option_names
        assert "bankAccount" in option_names
        assert "paypal" in option_names
        
    finally:
        xsd_file.unlink()


def test_simple_type_restrictions():
    """Test that simple type restrictions are properly converted."""
    xsd_content = '''<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xs:simpleType name="NameType">
        <xs:restriction base="xs:string">
            <xs:maxLength value="50"/>
            <xs:minLength value="1"/>
            <xs:pattern value="[A-Za-z ]+"/>
        </xs:restriction>
    </xs:simpleType>
    
    <xs:simpleType name="AgeType">
        <xs:restriction base="xs:int">
            <xs:minInclusive value="0"/>
            <xs:maxInclusive value="120"/>
        </xs:restriction>
    </xs:simpleType>
</xs:schema>'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xsd', delete=False) as f:
        f.write(xsd_content)
        xsd_file = Path(f.name)
    
    try:
        import sys
        sys.path.append(str(Path(__file__).parent.parent / "src"))
        from xsd_to_openapi.simple_parser import parse_xsd_simple, convert_to_openapi
        
        xsd_data = parse_xsd_simple(xsd_file)
        openapi_spec = convert_to_openapi(xsd_data)
        
        # Check NameType restrictions
        name_type = openapi_spec["components"]["schemas"]["NameType"]
        assert name_type["type"] == "string"
        assert name_type["maxLength"] == 50
        assert name_type["minLength"] == 1
        assert name_type["pattern"] == "[A-Za-z ]+"
        
        # Check AgeType restrictions
        age_type = openapi_spec["components"]["schemas"]["AgeType"]
        assert age_type["type"] == "integer"
        assert age_type["minimum"] == 0
        assert age_type["maximum"] == 120
        
    finally:
        xsd_file.unlink()


def test_builtin_type_mappings():
    """Test that XSD built-in types are correctly mapped to OpenAPI types."""
    import sys
    sys.path.append(str(Path(__file__).parent.parent / "src"))
    from xsd_to_openapi.simple_parser import convert_builtin_type
    
    # Test string types
    assert convert_builtin_type("string")["type"] == "string"
    
    # Test numeric types
    int_schema = convert_builtin_type("int")
    assert int_schema["type"] == "integer"
    assert int_schema["format"] == "int32"
    
    long_schema = convert_builtin_type("long")
    assert long_schema["type"] == "integer"
    assert long_schema["format"] == "int64"
    
    decimal_schema = convert_builtin_type("decimal")
    assert decimal_schema["type"] == "number"
    
    # Test boolean
    assert convert_builtin_type("boolean")["type"] == "boolean"
    
    # Test date types
    date_schema = convert_builtin_type("date")
    assert date_schema["type"] == "string"
    assert date_schema["format"] == "date"
    
    datetime_schema = convert_builtin_type("dateTime")
    assert datetime_schema["type"] == "string"
    assert datetime_schema["format"] == "date-time"


if __name__ == "__main__":
    # Run tests manually if pytest not available
    print("Running tests...")
    
    try:
        test_simple_xsd_parsing()
        print("✅ test_simple_xsd_parsing passed")
    except Exception as e:
        print(f"❌ test_simple_xsd_parsing failed: {e}")
    
    try:
        test_choice_element_conversion()
        print("✅ test_choice_element_conversion passed")
    except Exception as e:
        print(f"❌ test_choice_element_conversion failed: {e}")
    
    try:
        test_simple_type_restrictions()
        print("✅ test_simple_type_restrictions passed")
    except Exception as e:
        print(f"❌ test_simple_type_restrictions failed: {e}")
    
    try:
        test_builtin_type_mappings()
        print("✅ test_builtin_type_mappings passed")
    except Exception as e:
        print(f"❌ test_builtin_type_mappings failed: {e}")
    
    print("Tests completed!")