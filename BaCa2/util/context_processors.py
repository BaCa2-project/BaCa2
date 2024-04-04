from importlib.metadata import version


def version_tag(request):
    return {'version': version('baca2')}
