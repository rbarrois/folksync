import collections
import enum


class Action(enum.Enum):
    """An atomic change type.

    - CREATED: new item created on the replica
    - UPDATED: item updated on the replica
    - SKIPPED: explicit ignore required
    - UNCHANGED: no change => no update
    - DELETED: item no longer exists on the source => delete it
    """
    CREATED = 'created'
    UPDATED = 'updated'
    SKIPPED = 'skipped'
    UNCHANGED = 'unchanged'
    DELETED = 'deleted'


class ReplicationMode(enum.Enum):
    DRY_RUN = 0
    ADDITIVE = 1
    FULL = 2


class ReplicationStep(enum.Enum):
    EMPTY = 0x0
    SKIPPED = 0x1
    EXEC = 0x2

    NOTIFY = 0x10
    CHOOSE_MODE = 0x11


#: Change: an atomic change.
#: Attributes:
#: - action (Action): the action to perform
#: - key (text): the primary key for the field
#: - previous (dict text => object): data coming from the sink, or None for a creation
#: - target (dict text => object): data coming from the source, or None for a deletion
#: - delta (object): opaque object used by the DataSink to notify of a change,
#:     and keep context; None for a deletion.
Change = collections.namedtuple(
    'Change',
    ['action', 'key', 'previous', 'target', 'delta'],
)


#: ReplicationContext: the context of a replication run
#: Attributes:
#:  - keys (text set): all item keys
#:  - changes {Action: {key: Change}}: list of changes per type
#:  - stats ({Action: max_affected}): maps an action to the total number of items
ReplicationContext = collections.namedtuple(
    'ReplicationContext',
    ['keys', 'changes', 'stats'],
)


#: ReplicationEvent: a replication event
#: Attributes:
#:  - step (ReplicationStep): the kind of replication event
#:  - action (Action): the action to display
#:  - context (ReplicationContext): the step's context
ReplicationEvent = collections.namedtuple(
    'ReplicationEvent',
    ['step', 'action', 'context'],
)


#: ReplicationRun: a replication run description
#: Attributes:
#:  - source (DataSource): the data source
#:  - sink (DataSink): the sink being replicated to
#:  - mode (ReplicationMode): the replication mode
ReplicationRun = collections.namedtuple(
    'ReplicationRun',
    ['source', 'sink', 'mode'],
)
