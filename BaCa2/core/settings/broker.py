import os

BROKER_URL = os.getenv('BROKER_URL')
BROKER_TIMEOUT = 600  # seconds

SUBMITS_DIR = BASE_DIR / 'submits'  # noqa: F821
_auto_create_dirs.add_dir(SUBMITS_DIR)  # noqa: F821

# Passwords for protecting communication channels between the broker and BaCa2.
# PASSWORDS HAVE TO DIFFERENT IN ORDER TO BE EFFECTIVE
BACA_PASSWORD = os.getenv('BACA_PASSWORD')
BROKER_PASSWORD = os.getenv('BROKER_PASSWORD')


class BrokerRetryPolicy:
    """Broker retry policy settings"""
    # HTTP post request be sent to the broker for one submit
    individual_submit_retry_interval = 0.05
    individual_max_retries = 5

    # (In seconds) how long it should take for a submit to become expired
    expiration_timeout = 60 * 20
    # how many times a submit should be resent after it expires
    resend_max_retries = 2
    # (In minutes) how often should expiration check be performed
    retry_check_interval = 60.0

    # (In minutes) specify how old should error submits be before they are deleted
    deletion_timeout = 60.0 * 24
    # (In minutes) specify how often should the deletion check be performed
    deletion_check_interval = 60.0

    # Auto start broker daemons
    auto_start = True


BROKER_RETRY_POLICY = BrokerRetryPolicy()
