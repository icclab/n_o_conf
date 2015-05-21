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
def prepare_machine():
    sudo('rm -rf /root/.ssh/authorized_keys')
    sudo('mkdir -p /root/.ssh')
    sudo('chmod 777 /root')
    sudo('chmod 777 /root/.ssh')
    sudo('touch /root/.ssh/authorized_keys')
    put(local_path='/root/.ssh/id_rsa.pub',remote_path='/root/.ssh/id_rsa.pub') 
    sudo('chmod 777 /root/.ssh/authorized_keys')
    sudo('chmod 777 /root/.ssh/id_rsa.pub')
    sudo('cat /root/.ssh/id_rsa.pub > /root/.ssh/authorized_keys')
    sudo('chmod 644 /root/.ssh/authorized_keys')
    sudo('chmod 644 /root/.ssh/id_rsa.pub')
    sudo('chmod 700 /root/.ssh')
    sudo('chmod 700 /root')
    sudo('service ssh restart')
#    cuisine.package_update()


def prepare_machines(vms_to_update, nagios_server_ip, nagios_server_fixed_ip):
    config = configparser.ConfigParser()
    config.read('config.ini')    
    nagios_server = dict(config['NAGIOS_SERVER'])
    nagios_server_name = str(nagios_server['nagios_server'])
    

    
    ssh_credentials = dict(config['SSH_CREDENTIALS'])
    ssh_user = str(ssh_credentials['ssh.username'])
    ssh_password = str(ssh_credentials['ssh.password'])
    ssh_key_filename = str(ssh_credentials['ssh.key_filename'])

    env.hosts = [ip for (host, ip) in vms_to_update.items() if host != nagios_server_name]
    env.user = ssh_user
    env.password = ssh_password
    env.key_filename = ssh_key_filename
    env.warn_only = True
    env.connection_attempts = 5

    execute(prepare_machine)

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
    env.user = ssh_user
    env.password = ssh_password
    env.key_filename = ssh_key_filename
    nagios_server_fixed_ip = HOST_LIST[nagios_server_name]
    env.warn_only = True
    env.connection_attempts = 5

    execute(prepare_machine)

