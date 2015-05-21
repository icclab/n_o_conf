# -*- coding: utf-8 -*-
"""
Created on Fri Feb 27 09:42:19 2015

@author: Konstantin
"""

import keystoneclient.v2_0.client as ksclient
from novaclient import client as noclient
import configparser, time, os, copy, csv
import vm_control

from fabric.api import env, execute, task
import cuisine

@task
def update(package=None):
    cuisine.package_update(package)
    
@task
def upgrade(package=None):
    cuisine.package_upgrade(package)

@task
def install(package):
    cuisine.package_install(package)
    cuisine.package_ensure(package)
    
@task
def pip_install(package):
    cuisine.package_ensure('python-pip')
    command = str('pip install %s' % package)
    cuisine.sudo(command, shell=False)

@task
def upload_file(remote_location, local_location, sudo=False):
    cuisine.file_upload(remote_location, local_location, sudo=sudo)
    cuisine.file_ensure(remote_location)

@task
def chmod_file(chmod, remote_location):
    command = str('chmod %s %s' % (chmod, remote_location))
    cuisine.run(command, shell=False)

@task
def run_python_program(program=None, sudo=False):
    cuisine.file_ensure('/usr/bin/python')
    if sudo:
        cuisine.sudo(('/usr/bin/python %s' % program))
    else:
        cuisine.run(('/usr/bin/python %s' % program))
    
def get_vm_ips(vm_data):
    return [vm.networks.values()[0][0] for vm in vm_data]

def write_hosts_file(host_ip_list):
    with open('host_ips.csv', 'wb') as f:
        writer = csv.writer(f, delimiter=';', quotechar='|')
        [writer.writerow([str(host_ip)]) for host_ip in host_ip_list]

def read_hosts_file(path):
    with open(path, 'rb') as f:
        reader = csv.reader(f, delimiter=';', quotechar='|')
        host_ip_list = [row[0] for row in reader]
    return host_ip_list

@task    
def fix_docker_links():
    cuisine.sudo("ln -sf /usr/bin/docker /usr/local/bin/docker")
#    cuisine.sudo("sed -i '$acomplete -F _docker docker' /etc/bash_completion.d/docker")

@task    
def set_upstart(name):
    cuisine.upstart_ensure(name)
    
@task    
def set_auto_boot(name):
    cmd = ("update-rc.d %s defaults" % name)
    cuisine.sudo(cmd)

@task
def install_docker():
    installed = cuisine.command_check('docker -v')
    if not installed:
        cuisine.sudo("wget -qO- https://get.docker.com/ | sh")

@task
def upgrade_docker():
    installed = cuisine.command_check('docker -v')
    if installed:
        cuisine.sudo("wget -N https://get.docker.com/ | sh")

@task
def docker_build():
    cuisine.sudo("docker build -t master/nagios .")
    
@task
def docker_run():
    cuisine.sudo("sudo docker rm -f $(sudo docker ps -aq)")
    cuisine.sudo("docker run -d -p 172.17.42.1:8080:80 -h docker0 -t master/nagios")

@task
def a2enmod(module=None, sudo=True):
    cuisine.file_ensure('/usr/sbin/a2enmod')
    if sudo:
        cuisine.sudo(('/usr/sbin/a2enmod %s' % module))
    else:
        cuisine.run(('/usr/sbin/a2enmod %s' % module))
        
@task
def restart_service(service=None, sudo=True):
#    cuisine.upstart_ensure(service)
    if sudo:
        cuisine.sudo(('service %s restart' % service))
    else:
        cuisine.run(('service %s restart' % service))

def setup():
    execfile('openrc.py')

    
#ss -plnt sport eq :80

if __name__ == "__main__":       
    execfile('openrc.py')
    print os.environ['OS_USERNAME']
    config = configparser.ConfigParser()
    config.read('config.ini')
    print(config.sections())

    vm_credentials = dict(config['SSH_CREDENTIALS'])
    ssh_username = str(vm_credentials['ssh.username'])
    ssh_password = str(vm_credentials['ssh.password'])
    ssh_key_filename = str(vm_credentials['ssh.key_filename'])
    ssh_public_key_filename = str(vm_credentials['ssh.public_key_filename'])
    
    vm_list = []    
    
    with open('vm_list.csv', 'rb') as csvfile:
        listreader = csv.reader(csvfile, delimiter=';', quotechar='|')
        [vm_list.append(row[0]) for row in listreader]
    
    print vm_list
    
    VM_control = vm_control.VM_Control()
    VM_control.create_vms(vm_list)
