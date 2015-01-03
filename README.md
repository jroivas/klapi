# KLAPI

Kleine cLoud API

Copyright (c)2014-2015 Jouni Roivas <jroivas@iki.fi>

Released under MIT license. See LICENSE for more info.


## Install

You need flask, pyzmq (ZeroMQ), qemu-img, libvirt,
and python-libvirt (libvirt-python) to get minimum setup working.

On Debian/Ubuntu first do:

    sudo apt-get install kvm
    sudo apt-get install qemu-utils
    sudo apt-get install libvirt-bin
    sudo apt-get install python-libvirt
    sudo apt-get install python-dev

Start the libvirt service (may be different depending of your system):

    sudo service libvirt-bin start
    sudo service libvirtd start

In order to setup Ubuntu cloud images you need cloud utils:

    sudo apt-get install "cloud-init-utils|cloud-utils"

Recommended way to setup flask and other Python dependencies by using virtualenv:

    sudo apt-get install virtualenv
    virtualenv --system-site-packages flask
    flask/bin/pip install flask
    flask/bin/pip install flask-httpauth
    flask/bin/pip install libvirt-python
    flask/bin/pip install pyzmq


## Settings

In order for klapi to work, proper setting.py is required.
Use settings.py.sample as base:

    cp setting.py.sample settings.py

If you take the default settings, create images and volumes folders:

    sudo mkdir -p /usr/local/klapi/images
    sudo mkdir -p /usr/local/klapi/volumes
    sudo chmod 777 /usr/local/klapi/volumes

Next you need to download base images, let's take [Ubuntu cloud images](https://cloud-images.ubuntu.com/).
For example [trusty image](https://cloud-images.ubuntu.com/trusty/current/trusty-server-cloudimg-amd64-disk1.img).

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

You need to start the backend as well:

    ./klapi-backend.py

Start order of appliction and backend does not matter. They utilize ZeroMQ (0MQ)
for communication. Next one should be able to fetch the main page:

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

At least one image is needed to setup a machine properly. To list available base images:

    curl -u testuser:4RkSUsNYdM4fdDoCjhJK -H "Content-Type: application/json" -X GET http://localhost:5050/klapi/v0.1/image

Result will be (if you downloaded trusty cloud image):

    {
      "images": [
        "trusty-server-cloudimg-amd64-disk1"
      ]
    }

If everything is in place you should be now able to create new machine:

    curl -u testuser:4RkSUsNYdM4fdDoCjhJK -H "Content-Type: application/json" -X POST -d '{"image": "trusty-server-cloudimg-amd64-disk1"}' http://localhost:5050/klapi/v0.1/machine

You will be given id to the machine:

    {
      "id": "e4bc9c6f-ce67-448a-98f5-140c409937d2",
      "uri": "http://localhost:5050/klapi/v0.1/machine/e4bc9c6f-ce67-448a-98f5-140c409937d2"
    }

To get more information about it (replace ID at the end with given one):

    curl -u testuser:4RkSUsNYdM4fdDoCjhJK -X GET http://localhost:5050/klapi/v0.1/machine/e4bc9c6f-ce67-448a-98f5-140c409937d2

Example details output:

    {
      "active": 1,
      "address": "",
      "base": "trusty-server-cloudimg-amd64-disk1",
      "config": {
          "password": "iEQ1xYH6",
      },
      "id": "e4bc9c6f-ce67-448a-98f5-140c409937d2",
      "max-cpus": 1,
      "max-memory": 262144,
      "memory-stats": {
        "actual": 262144,
        "rss": 235412,
        "swap_in": 0
      },
      "owner": "testuser",
      "state": "running"
    }

Destroying the machine is easy as:

    curl -u testuser:4RkSUsNYdM4fdDoCjhJK -X DELETE http://localhost:5050/klapi/v0.1/machine/e4bc9c6f-ce67-448a-98f5-140c409937d2


### Options for machine

Previously we gave only "image" as parameter for machine creation. It supports at least these values:

    memory   Value is given in KiB (default 256 MiB)
    cpus     Number of CPUs (default 1)
    image    Base image for VM
    cdrom    CDROM image to attach
    size     Disk image size
    name     Machine name (default uuid4)


These need to be given as JSON like "image" was given previously.
For example this shows how to use almost all of those variables in a query:

    curl -u testuser:4RkSUsNYdM4fdDoCjhJK -H "Content-Type: application/json" -X POST -d '{"image": "trusty-server-cloudimg-amd64-disk1", "memory": 512000, "cpus": 2, "size": "40G"}' http://localhost:5050/klapi/v0.1/machine


## Network config

By default setup.py script creates NAT bridge, and does not support different schemes.
It's still possible to enable more complex setups, but for now those need to be manually created.
Good resource for [setting virtual network](http://wiki.libvirt.org/page/VirtualNetworking).

Just create a named network, and put the name to settings as 'network_name'.
