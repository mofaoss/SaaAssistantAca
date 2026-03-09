def get_all_children(widget):
    """Recursively flatten all descendant Qt children."""
    children = []
    for child in widget.children():
        children.append(child)
        children.extend(get_all_children(child))
    return children

