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
    EMPTY = 0
    SKIPPED = 1
    START = 2
    SUCCESS = 3


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
