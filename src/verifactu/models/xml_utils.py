"""Helpers to read VERI*FACTU XML elements"""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Optional, TypeVar, Union
from xml.etree import ElementTree as ET

from pydantic import ValidationError

from verifactu.exceptions.import_exception import ImportException
from verifactu.exceptions.invalid_model_exception import InvalidModelException

NS_SUM1 = "https://www2.agenciatributaria.gob.es/static_files/common/internet/dep/aplicaciones/es/aeat/tike/cont/ws/SuministroInformacion.xsd"

XmlInput = Union[str, bytes, ET.Element]

T = TypeVar("T")


def to_element(xml: XmlInput) -> ET.Element:
    """
    Get an XML element from a string, bytes or an already parsed element

    Args:
        xml: XML string, bytes or element

    Returns:
        XML element

    Raises:
        ImportException: If the XML is not well-formed
    """
    if isinstance(xml, ET.Element):
        return xml
    try:
        return ET.fromstring(xml)
    except ET.ParseError as e:
        raise ImportException(f"Invalid XML: {e}") from e


def _path(path: str) -> str:
    """Expand "sum1:" prefixes of an XPath-like path to the full namespace"""
    return "/".join(
        f"{{{NS_SUM1}}}{part[5:]}" if part.startswith("sum1:") else part for part in path.split("/")
    )


def get(element: ET.Element, path: str) -> Optional[ET.Element]:
    """Get the first child element matching a path, or None"""
    return element.find(_path(path))


def get_all(element: ET.Element, path: str) -> list:
    """Get all child elements matching a path"""
    return element.findall(_path(path))


def get_text(element: ET.Element, path: str) -> Optional[str]:
    """Get the text of the first child element matching a path, or None if missing"""
    child = get(element, path)
    if child is None:
        return None
    return child.text or ""


def require_text(element: ET.Element, path: str, context: str = "") -> str:
    """
    Get the text of a required child element

    Raises:
        ImportException: If the element is missing
    """
    text = get_text(element, path)
    if text is None:
        name = path.split("/")[-1]
        suffix = f" from <sum1:{context} /> element" if context else " element"
        raise ImportException(f"Missing <{name} />{suffix}")
    return text


def parse_date(value: str, name: str) -> datetime:
    """
    Parse a date in DD-MM-YYYY format

    Raises:
        ImportException: If the value is not a valid date
    """
    try:
        return datetime.strptime(value, "%d-%m-%Y")
    except ValueError as e:
        raise ImportException(f"Invalid value for <sum1:{name} /> element") from e


def to_enum(enum_class: Callable[[str], T], value: str, name: str) -> T:
    """
    Convert a raw value to an enum member

    Raises:
        ImportException: If the value is not a member of the enum
    """
    try:
        return enum_class(value)
    except ValueError as e:
        raise ImportException(f"Invalid value for <sum1:{name} /> element") from e


def build(model_class: Callable[..., T], **data: object) -> T:
    """
    Instantiate a model, converting validation errors to InvalidModelException

    Raises:
        InvalidModelException: If the imported values do not pass validation
    """
    try:
        return model_class(**data)
    except ValidationError as e:
        raise InvalidModelException(e) from e
