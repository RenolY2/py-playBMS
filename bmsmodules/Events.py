from operator import isCallable


class Events(object):
    def __init__(self):
        self._events = {}
    
    def add_event(self, eventname, func):
        if not isCallable(func):
            raise RuntimeError("func argument must be a function!")
        elif not isinstance(eventname, (basestring, int)):
            raise RuntimeError("Event name must be a string!")
        elif eventname in self._events:
            raise RuntimeError("Event name already exists!")
        
        else:
            self._events[eventname] = func
    
    def exec_event(self, eventname, *args, **kwargs):
        if eventname not in self._events:
            raise RuntimeError("No such Event name '{0}'".format(eventname))
        else:
            self._events[eventname](*args, **kwargs)