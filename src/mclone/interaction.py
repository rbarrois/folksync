

class BaseInteraction:
    def __init__(self, **kwargs):
        pass

    def notify_changes(self, changes):
        pass

    def choose_mode(self, mode):
        return mode

    def notify_step(self, sink, action, state):
        pass
