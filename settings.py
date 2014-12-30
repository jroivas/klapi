def settings():
    return {
        'image': 'local',
        'image_storage': '/store/cloud/images/iso',
        'volume': 'local',
        'volume_storage': '/store/cloud/images/volume',
        'infra': 'libvirt',
        'infra_connection': 'qemu:///system',
        'db': 'sqlite3',
        'db_table': 'klapi.db'
    }
