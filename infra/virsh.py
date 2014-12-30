import libvirt

class Virsh(object):
    def __init__(self, connection):
        self.connection = connection
        self.conn = None
        self.connected = self.connect()

    def connect(self):
        try:
            self.conn = libvirt.open(self.connection)
        except:
            return False

        return True

    @property
    def connected(self):
        try:
            return self.conn is not None and self.connected and self.conn.isAlive()
        except:
            return False
