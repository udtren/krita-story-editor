from krita import Krita


def get_svg_from_activenode():
    """
    Get SVG data from the active node (if it's a vector layer)
    Prints shape names and SVG content to stdout
    """
    doc = Krita.instance().activeDocument()

    if not doc:
        print("No active document")
        return

    active_node = doc.activeNode()

    if not active_node:
        print("No active node")
        return

    if str(active_node.type()) == "vectorlayer":
        print(f"Vector Layer Full SVG Data\n")
        print("=" * 60)
        print(active_node.toSvg())
        print("=" * 60)

        shapes = active_node.shapes()

        if not shapes:
            print("No shapes found in vector layer")
            return

        print(f"Layer Name: {active_node.name()}")
        print(f"Node Id: {active_node.uniqueId()}")
        print(f"Node Id String: {active_node.uniqueId().toString()}")
        print(f"Number of shapes: {len(shapes)}\n")
        print("=" * 60)

        for idx, shape in enumerate(shapes):
            print(f"\n--- Shape {idx + 1} ---")
            print(f"Name: {shape.name()}")
            print(f"\nSVG Content:")
            print(shape.toSvg())
            print("=" * 60)
    else:
        print(f"Active node is not a vector layer. Type: {active_node.type()}")
