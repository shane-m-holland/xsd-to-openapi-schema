"""Main XSD to OpenAPI converter implementation."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import xmlschema
from xmlschema import XMLSchema

from .models import (
    ChoiceElement,
    OpenAPIDocument,
    OpenAPISchema,
    SchemaInfo,
    ValidationResult,
    XSDType,
)


class XSDConverter:
    """Converts XSD schemas to OpenAPI specifications."""

    def __init__(
        self,
        title: Optional[str] = None,
        version: str = "1.0.0",
        description: Optional[str] = None,
        validate_output: bool = True,
    ):
        """Initialize the converter.
        
        Args:
            title: OpenAPI specification title
            version: API version
            description: API description
            validate_output: Whether to validate generated OpenAPI schema
        """
        self.title = title
        self.version = version
        self.description = description
        self.validate_output = validate_output
        self.schema: Optional[XMLSchema] = None
        self._type_mappings: Dict[str, OpenAPISchema] = {}
        self._processed_types: set = set()

    def convert_file(self, xsd_file: Path) -> Dict[str, Any]:
        """Convert an XSD file to OpenAPI specification.
        
        Args:
            xsd_file: Path to the XSD file
            
        Returns:
            OpenAPI specification as dictionary
        """
        self.schema = XMLSchema(str(xsd_file))
        return self._convert_schema()

    def convert_string(self, xsd_content: str) -> Dict[str, Any]:
        """Convert XSD content string to OpenAPI specification.
        
        Args:
            xsd_content: XSD content as string
            
        Returns:
            OpenAPI specification as dictionary
        """
        self.schema = XMLSchema(xsd_content)
        return self._convert_schema()

    def validate_xsd(self, xsd_file: Path) -> ValidationResult:
        """Validate an XSD file for conversion compatibility.
        
        Args:
            xsd_file: Path to the XSD file
            
        Returns:
            Validation result
        """
        try:
            schema = XMLSchema(str(xsd_file))
            warnings = []
            
            # Check for unsupported features
            if schema.substitution_groups:
                warnings.append("Substitution groups found - may not convert perfectly")
            
            # Check for complex inheritance patterns
            for type_name, type_def in schema.types.items():
                if hasattr(type_def, 'is_complex') and type_def.is_complex() and hasattr(type_def, 'base_type') and type_def.base_type:
                    if hasattr(type_def, 'derivation') and type_def.derivation == "extension":
                        warnings.append(f"Complex type extension found in {type_name}")
            
            return ValidationResult(is_valid=True, warnings=warnings)
            
        except Exception as e:
            return ValidationResult(is_valid=False, errors=[str(e)])

    def analyze_schema(self, xsd_file: Path) -> SchemaInfo:
        """Analyze an XSD schema and return information about it.
        
        Args:
            xsd_file: Path to the XSD file
            
        Returns:
            Schema information
        """
        schema = XMLSchema(str(xsd_file))
        info = SchemaInfo()
        
        info.target_namespace = schema.target_namespace
        info.element_form_default = schema.element_form_default
        info.attribute_form_default = schema.attribute_form_default
        
        # Count elements
        for type_name, type_def in schema.types.items():
            if hasattr(type_def, 'is_complex') and type_def.is_complex():
                info.complex_types_count += 1
                info.complex_types.append(type_name)
            elif hasattr(type_def, 'is_simple') and type_def.is_simple():
                info.simple_types_count += 1
                info.simple_types.append(type_name)
        
        info.global_elements_count = len(schema.elements)
        info.global_elements = list(schema.elements.keys())
        
        # Count choice elements
        info.choice_elements_count = self._count_choice_elements(schema)
        
        # Get imports and includes
        for imp in schema.imports:
            info.imports.append(imp.namespace or imp.schema_location)
            info.imports_count += 1
            
        for inc in schema.includes:
            info.includes.append(inc.schema_location)
            info.includes_count += 1
        
        return info

    def _convert_schema(self) -> Dict[str, Any]:
        """Convert the loaded XSD schema to OpenAPI."""
        if not self.schema:
            raise ValueError("No schema loaded")

        # Create OpenAPI document
        doc = OpenAPIDocument()
        
        # Set info
        doc.info = {
            "title": self.title or self._generate_title(),
            "version": self.version,
            "description": self.description or self._generate_description(),
        }
        
        # Initialize components
        doc.components = {"schemas": {}}
        
        # Convert all types
        self._convert_all_types(doc)
        
        # Add placeholder paths (since we're generating schemas, not APIs)
        doc.paths = {}
        
        return doc.to_dict()

    def _generate_title(self) -> str:
        """Generate a title from the schema."""
        if self.schema and self.schema.target_namespace:
            # Extract meaningful name from namespace
            namespace = self.schema.target_namespace
            if "/" in namespace:
                return namespace.split("/")[-1].replace("-", " ").title()
            return namespace.replace(":", " ").title()
        return "Generated API"

    def _generate_description(self) -> str:
        """Generate a description from the schema."""
        if self.schema and self.schema.target_namespace:
            return f"API generated from XSD schema: {self.schema.target_namespace}"
        return "API generated from XSD schema"

    def _convert_all_types(self, doc: OpenAPIDocument) -> None:
        """Convert all types in the schema."""
        if not self.schema:
            return
        
        # FIRST: Convert all named types (components) so they're available for referencing
        for type_name, type_def in self.schema.types.items():
            if type_name not in self._processed_types:
                clean_name = self._clean_element_name(type_name)
                # Convert without referencing (since we're creating the components)
                schema = self._convert_type(type_def, None)  # Pass None to avoid self-reference
                if schema:
                    # Add XML metadata for named types
                    if not schema.xml:
                        schema.xml = {}
                    schema.xml["name"] = clean_name
                    if self.schema.target_namespace:
                        schema.xml["namespace"] = self.schema.target_namespace
                    
                    doc.components["schemas"][clean_name] = schema.to_dict()
                    self._processed_types.add(clean_name)
            
        # SECOND: Convert global elements (now they can reference the components)
        for elem_name, element in self.schema.elements.items():
            clean_elem_name = self._clean_element_name(elem_name)
            # Skip if element has same name as a type (avoid duplicate/self-reference)
            if clean_elem_name not in self._processed_types:
                schema = self._convert_element(element)
                if schema:
                    doc.components["schemas"][clean_elem_name] = schema.to_dict()

    def _convert_element(self, element: Any) -> Optional[OpenAPISchema]:
        """Convert an XSD element to OpenAPI schema."""
        schema = OpenAPISchema()
        
        # Handle element name and documentation
        if element.annotation and element.annotation.documentation:
            schema.description = self._extract_documentation(element.annotation.documentation[0])
        
        # Add XML metadata
        if hasattr(element, 'name') and element.name:
            clean_name = self._clean_element_name(element.name)
            xml_metadata = {"name": clean_name}
            
            # Add namespace if present
            if hasattr(element, 'target_namespace') and element.target_namespace:
                xml_metadata["namespace"] = element.target_namespace
            elif self.schema and self.schema.target_namespace:
                xml_metadata["namespace"] = self.schema.target_namespace
            
            schema.xml = xml_metadata
        
        # Handle type
        if element.type:
            type_name = getattr(element.type, 'name', None)
            
            # Check if this should be a reference to a component schema
            if type_name and self._should_use_reference(type_name):
                clean_name = self._clean_element_name(type_name)
                schema.ref = f"#/components/schemas/{clean_name}"
                # Note: XML metadata is preserved in the element's XML metadata set earlier
            else:
                # Handle inline types (anonymous complex types or built-in types)
                if hasattr(element.type, 'base_type') or hasattr(element.type, 'content_type'):
                    type_schema = self._convert_type(element.type)
                    if type_schema:
                        # Merge type schema properties
                        if type_schema.ref:
                            schema.ref = type_schema.ref
                        else:
                            schema = type_schema
                            
                else:
                    # Built-in or domain-specific type
                    if type_name:
                        clean_name = self._clean_element_name(type_name)
                        
                        # Try domain-specific type first
                        domain_schema = self._convert_domain_type(type_name)
                        if domain_schema:
                            schema = domain_schema
                        else:
                            # Fall back to built-in type
                            schema = self._convert_builtin_type(clean_name)
                    else:
                        schema = self._convert_builtin_type('string')
        
        # Handle nullable (minOccurs=0) and nillable
        if getattr(element, 'min_occurs', 1) == 0:
            schema.x_nullable = True
            if schema.xml:
                schema.xml["nillable"] = True
        elif getattr(element, 'nillable', False):
            if schema.xml:
                schema.xml["nillable"] = True
            
        # Handle array (maxOccurs > 1)
        max_occurs = getattr(element, 'max_occurs', 1)
        if max_occurs and max_occurs != 1:
            array_schema = OpenAPISchema(type="array", items=schema)
            if max_occurs != "unbounded":
                array_schema.max_items = int(max_occurs)
            min_occurs = getattr(element, 'min_occurs', 1)
            if min_occurs > 0:
                array_schema.min_items = min_occurs
            return array_schema
            
        return schema

    def _convert_type(
        self, type_def: Any, type_name: Optional[str] = None
    ) -> Optional[OpenAPISchema]:
        """Convert an XSD type definition to OpenAPI schema."""
        # If this is a named type that should be referenced, return a reference
        if type_name and self._should_use_reference(type_name):
            clean_name = self._clean_element_name(type_name)
            return OpenAPISchema(ref=f"#/components/schemas/{clean_name}")
        
        # Use duck typing to identify type classes for inline conversion
        if hasattr(type_def, 'is_simple') and type_def.is_simple():
            return self._convert_simple_type(type_def, type_name)
        elif hasattr(type_def, 'is_complex') and type_def.is_complex():
            return self._convert_complex_type(type_def, type_name)
        return None

    def _convert_simple_type(
        self, simple_type: Any, type_name: Optional[str] = None
    ) -> OpenAPISchema:
        """Convert an XSD simple type to OpenAPI schema."""
        schema = OpenAPISchema()
        
        # Add documentation
        if simple_type.annotation and simple_type.annotation.documentation:
            schema.description = self._extract_documentation(simple_type.annotation.documentation[0])
        
        # Add XML metadata for named types
        if type_name:
            clean_name = self._clean_element_name(type_name)
            xml_metadata = {"name": clean_name}
            if self.schema and self.schema.target_namespace:
                xml_metadata["namespace"] = self.schema.target_namespace
            schema.xml = xml_metadata
        
        # Handle base type
        if simple_type.base_type:
            base_schema = self._convert_builtin_type(simple_type.base_type.name)
            schema.type = base_schema.type
            schema.format = base_schema.format
        
        # First, try structural analysis for unions and restrictions
        # Handle unions - use structural analysis instead of generic conversion
        if hasattr(simple_type, 'member_types') and simple_type.member_types:
            union_schema = self._analyze_union_constraints(simple_type)
            if union_schema:
                # Preserve any documentation that was set
                if simple_type.annotation and simple_type.annotation.documentation:
                    doc = self._extract_documentation(simple_type.annotation.documentation[0])
                    if doc:
                        union_schema.description = doc
                # Preserve XML metadata
                if schema.xml:
                    union_schema.xml = schema.xml
                return union_schema

        # Handle domain-specific types by name as fallback
        if type_name:
            domain_schema = self._convert_domain_type(type_name)
            if domain_schema:
                # Use domain schema completely, don't merge
                schema = domain_schema
                # But preserve any documentation that was set
                if simple_type.annotation and simple_type.annotation.documentation:
                    doc = self._extract_documentation(simple_type.annotation.documentation[0])
                    if doc:
                        schema.description = doc
                # Preserve XML metadata
                if type_name:
                    clean_name = self._clean_element_name(type_name)
                    xml_metadata = {"name": clean_name}
                    if self.schema and self.schema.target_namespace:
                        xml_metadata["namespace"] = self.schema.target_namespace
                    schema.xml = xml_metadata
                # Skip further processing for domain types
                return schema
        
        # Handle restrictions - clean facet names first
        if hasattr(simple_type, "facets") and simple_type.facets:
            cleaned_facets = {}
            for facet_name, facet in simple_type.facets.items():
                if facet_name:  # Ensure facet_name is not None
                    clean_facet_name = self._clean_element_name(facet_name)
                    cleaned_facets[clean_facet_name] = facet
            self._apply_facets(schema, cleaned_facets)
        
        # Handle enumerations
        if hasattr(simple_type, "enumeration") and simple_type.enumeration:
            schema.enum = []
            for facet in simple_type.enumeration:
                if hasattr(facet, 'value'):
                    schema.enum.append(facet.value)
                else:
                    schema.enum.append(str(facet))
            
        
        return schema

    def _convert_complex_type(
        self, complex_type: Any, type_name: Optional[str] = None
    ) -> OpenAPISchema:
        """Convert an XSD complex type to OpenAPI schema."""
        # If this is a named type that we've seen before, return a reference
        if type_name and type_name in self._processed_types:
            return OpenAPISchema(ref=f"#/components/schemas/{type_name}")
        
        schema = OpenAPISchema(type="object")
        
        # Add documentation
        if complex_type.annotation and complex_type.annotation.documentation:
            schema.description = self._extract_documentation(complex_type.annotation.documentation[0])
        
        # Add XML metadata for named types
        if type_name:
            clean_name = self._clean_element_name(type_name)
            xml_metadata = {"name": clean_name}
            if self.schema and self.schema.target_namespace:
                xml_metadata["namespace"] = self.schema.target_namespace
            schema.xml = xml_metadata
        
        schema.properties = {}
        schema.required = []
        
        # Handle content model - use 'content' instead of 'content_type'
        if hasattr(complex_type, 'content') and complex_type.content:
            self._process_content_model(complex_type.content, schema)
        
        # Handle attributes
        if hasattr(complex_type, "attributes"):
            for attr in complex_type.attributes.values():
                if hasattr(attr, 'name') and hasattr(attr, 'type'):
                    attr_schema = self._convert_attribute(attr)
                    if attr_schema:
                        clean_name = self._clean_element_name(attr.name)
                        # Mark as XML attribute
                        if not attr_schema.xml:
                            attr_schema.xml = {}
                        attr_schema.xml["attribute"] = True
                        attr_schema.xml["name"] = clean_name
                        
                        schema.properties[clean_name] = attr_schema
                        if getattr(attr, 'use', None) == "required":
                            schema.required.append(clean_name)
        
        # Mark type as processed if it has a name
        if type_name:
            self._processed_types.add(type_name)
        
        return schema

    def _process_content_model(self, content: Any, schema: OpenAPISchema) -> None:
        """Process the content model of a complex type."""
        # Use duck typing to identify content model types
        if hasattr(content, 'model') and content.model == 'sequence':
            self._process_sequence(content, schema)
        elif hasattr(content, 'model') and content.model == 'choice':
            self._process_choice(content, schema)
        elif hasattr(content, 'model') and hasattr(content, 'iter_elements'):
            # Generic group handling
            if content.model:
                self._process_content_model(content.model, schema)
        else:
            # Fallback: iterate through elements if possible
            if hasattr(content, '__iter__'):
                for item in content:
                    if hasattr(item, 'name'):  # Element
                        elem_schema = self._convert_element(item)
                        if elem_schema:
                            clean_name = self._clean_element_name(item.name)
                            schema.properties[clean_name] = elem_schema
                            if getattr(item, 'min_occurs', 1) > 0:
                                schema.required.append(clean_name)

    def _process_sequence(self, sequence: Any, schema: OpenAPISchema) -> None:
        """Process an XSD sequence."""
        for item in sequence:
            if hasattr(item, 'name') and hasattr(item, 'type'):  # Element
                elem_schema = self._convert_element(item)
                if elem_schema:
                    clean_name = self._clean_element_name(item.name)
                    schema.properties[clean_name] = elem_schema
                    if getattr(item, 'min_occurs', 1) > 0:
                        schema.required.append(clean_name)
            elif hasattr(item, 'model') and item.model == 'choice':  # Choice
                self._process_choice(item, schema)
            elif hasattr(item, 'model'):  # Other group types
                self._process_content_model(item, schema)

    def _process_choice(self, choice: Any, schema: OpenAPISchema) -> None:
        """Process an XSD choice element - this is the key feature!"""
        choice_schemas = []
        
        for item in choice:
            if hasattr(item, 'name') and hasattr(item, 'type'):  # Element
                elem_schema = self._convert_element(item)
                if elem_schema:
                    # Wrap element in an object schema
                    clean_name = self._clean_element_name(item.name)
                    choice_option = OpenAPISchema(
                        type="object",
                        properties={clean_name: elem_schema}
                    )
                    if getattr(item, 'min_occurs', 1) > 0:
                        choice_option.required = [clean_name]
                    choice_schemas.append(choice_option)
        
        if choice_schemas:
            if len(choice_schemas) == 1:
                # Single choice - merge into parent
                choice_schema = choice_schemas[0]
                if choice_schema.properties:
                    schema.properties.update(choice_schema.properties)
                if choice_schema.required:
                    schema.required.extend(choice_schema.required)
            else:
                # Multiple choices - use oneOf
                if not schema.one_of:
                    schema.one_of = []
                schema.one_of.extend(choice_schemas)

    def _convert_attribute(self, attribute: Any) -> Optional[OpenAPISchema]:
        """Convert an XSD attribute to OpenAPI schema."""
        if attribute.type:
            schema = self._convert_type(attribute.type)
            if schema and attribute.annotation and attribute.annotation.documentation:
                schema.description = self._extract_documentation(attribute.annotation.documentation[0])
            return schema
        return None

    def _convert_builtin_type(self, type_name: str) -> OpenAPISchema:
        """Convert XSD built-in types to OpenAPI schema."""
        type_mappings = {
            # String types
            "string": OpenAPISchema(type="string"),
            "normalizedString": OpenAPISchema(type="string"),
            "token": OpenAPISchema(type="string"),
            "language": OpenAPISchema(type="string"),
            "Name": OpenAPISchema(type="string"),
            "NCName": OpenAPISchema(type="string"),
            "ID": OpenAPISchema(type="string"),
            "IDREF": OpenAPISchema(type="string"),
            "IDREFS": OpenAPISchema(type="string"),
            "ENTITY": OpenAPISchema(type="string"),
            "ENTITIES": OpenAPISchema(type="string"),
            "NMTOKEN": OpenAPISchema(type="string"),
            "NMTOKENS": OpenAPISchema(type="string"),
            
            # Numeric types
            "decimal": OpenAPISchema(type="number"),
            "float": OpenAPISchema(type="number", format="float"),
            "double": OpenAPISchema(type="number", format="double"),
            "integer": OpenAPISchema(type="integer"),
            "nonPositiveInteger": OpenAPISchema(type="integer", maximum=0),
            "negativeInteger": OpenAPISchema(type="integer", maximum=-1),
            "long": OpenAPISchema(type="integer", format="int64"),
            "int": OpenAPISchema(type="integer", format="int32"),
            "short": OpenAPISchema(type="integer"),
            "byte": OpenAPISchema(type="integer"),
            "nonNegativeInteger": OpenAPISchema(type="integer", minimum=0),
            "unsignedLong": OpenAPISchema(type="integer", minimum=0),
            "unsignedInt": OpenAPISchema(type="integer", minimum=0),
            "unsignedShort": OpenAPISchema(type="integer", minimum=0),
            "unsignedByte": OpenAPISchema(type="integer", minimum=0),
            "positiveInteger": OpenAPISchema(type="integer", minimum=1),
            
            # Date/time types
            "dateTime": OpenAPISchema(type="string", format="date-time"),
            "date": OpenAPISchema(type="string", format="date"),
            "time": OpenAPISchema(type="string", format="time"),
            "duration": OpenAPISchema(type="string"),
            "gYearMonth": OpenAPISchema(type="string"),
            "gYear": OpenAPISchema(type="string"),
            "gMonthDay": OpenAPISchema(type="string"),
            "gDay": OpenAPISchema(type="string"),
            "gMonth": OpenAPISchema(type="string"),
            
            # Other types
            "boolean": OpenAPISchema(type="boolean"),
            "base64Binary": OpenAPISchema(type="string", format="byte"),
            "hexBinary": OpenAPISchema(type="string", format="binary"),
            "anyURI": OpenAPISchema(type="string", format="uri"),
            "QName": OpenAPISchema(type="string"),
            "NOTATION": OpenAPISchema(type="string"),
        }
        
        return type_mappings.get(type_name, OpenAPISchema(type="string"))
    
    def _convert_domain_type(self, type_name: str) -> Optional[OpenAPISchema]:
        """Convert domain-specific types to appropriate OpenAPI schemas."""
        # Remove namespace prefix if present
        clean_type_name = self._clean_element_name(type_name) if type_name else type_name
        domain_mappings = {
            # Money types - should be numbers with decimal constraints
            "Money": OpenAPISchema(
                type="number",
                format="decimal",
                minimum=-99999999.99,
                maximum=99999999.99,
                multiple_of=0.01
            ),
            "PositiveMoney": OpenAPISchema(
                type="number", 
                format="decimal",
                minimum=0,
                maximum=99999999.99,
                multiple_of=0.01
            ),
            
            # Percentage types
            "Percent": OpenAPISchema(
                type="number",
                minimum=0,
                maximum=100
            ),
            "NonEmptyPercent": OpenAPISchema(
                type="number",
                minimum=0.01,
                maximum=100
            ),
            
            # String constraints with better types
            "Guid": OpenAPISchema(
                type="string",
                format="uuid"
            ),
            "ConversationId": OpenAPISchema(
                type="string",
                format="uuid"
            ),
            
            # Date types  
            "Date": OpenAPISchema(
                type="string",
                format="date"
            ),
            
            # Specific ID types
            "DemandId": OpenAPISchema(
                type="string",
                pattern=r"^\d+$"  # Numeric string
            ),
            "AFCaseId": OpenAPISchema(
                type="string", 
                pattern=r"^\d+$"  # Numeric string
            ),
            "CompanyCaseId": OpenAPISchema(
                type="string",
                pattern=r"^\d+$"  # Numeric string
            ),
            "DocketNo": OpenAPISchema(
                type="string",
                pattern=r"^\d{2}-\d{6}$"  # Format like 25-123456
            ),
            
            # Company codes
            "Cocode": OpenAPISchema(
                type="string",
                pattern=r"^\d{5}$",  # 5-digit company code
                min_length=5,
                max_length=5
            ),
        }
        
        # Return domain mapping if found, otherwise None
        return domain_mappings.get(clean_type_name)

    def _apply_facets(self, schema: OpenAPISchema, facets: Dict[str, Any]) -> None:
        """Apply XSD facets to OpenAPI schema."""
        total_digits = None
        fraction_digits = None
        
        for facet_name, facet in facets.items():
            facet_value = getattr(facet, 'value', facet) if hasattr(facet, 'value') else facet
            
            if facet_name == "length":
                schema.min_length = schema.max_length = facet_value
            elif facet_name == "minLength":
                schema.min_length = facet_value
            elif facet_name == "maxLength":
                schema.max_length = facet_value
            elif facet_name == "pattern":
                schema.pattern = facet_value
            elif facet_name == "minInclusive":
                schema.minimum = facet_value
            elif facet_name == "maxInclusive":
                schema.maximum = facet_value
            elif facet_name == "minExclusive":
                schema.minimum = facet_value
                schema.exclusive_minimum = True
            elif facet_name == "maxExclusive":
                schema.maximum = facet_value
                schema.exclusive_maximum = True
            elif facet_name == "totalDigits":
                total_digits = facet_value
            elif facet_name == "fractionDigits":
                fraction_digits = facet_value
        
        # Apply numeric constraints based on totalDigits and fractionDigits
        if total_digits is not None:
            self._apply_numeric_constraints(schema, total_digits, fraction_digits)

    def _apply_numeric_constraints(self, schema: OpenAPISchema, total_digits: int, fraction_digits: Optional[int] = None) -> None:
        """Apply numeric constraints based on XSD totalDigits and fractionDigits."""
        # If fractionDigits is 0, this is an integer type
        if fraction_digits == 0:
            schema.type = "integer"
            # Set min/max based on total digits
            max_value = 10**total_digits - 1
            schema.minimum = -max_value
            schema.maximum = max_value
        else:
            # This is a decimal type
            schema.type = "number"
            # Calculate precision based on total digits
            if fraction_digits is not None:
                integer_digits = total_digits - fraction_digits
                max_integer_part = 10**integer_digits - 1
                fraction_part = 10**(-fraction_digits)
                max_value = max_integer_part + (1 - fraction_part)
                schema.minimum = -max_value
                schema.maximum = max_value
                schema.multiple_of = fraction_part
            else:
                # Default decimal handling
                max_value = 10**total_digits - 1
                schema.minimum = -max_value
                schema.maximum = max_value

    def _analyze_union_constraints(self, simple_type: Any) -> Optional[OpenAPISchema]:
        """Analyze union types and create appropriate oneOf constructs."""
        if not hasattr(simple_type, 'member_types') or not simple_type.member_types:
            return None
        
        union_schemas = []
        
        for member_type in simple_type.member_types:
            member_schema = OpenAPISchema()
            
            # Get base type and clean namespace
            if hasattr(member_type, 'base_type') and member_type.base_type:
                base_type_name = self._clean_element_name(member_type.base_type.name)
                base_schema = self._convert_builtin_type(base_type_name)
                member_schema.type = base_schema.type
                member_schema.format = base_schema.format
            
            # Apply facets from this member type, cleaning facet names
            if hasattr(member_type, 'facets') and member_type.facets:
                cleaned_facets = {}
                for facet_name, facet in member_type.facets.items():
                    if facet_name:  # Ensure facet_name is not None
                        clean_facet_name = self._clean_element_name(facet_name)
                        cleaned_facets[clean_facet_name] = facet
                self._apply_facets(member_schema, cleaned_facets)
            
            union_schemas.append(member_schema)
        
        if len(union_schemas) == 1:
            return union_schemas[0]
        elif len(union_schemas) > 1:
            return OpenAPISchema(one_of=union_schemas)
        
        return None

    def _count_choice_elements(self, schema: XMLSchema) -> int:
        """Count choice elements in the schema."""
        count = 0
        
        def count_in_component(component):
            nonlocal count
            if hasattr(component, 'model') and component.model == 'choice':
                count += 1
            if hasattr(component, "__iter__"):
                try:
                    for item in component:
                        count_in_component(item)
                except:
                    pass
        
        for type_def in schema.types.values():
            if hasattr(type_def, 'content') and type_def.content:
                count_in_component(type_def.content)
        
        return count

    def _clean_documentation(self, doc: str) -> str:
        """Clean up documentation text."""
        # Remove extra whitespace and normalize
        doc = re.sub(r"\s+", " ", doc.strip())
        # Remove common XML artifacts
        doc = doc.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
        return doc
    
    def _clean_element_name(self, name: str) -> str:
        """Remove namespace prefix from element names."""
        if '}' in name:
            # Remove namespace URI: {http://namespace}ElementName -> ElementName
            return name.split('}')[1]
        return name
    
    def _should_use_reference(self, type_name: str) -> bool:
        """Determine if a type should use a $ref instead of inline definition."""
        if not type_name or not self.schema:
            return False
        
        clean_name = self._clean_element_name(type_name)
        
        # Check if this is a named type in the schema that should be referenced
        if clean_name in self.schema.types:
            return True
            
        # Check if we've already processed this type (it exists in components)
        if clean_name in self._processed_types:
            return True
            
        return False
    
    def _extract_documentation(self, doc_element: Any) -> Optional[str]:
        """Extract documentation text from XML documentation element."""
        if doc_element is None:
            return None
            
        # Try different ways to extract text content
        text_content = None
        
        # Method 1: Direct text attribute
        if hasattr(doc_element, 'text') and doc_element.text:
            text_content = doc_element.text.strip()
        
        # Method 2: String conversion and check if it looks like XML element object
        elif not (str(doc_element).startswith('<Element') and 'documentation' in str(doc_element)):
            # Only use string conversion if it doesn't look like an XML element object
            text_content = str(doc_element).strip()
        
        # Method 3: Try to get text from element tree
        elif hasattr(doc_element, 'tag'):
            try:
                # Try to extract text from XML element
                if doc_element.text:
                    text_content = doc_element.text.strip()
                elif len(doc_element) == 0:
                    # Element has no children, might be empty
                    text_content = ''
            except:
                pass
        
        # Clean and return
        if text_content and text_content.strip():
            return self._clean_documentation(text_content)
        else:
            # Return None instead of empty string or XML object representation
            return None