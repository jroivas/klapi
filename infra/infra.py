class InfraProvider(object):

    def pool(self, name):
        """ Get pool instance by name

        @param name Pool name to get
        @returns Pool instance
        """
        return None

    def createPool(self, opts):
        """ Create pool instance defined by options

        @param opts Options defining the pool
        @returns Pool instance
        """
        return None

    def definePool(self, name, location, pool_type='dir'):
        """ Define a new pool options

        @param name Name of pool
        @param location Location of pool
        @param pool_type Type of pool
        @returns Options which can be passed to createPool
        """
        return ""

    def definePoolDir(self, name, location):
        """ Define a new pool options for directory

        @param name Name of pool
        @param location Location of pool
        @param pool_type Type of pool
        @returns Options which can be passed to createPool
        """
        return self.definePool(name, location)

    def registerPool(self, name, location):
        """ Register pool to system. This really creates the pool

        @param name Name of pool
        @param location Location of pool
        @returns Pool instance
        """
        return self.createPool(self.definePoolDir(name, location))

    def registerVolume(self, pool, location):
        """ Register a volume to pool

        @param pool Name of pool
        @param location Location of storage
        """
        pass


import virsh

def provider(sets):
    infr = sets.get('infra', None)
    if infr is None:
        return None

    if infr == 'libvirt' or infr == 'virsh':
        conn = sets.get('infra_connection', None)
        storage_name = sets.get('volume_storage_name', None)
        storage_loc = sets.get('volume_storage', None)
        return virsh.Virsh(conn)

    return None
