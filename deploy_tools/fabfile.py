import random

from fabric import Connection
from patchwork.files import append, exists, directory

REPO_URL = 'https://github.com/eailfly/superlist.git'
REMOTE_USER = 'vagrant'
SITE_NAME = 'superlits-staging.example.org'
PACKAGE = ['vim', 'git', 'python3-venv', 'nginx']


def _install_the_nessary_package(c, package):
    c.sudo(f'apt install {package} -y', echo=True)


def _create_directory_structure_if_necessary(c, site_folder):
    for subfolder in ('database', 'static', 'virtualenv', 'source'):
        directory(c, f'{site_folder}/{subfolder}')


def _get_latest_source(c, source_folder):
    if exists(c, source_folder + '/.git'):
        c.run(f'cd {source_folder} && git fetch')
    else:
        c.run(f'git clone {REPO_URL} {source_folder}')
    current_commit = c.local('git log -n 1 --format=%H')
    c.run(f'cd {source_folder} && git reset --hard {current_commit.stdout}')


def _update_settings(c, source_folder, host):
    settings_path = source_folder + '/superlists/settings.py'
    c.run(f"sed -i 's/DEBUG = True/DEBUG = False/' {settings_path}")
    c.run(f"sed -i 's/ALLOWED_HOSTS = \[\]/ALLOWED_HOSTS = [\"127.0.0.1\"]/' {settings_path}")
    secret_key_file = source_folder + '/superlists/secret_key.py'
    if not exists(c, secret_key_file):
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        key = ''.join(random.SystemRandom().choice(chars) for _ in range(50))
        append(c, secret_key_file, f'SECRET_KEY = "{key}"')
    append(c, settings_path, '\nfrom .secret_key import SECRET_KEY')


def _update_virtualenv(c, source_folder):
    virtualenv_folder = source_folder + '/../virtualenv'
    if not exists(c, virtualenv_folder + '/bin/pip'):
        c.run(f'python3 -m venv {virtualenv_folder}')
    c.run(f'{virtualenv_folder}/bin/pip install -r {source_folder}/requirements.txt')


def _update_static_files(c, source_folder):
    c.run(f'cd {source_folder}'
          f' && ../virtualenv/bin/python manage.py collectstatic --noinput')


def _update_database(c, source_folder):
    c.run(f'cd {source_folder}'
          f' && ../virtualenv/bin/python manage.py migrate --noinput')


def _set_webservers(c):
    c.put('nginx.template.conf')
    c.put('gunicorn-superlists-staging.service')
    c.sudo('mv nginx.template.conf /etc/nginx/sites-available/superlists')
    c.sudo('chown root.root /etc/nginx/sites-available/superlists')
    c.sudo('ln -s /etc/nginx/sites-available/superlists /etc/nginx/sites-enabled/superlists')
    c.sudo('rm /etc/nginx/sites-enabled/default')
    c.sudo('mv gunicorn-superlists-staging.service /etc/systemd/system/')
    c.sudo('chown root.root /etc/systemd/system/gunicorn-superlists-staging.service')
    c.sudo('systemctl daemon-reload')
    c.sudo('systemctl start nginx')
    c.sudo('systemctl start gunicorn-superlists-staging')


def deploy(c):
    # site_folder = f'/home/{REMOTE_USER}/sites/superlits-staging.example.org'
    # source_folder = site_folder + '/source'
    # package = ' '.join(PACKAGE)
    # _install_the_nessary_package(c, package)
    # _create_directory_structure_if_necessary(c, site_folder)
    # _get_latest_source(c, source_folder)
    # _update_settings(c, source_folder, SITE_NAME)
    # _update_virtualenv(c, source_folder)
    # _update_static_files(c, source_folder)
    # _update_database(c, source_folder)
    _set_webservers(c)


if __name__ == '__main__':
    connection = Connection(host='127.0.0.1',
                            user=REMOTE_USER,
                            port=2222,
                            connect_kwargs={
                                'key_filename': '../.vagrant/machines/default/virtualbox/private_key'
                            },
                            )
    deploy(connection)
    connection.close()
