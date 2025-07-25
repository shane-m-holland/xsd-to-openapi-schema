"""XSD to OpenAPI Schema Converter.

A Python tool to convert XML Schema Definition (XSD) files to OpenAPI 3.0+ specifications.
"""

from .converter import XSDConverter
from .models import OpenAPISchema

# Also expose simple parser functions for lightweight usage
try:
    from .simple_parser import parse_xsd_simple, convert_to_openapi
    __all__ = ["XSDConverter", "OpenAPISchema", "parse_xsd_simple", "convert_to_openapi"]
except ImportError:
    # If simple_parser import fails, continue without it
    __all__ = ["XSDConverter", "OpenAPISchema"]

__version__ = "0.1.0"