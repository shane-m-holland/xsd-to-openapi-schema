"""XSD to OpenAPI Schema Converter.

A Python tool to convert XML Schema Definition (XSD) files to OpenAPI 3.0+ specifications.
"""

from .converter import XSDConverter
from .models import OpenAPISchema

__all__ = ["XSDConverter", "OpenAPISchema"]

__version__ = "0.1.0"
