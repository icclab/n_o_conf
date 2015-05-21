# -*- coding: utf-8 -*-
"""
Created on Tue Oct 28 12:41:21 2014

@author: Konstantin
"""
import cuisine, configparser, json
from fabric.api import env, execute, task, run, sudo, put, parallel
from fabric.contrib.files import sed

@parallel(pool_size=5)
@task
def cleanup():
    sudo("ps aux | grep apt | grep -v grep | awk '{print $2;}' > pids.txt")
#    sudo("ps aux | grep dpkg | grep -v grep | awk '{print $2;}' >> pids.txt")
    put(local_path='/root/clean_apt.py',remote_path='/root/clean_apt.py',use_sudo=True)
    sudo('python /root/clean_apt.py')
    sudo('rm -rf /var/lib/apt/lists/lock')
    sudo('rm -rf /var/cache/apt/archives/lock')
    sudo('dpkg --configure -a')
#    sudo('dpkg-reconfigure debconf -f noninteractive')


@parallel(pool_size=5)
@task
def update(package=None):   
    cuisine.package_update(package)

@parallel(pool_size=5)   
@task
def upgrade(package=None):
    cuisine.package_upgrade(package)

@parallel(pool_size=5)
@task
def install(package):
    cuisine.package_install(package)
    cuisine.package_ensure(package)

@parallel(pool_size=5)    
@task
def pip_install(package):
    sudo('apt-get -y install python-pip')
    command = str('pip install %s' % package)
    cuisine.sudo(command, shell=False)

@parallel(pool_size=5)
@task
def upload_file(remote_location, local_location, sudo=False):
    cuisine.file_upload(remote_location, local_location, sudo=sudo)
    cuisine.file_ensure(remote_location)

@parallel(pool_size=5)
@task
def chmod_file(chmod, remote_location):
    command = str('chmod %s %s' % (chmod, remote_location))
    cuisine.run(command, shell=False)

@parallel(pool_size=5)
@task
def run_python_program(program=None, sudo=False):
    cuisine.file_ensure('/usr/bin/python')
    if sudo:
        cuisine.sudo(('/usr/bin/python %s' % program))
    else:
        cuisine.run(('/usr/bin/python %s' % program))

@parallel(pool_size=5)
@task
def install_prerequisites():
    '''
    Installs prerequisites on monitored VMs.
    '''
#    update()
#    upgrade()
    sudo('apt-get -y --allow-unauthenticated --force-yes -o DPkg::Options::="--force-overwrite" -o DPkg::Options::="--force-confdef" update')
#    sudo('apt-get -y --allow-unauthenticated --force-yes -o DPkg::Options::="--force-overwrite" -o DPkg::Options::="--force-confdef" upgrade')
#    sudo('apt-get -y install linux-virtual')
    sudo('apt-get -y --allow-unauthenticated --force-yes -o DPkg::Options::="--force-overwrite" -o DPkg::Options::="--force-confdef" install gcc')
    sudo('apt-get -y --allow-unauthenticated --force-yes -o DPkg::Options::="--force-overwrite" -o DPkg::Options::="--force-confdef" install make')
    sudo('apt-get -y --allow-unauthenticated --force-yes -o DPkg::Options::="--force-overwrite" -o DPkg::Options::="--force-confdef" install build-essential')
    sudo('apt-get -y --allow-unauthenticated --force-yes -o DPkg::Options::="--force-overwrite" -o DPkg::Options::="--force-confdef" install libssl-dev')
    sudo('apt-get -y --allow-unauthenticated --force-yes -o DPkg::Options::="--force-overwrite" -o DPkg::Options::="--force-confdef" install xinetd')
#    sudo('apt-get -y install iptables-persistent')

def nagios_plugins_downloaded():
    '''
    Checks if Nagios plugins are downloaded to VMs.
    '''
    return cuisine.file_exists("~/nagios-plugins-2.0.3.tar.gz")

def nrpe_plugins_downloaded():
    '''
    Checks if NRPE plugins are downloaded to VMs.
    '''
    return cuisine.file_exists("~/nrpe-2.15.tar.gz")

@parallel(pool_size=5)
@task
def add_nagios_user():
    '''
    Adds Nagios user and groups to VMs and sets the right permissions.
    '''
    sudo('useradd nagios')
    sudo('groupadd nagios')
    sudo('usermod nagios -G nagios')
    sudo('mkdir -p /usr/local/nagios')
    sudo('mkdir -p /usr/local/nagios/libexec')
#    cuisine.dir_ensure('/usr/local/nagios')
#    cuisine.dir_ensure('/usr/local/nagios/libexec')
    sudo('chown nagios.nagios /usr/local/nagios', shell=False)
    sudo('chown -R nagios.nagios /usr/local/nagios/libexec', shell=False)

@parallel(pool_size=5)
@task
def add_nrpe_port():
    '''
    Configures settings to permit incoming NRPE connections on port 5666.
    '''
    sudo('apt-get -y install xinetd')
    sudo('echo "nrpe 5666/tcp" >> /etc/services')
    sudo('iptables -A INPUT -p tcp --dport 5666 -j ACCEPT')

@parallel(pool_size=5)
@task
def install_nagios_plugins_from_source():
    '''
    Downloads Nagios plugins source code and installs Nagios plugins on VMs.
    '''
#    sudo('mkdir -p /usr/local/src')
#    run('cd /usr/local/src')
#    if not nagios_plugins_downloaded():
#        
    sudo('wget http://nagios-plugins.org/download/nagios-plugins-2.0.3.tar.gz nagios-plugins-2.0.3.tar.gz')
    sudo('tar xzf ~/nagios-plugins-2.0.3.tar.gz')
