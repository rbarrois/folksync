


class Syncer:
    def __init__(self, source, sinks):
        self.source = source
        self.sinks = sinks

    def run(self, dry_run=True):
        self.source.connect()
        master_data = {
            kind: self.source.fetch(kind)
            for kind in datastructs.ObjectKind
        }

        for sink in self.sinks:
            for kind in datastructs.ObjectKind:
                self.apply(sink, kind, master_data=master_data[kind])

    def apply(self, sink, kind, master_data):
        sink_data = sink.fetch(kind)
        data = self.match(master_data, sink_data)
        for _key, (source, remote) in data.items():
            new_remote = sink.merge(source, remote)
        sink_users = sink.fetch_users()
        sink_groups = sink.fetch_groups()

        for user in sorted(self.source.fetch_users(), key=lambda a: a.hrid):
            print(user)

        for group in sorted(self.source.fetch_groups(), key=lambda g: g.hrid):
            print(group)
