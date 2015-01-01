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
import uuid
import os

try:
    import cElementTree as ElementTree
except ImportError:
    from xml.etree import ElementTree

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
    _db = db.connect(settings.settings())
    db.create(_db, 'machines', ['id', 'base', 'address', 'owner'])
    db.create(_db, 'images', ['name', 'url', 'type'])
    db.create(_db, 'users', ['name', 'pass', 'apikey'])

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

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.route('/' + api_prefix, methods=['GET'])
def klapi():
    return jsonify({api_prefix: api_version})

@app.route(api_url, methods=['GET'])
def klapi_version():
    return jsonify({api_prefix + '/' + api_version: ['ids']})

@app.route(api_url + '/machine', methods=['GET'])
@auth.login_required
def machine():
    _db = db.connect(settings.settings())
    res = db.select(_db, 'machines', where='owner=\'%s\'' % auth.username())
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

def get_device_items(dom, item_type, item_name='source', element='file'):
    sources = set()
    tree = ElementTree.fromstring(dom.XMLDesc(0))

    for source in tree.findall('devices/%s/%s' % (item_type, item_name)):
        file_item = source.get(element)
        sources.update([file_item])

    return list(sources)

@app.route(api_url + '/machine/<string:machine_id>', methods=['GET'])
@auth.login_required
def machine_id(machine_id):
    _db = db.connect(settings.settings())
    res = db.select(_db, 'machines', where='id=\'%s\'' % machine_id)
    if not res:
        abort(400)

    res = res[0]
    inf = infra.provider(settings.settings())
    dom = inf.getDomain(res[0])
    if not dom or dom is None:
        abort(400)

    data = {
        'id': res[0],
        'base': res[1],
        'address': res[2],
        'active': dom.isActive(),
        'max-memory': dom.maxMemory(),
        #'max-cpus': dom.maxVcpus(),
        #'memory-stats': dom.memoryStats(),
        #'info': dom.info(),
        #'cpus': dom.vcpus(),
        #'state': '%s' % dom.state(),
        #'state': '%s' % dir(dom),
        'owner': res[3]
    }
    #data['vols'] = get_device_items(dom, 'disk')

    if dom.isActive():
        data['max-cpus'] = dom.maxVcpus()
        data['memory-stats'] = dom.memoryStats()
    return jsonify(data)

@app.route(api_url + '/machine/<string:machine_id>', methods=['DELETE'])
@auth.login_required
def machine_del(machine_id):
    _db = db.connect(settings.settings())
    res = db.select(_db, 'machines', where='id=\'%s\'' % machine_id)
    if not res:
        abort(400)

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

    #adisks = dom.XMLDesc(0)
    vol_provider = images.volume_provider(settings.settings())
    vols = get_device_items(dom, 'disk')

    error_msg = ''
    try:
        dom.undefineFlags(flags)
    except:
        error_msg = 'ERROR: Undefining domain: %s' % macine_id
        print (error_msg)


    # FIXME Clean up, and separate function/section
    for vol in vols:
        if not vol_provider.remove(os.path.basename(vol)):
            ok = False
            if vol.startswith('/tmp'):
                try:
                    os.remove(vol)
                    ok = True
                except:
                    ok = False
            if not ok:
                error_msg += '\nWARNING: Can\'t remove image: %s' % (vol)


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

def get_volume_from_image(image, prefix='', resize=''):
    img = images.provider(settings.settings())
    vol = images.volume_provider(settings.settings())

    try:
        src_img = img.get(image)
        return vol.copyFrom(src_img, prefix=prefix, resize=resize)
    except Exception as e:
        print ('ERROR: %s' % (e))
        return ''

def get_cdrom_image(image):
    img = images.provider(settings.settings())
    try:
        return img.get(image)
    except:
        return ''

def image_extra_config(name, init_name):
    loader = images.config.ImageConfig()
    image_class = loader.search(name)
    if image_class is None:
        return None

    return image_class(init_name)

@app.route(api_url + '/machine', methods=['POST'])
@auth.login_required
def post_machine():
    if not request.json:
        abort(400)

    res = {
        'memory': 256 * 1024, # FIXME some reasonable default
        'cpus': 1,
        'name': str(uuid.uuid4()),
        'net': '',
        'image': '',
        'size': '',
        'cdrom': '',
        }
    if 'mem' in request.json:
       res['memory'] = request.json['mem']
    if 'memory' in request.json:
       res['memory'] = request.json['mem']
    if 'mem' in request.json:
       res['memory'] = request.json['mem']
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

    inf = infra.provider(settings.settings())

    extras = []
    extra = ''

    base = ''
    volume = get_volume_from_image(res['image'], str(uuid.uuid4()) + '_', resize=res['size'])
    if volume:
        base = os.path.basename(res['image'])
        extras.append(inf.fileStorage(volume))

    cdrom = get_cdrom_image(res['cdrom'])
    if cdrom:
        if not base:
            base = os.path.basename(cdrom)
        extras.append(inf.cdromStorage(cdrom))

    image_extra_loader = None
    if volume or cdrom:
        item = cdrom
        if volume:
            item = volume

        image_extra_loader = image_extra_config(os.path.basename(item), res['name'])

    image_extra_userdata = {}
    if image_extra_loader is not None:
        print ('Found image loader: %s' % (image_extra_loader.base()))
        extra_device = image_extra_loader.extraDeviceConfig(inf)
        if extra_device:
            extras.append(extra_device)
        image_extra = image_extra_loader.extra()
        if image_extra:
            extra += image_extra

        image_extra_userdata = image_extra_loader.userdata()
        # TODO: Support other features

    extras.append(inf.defineNetwork())

    extradevices = '\n'.join(extras)

    dom_xml = inf.customDomain(res['name'], res['cpus'], res['memory'], extradevices=extradevices, extra=extra)
    dom = inf.createDomain(dom_xml)

    dom_res = dom.create()

    _db = db.connect(settings.settings())
    # FIXME Put more accurate info
    db.insert(_db, 'machines', [res['name'], base, '', auth.username()])

    data = {
        'uri': url_for('machine_id', machine_id=res['name'], _external=True),
        'id': res['name']
    }
    data.update(image_extra_userdata)

    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
