#!flask/bin/python
import zmq
import sys
import threading
import json
import settings
import utils
import os
from db import db
from images import images
from infra import infra

class KlapiServer(threading.Thread):
    def __init__(self, sets):
        threading.Thread.__init__(self)

        self.port = 5555
        self.backend_name = 'klapi_backend'
        self.worker_count = 5

        if 'backend_port' in sets:
            self.port = sets['backend_port']
        if 'backend_name' in sets:
            self.backend_name = sets['backend_name']
        if 'backend_workers' in sets:
            self.worker_count = sets['backend_workers']

        self.running = False

    def _init_connection(self):
        context = zmq.Context()
        server = context.socket(zmq.ROUTER)
        server.bind('tcp://*:%s' % (self.port))

        backend = context.socket(zmq.DEALER)
        backend.bind('inproc://%s' % (self.backend_name))

        return (context, server, backend)

    def _deinit_connection(self, context, server, backend):
        server.close()
        backend.close()
        context.term()

    def launch_workers(self, context):
        workers = []
        for _ in range(self.worker_count):
            worker = KlapiWorker(context, self.backend_name)
            worker.start()
            workers.append(worker)

        return workers

    def init_poller(self, server, backend):
        poll = zmq.Poller()
        poll.register(server, zmq.POLLIN)
        poll.register(backend, zmq.POLLIN)

        return poll

    def serve(self, server, backend):
        self.running = True
        poll = self.init_poller(server, backend)

        print ('Klapi-backend on port %s (%s workers), worker IPC on "%s"' % (
            self.port, self.worker_count, self.backend_name))

        while self.running:
            sockets = dict(poll.poll())

            # Work as a simple proxy
            if server in sockets:
                data = server.recv_multipart()
                backend.send_multipart(data)
            if backend in sockets:
                data = backend.recv_multipart()
                server.send_multipart(data)

    def run(self):
        (context, server, backend) = self._init_connection()
        workers = self.launch_workers(context)

        self.serve(server, backend)

        self._deinit_connection(context, server, backend)
        for worker in self.workers:
            worker.join()

class KlapiWorker(threading.Thread):
    def __init__(self, context, backend_name):
        threading.Thread.__init__ (self)
        self.context = context
        self.backend_name = backend_name
        self.running = False

    def run(self):
        worker = self.context.socket(zmq.DEALER)
        worker.connect('inproc://%s' % (self.backend_name))
        self.running = True

        while self.running:
            ident, msg  = worker.recv_multipart()
            msg_json = json.loads(msg)

            result = self.handle(msg_json)
            if 'terminate' in result:
                self.running = False

            new_msg = json.dumps(result)
            worker.send_multipart([ident, new_msg])

        worker.close()

    def handle(self, msg):
        # TODO: Handle dict message, send back as dict
        if 'createMachine' in msg:
            self.createMachine(msg['createMachine'])
        return msg

    def createMachine(self, res):
        extras = []
        extra = ''

        base = ''

        inf = infra.provider(settings.settings())

        volume = self.get_volume_from_image(res['image'], utils.generateID() + '_', resize=res['size'])
        if volume:
            base = os.path.basename(res['image'])
            extras.append(inf.fileStorage(volume))

        cdrom = self.get_cdrom_image(res['cdrom'])
        if cdrom:
            if not base:
                base = os.path.basename(cdrom)
            extras.append(inf.cdromStorage(cdrom))

        image_extra_loader = None
        if volume or cdrom:
            item = cdrom
            if volume:
                item = volume

            image_extra_loader = self.image_extra_config(os.path.basename(item), res['name'])

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


        if 'network_name' in settings.settings():
            extras.append(inf.defineNetworkInterface(settings.settings()['network_name']))

        extradevices = '\n'.join(extras)

        dom_xml = inf.customDomain(res['name'], res['cpus'], res['memory'], extradevices=extradevices, extra=extra)
        dom = inf.createDomain(dom_xml)

        dom_res = dom.create()

        _db = db.connect(settings.settings())
        config_data = json.dumps(image_extra_userdata)
        config_data = config_data.replace('\'', '\\\'')
        db.update(_db, 'machines',
            'config=\'%s\'' % (config_data),
            where='id="%s"' % (res['name']))

    def get_volume_from_image(self, image, prefix='', resize=''):
        img = images.provider(settings.settings())
        vol = images.volume_provider(settings.settings())

        try:
            src_img = img.get(image)
            return vol.copyFrom(src_img, prefix=prefix, resize=resize)
        except Exception as e:
            print ('ERROR: %s' % (e))
            return ''

    def get_cdrom_image(self, image):
        img = images.provider(settings.settings())
        try:
            return img.get(image)
        except:
            return ''

    def image_extra_config(self, name, init_name):
        loader = images.config.ImageConfig()
        image_class = loader.search(name)
        if image_class is None:
            return None

        return image_class(init_name)

if __name__ == '__main__':
    server = KlapiServer(settings.settings())
    server.start()
    server.join()
