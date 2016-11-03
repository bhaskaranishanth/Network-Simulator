
class EventQueue:
    """
    
    """
    def __init__(self):
        events = []

    def is_empty(self):
        return self.events == []

    def enqueue(self, event):
        self.events.insert(0, event)

    def dequeue(self):
        return self.events.pop()

    def peek(self):
        return start

    def size(self):
        return len(self.events)