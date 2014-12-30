import os
import shutil
import thread

class ImageProvider(object):
    def __init__(self):
        pass

    def list(self):
        return []

    def get(self, name):
        pass

    def clone(self, name):
        pass

    def delete(self, name):
        pass

    def add(self, name, url):
        pass


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

def thread_downloader(url, dest):
    os.chdir(dest)
    # FIXME Depends on wget
    os.system('wget -q %s')

class LocalImageProvider(ImageProvider):
    def __init__(self, directory=''):
        self.dir = directory
        os.makedirs(self.dir, 0777)

    def update_db(self):
        self.images = {}
        for item in os.listdir(self.dir):
            try:
                base = os.path.basename(item[0:item.index('.')])
            except:
                base = item
            self.images[base] = item

    def list(self):
        self.update_db()
        return self.images.keys()

    def clone(self, name):
        img = self.get(name)

        index = 1
        new_name = name + 'clone%s' % (index)
        while new_name in self.images:
            index += 1
            new_name = name + 'clone%s' % (index)

        try:
            base = img[0:img.index('.')]
            ext = img[img.index('.'):]
        except:
            base = img
            ext = ''

        img_name = base + 'clone%s' % (index) + ext
        while os.path.exists(self.dir + '/' + img_name):
            index += 1
            img_name = base + 'clone%s' % (index) + ext

        shutil.copyfile(self.dir + '/' + img, self.dir + '/' + img_name)

        return new_name

    def delete(self, name):
        self.update_db()

        for item in self.images:
            if item == name:
                img = self.get(name)
                os.remove(self.dir + '/' + img)

        self.update_db()

    def add(self, url):
        if url.startswith('http') or url.startswith('ftp'):
            thread.start_new_thread(thread_downloader, (url, self.dir))
            return
        elif url.starstwith('file://'):
            url = url[7:]

        if os.path.exists(url):
            img_name = os.path.basename(url)
            if os.path.exists(self.dir + '/' + img_name):
                raise ValueError('Image already exists: %s' % (img_name))

            shutil.copyfile(url, self.dir + '/' + img_name)

            return

        raise ValueError('Image not found: %s' % (url))

def provider(sets):
    image = sets.get('image', None)

    if image is None or image == 'dummy':
        return DummyImageProvider()
    if image == 'local':
        image_storage = sets.get('image_storage', '/tmp')
        return LocalImageProvider(image_storage)

    return None
