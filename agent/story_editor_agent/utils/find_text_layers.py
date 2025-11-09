def find_text_layers(node, text_layers, path=""):
    """Recursively find all vector/text layers"""
    current_path = f"{path}/{node.name()}" if path else node.name()

    if node.type() == 'vectorlayer':
        text_layers.append({
            'name': node.name(),
            'path': current_path,
            'visible': node.visible(),
            'type': node.type()
        })

    # Recurse into child nodes
    for child in node.childNodes():
        find_text_layers(child, text_layers, current_path)
