import config
import os
import random
import string
import tempfile
import utils

class Image(config.Image):
    def __init__(self, name):
        super(Image, self).__init__(name)
        self.password = ''
        self.temp_init = ''

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
        tempdir = tempfile.gettempdir() + '/klapi_ubuntu_cloud_image'
        if not os.path.exists(tempdir):
            try:
                os.makedirs(tempdir)
            except:
                tempdir = ''

        if tempdir:
            try:
                os.chmod(tempdir, 0777)
            except:
                pass

        fd = tempfile.NamedTemporaryFile(delete=False)
        fd.write(data)
        fd.close()

        init_fd = tempfile.NamedTemporaryFile(delete=False, dir=tempdir)
        self.temp_init = init_fd.name

        os.system('cloud-localds "%s" "%s"' % (init_fd.name, fd.name))
        os.chmod(init_fd.name, 0666)

        os.unlink(fd.name)

    def extraDeviceConfig(self, infra):
        self._initCloud(password=utils.generatePassword())
        if self.temp_init:
           return infra.cdromStorage(self.temp_init)

        return ""

    def userdata(self):
        return {
            'password': self.password
            }
