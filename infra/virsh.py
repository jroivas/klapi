import libvirt
import os
import string
try:
    import xml.etree.cElementTree as ElementTree
except ImportError:
    from xml.etree import ElementTree

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

    def defineNetwork(self, data):
        if 'forward' in data:
            forward_mode = data['forward']
        else:
            forward_mode = 'none'

        if forward_mode in ['nat', 'bridge', 'route']:
            data['forward'] = "<forward mode='%s' />\n" % (data['forward'])
        else:
            data['forward'] = ''

        if forward_mode in ['nat', 'route', 'none']:
            data['forward'] += "<bridge stp='on' delay='0'/>\n"
        elif forward_mode == 'bridge' and 'bridge_name' in data:
            data['forward'] += "<bridge name='%s'/>\n" % (data['brigde_name'])

        if 'extra' not in data:
            data['extra'] = ''

        if forward_mode != 'bridge' and 'address' in data and 'netmask' in data:
            data['extra'] += "<ip address='%(address)s' netmask='%(netmask)s'>\n" % (data)
            if 'dhcp_start' in data and 'dhcp_end' in data:
                data['extra'] += "<dhcp>\n<range start='%(dhcp_start)s' end='%(dhcp_end)s' />\n</dhcp>\n" % (data)
            data['extra'] += '</ip>\n'

        xml = """<network>
    <name>%(name)s</name>
    %(forward)s
    %(extra)s
</network>
""" % (data)
        return xml

    def network(self, name):
        try:
            return self.conn.networkLookupByName(name)
        except:
            return None

    def createNetwork(self, xml):
        net = self.conn.networkDefineXML(xml)
        if net:
            net.create()

        return net

    def defineNatNetwork(self, name, ip, netmask='255.255.255.0', dhcp=True):
        data = {
            'name': name,
            'address': ip,
            'netmask': netmask,
            'forward': 'nat',
            'extra': ''
        }
        if dhcp:
            parts = [int(x) for x in ip.split('.')]
            if len(parts) != 4:
                raise ValueError('Invalid IP for network: %s' % (ip))
            parts[3] += 1
            data['dhcp_start'] = '.'.join([str(x) for x in parts])
            if parts[3] < 254:
                parts[3] = 254
            data['dhcp_end'] = '.'.join([str(x) for x in parts])

        return self.defineNetwork(data)

    def defineNetworkInterface(self, network, driver='virtio', mac='', pci_address=''):
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

    def domState(self, dom):
        states = {
            libvirt.VIR_DOMAIN_NOSTATE: 'no state',
            libvirt.VIR_DOMAIN_RUNNING: 'running',
            libvirt.VIR_DOMAIN_BLOCKED: 'blocked',
            libvirt.VIR_DOMAIN_PAUSED: 'paused',
            libvirt.VIR_DOMAIN_SHUTDOWN: 'being shut down',
            libvirt.VIR_DOMAIN_SHUTOFF: 'shut off',
            libvirt.VIR_DOMAIN_CRASHED: 'crashed',
        }
        #[state, maxmem, mem, ncpu, cputime] = dom.info()
        [state, _] = dom.state()
        return states.get(state, state)


    def domItems(self, dom_xml, item_class, item_type, item_name, element):
        sources = set()
        tree = ElementTree.fromstring(dom_xml)

        for source in tree.findall('%s/%s/%s' % (item_class, item_type, item_name)):
            file_item = source.get(element)
            sources.update([file_item])

        return list(sources)

    def deviceItems(self, dom, item_type, item_name='source', element='file'):
        dom_xml = dom.XMLDesc(0)
        return self.domItems(dom_xml, 'devices', item_type, item_name, element)
