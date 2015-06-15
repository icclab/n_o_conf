# -*- coding: utf-8 -*-
"""
Created on Fri May 15 18:34:19 2015

@author: Konstantin
"""
import keystoneclient.v2_0.client as ksclient
from novaclient import client as noclient
import neutronclient.client as neclient
import configparser, time, os, copy, csv, json
import vm_control, nagios_preparer

from fabric.api import env, execute, task, put, get, sudo
import cuisine

#@task
#def prepare_machine():
#    put(local_path='/root/.ssh/id_rsa.pub',remote_path='/root/.ssh/authorized_keys', use_sudo=True)
#    cuisine.file_upload('/root/.ssh/authorized_keys','/root/.ssh/id_rsa.pub', sudo=True)

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
def run_python_program(program=None, use_sudo=False):
    cuisine.file_ensure('/usr/bin/python')
    if use_sudo:
        cuisine.sudo(('/usr/bin/python %s' % program))
    else:
        cuisine.run(('/usr/bin/python %s' % program))
        
@task
def service_ctl(service='listenerdaemon', command='start', use_sudo=False):
    cuisine.file_ensure(('/etc/init.d/%s' % service))
    cmd = str('/etc/init.d/%s %s' % (service, command))
    if use_sudo:
        cuisine.sudo(cmd, shell=False)
    else:
        cuisine.run(cmd, shell=False)
    
def get_vm_ips(vm_data):
    return [vm.networks.values()[0][0] for vm in vm_data]

def write_hosts_file(host_ip_list):
    json.dump(host_ip_list, 'host_ips', encoding='utf-8')

def read_hosts_file(path):
    host_ip_list = json.load(path, encoding='utf-8')
    return host_ip_list

def install_prerequisites():
    '''
    Installs prerequisites for running Nagios on VM.
    '''
    execute(install, 'linux-headers-virtual')
    execute(install, 'linux-image-virtual')
    execute(install, ' linux-image-extra-virtual')
    execute(install, 'linux-virtual')
#    execute(install_docker)
    execute(install, 'python-pip')
    execute(install, 'python-dev')
    execute(pip_install, 'dispy')
    execute(pip_install, 'ecdsa')
    execute(pip_install, 'pycrypto')
    execute(pip_install, 'fabric')
    execute(pip_install, 'cuisine')
    execute(pip_install, 'configparser')
    execute(pip_install, 'multiprocessing')
    execute(install,'apache2')
    execute(install,'apache2-utils')
    execute(install,'libapache2-mod-php5')
    execute(install,'build-essential')
    execute(install,'libgd2-xpm-dev')
    execute(install,'libssl-dev')
    execute(install,'git')
    execute(install,'subversion')
    execute(install,'iputils-ping')
    execute(install,'netcat')
    execute(install,'php5-cli')
    execute(install,'librrds-perl')
    execute(install,'rrdtool') 
    execute(pip_install,'python-keystoneclient')
    execute(pip_install,'python-novaclient')

def nagios_downloaded():
    '''
    Checks if Nagios is downloaded to VM.
    '''
    return cuisine.file_exists("~/nagios-3.4.1.tar.gz")

def nagios_plugins_downloaded():
    '''
    Checks if Nagios plugins are downloaded to VM.
    '''
    return cuisine.file_exists("~/nagios-plugins-2.0.3.tar.gz")

def nrpe_plugins_downloaded():
    '''
    Checks if NRPE plugins are downloaded to VM.
    '''
    return cuisine.file_exists("~/nrpe-2.15.tar.gz")

@task
def add_nagios_user():
    '''
    Adds Nagios user and group and sets correct file permissions.
    '''
    cuisine.group_ensure('nagcmd')
    cuisine.group_ensure('nagios')
    cuisine.user_ensure('nagios')
    cuisine.group_user_ensure('nagios', 'nagios')
    cuisine.group_user_ensure('nagcmd', 'nagios')
    cuisine.user_ensure('www-data')
    cuisine.group_user_ensure('nagcmd', 'www-data')
    cuisine.sudo('mkdir -p /usr/local/nagios')
    cuisine.sudo('mkdir -p /usr/local/nagios/libexec')
    cuisine.dir_ensure('/usr/local/nagios')
    cuisine.dir_ensure('/usr/local/nagios/libexec')
    cuisine.sudo('chown nagios.nagcmd /usr/local/nagios')
    cuisine.sudo('chown -R nagios.nagcmd /usr/local/nagios/libexec')



