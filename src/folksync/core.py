import enum
import importlib


class SourceRegistry(enum.Enum):
    ldap = 'folksync.sources.ldap.LdapSource'


def load_source(name, config):
    path = SourceRegistry[name].value
    return load_plugin(path, config)


class SinkRegistry(enum.Enum):
    null = 'folksync.sinks.NullSink'


def load_sink(name, config):
    path = SinkRegistry[name].value
    return load_plugin(path, config)


def load_plugin(path, config):
    mod_name, obj_name = path.rsplit('.', 1)
    mod = importlib.import_module(mod_name)
    plugin_class = getattr(mod, obj_name)

    return plugin_class(config)
