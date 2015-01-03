#!flask/bin/python
from flask import Flask, jsonify
from flask import abort
from flask import make_response
from flask import request
from flask import url_for
from flask.ext.httpauth import HTTPBasicAuth
import settings
from db import db
from images import images
from infra import infra
from actions import actions
import utils
import os
import setup
import json

app = Flask(__name__)
auth = HTTPBasicAuth()

api_version = 'v0.1'
api_prefix = 'klapi'
api_url = '/%s/%s' % (api_prefix, api_version)

_db = None

@auth.error_handler
def unauthorized():
    return make_response(jsonify({'error': 'Unauthorized access'}), 401)

@app.before_request
def before_request():
    setup.create_db()
    _db = db.connect(settings.settings())
    res = db.select(_db, 'users', ['pass'], 'name=\'%s\'' % ('admin'))
    if res is None or not res:
        admin_pass = utils.generatePassword(20)
        db.insert(_db, 'users',
            ['admin',
            admin_pass,
            utils.generateApiKey()])
        print ('Password for admin: "%s", keep this in safe place!\n' % (admin_pass))

@app.teardown_request
def teardown_request(exception):
    if _db is not None:
        _db.close()

@auth.get_password
def get_password(username):
    _db = db.connect(settings.settings())
    res = db.select(_db, 'users', ['pass'], 'name=\'%s\'' % (username))
    for item in res:
        return str(item[0])
    return None

def abort_msg(code, msg):
    abort(make_response(jsonify({'error': msg}), code))

@app.errorhandler(400)
def not_found400(error):
    return make_response(jsonify({'error': 'Item does not exist'}), 400)

