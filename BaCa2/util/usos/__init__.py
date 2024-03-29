from core.settings import (
    BASE_DIR,
    USOS_CONSUMER_KEY,
    USOS_CONSUMER_SECRET,
    USOS_GATEWAY,
    USOS_SCOPES
)

from .communicator import USOS, RegisterUSOS

__all__ = ['RegisterUSOS', 'USOS', 'BASE_DIR', 'USOS_CONSUMER_KEY', 'USOS_CONSUMER_SECRET',
           'USOS_GATEWAY', 'USOS_SCOPES']
