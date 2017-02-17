class Syncer:
    def __init__(self, source, sinks):
        self.source = source
        self.sinks = sinks

    def run(self, dry_run=True):
        self.source.connect()
        for user in sorted(self.source.fetch_users(), key=lambda a: a.hrid):
            print(user)

        for group in sorted(self.source.fetch_groups(), key=lambda g: g.hrid):
            print(group)
