import xml.etree.ElementTree as ET
import re


def format_svg_for_krita(svg_string):
    """
    Format SVG to match Krita's format by removing namespace prefixes.

    Converts:
        <ns0:text ... ns1:textVersion="3">
    To:
        <text ... krita:textVersion="3">

    Args:
        svg_string: SVG string with namespace prefixes

    Returns:
        Formatted SVG string matching Krita's format
    """
    try:
        # Parse the SVG
        root = ET.fromstring(svg_string)

        # Register namespaces to preserve them in output
        ET.register_namespace("", "http://www.w3.org/2000/svg")
        ET.register_namespace("krita", "http://krita.org/namespaces/svg/krita")
        ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
        ET.register_namespace(
            "sodipodi", "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
        )

        # Convert to string
        formatted_svg = ET.tostring(root, encoding="unicode", method="xml")

        # Remove namespace prefixes (ns0:, ns1:, etc.)
        # Replace ns0:tag with tag
        formatted_svg = re.sub(r"<ns\d+:", "<", formatted_svg)
        formatted_svg = re.sub(r"</ns\d+:", "</", formatted_svg)

        # Replace ns1:attribute with krita:attribute
        formatted_svg = re.sub(
            r"\sns\d+:textVersion=", " krita:textVersion=", formatted_svg
        )
        formatted_svg = re.sub(r"\sns\d+:(\w+)=", r" krita:\1=", formatted_svg)

        # Clean up any remaining namespace declarations that aren't needed
        formatted_svg = re.sub(r'\sxmlns:ns\d+="[^"]*"', "", formatted_svg)

        return formatted_svg

    except Exception as e:
        print(f"Error formatting SVG: {e}")
        return svg_string


def remove_namespace_prefixes(svg_string):
    """
    Alternative method: Simple regex replacement to remove namespace prefixes.
    This is faster but less robust than XML parsing.

    Args:
        svg_string: SVG string with namespace prefixes

    Returns:
        SVG string without namespace prefixes
    """
    # Remove ns0:, ns1:, etc. from tags
    result = re.sub(r"<ns\d+:", "<", svg_string)
    result = re.sub(r"</ns\d+:", "</", result)

    # Convert ns1:textVersion to krita:textVersion
    result = re.sub(r"\sns\d+:textVersion=", " krita:textVersion=", result)

    # Convert other ns*: attributes to krita: if needed
    result = re.sub(r"\sns\d+:(\w+)=", r" krita:\1=", result)

    # Remove xmlns:ns* declarations
    result = re.sub(r'\sxmlns:ns\d+="[^"]*"', "", result)

    return result


def restore_tspan_tags(svg_string):
    """
    Restore <tspan> tags in the SVG string if they were removed.

    Args:
        svg_string: SVG string possibly missing <tspan> tags
    """
    # Replace placeholders with actual <tspan> tags
    restored = svg_string.replace("__tspan", "<tspan").replace("__/tspan__", "</tspan>")
    return restored


def clean_svg_namespaces(svg_string):
    """
    Comprehensive cleaning of SVG namespaces to match Krita format.

    This function:
    1. Removes namespace prefixes from tags (ns0:text -> text)
    2. Converts namespace prefixes in attributes to krita: (ns1:textVersion -> krita:textVersion)
    3. Preserves the xmlns declarations
    4. Maintains proper formatting

    Args:
        svg_string: SVG string possibly containing namespace prefixes

    Returns:
        Cleaned SVG string in Krita's format
    """
    if not svg_string:
        return svg_string

    # Step 1: Remove namespace prefixes from tags
    # <ns0:text> -> <text>, </ns0:text> -> </text>
    cleaned = re.sub(r"<ns\d+:(\w+)", r"<\1", svg_string)
    cleaned = re.sub(r"</ns\d+:(\w+)", r"</\1", cleaned)

    # Step 2: Convert namespace prefixes in attributes
    # ns1:textVersion -> krita:textVersion
    # ns0:attribute -> krita:attribute
    cleaned = re.sub(r"\s+ns\d+:(\w+)=", r" krita:\1=", cleaned)

    # Step 3: Remove auto-generated xmlns:ns* declarations
    # Keep the main xmlns declarations intact
    cleaned = re.sub(r'\s+xmlns:ns\d+="[^"]*"', "", cleaned)

    return cleaned