@task
def install_nagios_from_source():
    '''
    Downloads Nagios source code and installs Nagios on VM.
    '''
    cuisine.dir_ensure('/usr/local/src')
    cuisine.sudo('mkdir -p /etc/httpd/conf.d/')
    cuisine.dir_ensure('/etc/httpd/conf.d/')
    cuisine.sudo('cd /usr/local/src')
    if not nagios_downloaded():
        cuisine.sudo('wget http://prdownloads.sourceforge.net/sourceforge/nagios/nagios-3.4.1.tar.gz')
    cuisine.sudo('tar xzf nagios-3.4.1.tar.gz')
    cuisine.run('cd ~/nagios && ./configure --with-command-group=nagcmd && make all && make install', shell=False)
    cuisine.run('cd ~/nagios && make install-init && make install-config && make install-commandmode', shell=False)
    cuisine.run('cd ~/nagios && make install-webconf', shell=False)
    cuisine.run('cp /etc/httpd/conf.d/nagios.conf /etc/apache2/conf-available/nagios.conf', shell=False)
    cuisine.run('cp /etc/httpd/conf.d/nagios.conf /etc/apache2/conf-enabled/nagios.conf', shell=False)
    cuisine.run('rm -rf /etc/apache2/conf-available/nagios3.conf')
    cuisine.run('rm -rf /etc/apache2/conf-enabled/nagios3.conf')

@task
def prepare_apache(nagios_server_user, nagios_server_password):
    '''
    Creates Nagios admin user and configures Apache.
    '''
    cuisine.run(str('htpasswd -bc /usr/local/nagios/etc/htpasswd.users %s %s'% (nagios_server_user, nagios_server_password)))
    cuisine.run('a2enmod cgi', shell=False)
    cuisine.run('/etc/init.d/apache2 restart', shell=False)

@task
def install_nagios_plugins_from_source():
    '''
    Downloads Nagios plugins source code and installs Nagios plugins on VM.
    '''
    if not nagios_plugins_downloaded():
        cuisine.sudo('wget http://nagios-plugins.org/download/nagios-plugins-2.0.3.tar.gz')
    cuisine.run('tar xzf nagios-plugins-2.0.3.tar.gz')
    cuisine.run('cd ~/nagios-plugins-2.0.3 && ./configure --with-nagios-user=nagios --with-nagios-group=nagios && make && make install', shell=False)

@task
def install_nrpe_plugin_from_source():
    '''
    Downloads NRPE plugin source code and installs NRPE plugin on VM.
    '''
    cuisine.package_ensure_apt('libssl-dev')
    cuisine.dir_ensure('/usr/local/src')
    cuisine.sudo('cd /usr/local/src')
    if not nrpe_plugins_downloaded():
        cuisine.sudo('wget http://sourceforge.net/projects/nagios/files/nrpe-2.x/nrpe-2.15/nrpe-2.15.tar.gz')
    cuisine.sudo('tar xzf nrpe-2.15.tar.gz')
    cuisine.run('cd ~/nrpe-2.15 && ./configure --with-ssl=/usr/bin/openssl --with-ssl-lib=/usr/lib/x86_64-linux-gnu && make all && make install-plugin')

@task
def start_nagios():
    '''
    Starts Nagios on VM and sets up Nagios as upstart job.
    '''
    cuisine.file_upload('/usr/local/nagios/etc/objects/commands.cfg','nrpe_commands.cfg', sudo=True)
    cuisine.sudo('ln -sf /etc/init.d/nagios /etc/rcS.d/S99nagios')
    cuisine.sudo('/etc/init.d/nagios start')

