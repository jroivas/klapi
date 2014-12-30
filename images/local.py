import os
import shutil
import thread
from images import ImageProvider

def thread_downloader(url, dest):
    os.chdir(dest)
    # FIXME Depends on wget
    print os.system('wget -q %s' % (url))

class LocalImageProvider(ImageProvider):
    def __init__(self, directory=''):
        self.dir = directory
        try:
            os.makedirs(self.dir, 0777)
        except:
            pass

    def update_db(self):
        self.images = {}
        for item in os.listdir(self.dir):
            (base, ext) = os.path.splitext(item)
            base = os.path.basename(base)
            self.images[base] = item

    def list(self):
        self.update_db()
        return self.images.keys()

    def get(self, name):
        self.update_db()
        img = self.images.get(name, None)
        if img is None:
            return None
        return self.dir + '/' + img

    def clone(self, name):
        img = self.get(name)

        (base, ext) = os.path.splitext(img)
        base = os.path.basename(base)

        index = 1
        img_name = 'clone%s_%s%s' % (index, base, ext)
        while os.path.exists(self.dir + '/' + img_name):
            index += 1
            img_name = 'clone%s_%s%s' % (index, base, ext)

        shutil.copyfile(img, self.dir + '/' + img_name)

        return 'clone%s_%s' % (index, base)

    def delete(self, name):
        self.update_db()

        for item in self.images:
            if item == name:
                img = self.get(name)
                os.remove(img)

        self.update_db()

    def add(self, url):
        if url.startswith('http') or url.startswith('ftp'):
            print ("Downloading...")
            #thread.start_new_thread(thread_downloader, (url, self.dir))
            # TODO backend for downloading...
            thread_downloader(url, self.dir)
            return
        elif url.starstwith('file://'):
            url = url[7:]

        if os.path.exists(url):
            img_name = os.path.basename(url)
            if os.path.exists(self.dir + '/' + img_name):
                raise ValueError('Image already exists: %s' % (img_name))

            shutil.copyfile(url, self.dir + '/' + img_name)

            return

        raise ValueError('Image not found: %s' % (url))
