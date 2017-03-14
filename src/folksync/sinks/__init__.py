class NullSink:
    name = 'Null'

    def __init__(self, config):
        pass

    def fetch(self, kind):
        return {}

    def merge(self, source, remote):
        return source