@task
def install_nagiosbpi():
    cuisine.sudo('rm -rf /tmp/nagios-nagiosbpi')
    cuisine.run('git clone git://git.code.sf.net/p/nagios/nagiosbpi /tmp/nagios-nagiosbpi')
    cuisine.run('cp -R /tmp/nagios-nagiosbpi/nagiosbpi /usr/local/nagios/share')
    cuisine.sudo('mkdir -p /usr/local/nagios/share/nagiosbpi/tmp')
    chmod_file('o+rx', '/usr/local/nagios/share/nagiosbpi/config_functions')
    chmod_file('o+rx', '/usr/local/nagios/share/nagiosbpi/functions')
    chmod_file('o+rx', '/usr/local/nagios/share/nagiosbpi/images')
    chmod_file('o+rx', '/usr/local/nagios/share/nagiosbpi/tmp')
    chmod_file('o+rxw', '/usr/local/nagios/share/nagiosbpi/tmp')
    cuisine.file_upload('/usr/local/nagios/share/nagiosbpi/constants.conf', 'constants.conf', sudo=True)
    chmod_file('+x', '/usr/local/nagios/share/nagiosbpi/set_bpi_perms.sh')
    chmod_file('777', '/usr/local/nagios/share/nagiosbpi/bpi.conf')
    chmod_file('-R 777', '/usr/local/nagios/share/nagiosbpi/tmp')
    chmod_file('+x', '/usr/local/nagios/share/nagiosbpi/check_bpi.php')
#
#    cuisine.run('/usr/local/nagios/share/nagiosbpi/set_bpi_perms.sh', shell=False)

@task
def install_nagiosgraph():
    cuisine.run('svn checkout --force http://svn.code.sf.net/p/nagiosgraph/code/trunk /tmp/nagiosgraph-code')
    cuisine.sudo('mkdir -p /opt/nagiosgraph/etc')
    cuisine.sudo('cp /tmp/nagiosgraph-code/nagiosgraph/lib/insert.pl /usr/local/nagios/libexec/insert.pl')
    cuisine.sudo('chown nagios.nagios /usr/local/nagios/libexec/insert.pl')
    cuisine.sudo('cp /tmp/nagiosgraph-code/nagiosgraph/cgi/*.cgi /usr/local/nagios/sbin')
    cuisine.sudo('chown -R nagios.nagios /usr/local/nagios/sbin')
    cuisine.sudo('cp /tmp/nagiosgraph-code/nagiosgraph/share/nagiosgraph.css /usr/local/nagios/share')
    cuisine.sudo('cp /tmp/nagiosgraph-code/nagiosgraph/share/nagiosgraph.js /usr/local/nagios/share')
    cuisine.sudo('chown -R nagios.nagios /usr/local/nagios/share')
    cuisine.sudo('cp /tmp/nagiosgraph-code/nagiosgraph/etc/* /opt/nagiosgraph/etc')
#    cuisine.sudo('mkdir -p /opt/nagiosgraph/etc/map')
#    cuisine.sudo('cp -r /tmp/nagiosgraph-code/nagiosgraph/etc/map/* /opt/nagiosgraph/etc/map')
    cuisine.file_upload('/opt/nagiosgraph/etc/nagiosgraph.conf','nagiosgraph.conf',sudo=True)
    cuisine.file_upload('/usr/local/nagios/etc/nagios.cfg','nagios.cfg',sudo=True)
    cuisine.file_upload('/usr/local/nagios/etc/objects/commands.cfg','commands.cfg',sudo=True)
    cuisine.file_upload('/usr/local/nagios/etc/objects/graphed_service.cfg','graphed_service.cfg',sudo=True)
    cuisine.sudo('mkdir -p /var/nagios')
    cuisine.sudo('chown nagios.nagios /var/nagios')
    cuisine.sudo('chmod 775 /var/nagios')
    cuisine.sudo('mkdir -p /var/nagios/rrd')
    cuisine.sudo('chown nagios.nagios /var/nagios/rrd')
    cuisine.sudo('chmod 775 /var/nagios/rrd')
    cuisine.sudo('touch /var/log/nagiosgraph.log')
    cuisine.sudo('chown nagios.nagios /var/log/nagiosgraph.log')
    cuisine.sudo('chmod 664 /var/log/nagiosgraph.log')
    cuisine.sudo('touch /var/log/nagiosgraph-cgi.log')
    cuisine.sudo('chown nagios.nagios /var/log/nagiosgraph-cgi.log')
    cuisine.sudo('chmod 664 /var/log/nagiosgraph-cgi.log')
    cuisine.sudo('cp /tmp/nagiosgraph-code/nagiosgraph/share/graph.gif /usr/local/nagios/share/images/action.gif')
    cuisine.file_upload('/usr/local/nagios/share/ssi/common-header.ssi', 'common-header.ssi', sudo=True)
    cuisine.file_upload('/usr/local/nagios/share/side.php', 'side.php', sudo=True)