@app.errorhandler(404)
def not_found404(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route('/' + api_prefix, methods=['GET'])
def klapi():
    return jsonify({api_prefix: api_version})

@app.route(api_url, methods=['GET'])
def klapi_version():
    return jsonify({api_prefix + '/' + api_version: ['ids']})

@app.route(api_url + '/user', methods=['GET'])
@auth.login_required
def user():
    data = {
        'user': auth.username()
    }
    _db = db.connect(settings.settings())
    res = db.select(_db, 'users', items=['apikey'], where='name=\'%s\'' % auth.username())
    if res:
        res = res[0]
        data['api_key'] = res[0]

    return jsonify(data)

@app.route(api_url + '/user', methods=['POST'])
@auth.login_required
def post_user():
    if auth.username() != 'admin':
        abort_msg(400, 'Access denied, admin needed!')

    if not request.json:
        abort_msg(400, 'Expected JSON parameters')

    if 'user' not in request.json:
        abort_msg(400, 'Value for "user" not defined')
    user = request.json['user']
    passwd = ''
    if 'password' in request.json:
        passwd = request.json['password']

    if user == 'admin':
        abort_msg(400, 'Can\'t create admin')

    _db = db.connect(settings.settings())
    res = db.select(_db, 'users', where='name=\'%s\'' % user)
    if res:
        abort_msg(400, 'User \"%s\" already exists' % user)

    if not passwd:
        passwd = utils.generatePassword(20)

    db.insert(_db, 'users',
        [user, passwd, utils.generateApiKey()])

    data = {
        'user': request.json['user'],
        'password': passwd
    }

    return jsonify(data)

@app.route(api_url + '/user', methods=['DELETE'])
@auth.login_required
def delete_user():
    if auth.username() != 'admin':
        abort_msg(400, 'Access denied, admin needed!')

    if not request.json:
        abort_msg(400, 'Expected JSON parameters')

    if 'user' not in request.json:
        abort_msg(400, 'Value for "user" not defined')

    user = request.json['user']
    _db = db.connect(settings.settings())
    res = db.select(_db, 'users', where='name=\'%s\'' % user)
    if not res:
        abort_msg(400, 'User \"%s\" does not exist' % user)

    res = db.delete(_db, 'users', where='name=\'%s\'' % user)

    data = {
        'deleted': request.json['user'],
    }

    return jsonify(data)

@app.route(api_url + '/user', methods=['PUT'])
@auth.login_required
def put_user():
    if not request.json:
        abort_msg(400, 'Expected JSON parameters')

    if 'password' in request.json:
        passwd = request.json['password']
        if not passwd:
            passwd = utils.generatePassword(20)

        _db = db.connect(settings.settings())
        db.update(_db, 'users', 'pass="%s"' % (passwd), where='name="%s"' % auth.username())
        data = {
            'user': auth.username(),
            'password': passwd
        }

        return jsonify(data)

    if 'api_key' in request.json:
        apikey = utils.generateApiKey()
        _db = db.connect(settings.settings())
        db.update(_db, 'users', 'apikey="%s"' % (apikey), where='name="%s"' % auth.username())

        data = {
            'user': auth.username(),
            'api_key': apikey
        }

        return jsonify(data)

    abort_msg(400, 'Expected "password" or "api_key"')

@app.route(api_url + '/machine', methods=['GET'])
@auth.login_required
def machine():
    _db = db.connect(settings.settings())
    user = auth.username()
    if user == 'admin':
        res = db.select(_db, 'machines')
    else:
        res = db.select(_db, 'machines', where='owner=\'%s\'' % user)
    items = [x[0] for x in res]
    return jsonify(
    {
        'machines': [

            {
            'uri': url_for('machine_id', machine_id=x, _external=True),
            'id': x
            }
            for x in items]
    })

@app.route(api_url + '/machine/<string:machine_id>', methods=['GET'])
@auth.login_required
def machine_id(machine_id):
    user = auth.username()
    _db = db.connect(settings.settings())
    if user == 'admin':
        res = db.select(_db, 'machines', where='id=\'%s\'' % machine_id)
    else:
        res = db.select(_db, 'machines', where='id=\'%s\' AND owner=\'%s\'' % (machine_id, user))
    if not res:
        abort_msg(400, 'Machine "%s" not found' % (machine_id))

    res = res[0]
    inf = infra.provider(settings.settings())
    dom = inf.getDomain(res[0])
    if not dom or dom is None:
        abort(400)

    data = {
        'id': res[0],
        'base': res[1],
        'address': res[2],
        'config': json.loads(res[4]),
        'active': dom.isActive(),
        'max-memory': dom.maxMemory(),
        #'max-cpus': dom.maxVcpus(),
        #'memory-stats': dom.memoryStats(),
        #'info': dom.info(),
        #'cpus': dom.vcpus(),
        #'state': '%s' % dom.state(),
        #'state': '%s' % dir(dom),
        'state': inf.domState(dom),
        'owner': res[3]
    }
    #data['vols'] = inf.deviceItems(dom, 'disk')

    if dom.isActive():
        data['max-cpus'] = dom.maxVcpus()
        data['memory-stats'] = dom.memoryStats()
    return jsonify(data)

@app.route(api_url + '/machine/<string:machine_id>', methods=['DELETE'])
@auth.login_required
def machine_del(machine_id):
    user = auth.username()
    _db = db.connect(settings.settings())
    if user == 'admin':
        res = db.select(_db, 'machines', where='id=\'%s\'' % machine_id)
    else:
        res = db.select(_db, 'machines', where='id=\'%s\' AND owner=\'%s\'' % (machine_id, user))

    if not res:
        abort_msg(400, 'Machine "%s" not found' % (machine_id))

    res = res[0]
    inf = infra.provider(settings.settings())
    dom = inf.getDomain(res[0])
    if not dom or dom is None:
        abort(400)

    if dom.isActive():
        dom.destroy()

    flags = 0
    if dom.hasManagedSaveImage():
        flags |= libvirt.VIR_DOMAIN_UNDEFINE_MANAGED_SAVE

    if dom.snapshotNum() > 0:
        flags |= VIR_DOMAIN_UNDEFINE_SNAPSHOTS_METADATA

    vol_provider = images.volume_provider(settings.settings())
    vols = inf.deviceItems(dom, 'disk')

    error_msg = ''
    try:
        dom.undefineFlags(flags)
    except:
        error_msg = 'ERROR: Undefining domain: %s' % macine_id
        print (error_msg)

    error_msg += vol_provider.removeVolumes(vols)

    _db = db.connect(settings.settings())
    db.delete(_db, 'machines', where='id=\'%s\'' % machine_id)

    data = {'removed': machine_id}
    if error_msg:
        data['error'] = error_msg

    return jsonify(data)

@app.route(api_url + '/image', methods=['GET'])
@auth.login_required
def image():
    img = images.provider(settings.settings())
    return jsonify({'images': img.list()})

@app.route(api_url + '/image/<string:img_id>', methods=['GET'])
@auth.login_required
def image_id(img_id):
    img = images.provider(settings.settings())
    loc = img.get(img_id)
    if loc is None:
        abort(404)

    res = {
        'image': img_id,
        'location': loc,
        'uri': url_for('get_image', img_id=img_id, _external=True),
    }

    if loc.lower().endswith('.img'):
        res['type'] = 'img'
    elif loc.lower().endswith('.iso'):
        res['type'] = 'iso'
    elif loc.lower().endswith('.ext2'):
        res['type'] = 'ext2'

    return jsonify(res)

@app.route(api_url + '/image/get/<string:img_id>', methods=['GET'])
@auth.login_required
def get_image(img_id):
    img = images.provider(settings.settings())
    loc = img.get(img_id)
    if loc is None:
        abort(404)

    with open(loc, 'r') as fd:
        return fd.read()

@app.route(api_url + '/machine/<string:machine_id>', methods=['PUT'])
@auth.login_required
def put_machine(machine_id):
    if not request.json:
        abort_msg(400, 'Expected JSON input')

    user = auth.username()
    _db = db.connect(settings.settings())
    if user == 'admin':
        res = db.select(_db, 'machines', where='id=\'%s\'' % machine_id)
    else:
        res = db.select(_db, 'machines', where='id=\'%s\' AND owner=\'%s\'' % (machine_id, user))
    if not res:
        abort_msg(400, 'Machine "%s" not found' % (machine_id))

    res = res[0]
    inf = infra.provider(settings.settings())
    dom = inf.getDomain(res[0])
    if not dom or dom is None:
        abort_msg(400, 'Machine "%s" not in backedn' % (machine_id))

    if 'operation' not in request.json:
        abort_msg(400, 'No operation defined')

    data = {}
    if request.json['operation'] == 'reboot':
        data['result'] = dom.reboot()
    elif request.json['operation'] == 'reset':
        data['result'] = dom.reset()
    elif request.json['operation'] == 'shutdown':
        data['result'] = dom.shutdown()
    elif request.json['operation'] == 'start':
        st = dom.state()[0]
        if st in [0,4,5,6]:
            data['result'] = dom.create()
        else:
            abort_msg(400, 'Can\'t start, invalid state: %s' % (inf.domState(dom)))
    elif request.json['operation'] == 'forceoff':
        data['result'] = dom.destroy()
    elif request.json['operation'] == 'suspend':
        data['result'] = dom.suspend()
    elif request.json['operation'] == 'resume':
        data['result'] = dom.resume()
    else:
        abort_msg(400, 'Unknown operation: %s' % (request.json['operation']))

    data[request.json['operation']] = machine_id
    return jsonify(data)

@app.route(api_url + '/machine', methods=['POST'])
@auth.login_required
def post_machine():
    if not request.json:
        abort_msg(400, 'Expected JSON input')

    # TODO: quota per user

    res = {
        'memory': 256 * 1024, # FIXME some reasonable default
        'cpus': 1,
        'name': utils.generateID(),
        'net': '',
        'image': '',
        'size': '',
        'cdrom': '',
        }
    if 'mem' in request.json:
       res['memory'] = request.json['mem']
    if 'memory' in request.json:
       res['memory'] = request.json['memory']
    if 'size' in request.json:
       res['size'] = request.json['size']
    if 'cpus' in request.json:
        try:
           res['cpus'] = int(request.json['cpus'])
        except:
            pass
    if 'image' in request.json:
       res['image'] = request.json['image']
    if 'cdrom' in request.json:
       res['cdrom'] = request.json['cdrom']
    if 'name' in request.json:
       res['name'] = request.json['name']

    _db = db.connect(settings.settings())
    db.insert(_db, 'machines', [res['name'], '', '', auth.username(), ''])

    act = actions.provider(settings.settings())
    act.sendActionNow({'createMachine': res}, None)

    data = {
        'uri': url_for('machine_id', machine_id=res['name'], _external=True),
        'id': res['name']
    }

    return jsonify(data)

if __name__ == '__main__':
    port = 5050
    sets = settings.settings()
    if 'server_port' in sets:
        port = int(sets['server_port'])
    app.run(host='0.0.0.0', port=port, debug=True)
