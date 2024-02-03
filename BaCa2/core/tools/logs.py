from typing import Dict
import logging
import pathlib


class CustomFormatter(logging.Formatter):
    """
    Custom formatter for BaCa2 logs. Adds levelname, pathname, and funcName formatting.
    """

    def __init__(self,
                 fmt: str,
                 const_levelname_width: bool = True,
                 levelname_width: int = 10,
                 dot_pathname: bool = True,
                 **kwargs) -> None:
        """
        :param fmt: format string
        :type fmt: str
        :param const_levelname_width: whether to use constant levelname width
        :type const_levelname_width: bool
        :param levelname_width: constant levelname width, default is 10
        :type levelname_width: int
        :param dot_pathname: whether to replace path separators with dots
        :type dot_pathname: bool
        """
        if not hasattr(self, 'funcName_after_pathname'):
            self.funcName_after_pathname = self.funcname_after_pathname(fmt)

        fmt = self.format_lineno(fmt)

        self.const_levelname_width = const_levelname_width
        self.levelname_width = levelname_width
        self.dot_pathname = dot_pathname

        super().__init__(fmt=fmt, style='%', **kwargs)

    @staticmethod
    def funcname_after_pathname(fmt: str) -> bool:
        """
        :param fmt: format string
        :type fmt: str
        :return: whether the funcName is placed after the pathname in the format string
        :rtype: bool
        """
        if '%(pathname)s' in fmt and '%(funcName)s' in fmt:
            p_index = fmt.find('%(pathname)s')
            f_index = p_index + len('%(pathname)s')
            return fmt.startswith('%(funcName)s', f_index)
        else:
            return False

    def format_lineno(self, fmt: str) -> str:
        """
        :param fmt: format string
        :type fmt: str
        :return: format string with modified lineno format
        :rtype: str
        """
        return fmt.replace('%(lineno)d', f'%(lineno)d::')

    def format(self, record) -> str:
        """
        Format the levelname, pathname, and funcName in the log record. Restore the original
        values after generating the log message.

        :param record: log record
        :type record: logging.LogRecord
        :return: formatted log message
        :rtype: str
        """
        levelname = record.levelname
        pathname = record.pathname
        funcname = record.funcName
        self.format_levelname(record)
        self.format_pathname(record)
        self.format_funcname(record)
        out = super().format(record)
        record.levelname = levelname
        record.pathname = pathname
        record.funcName = funcname
        return out

    def format_funcname(self, record) -> None:
        """
        Formats the funcName in the log record.

        :param record: log record
        :type record: logging.LogRecord
        """
        record.funcName = f'{record.funcName}:'

    def format_pathname(self, record) -> None:
        """
        Formats the pathname in the log record. Relativaize the pathname to the BASE_DIR or the
        django directory, and replace path separators with dots if dot_pathname is True.

        :param record: log record
        :type record: logging.LogRecord
        """
        from django.conf import settings

        pathname = pathlib.Path(record.pathname)

        if 'django' in pathname.parts:
            pathname = pathname.relative_to(pathname.parents[~(pathname.parts.index('django') - 1)])
        else:
            pathname = pathname.relative_to(settings.BASE_DIR)

        pathname = str(pathname.with_suffix(''))

        if self.dot_pathname:
            pathname = self.format_dot_pathname(pathname)

        record.pathname = pathname

    def format_dot_pathname(self, pathname: str) -> str:
        """
        :param pathname: pathname
        :type pathname: str
        :return: pathname with path separators replaced by dots
        :rtype: str
        """
        pathname = pathname.replace('\\', '.').replace('/', '.')

        if self.funcName_after_pathname:
            pathname = f'{pathname}.'

        return pathname

    def format_levelname(self, record) -> None:
        """
        Formats the levelname in the log record. Adds square brackets around the levelname and
        pads it to the levelname_width if const_levelname_width is True.

        :param record: log record
        :type record: logging.LogRecord
        """
        record.levelname = f'[{record.levelname}]'

        if self.const_levelname_width:
            record.levelname = record.levelname.ljust(self.levelname_width)