def write_ip_list(vm_list, VM_control):
    address_dict = dict((vm, VM_control.get_fixed_ip(vm)) for vm in vm_list)
    json.dump(address_dict,open('server_list','w'), encoding='utf-8')
    return 'server_list'


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
    
    nagios_server = dict(config['NAGIOS_SERVER'])
    nagios_server_user = str(nagios_server['nagios_server.user'])
    nagios_server_password = str(nagios_server['nagios_server.password'])
    
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
    
    host_list = write_ip_list(vm_list, VM_control)
    nagios_server_ip = VM_control.get_floating_ip('master')
    
    nagios_preparer.prepare_server(nagios_server_ip)
    
    
    env.hosts = [nagios_server_ip]
    env.user = 'root'
    env.password = ssh_password
    env.key_filename = ssh_key_filename
    env.connection_attempts = 5
    
    execute(update)
    
    install_prerequisites()
    execute(add_nagios_user)
    execute(install_nagios_from_source)
    execute(prepare_apache, nagios_server_user, nagios_server_password)
    execute(install_nagios_plugins_from_source)
    execute(install_nrpe_plugin_from_source)
    execute(start_nagios)
    execute(install_nagiosbpi)
    execute(install_nagiosgraph)
    
    execute(upload_file, '~/server_list','server_list')
    execute(upload_file, '~/.ssh/id_rsa','id_rsa')
    execute(upload_file, '~/.ssh/id_rsa.pub','id_rsa.pub')
    execute(chmod_file, '0600', '~/.ssh/id_rsa')
    execute(upload_file, '~/vm_preparer.py','vm_preparer.py')
    execute(upload_file, '~/clean_apt.py','clean_apt.py')
    execute(upload_file, '~/clientside_monitoring_environment_installer.py','clientside_monitoring_environment_installer.py')
    execute(upload_file, '~/config.ini','remote_config.ini')
    execute(run_python_program, '~/vm_preparer.py', use_sudo=True)
    execute(run_python_program, '~/clientside_monitoring_environment_installer.py', use_sudo=True)
    execute(upload_file, '~/client_nrpe.cfg','client_nrpe.cfg')
    execute(upload_file, '~/client_check_memory.sh','client_check_memory.sh')
    execute(upload_file, '~/vm_control.py','vm_control.py')
    execute(upload_file, '~/openrc.py','openrc.py')
    execute(upload_file, '~/vm_configuration_updater.py','vm_configuration_updater.py')
    execute(upload_file, '/usr/local/nagios/etc/vm_template.cfg','vm_template.cfg')
    execute(upload_file, '/usr/local/nagios/etc/nagios_template.cfg','nagios_template.cfg')
    execute(upload_file, '~/nagios_configuration_updater.py','nagios_configuration_updater.py')
    execute(upload_file, '~/cloud_vm_change_listener.py','cloud_vm_change_listener.py')
    execute(upload_file, '~/daemon.py','daemon.py')
    execute(upload_file, '~/listenerdaemon.py','listenerdaemon.py')
    execute(upload_file, '/etc/init.d/listenerdaemon','listenerdaemon')
    execute(service_ctl, service='listenerdaemon', command='start')
#    execute(run_python_program, '~/cloud_vm_change_listener.py')
        
