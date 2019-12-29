import logging


class ColorFormatter(logging.Formatter):
    colors = {
        'error': dict(fg='red'),
        'exception': dict(fg='red'),
        'critical': dict(fg='red'),
        'debug': dict(fg='blue'),
        'warning': dict(fg='yellow'),
        'info': dict(fg='green')
    }

    def format(self, record):
        import click
        s = super(ColorFormatter, self).format(record)
        if not record.exc_info:
            level = record.levelname.lower()
            if level in self.colors:
                s = click.style(s, **self.colors[level])
        return s


class CustomFormatter(logging.Formatter):
    def format(self, record):
        s = super(CustomFormatter, self).format(record)
        if record.levelno == logging.ERROR:
            s = s.replace('[.]', '[x]')
        return s


def setup(name=__name__, level=logging.INFO):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(level)
    try:
        # check if click exists to swap the logger
        import click  # noqa
        formatter = ColorFormatter('[.] %(message)s')
    except ImportError:
        formatter = CustomFormatter('[.] %(message)s')
    handler = logging.StreamHandler(None)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
