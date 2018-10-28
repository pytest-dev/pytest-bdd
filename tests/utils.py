def get_parametrize_markers_args(node):
    mark_name = 'parametrize'
    try:
        return get_markers_args_using_iter_markers(node, mark_name)
    except AttributeError:
        return get_markers_args_using_mark_objects(node, mark_name)


def get_markers_args_using_iter_markers(node, mark_name):
    """Recommended on pytest>=3.6"""
    args = []
    for mark in node.iter_markers(mark_name):
        args += mark.args
    return tuple(args)


def get_markers_args_using_mark_objects(node, mark_name):
    """Deprecated on pytest>=3.6"""
    return getattr(node.keywords._markers.get(mark_name), 'args', ())
