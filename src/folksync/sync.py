from .mclone import datastructs as mc_datastructs
from .mclone import interaction as mclone_interaction
from .mclone import syncer as mclone_syncer
from . import datastructs


class Syncer:
    def __init__(self, source, sinks):
        self.source = source
        self.sinks = sinks

    def run(self, dry_run=True):
        self.source.connect()
        master_data = {
            kind: {a.uids: a for a in self.source.fetch(kind)}
            for kind in datastructs.ObjectKind
        }

        for sink in self.sinks:
            sink.connect()
            for kind in datastructs.ObjectKind:
                self.apply(sink, kind, master_data=master_data[kind])

    def apply(self, sink, kind, master_data):
        sink_data = sink.fetch(kind)

        # Match sink_data to master_data keys
        uid_fields = datastructs.UID_FIELDS[kind]
        matches = {}
        unmatched = set(sink_data.keys())
        for uid_field in uid_fields:
            if not unmatched:
                break

            master_subkeys = {getattr(k, uid_field): k for k in master_data}

            for remote in set(unmatched):
                subkey = getattr(remote, uid_field)
                if subkey in master_subkeys:
                    unmatched.remove(remote)
                    matches[remote] = master_subkeys[subkey]

        matched_sink_data = {
            master_key: sink_data[sink_key]
            for sink_key, master_key in matches.items()
        }
        matched_sink_data.update({
            sink_key: sink_data[sink_key]
            for sink_key in unmatched
        })

        replicator = mclone_syncer.replicate(
            source_data=master_data,
            remote_data=matched_sink_data,
            mapper=sink.merger(kind),
            keys={k: None for k in master_data},
        )
        run = mc_datastructs.ReplicationRun(
            source=self.source,
            sink=sink,
            mode=mc_datastructs.ReplicationMode.FULL,
        )

        interactor = mclone_interaction.BaseInteractor()
        mclone_syncer.apply_replicator(
            replicator=replicator,
            interact=interactor,
            act=lambda event, run: None,
            run=run,
        )
