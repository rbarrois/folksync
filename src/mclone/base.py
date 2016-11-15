class DataSource:
    def __init__(self, **kwargs):
        pass

    def _connect(self):
        raise NotImplementedError()

    def _disconnect(self):
        raise NotImplementedError()

    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._disconnect()

    def all(self):
        raise NotImplementedError()

    def get(self, key):
        raise NotImplementedError()


class DataSink(DataSource):

    def get_skipped_keys(self):
        return {}

    def merge(self, base, updated):
        raise NotImplementedError()

    def create_batch(self, changes):
        raise NotImplementedError()

    def update_batch(self, changes):
        raise NotImplementedError()

    def delete_batch(self, changes):
        raise NotImplementedError()