#    vm_control.stop_vms(vm_list)
#    vm_control.start_vms(vm_list)
    ip_list = VM_control.get_free_floating_ips()
    VM_control.assign_floating_ip_to_vm('master',ip_list)
    vm_data = VM_control.get_vms_data(vm_list)
    ssh_url = VM_control.get_floating_ip('master')
    
    env.hosts = [ssh_url]
    env.user = ssh_username
    env.password = ssh_password
    env.key_filename = ssh_key_filename
    env.connection_attempts = 5
    
    execute(upload_file,'/etc/apt/sources.list','sources.list',sudo=True)
    execute(update)
    execute(upgrade)  
    execute(install, 'linux-headers-virtual')
    execute(install, 'linux-image-virtual')
    execute(install, ' linux-image-extra-virtual')
    execute(install, 'linux-virtual')
    execute(install_docker)
    execute(install, 'python-pip')
    execute(install, 'python-dev')
    execute(pip_install, 'dispy')
    execute(pip_install, 'ecdsa')
    execute(pip_install, 'pycrypto')
    execute(pip_install, 'fabric')
    execute(pip_install, 'cuisine')
    execute(pip_install, 'configparser')
    execute(pip_install, 'multiprocessing')

    
    host_ip_list = get_vm_ips(vm_data[1:])
    write_hosts_file(host_ip_list)
    test = read_hosts_file('host_ips.csv')
    execute(upload_file,'/etc/host_ips.csv','host_ips.csv',sudo=True)
    execute(upload_file,'/home/ubuntu/.ssh/id_rsa','id_rsa',sudo=True)
    execute(upload_file,'/home/ubuntu/.ssh/id_rsa.pub','id_rsa.pub',sudo=True)
    execute(chmod_file,'0600','/home/ubuntu/.ssh/id_rsa')
    execute(upload_file,'/home/ubuntu/config.ini','remote_config.ini',sudo=True)
    execute(upload_file,'/home/ubuntu/Dockerfile','Dockerfile',sudo=True)
    execute(upload_file,'/home/ubuntu/apache.init','apache.init',sudo=True)
    execute(upload_file,'/home/ubuntu/nagios.init','nagios.init',sudo=True)
    execute(upload_file,'/home/ubuntu/postfix.init','postfix.init',sudo=True)
    execute(upload_file,'/home/ubuntu/postfix.stop','postfix.stop',sudo=True)
    execute(upload_file,'/home/ubuntu/start.sh','start.sh',sudo=True)
    execute(docker_build)
    execute(docker_run)
    
    execute(install, 'apache2') 
    execute(install, 'libapache2-mod-proxy-html') 
    execute(install, 'libxml2-dev')
    execute(a2enmod, 'proxy')
    execute(a2enmod, 'proxy_http')
    execute(a2enmod, 'proxy_ajp')
    execute(a2enmod, 'rewrite')
    execute(a2enmod, 'deflate')
    execute(a2enmod, 'headers')
    execute(a2enmod, 'proxy_balancer')
    execute(a2enmod, 'proxy_connect')
    execute(a2enmod, 'proxy_html')
    execute(a2enmod, 'cgi')
    execute(restart_service, 'apache2')
    #TBD Add Master IP of VM to docker
    execute(upload_file, '/etc/apache2/sites-enabled/000-default.conf', '000-default.conf', sudo=True)
    execute(upload_file, '/etc/hosts', 'hosts', sudo=True)
    execute(restart_service, 'apache2')
    execute(upload_file, '/home/ubuntu/.ssh/id_rsa', 'id_rsa')
#    execute(upload_file,'/home/ubuntu/node_config.py','node_config.py',sudo=True)
#    execute(upload_file,'/home/ubuntu/test_program.py','test_program.py',sudo=True)
#    execute(upload_file,'/home/ubuntu/failures.csv','failures.csv',sudo=True)
#    execute(upload_file,'/home/ubuntu/response_time.csv','response_time.csv',sudo=True)    
#    execute(run_python_program,program='/home/ubuntu/node_config.py')
#    execute(upload_file,'/home/ubuntu/test_runner.py','test_runner.py',sudo=True) 
#    execute(upload_file,'/home/ubuntu/measurements_downloader.py','measurements_downloader.py',sudo=True)
#    execute(upload_file,'/home/ubuntu/config_clearer.py','config_clearer.py',sudo=True)
