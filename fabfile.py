from fabric.api import *
from fabvenv import virtualenv
from os import path

env.hosts = ['me@example.com']
home = '/var/www/example/'
project = path.join(home, 'backend/')
venv = path.join(home, 'env')
logl = path.join(home, 'log/')


def pull(*args):
    with cd(project):
        run('git pull -u origin master')
        run('chown www-data:www-data -R *')


def reset():
    run('touch %s' % path.join(home, 'reload'))
    run('service nginx reload')


def pull_in_server():
    pull()
    jsons()
    reset()
    doc()


def clean():
    with cd(project):
        run('find . -name "*.pyc" -exec rm -rf {} \;')
        run('rm -rf /tmp/cache/')


def sync():
    local("git pull origin master")
    local("git push origin master")


def serlog():
    run('tail -n 100 %s' % path.join(logl, 'uwsgi.log'))


def doc():
    with cd(project):
        with virtualenv(venv):
            run('./manager.py doc')


def jsons():
    with cd(project):
        with virtualenv(venv):
            run('./manager.py jsons')


def deploy():
    sync()
    pull_in_server()
    serlog()


def requirements():
    sync()
    pull()
    with cd(project):
        with virtualenv(venv):
            run('pip install -r requirements')
        reset()
    serlog()


def errors():
    run('tail -n 100 %s' % path.join(logl, 'nginx-error.log'))


def log():
    run('tail -n 100 %s' % path.join(logl, 'nginx-access.log'))
