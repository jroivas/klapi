#!flask/bin/python

import settings
import sys
import utils
from db import db
from infra import infra

def create_db():
    _db = db.connect(settings.settings())
    db.create(_db, 'machines', ['id', 'base', 'address', 'owner', 'config'])
    db.create(_db, 'images', ['name', 'url', 'type'])
    db.create(_db, 'users', ['name', 'pass', 'apikey'])

def setup_admin(show_passwd=False):
    _db = db.connect(settings.settings())
    res = db.select(_db, 'users', ['pass'], 'name=\'%s\'' % ('admin'))
    if res is None or not res:
        admin_pass = utils.generatePassword(20)
        db.insert(_db, 'users',
            ['admin',
            admin_pass,
            utils.generateApiKey()])
        print ('Password for admin: "%s", keep this in safe place!' % (admin_pass))
    elif show_passwd:
        print ('Admin password: %s' % (res[0]))
    else:
        print ('Admin already set up')

def network_info(net):
    print ('Network: %s' % (net.name()))

def define_network():
    sets = settings.settings()
    if 'network_name' not in sets:
        return False

    inf = infra.provider(settings.settings())

    net = inf.network(sets['network_name'])
    if net is not None and net.name() == sets['network_name']:
        if not net.isActive():
            net.create()
        network_info(net)
        return True

    if 'network_ip' not in sets:
        print ('ERROR: No IP for network')
        return False

    net_xml = inf.defineNatNetwork(sets['network_name'], sets['network_ip'])
    net = inf.createNetwork(net_xml)
    if net is not None and net.name() == sets['network_name']:
        network_info(net)
        return True

    print ('Failed to setup network: %s' % (sets['network_name']))
    return False

def usage(name):
    print 'Usage: %s options' % (name)
    print '    -h | --help          Show help'
    print '    --show-admin-pass    Show admin password'

    sys.exit(1)

if __name__ == '__main__':
    show_admin = False
    if len(sys.argv) > 1:
        for item in sys.argv:
            if item == '--show-admin-pass':
                show_admin = True
            elif item == '--help' or item == '-h':
                usage(sys.argv[0])

    create_db()
    setup_admin(show_admin)
    define_network()
