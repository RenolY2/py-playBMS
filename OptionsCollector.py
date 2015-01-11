


# To make it easy to pass around options that have been set,
# the OptionsCollector will act as a container for options
# that have been set.
class OptionsCollector(object):
    def __init__(self, *args, **kwargs):
        self.opts = kwargs

    def set_options(self, **kwargs):
        for key, val in kwargs.iteritems():
            if key not in self.opts:
                raise RuntimeError("Key '{0}' does not exist in the option collector!".format(key))
            else:
                self.opts[key] = val

    def __getattr__(self, item):
        return self.opts[item]