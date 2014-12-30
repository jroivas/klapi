import libvirt

class Virsh(object):
    def __init__(self, connection):
        self.connection = connection
        self.conn = None
        self.connect()

    def connect(self):
        try:
            self.conn = libvirt.open(self.connection)
        except:
            return False

        return True

    @property
    def connected(self):
        try:
            return self.conn is not None and self.conn.isAlive()
        except:
            return False

    def setupDomain(self, data):
        return """<domain type='%(hypervisor)s'>
    <name>%(name)s</name>
    <memory unit='KiB'>%(memory)s</memory>
    <vcpu>%(cpus)s</vcpu>
    <os>
        <type arch='%(arch)s'>hvm</type>
    </os>
    %(extra)s
</domain>""" % data

    def simpleDomain(self, name, hypervisor='kvm'):
        data = {
            'name': name,
            'hypervisor': hypervisor,
            'memory': 256 * 1024,
            'cpus': 1,
            'arch': 'x86_64',
            'extra': ''
        }
        return self.setupDomain(data)

    def createDomain(self, xml):
        return self.conn.defineXML(xml)

    def getDomain(self, name):
        return self.conn.lookupByName(name)

    def setupStorage(self, data):
        return """
    <disk type='%(type)s' device='%(device)s'>
        <driver name='%(driver)s' type='%(driver_type)s' />
        <target dev='%(target)s' bus='%(target_bus)s' />
        <source file='%(source)s' />
        %(extra)s
    </disk>
    """ % data

    def fileStorage(self, location, format='qcow2'):
        return self.setupStorage({
            'type': 'file',
            'device': 'disk',
            'driver': 'qemu',
            'driver_type': format,
            'target': 'vda',
            'target_bus': 'virtio',
            'source': location,
            'extra': ''
            });

    def cdromStorage(self, location):
        return self.setupStorage({
            'type': 'file',
            'device': 'cdrom',
            'driver': 'qemu',
            'driver_type': 'raw',
            'target': 'hda',
            'target_bus': 'ide',
            'source': location,
            'extra': '<readonly/>'
            });
