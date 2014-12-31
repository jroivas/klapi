import os
import importlib
import sys

class Image(object):
    def __init__(self, name):
        self.name = name

    @classmethod
    def match(self, name):
        return False

    def extraDeviceConfig(self):
        return ""

    def extra(self):
        return ""

    def kernelConfig(self):
        return ""

    def bootOrder(self):
        return ""

class ImageConfig(object):
    def __init__(self):
        self.basedir = os.path.dirname(os.path.realpath(__file__))
        self.basename = os.path.basename(__file__)
        sys.path.append(self.basedir)
        self.items = {}
        self.modules = {}

    def list(self):
        return [x[:-3] for x in os.listdir(self.basedir) if x.endswith('.py') and '__' not in x and x != self.basename]

    def _load(self, name):
        module = importlib.import_module(name)
        self.modules[name] = module
        self.items[name] = getattr(module, 'Image')

    def load(self, name):
        if name not in self.items:
            items = self.list()
            if name not in items:
                return None

            self._load(name)

        return self.items[name]

    def loadAll(self):
        items = self.list()
        for item in items:
            if item in self.modules:
                continue
            self._load(item)
