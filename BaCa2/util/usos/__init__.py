from BaCa2.settings import SECRETS, BASE_DIR
import yaml

from communicator import RegisterUSOS, USOS

_USOS_CONFIG_DIR = BASE_DIR = BASE_DIR / 'usos_config.yaml'

with open(_USOS_CONFIG_DIR) as config_file:
    config = yaml.safe_load(config_file)

USOS_GATEWAY = config.get('gateway')
USOS_SCOPES = config.get('scopes')
USOS_CONSUMER_KEY = SECRETS.get('usos_consumer_key')
USOS_CONSUMER_SECRET = SECRETS.get('usos_consumer_secret')
