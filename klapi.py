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
    db.create(_db, 'machines', ['id', 'name', 'address', 'owner'])
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

"""
@app.route('/todo/api/v1.0/tasks', methods=['GET'])
def get_tasks():
    return jsonify({'tasks': tasks})
"""

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
    return jsonify({'machines': res})

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

def get_volume_from_image(image, prefix=''):
    img = image.provider(settings.settings())
    vol = image.volume_provider(settings.settings())

    try:
        src_img = img.get(image)
        return vol.copyFrom(src_img, prefix=prefix)
    except:
        return ''

@app.route(api_url + '/machine', methods=['POST'])
@auth.login_required
def post_machine():
    if not request.json:
        abort(400)

    res = {
        'size': '',
        'type': '',
        'image': '',
        'cdrom': '',
        }
    if 'size' in request.json:
       res['size'] = request.json['size']
    if 'type' in request.json:
       res['type'] = request.json['type']
    if 'image' in request.json:
       res['image'] = request.json['image']
    if 'cdrom' in request.json:
       res['cdrom'] = request.json['cdrom']

    inf = infra.provider(settings.settings())

    volume = get_volume_from_image(res['image'], uuid.uuid4())

    #_db = db.connect(settings.settings())
    #res = db.select(_db, 'machines', where='owner=\'%s\'' % auth.username())
    #return jsonify({'machines': res})

"""
@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = filter(lambda t: t['id'] == task_id, tasks)
    if len(task) == 0:
        abort(404)
    return jsonify({'task': task[0]})

@app.route('/todo/api/v1.0/tasks', methods=['POST'])
def create_task():
    if not request.json or 'title' not in request.json:
        abort(400)
    task = {
        'id': tasks[-1]['id'] + 1,
        'title': request.json['title'],
        'description': request.json.get('description', ""),
        'done': False
    }
    tasks.append(task)
    return jsonify({'task': task}), 201

@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = filter(lambda t: t['id'] == task_id, tasks)
    if len(task) == 0:
        abort(404)
    if not request.json:
        abort(400)
    if 'title' in request.json and type(request.json['title']) != unicode:
        abort(400)
    if 'description' in request.json and type(request.json['description']) is not unicode:
        abort(400)
    if 'done' in request.json and type(request.json['done']) is not bool:
        abort(400)
    task[0]['title'] = request.json.get('title', task[0]['title'])
    task[0]['description'] = request.json.get('description', task[0]['description'])
    task[0]['done'] = request.json.get('done', task[0]['done'])
    return jsonify({'task': task[0]})

@app.route('/todo/api/v1.0/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = filter(lambda t: t['id'] == task_id, tasks)
    if len(task) == 0:
        abort(404)
    tasks.remove(task[0])
    return jsonify({'result': True})

def make_public_task(task):
    new_task = {}
    for field in task:
        if field == 'id':
            new_task['uri'] = url_for('get_task', task_id=task['id'], _external=True)
        else:
            new_task[field] = task[field]
    return new_task
"""

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)
