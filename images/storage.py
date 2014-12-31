import os
import shutil

class LocalVolumeStorage(object):
    def __init__(self, location):
        self.location = location
        try:
            os.makedirs(self.location, 0777)
        except:
            pass

    def list(self):
        return os.listdir(self.location)

    def copyFrom(self, source, prefix='', resize='', force=False):
        if not os.path.exists(source):
            raise ValueError('Source image does not exists: %s' % (source))

        name = os.path.basename(source)
        destname = self.location + '/' + prefix + name
        if not force and os.path.exists(destname):
            raise ValueError('Destination already exists: %s' % destname)

        # FIXME run these in backend
        os.system('qemu-img convert -O qcow2 "%s" "%s"' % (source, destname))

        if resize:
            os.system('qemu-img resize "%s" %s' % (destname, resize))

        """
        os.system('qemu-img convert -O qcow2 "%s" "%s"' % (source, destname + '.orig'))

        if resize:
            os.system('qemu-img resize "%s" %s' % (destname + '.orig', resize))

        os.system('qemu-img create -f qcow2 -b "%s" "%s"' % (destname + '.orig', destname))
        """

        #shutil.copyfile(source, destname)
        return destname

    def customize(self, image, source):
        if not os.path.exists(source + '.sh'):
            return False

        return True

    def get(self, name):
        d = self.list()
        if name in d:
            return self.location + '/' + name

        return None

    def remove(self, name):
        d = self.list()
        if name in d:
            os.remove(self.location + '/' + name)
            return True

        return False
