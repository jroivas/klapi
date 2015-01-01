# KLAPI

Kleine cLoud API


## Install

You need flask, qemu-img, libvirt, and python-libvirt (libvirt-python)
to get minimum setup working.

On Debian/Ubuntu first do:

    sudo apt-get install kvm
    sudo apt-get install qemu-utils
    sudo apt-get install libvirt-bin
    sudo apt-get install python-libvirt

Start the libvirt service (may be different depending of your system):

    sudo service libvirt-bin start
    sudo service libvirtd start

In order to boot up Ubuntu images you need cloud utils:

    sudo apt-get install "cloud-init-utils|cloud-utils"

Recommended way to setup flask is to use virtualenv:

    sudo apt-get install virtualenv
    virtualenv --system-site-packages flask
    flask/bin/pip install flask
    flask/bin/pip install flask-httpauth
    flask/bin/pip install libvirt-python


## Settings

In order for klapi to work, proper setting.py is required.
Use settings.py.sample as base:

    cp setting.py.sample settings.py

If you take the default settings, create images and volumes folders:

    sudo mkdir -p /usr/local/klapi/images
    sudo mkdir -p /usr/local/klapi/volumes
    sudo chmod 777 /usr/local/klapi/volumes

Next you need to download base images, let's take ubuntu cloud images from:
https://cloud-images.ubuntu.com/

For example trusty image:
https://cloud-images.ubuntu.com/trusty/current/trusty-server-cloudimg-amd64-disk1.img

Place it under /usr/local/klapi/images:

    sudo curl https://cloud-images.ubuntu.com/trusty/current/trusty-server-cloudimg-amd64-disk1.img -o /usr/local/klapi/images/trusty-server-cloudimg-amd64-disk1.img

## First run setup

You can run the first time setup to ensure database, admin user and
libvirt network are set up and working. For that there's simple setup
script called setup.py. It will read your settings and act accordingly.

    ./setup.py

Note console for admin password, it will be printed only once:

    Password for admin: "abcdefghijlkmnopqrst", keep this in safe place!

If you forget the password you can query it with setup tool:

    ./setup.py --show-admin-pass

It will print the admin password.

If network creation fails for some reason (for example IP range already defined),
you might want to remove it before tring again:

    virsh net-undefine NETWORK_NAME


## Run

Start the application:

    ./klapi.py

Fetch main page:

    curl http://localhost:5050/klapi

You can create user accounts only as admin. Create now a test user:

    curl -u admin:gumYqvmYXc4wHsvwtvIv -H "Content-Type: application/json" -X POST -d '{"user": "testuser"}' http://localhost:5050/klapi/v0.1/user

This should return something like:

    {
      "password": "4RkSUsNYdM4fdDoCjhJK",
      "user": "testuser"
    }

Now you can access klapi with this account:

    $ curl -u testuser:4RkSUsNYdM4fdDoCjhJK http://localhost:5050/klapi/v0.1/user
    {
      "api_key": "c0b9fda6-65dd-4ba7-b8fe-be7b45a28e6b",
      "user": "testuser"
    }

To list available base images, one of these is needed to setup a machine properly:

    curl -u testuser:4RkSUsNYdM4fdDoCjhJK -H "Content-Type: application/json" -X GET http://localhost:5050/klapi/v0.1/image

If everything is in place you should be now able to create new machine:

    curl -u testuser:4RkSUsNYdM4fdDoCjhJK -H "Content-Type: application/json" -X POST -d '{"image": "trusty-server-cloudimg-amd64-disk1"}' http://localhost:5050/klapi/v0.1/machine