#    sudo('~/nagios-plugins-2.0.3/configure --with-nagios-user=nagios --with-nagios-group=nagios')
    run('cd /root/nagios-plugins-2.0.3 && ./configure --with-nagios-user=nagios --with-nagios-group=nagios && make && make install', shell=False)

@parallel(pool_size=5)
@task
def install_check_memory_script():
    '''
    Puts Nagios check_memory.sh script on VMs.
    '''
    sudo('mkdir -p /usr/local/nagios/libexec')
    put('/usr/local/nagios/libexec/check_memory.sh','~/client_check_memory.sh',use_sudo=True)
    sudo('chown nagios.nagios /usr/local/nagios/libexec/check_memory.sh')
    sudo('chmod 755 /usr/local/nagios/libexec/check_memory.sh')

@parallel(pool_size=5)
@task
def install_nrpe_plugin_from_source():
    '''
    Downloads NRPE plugin source code and installs NRPE plugins on VMs.
    '''
#    sudo('mkdir -p /usr/local/src')
#    run('cd /usr/local/src')
#    if not nrpe_plugins_downloaded():
#        
    sudo('wget http://sourceforge.net/projects/nagios/files/nrpe-2.x/nrpe-2.15/nrpe-2.15.tar.gz nrpe-2.15.tar.gz')
    sudo('tar xzf ~/nrpe-2.15.tar.gz')
    run('cd /root/nrpe-2.15 && ./configure --with-ssl=/usr/bin/openssl --with-ssl-lib=/usr/lib/x86_64-linux-gnu && make all && make install-plugin && make install-daemon && make install-daemon-config && make install-xinetd')

@parallel(pool_size=5)
@task
def configure_xinetd_for_nrpe(nagios_server_ip, nagios_server_fixed_ip):
    '''
    Configures Xinet daemon to accept connections from Nagios VM.
    '''
    sed('/etc/xinetd.d/nrpe', 'only_from       = 127.0.0.1', str('only_from       = %s %s 127.0.0.1'%(nagios_server_ip,nagios_server_fixed_ip)), use_sudo=True)
    sudo('service xinetd restart')

@parallel(pool_size=5)
@task
def configure_nrpe():
    '''
    Configures NRPE on VMs to perform service checks remotely.
    '''
    put('/usr/local/nagios/etc/nrpe.cfg', '~/client_nrpe.cfg', use_sudo=True)
    sudo('chown -R nagios.nagios /usr/local/nagios/etc')
    sudo('chown -R nagios.nagios /usr/local/nagios/etc/nrpe.cfg')
    put('/usr/local/nagios/libexec/check_memory.sh', '~/client_check_memory.sh', use_sudo=True)
    sudo('chown -R nagios.nagios /usr/local/nagios/libexec/check_memory.sh')
    sudo('chmod 0755 /usr/local/nagios/libexec/check_memory.sh')

def install_monitoring_environment(vms_to_update, nagios_server_ip, nagios_server_fixed_ip):
    config = configparser.ConfigParser()
    config.read('config.ini')
    nagios_server = dict(config['NAGIOS_SERVER'])
    nagios_server_name = str(nagios_server['nagios_server'])
    
    ssh_credentials = dict(config['SSH_CREDENTIALS'])
#    ssh_user = str(ssh_credentials['ssh.username'])
    ssh_password = str(ssh_credentials['ssh.password'])
    ssh_key_filename = str(ssh_credentials['ssh.key_filename'])

    env.hosts = [ip for (host, ip) in vms_to_update.items() if host != nagios_server_name]
    env.user = 'root'
    env.password = ssh_password
    env.key_filename = ssh_key_filename
#    nagios_server_fixed_ip = HOST_LIST[nagios_server_name]
    env.warn_only = True
    env.connection_attempts = 5
    execute(upload_file, '/root/clean_apt.py','/root/clean_apt.py', sudo=True)
    execute(cleanup)
#    execute(update)
#    execute(upgrade)    
    execute(install_prerequisites)
    execute(add_nagios_user)
    execute(add_nrpe_port)
    execute(install_nagios_plugins_from_source)
    execute(install_check_memory_script)
    execute(install_nrpe_plugin_from_source)
    execute(configure_nrpe)
    execute(configure_xinetd_for_nrpe, nagios_server_ip, nagios_server_fixed_ip)

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    HOST_LIST = json.load(open('server_list', 'r'))
    
    nagios_server = dict(config['NAGIOS_SERVER'])
    nagios_server_name = str(nagios_server['nagios_server'])
    
    nagios_server_ip = HOST_LIST[nagios_server_name]

    
    ssh_credentials = dict(config['SSH_CREDENTIALS'])
    ssh_user = str(ssh_credentials['ssh.username'])
    ssh_password = str(ssh_credentials['ssh.password'])
    ssh_key_filename = str(ssh_credentials['ssh.key_filename'])

    env.hosts = [ip for (host, ip) in HOST_LIST.items() if host != nagios_server_name]
    env.user = 'root'
    env.password = ssh_password
    env.key_filename = ssh_key_filename
    nagios_server_fixed_ip = HOST_LIST[nagios_server_name]
    env.warn_only = True
    env.connection_attempts = 5
    execute(upload_file, '/root/clean_apt.py','/root/clean_apt.py', sudo=True)
    execute(cleanup)
#    execute(update)
#    execute(upgrade)    
    execute(install_prerequisites)
    execute(add_nagios_user)
    execute(add_nrpe_port)
    execute(install_nagios_plugins_from_source)
    execute(install_check_memory_script)
    execute(install_nrpe_plugin_from_source)
    execute(configure_nrpe)
    execute(configure_xinetd_for_nrpe, nagios_server_ip, nagios_server_fixed_ip)
    