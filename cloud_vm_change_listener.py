# -*- coding: utf-8 -*-
"""
Created on Tue May 19 15:51:49 2015

@author: Konstantin
"""

import configparser, json

from fabric.api import task, local, env
import cuisine, os
import re
from string import Template as _template
import vm_control
import vm_preparer
import clientside_monitoring_environment_installer as mon_update
import vm_configuration_updater
import nagios_configuration_updater



@task
def restart_nagios():
    '''
    Restarts Nagios locally.
    '''
    local('/etc/init.d/nagios restart')


def write_ip_list(vm_list, VM_control, list_name):
    address_dict = dict((vm, VM_control.get_fixed_ip(vm)) for vm in vm_list)
    json.dump(address_dict,open(list_name,'w'), encoding='utf-8')
    return list_name

def calculate_delta(current_servers, new_servers):
    '''
    Calculates difference between new servers dictionary and
    current servers in order to find out which vms must be updated.
    '''
    updateable_servers = dict()
#    for (key, value) in current_servers.items():
#        if not new_servers.has_key(key):
#            # vm stopped or destroyed
#            updateable_servers[key] = current_servers[key]
    for (key, value) in new_servers.items():
        if not current_servers.has_key(key):
            # vm started or created
            updateable_servers[key] = new_servers[key]            
    return updateable_servers
    

def update_new_vms(nagios_public_ip, nagios_fixed_ip):
    current_servers = json.load(open('server_list','r'), encoding='utf-8')
    new_servers = json.load(open('new_list','r'), encoding='utf-8')
    updateable_servers = calculate_delta(current_servers, new_servers)
    vm_preparer.prepare_machines(updateable_servers, nagios_public_ip, nagios_fixed_ip)
    mon_update.install_monitoring_environment(updateable_servers, nagios_public_ip, nagios_fixed_ip)
    return updateable_servers

def main():
    pass  
    

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
    nagios_server_name = str(nagios_server['nagios_server'])

    

    
    VM_control = vm_control.VM_Control() 
    my_id = VM_control.get_current_userid()
    active_vms = [vm.name for vm in VM_control.find_vms(userid=my_id)]
    nagios_public_ip = VM_control.get_floating_ip(nagios_server_name)
    nagios_fixed_ip = VM_control.get_fixed_ip_from_floating_ip(nagios_public_ip)
    
    new_servers = write_ip_list(active_vms, VM_control, 'new_list')   
    updateable_vms = update_new_vms(nagios_public_ip, nagios_fixed_ip)
    current_servers = write_ip_list(active_vms, VM_control, 'server_list')
    
    vm_configuration_updater.main()
    nagios_configuration_updater.main()
    
#    config = configparser.ConfigParser()
#    config.read('remote_config.ini')
#    
#    HOST_LIST = json.load(open('server_list', 'r'))
#    
#    nagios_server = dict(config['NAGIOS_SERVER'])
#    nagios_server_name = str(nagios_server['nagios_server'])
#    
#    nagios_server_ip = HOST_LIST[nagios_server_name]
#
#    server_list = [(host, ip) for (host, ip) in HOST_LIST.items() if host != nagios_server_name]
#    
#    loaded_dict = dict()
#    for (server,ip) in server_list:
#        write_config_file(template_dir='.',file_dir='',name=server,vm_ip=ip)
#        loaded_dict[server] = ip
#    write_ip_list(loaded_dict)    
    
    
#    execute(run_python_program, '~/clientside_monitoring_environment_installer.py')
        
