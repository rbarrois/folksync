import enum
import importlib


class SourceRegistry(enum.Enum):
    openldap = 'folksync.sources.ldap.OpenLdapSource'


def load_source(name, config):
    path = SourceRegistry[name].value
    return load_plugin(path, config)


class SinkRegistry(enum.Enum):
    null = 'folksync.sinks.NullSink'
    gsuite = 'folksync.sinks.gsuite.GSuiteSink'
    trello = 'folksync.sinks.trello.TrelloSink'


def load_sink(name, config, cache=None):
    path = SinkRegistry[name].value
    return load_plugin(path, config, cache=cache)


class CacheRegistry(enum.Enum):
    null = 'folksync.cache.NullCache'
    file = 'folksync.cache.FileCache'


def load_cache(name, config):
    path = CacheRegistry[name].value
    return load_plugin(path, config)


def load_plugin(path, config, **kwargs):
    mod_name, obj_name = path.rsplit('.', 1)
    mod = importlib.import_module(mod_name)
    plugin_class = getattr(mod, obj_name)

    return plugin_class(config, **kwargs)