class CustomColoredFormatter(CustomFormatter):
    """
    Custom formatter for BaCa2 logs. Adds levelname and pathname formatting and allows for fully
    customizable log coloring.
    """

    #: names of all allowed record attributes
    RECORD_ATTRS = ('%(name)s', '%(levelno)s', '%(levelname)s', '%(pathname)s', '%(filename)s',
                    '%(module)s', '%(lineno)d', '%(funcName)s', '%(created)f', '%(asctime)s',
                    '%(msecs)d', '%(relativeCreated)d', '%(thread)d', '%(threadName)s',
                    '%(process)d', '%(message)s')

    #: default colors for log elements. Can be overridden by passing a custom colors_dict to the
    #: formatter constructor. The keys are the names of the record attributes and levels, as well as
    #: 'BRACES' for the square brackets around the levelname, 'DEFAULT' for the default color to use
    #: on elements that do not have specific color assigned, 'RESET' for the reset color code, and
    #: 'SPECIAL' used for special characters when formatting the log message.
    COLORS = {
        'DEFAULT': '\033[97m',  # White
        'DEBUG': '\033[94m',  # Blue
        'INFO': '\033[92m',  # Green
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',  # Red
        'CRITICAL': '\033[101m\033[30m',  # White text on red background
        'BRACES': '\033[37m',  # Gray
        'RESET': '\033[0m',  # Reset
        'SPECIAL': '\033[95m',  # Purple
        '%(asctime)s': '\033[32m',  # Green
        '%(pathname)s': '\033[37m',  # Gray
        '%(funcName)s': '\033[37m',  # Gray
        '%(lineno)d': '\033[36m',  # Cyan
        '%(name)s': '\033[37m',  # Gray
    }

    def __init__(self,
                 fmt: str,
                 colors_dict: Dict[str, str] = None,
                 const_levelname_width: bool = True,
                 levelname_width: int = 10,
                 dot_pathname: bool = True,
                 **kwargs) -> None:
        """
        :param fmt: format string
        :type fmt: str
        :param colors_dict: custom colors for log elements
        :type colors_dict: dict
        :param const_levelname_width: whether to use constant levelname width
        :type const_levelname_width: bool
        :param levelname_width: constant levelname width, default is 10
        :type levelname_width: int
        :param dot_pathname: whether to replace path separators with dots
        :type dot_pathname: bool
        """
        self.funcName_after_pathname = self.funcname_after_pathname(fmt)
        self.colors_dict = CustomColoredFormatter.COLORS

        if colors_dict:
            self.colors_dict.update(colors_dict)

        fmt = self.add_colors(fmt)

        super().__init__(fmt=fmt,
                         const_levelname_width=const_levelname_width,
                         levelname_width=levelname_width,
                         dot_pathname=dot_pathname, **kwargs)

    def add_colors(self, fmt: str) -> str:
        """
        Add colors to the log elements in the format string according to the colors_dict.

        :param fmt: format string
        :type fmt: str
        :return: format string with colors
        :rtype: str
        """
        reset = self.colors_dict.get('RESET', '')
        default = self.colors_dict.get('DEFAULT', reset)

        for attr in CustomColoredFormatter.RECORD_ATTRS:
            if attr in fmt:
                color = self.colors_dict.get(attr, default)
                fmt = fmt.replace(attr, f'{color}{attr}{reset}')

        return fmt

    def special_symbol(self, symbol: str, following_element: str = '') -> str:
        """
        Add color to a special symbol used in the log message formatting.

        :param symbol: special symbol
        :type symbol: str
        :param following_element: log message element following the special symbol
        (e.g. '%(message)s'), its color will be added following the special symbol (optional)
        :type following_element: str
        :return: special symbol with color
        :rtype: str
        """
        reset = self.colors_dict.get('RESET', '')
        default = self.colors_dict.get('DEFAULT', reset)
        special_color = self.colors_dict.get('SPECIAL', default)
        symbol = f'{special_color}{symbol}{reset}'

        if following_element:
            following_color = self.colors_dict.get(following_element, default)
            return f'{symbol}{following_color}'

        return symbol

    def format_lineno(self, fmt: str) -> str:
        """
        :param fmt: format string
        :type fmt: str
        :return: format string with modified lineno format
        :rtype: str
        """
        return fmt.replace('%(lineno)d', f'%(lineno)d{self.special_symbol("::")}')

    def format_funcname(self, record) -> None:
        """
        Formats the funcName in the log record.

        :param record: log record
        :type record: logging.LogRecord
        """
        record.funcName = f'{record.funcName}{self.special_symbol(":")}'

    def format_dot_pathname(self, pathname: str) -> str:
        """
        :param pathname: pathname
        :type pathname: str
        :return: pathname with path separators replaced by dots
        :rtype: str
        """
        dot = self.special_symbol('.', '%(pathname)s')
        pathname = pathname.replace('\\', dot).replace('/', dot)

        if self.funcName_after_pathname:
            dot = self.special_symbol('.')
            pathname = f'{pathname}{dot}'

        return pathname

    def format_levelname(self, record) -> None:
        """
        Formats the levelname in the log record. Adds square brackets around the levelname and
        pads it to the levelname_width if const_levelname_width is True.

        :param record: log record
        :type record: logging.LogRecord
        """
        added_width = 0
        r = self.colors_dict.get('RESET', '')
        color = self.colors_dict.get(record.levelname, r)
        braces_color = self.colors_dict.get('BRACES', '')
        added_width += len(color) + len(r) * 3 + len(braces_color) * 2
        record.levelname = f'{braces_color}[{r}{color}{record.levelname}{r}{braces_color}]{r}'

        if self.const_levelname_width:
            record.levelname = record.levelname.ljust(self.levelname_width + added_width)
