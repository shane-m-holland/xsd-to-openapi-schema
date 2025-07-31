"""Data models for XSD to OpenAPI conversion."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


@dataclass
class OpenAPISchema:
    """Represents an OpenAPI schema object."""

    type: Optional[str] = None
    format: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    enum: Optional[List[Any]] = None
    default: Optional[Any] = None

    # Numeric constraints
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    exclusive_minimum: Optional[bool] = None
    exclusive_maximum: Optional[bool] = None
    multiple_of: Optional[float] = None

    # String constraints
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None

    # Array constraints
    min_items: Optional[int] = None
    max_items: Optional[int] = None
    unique_items: Optional[bool] = None
    items: Optional["OpenAPISchema"] = None

    # Object properties
    properties: Optional[Dict[str, "OpenAPISchema"]] = None
    required: Optional[List[str]] = None
    additional_properties: Optional[Union[bool, "OpenAPISchema"]] = None

    # Composition
    all_of: Optional[List["OpenAPISchema"]] = None
    any_of: Optional[List["OpenAPISchema"]] = None
    one_of: Optional[List["OpenAPISchema"]] = None
    not_schema: Optional["OpenAPISchema"] = None

    # Reference
    ref: Optional[str] = None

    # Extensions
    x_nullable: Optional[bool] = None
    x_xml_name: Optional[str] = None
    x_xml_namespace: Optional[str] = None
    x_xml_prefix: Optional[str] = None
    x_xml_attribute: Optional[bool] = None
    x_xml_wrapped: Optional[bool] = None

    # OpenAPI 3.0 xml metadata (standard, not extension)
    xml: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result: Dict[str, Any] = {}

        # Basic properties
        if self.ref:
            result["$ref"] = self.ref
            return result

        if self.type:
            result["type"] = self.type
        if self.format:
            result["format"] = self.format
        if self.title:
            result["title"] = self.title
        if self.description:
            result["description"] = self.description
        if self.enum is not None:
            result["enum"] = self.enum
        if self.default is not None:
            result["default"] = self.default

        # Numeric constraints
        if self.minimum is not None:
            result["minimum"] = self.minimum
        if self.maximum is not None:
            result["maximum"] = self.maximum
        if self.exclusive_minimum is not None:
            result["exclusiveMinimum"] = self.exclusive_minimum
        if self.exclusive_maximum is not None:
            result["exclusiveMaximum"] = self.exclusive_maximum
        if self.multiple_of is not None:
            result["multipleOf"] = self.multiple_of

        # String constraints
        if self.min_length is not None:
            result["minLength"] = self.min_length
        if self.max_length is not None:
            result["maxLength"] = self.max_length
        if self.pattern:
            result["pattern"] = self.pattern

        # Array constraints
        if self.min_items is not None:
            result["minItems"] = self.min_items
        if self.max_items is not None:
            result["maxItems"] = self.max_items
        if self.unique_items is not None:
            result["uniqueItems"] = self.unique_items
        if self.items:
            result["items"] = self.items.to_dict()

        # Object properties
        if self.properties:
            result["properties"] = {k: v.to_dict() for k, v in self.properties.items()}
        if self.required:
            result["required"] = self.required
        if self.additional_properties is not None:
            if isinstance(self.additional_properties, bool):
                result["additionalProperties"] = self.additional_properties
            else:
                result["additionalProperties"] = self.additional_properties.to_dict()

        # Composition
        if self.all_of:
            result["allOf"] = [schema.to_dict() for schema in self.all_of]
        if self.any_of:
            result["anyOf"] = [schema.to_dict() for schema in self.any_of]
        if self.one_of:
            result["oneOf"] = [schema.to_dict() for schema in self.one_of]
        if self.not_schema:
            result["not"] = self.not_schema.to_dict()

        # Extensions
        if self.x_nullable is not None:
            result["x-nullable"] = self.x_nullable
        if self.x_xml_name:
            result["x-xml-name"] = self.x_xml_name
        if self.x_xml_namespace:
            result["x-xml-namespace"] = self.x_xml_namespace
        if self.x_xml_prefix:
            result["x-xml-prefix"] = self.x_xml_prefix
        if self.x_xml_attribute is not None:
            result["x-xml-attribute"] = self.x_xml_attribute
        if self.x_xml_wrapped is not None:
            result["x-xml-wrapped"] = self.x_xml_wrapped

        # Standard XML metadata
        if self.xml:
            result["xml"] = self.xml

        return result


@dataclass
class ValidationResult:
    """Result of XSD validation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class SchemaInfo:
    """Information about an XSD schema."""

    target_namespace: Optional[str] = None
    element_form_default: str = "unqualified"
    attribute_form_default: str = "unqualified"

    complex_types_count: int = 0
    simple_types_count: int = 0
    global_elements_count: int = 0
    choice_elements_count: int = 0
    imports_count: int = 0
    includes_count: int = 0

    imports: List[str] = field(default_factory=list)
    includes: List[str] = field(default_factory=list)
    complex_types: List[str] = field(default_factory=list)
    simple_types: List[str] = field(default_factory=list)
    global_elements: List[str] = field(default_factory=list)


@dataclass
class ChoiceElement:
    """Represents an XSD choice element."""

    min_occurs: int = 1
    max_occurs: Union[int, str] = 1  # Can be "unbounded"
    elements: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class XSDType:
    """Represents an XSD type definition."""

    name: str
    namespace: Optional[str] = None
    is_complex: bool = False
    is_simple: bool = False
    base_type: Optional[str] = None
    restrictions: Dict[str, Any] = field(default_factory=dict)
    elements: List[Dict[str, Any]] = field(default_factory=list)
    attributes: List[Dict[str, Any]] = field(default_factory=list)
    choices: List[ChoiceElement] = field(default_factory=list)
    documentation: Optional[str] = None


@dataclass
class OpenAPIDocument:
    """Represents a complete OpenAPI document."""

    openapi: str = "3.0.3"
    info: Dict[str, Any] = field(default_factory=dict)
    paths: Dict[str, Any] = field(default_factory=dict)
    components: Dict[str, Any] = field(default_factory=dict)
    servers: List[Dict[str, Any]] = field(default_factory=list)
    security: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[Dict[str, Any]] = field(default_factory=list)
    external_docs: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "openapi": self.openapi,
            "info": self.info,
            "paths": self.paths,
        }

        if self.components:
            result["components"] = self.components
        if self.servers:
            result["servers"] = self.servers
        if self.security:
            result["security"] = self.security
        if self.tags:
            result["tags"] = self.tags
        if self.external_docs:
            result["externalDocs"] = self.external_docs

        return result
