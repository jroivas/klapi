# KLAPI

Kleine cLoud API


## Install

You need flask and libvirt-python to get minimum local setup working.

Recommended way is to use virtualenv:

    virtualenv --system-site-packages flask
    flask/bin/pip install flask
    flask/bin/pip install flask-httpauth
    flask/bin/pip install libvirt-python


Tools required on host system:

 - qemu-img


## Add users

Start the application and setup first user.
