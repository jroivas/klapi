import config
import os
import tempfile

class Image(config.Image):
    def __init__(self, name):
        super(Image, self).__init__(name)
        self.password = ''
        self.temp_init = ''

    def __del__(self):
        #if os.path.exists(self.temp_init):
        #   os.unlink(self.temp_init)
        pass

    def base(self):
        return 'Ubuntu cloud image'

    @classmethod
    def match(self, name):
        if 'trusty-server-cloudimg-amd64-disk1.img' in name:
            return True
        if 'utopic-server-cloudimg-amd64-disk1.img' in name:
            return True
        if 'precise-server-cloudimg-amd64-disk1.img' in name:
            return True

        return False

    def _initCloud(self, password='ubuntu', expire='False'):
        data ="""#cloud-config
password: %s
chpasswd: { expire: %s }
ssh_pwauth: True
""" % (password, expire)
        self.password = password

        fd = tempfile.NamedTemporaryFile(delete=False)
        fd.write(data)
        fd.close()

        init_fd = tempfile.NamedTemporaryFile(delete=False)
        self.temp_init = init_fd.name

        os.system('cloud-localds "%s" "%s"' % (init_fd.name, fd.name))

        os.unlink(fd.name)

    def extraDeviceConfig(self, infra):
        self._initCloud()
        if self.temp_init:
           return infra.fileStorage(self.temp_init, format='raw', virtio=False)
           #return infra.cdromStorage(self.temp_init)

        return ""
