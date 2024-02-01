LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
        }
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'filters': [],
        }
    },
    'loggers': {
        loger_name: {
            'level': 'INFO',
            'propagate': True,
        } for loger_name in ('broker_api', 'course', 'package', 'util', 'main', 'django')
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console'],
    },
}