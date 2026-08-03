__version__ = '0.1.0'
__all__ = ['taos_config', 'taos_config_error']


def __getattr__(name):
    """Import taos.config lazily on first attribute access.

    Importing it eagerly here would put taos.config in sys.modules before
    `python -m taos.config` runs the file as __main__, which makes runpy
    emit a RuntimeWarning on every CLI invocation.
    """
    if name in __all__:
        from taos import config
        return getattr(config, name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
