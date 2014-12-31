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

from config import config

import dummy
import local
import storage

def provider(sets):
    image = sets.get('image', None)

    if image is None or image == 'dummy':
        return dummy.DummyImageProvider()
    if image == 'local':
        image_storage = sets.get('image_storage', '/tmp')
        return local.LocalImageProvider(image_storage)

    return None

def volume_provider(sets):
    vol = sets.get('volume', None)

    if vol is None:
        return None
    if vol == 'local':
        volume_storage = sets.get('volume_storage', '/tmp')
        return storage.LocalVolumeStorage(volume_storage)

    return None
