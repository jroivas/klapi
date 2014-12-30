import virsh

def provider(sets):
    infr = sets.get('infra', None)
    if infr is None:
        return None

    if infr == 'libvirt' or infr == 'virsh':
        conn = sets.get('infra_connection', None)
        return virsh.Virsh(conn)

    return None
