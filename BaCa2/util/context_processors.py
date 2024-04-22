from django.conf import settings


def version_tag(request):
    return {'version': settings.BACA2_VERSION}
