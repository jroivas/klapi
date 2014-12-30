from images import ImageProvider

class DummyImageProvider(ImageProvider):
    def __init__(self, images={}):
        self.images = images

    def list(self):
        """
        >>> p = DummyImageProvider()
        >>> p.list()
        []
        >>> p = DummyImageProvider({'test': '/path/to/test', 'dummy': '/path/to/dummy'})
        >>> p.list()
        ['test', 'dummy']
        """
        return self.images.keys()

    def get(self, name):
        """
        >>> p = DummyImageProvider({'test': '/path/to/test', 'dummy': '/path/to/dummy'})
        >>> p.get('') is None
        True
        >>> p.get('a') is None
        True
        >>> p.get('test') is None
        False
        >>> p.get('test')
        '/path/to/test'
        >>> p.get('dummy')
        '/path/to/dummy'
        """
        if name in self.images:
            return self.images[name]
        return None

    def clone(self, name):
        """
        >>> p = DummyImageProvider({'test': '/path/to/test', 'dummy': '/path/to/dummy'})
        >>> p.clone('') is None
        True
        >>> p.clone(None) is None
        True
        >>> p.clone('test')
        '/path/to/test_clone'
        >>> p.clone('dummy')
        '/path/to/dummy_clone'
        """
        img = self.get(name)
        if img is not None:
            return img + '_clone'

        return None

    def delete(self, name):
        """
        >>> p = DummyImageProvider({'test': '/path/to/test', 'dummy': '/path/to/dummy'})
        >>> p.list()
        ['test', 'dummy']
        >>> p.delete('')
        >>> p.list()
        ['test', 'dummy']
        >>> p.delete(None)
        >>> p.list()
        ['test', 'dummy']
        >>> p.delete('test')
        >>> p.list()
        ['dummy']
        >>> p.delete('dummy')
        >>> p.list()
        []
        >>> p.delete('dummy')
        >>> p.list()
        []
        """
        res = {}
        for item in self.images:
            if item != name:
                res[item] = self.images[item]
        self.images = res

    def add(self, name, url):
        """
        >>> p = DummyImageProvider({'test': '/path/to/test', 'dummy': '/path/to/dummy'})
        >>> p.list()
        ['test', 'dummy']
        >>> p.add('test4', 'http://location')
        >>> p.list()
        ['test', 'dummy', 'test4']
        >>> p.get('test4')
        'http://location'
        >>> p.add('test4', 'http://location') # doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        ValueError: Image already exists: test4
        """
        if name in self.images:
            raise ValueError('Image already exists: %s' % (name))

        self.images[name] = url

