import libvirt
import os
import string

class Virsh(object):
    def __init__(self, connection):
        self.connection = connection
        self.conn = None
        self.connect() # FIXME Do we want autoconnect?
        self.drive_letters = list(string.lowercase)

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
    <devices>
        <input type='mouse' bus='ps2'/>
        <graphics type='vnc' port='-1' autoport='yes' listen='0.0.0.0'>
            <listen type='address' address='0.0.0.0'/>
        </graphics>
        <console type='pty'/>
        <video>
          <model type='cirrus'/>
        </video>
        <memballoon model='virtio'/>
        %(extradevices)s
    </devices>
    %(extra)s
</domain>""" % data

    def simpleDomain(self, name, hypervisor='kvm'):
        data = {
            'name': name,
            'hypervisor': hypervisor,
            'memory': 256 * 1024,
            'cpus': 1,
            'arch': 'x86_64',
            'extradevices': '',
            'extra': ''
        }
        return self.setupDomain(data)

    def customDomain(self, name, cpus, mem, arch='x86_64', hypervisor='kvm', extradevices='', extra=''):
        data = {
            'name': name,
            'hypervisor': hypervisor,
            'memory': mem,
            'cpus': cpus,
            'arch': arch,
            'extradevices': extradevices,
            'extra': extra
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

    def fileStorage(self, location, format='qcow2', letter='', virtio=True):
        data = {
            'type': 'file',
            'device': 'disk',
            'driver': 'qemu',
            'driver_type': format,
            'source': location,
            'extra': ''
            }

        if virtio:
            target_type = 'vd'
            data['target_bus'] = 'virtio'
        else:
            target_type = 'hd'
            data['target_bus'] = 'ide'

        if not letter:
            data['target'] = target_type + self.drive_letters.pop(0)
        else:
            data['target'] = target_type + letter

        return self.setupStorage(data)

    def cdromStorage(self, location, letter=''):
        data = {
            'type': 'file',
            'device': 'cdrom',
            'driver': 'qemu',
            'driver_type': 'raw',
            'target_bus': 'ide',
            'source': location,
            'extra': '<readonly/>'
            }

        if not letter:
            data['target'] = 'hd' + self.drive_letters.pop(0)
        else:
            data['target'] = 'hd' + letter

        return self.setupStorage(data)

    def volume(self, location, size, format='qcow2'):
        return """<volume type='file'>
  <name>%s</name>
  <capacity unit='bytes'>%s</capacity>
  <allocation unit='bytes'>%s</allocation>
  <target>
    <format type='%s'/>
    <permissions>
      <mode>0644</mode>
    </permissions>
  </target>
</volume>
""" % (os.path.basename(location), size, 0, format)

    def pool(self, name):
        return self.conn.storagePoolLookupByName(name)

    def definePool(self, name, location, pool_type='dir'):
        return """<pool type='%(type)s'>
  <name>%(name)s</name>
  <target>
    <path>%(location)s</path>
    <permissions>
      <mode>0755</mode>
    </permissions>
  </target>
  %(extra)s
</pool>
""" % {
        'type': pool_type,
        'name': name,
        'location': location,
        'extra': ''
      }

    #def definePoolDir(self, name, location):
    #    return self.definePool(name, location)

    def createPool(self, xml):
        obj = self.conn.storagePoolDefineXML(xml)
        obj.create()
        return obj

    def createVolume(self, pool, xml):
        return pool.createXML(xml)

    def defineNetwork(self, network='default', driver='virtio', mac='', pci_address=''):
        if mac:
            mac_str = "<mac address='%s'/>" % (mac)
        else:
            mac_str = ''

        if pci_address:
            pci_str = "<address type='pci' %s/>" % (pci_address)
        else:
            pci_str = ''

        return """
    <interface type='network'>
      <source network='%s'/>
      %s
      <model type='%s'/>
      %s
    </interface>
""" % (network, mac_str, driver, pci_str)
