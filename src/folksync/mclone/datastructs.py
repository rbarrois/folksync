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


class ReplicationStepState(enum.Enum):
    EMPTY = 0x0
    SKIPPED = 0x1
    EXEC = 0x2

    START = 0x10
    SUCCESS = 0x11


#: Change: an atomic change.
#: Attributes:
#: - action (Action): the action to perform
#: - key (text): the primary key for the field
#: - previous (dict text => object): data coming from the sink, or None for a creation
#: - target (dict text => object): data coming from the source, or None for a deletion
#: - sink (DataSink): the DataSink managing the change
#: - delta (object): opaque object used by the DataSink to notify of a change,
#:     and keep context; None for a deletion.
Change = collections.namedtuple(
    'Change',
    ['action', 'key', 'previous', 'target', 'sink', 'delta'],
)


#: ReplicationContext: the context of a replication run
#: Attributes:
#:  - source (DataSource): the data source
#:  - sinks (DataSink list): all sinks
#:  - keys (text set): all item keys
#:  - changes ((DataSink, {Action: {key: Change}}) list): list of changes per sink
#:  - stats ({Action: max_affected}): maps an action to the total number of items
ReplicationContext = collections.namedtuple(
    'ReplicationContext',
    ['source', 'sinks', 'keys', 'changes', 'stats'],
)


#: ReplicationStep: a replication step
#: Attributes:
#:  - sink (DataSink): the sink
#:  - action (Action): the action to display
#:  - state (ReplicationStepState): the state of the replication step
#:  - context (ReplicationContext): the step's context
ReplicationStep = collections.namedtuple(
    'ReplicationStep',
    ['sink', 'action', 'state', 'context'],
)
