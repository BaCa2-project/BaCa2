LOGS_DIR = BASE_DIR / 'logs'

FORMATTER_MODULE = 'core.tools.logs'

FORMATTER = f'{FORMATTER_MODULE}.CustomFormatter'

COLORED_FORMATTER = f'{FORMATTER_MODULE}.CustomColoredFormatter'

FORMATTERS = {
    'simple': {
        '()': COLORED_FORMATTER,
        'fmt': '%(levelname)s '
               '%(asctime)s '
               '%(pathname)s'
               '%(funcName)s'
               '%(lineno)d '
               '%(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S',
    },
    'server_console': {
        '()': COLORED_FORMATTER,
        'fmt': '%(levelname)s '
               '%(asctime)s '
               '%(name)s\033[95m::\033[0m '
               '%(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S',
    },
    'verbose': {
        '()': FORMATTER,
        'fmt': '%(levelname)s '
               '%(asctime)s '
               '%(threadName)s '
               '%(thread)d '
               '%(process)d '
               '%(pathname)s'
               '%(funcName)s'
               '%(lineno)d '
               '%(message)s',
        'datefmt': '%Y-%m-%d %H:%M:%S',
    },
}

HANDLERS = {
    'console': {
        'class': 'logging.StreamHandler',
        'formatter': 'simple',
        'level': 'DEBUG',
    },
    'server_console': {
        'class': 'logging.StreamHandler',
        'formatter': 'server_console',
        'level': 'DEBUG',
    },
    'info': {
        'class': 'logging.handlers.RotatingFileHandler',
        'formatter': 'verbose',
        'level': 'INFO',
        'filename': str(LOGS_DIR / 'info.log'),
        'mode': 'a',
        'encoding': 'utf-8',
        'backupCount': 5,
        'maxBytes': 1024 * 1024,
    },
    'error': {
        'class': 'logging.handlers.RotatingFileHandler',
        'formatter': 'verbose',
        'level': 'ERROR',
        'filename': str(LOGS_DIR / 'error.log'),
        'mode': 'a',
        'encoding': 'utf-8',
        'backupCount': 5,
        'maxBytes': 1024 * 1024,
    },
}

LOGGERS = {
    'django': {
      'handlers': ['console', 'info'],
      'level': 'INFO',
    },
    'django.request': {
      'handlers': ['error'],
      'level': 'INFO',
      'propagate': True,
    },
    'django.server': {
      'handlers': ['error', 'server_console'],
      'level': 'INFO',
      'propagate': False,
    },
    'django.template': {
      'handlers': ['error'],
      'level': 'DEBUG',
      'propagate': False,
    },
} | {
    app_name: {
      'handlers': ['console', 'info', 'error'],
      'level': 'DEBUG',
    } for app_name in ('broker_api', 'course', 'package', 'util', 'main')
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': FORMATTERS,
    'handlers': HANDLERS,
    'loggers': LOGGERS,
}
