# -*- coding: utf-8 -*-
"""
Created on Tue May 19 14:00:29 2015

@author: Konstantin
"""

# -*- coding: utf-8 -*-
"""
Created on Fri May 15 18:34:19 2015

@author: Konstantin
"""

import configparser, json

from fabric.api import task, local
import cuisine
import re
from string import Template as _template



@task
def restart_nagios():
    '''
    Restarts Nagios locally.
    '''
    local('/etc/init.d/nagios restart')

def write_config_file(**kwargs):
    '''
    Writes a single Nagios config file that represents a VM in the /etc/
    directory of the Nagios VM. It uses a template for creating the config
    file.

    Arguments:
        :file_dir: local directory on Nagios server
            where the VM config resides.
        :template_dir: local directory on Nagios server
            where the template resides.
        :name: name of the VM that is configured.
        :vm_ip: IP of the VM that is configured.
'''
    file_dir = kwargs.pop('file_dir', '')
    template_dir = kwargs.pop('template_dir', '/usr/local/nagios/etc')
    name = kwargs.pop('name', 'def')
    vm_ip = kwargs.pop('vm_ip', '1.1.1.1')
    target_config_file = open(str('%s%s_nagios.cfg' % (file_dir, name)), 'w')
    template_file_name = str('%s/vm_template.cfg' % template_dir)
    with open(template_file_name, 'r') as template_file:
        for line in template_file:
            if re.search('vm_name', line):
                param = _template(line)
                line = param.substitute(vm_name=name)
            elif re.search('vm_ip', line):
                param = _template(line)
                line = param.substitute(vm_ip=vm_ip)
            buf = str(line)
            target_config_file.write(buf)
    target_config_file.close()

def write_ip_list(address_dict):
    json.dump(address_dict,open('loaded_list','w'), encoding='utf-8')
    return 'loaded_list'

def vm_config_files(vm_template_dir='/usr/local/nagios/etc',nagios_objects_dir='/usr/local/nagios/etc/objects/'):
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    HOST_LIST = json.load(open('server_list', 'r'))
    
    nagios_server = dict(config['NAGIOS_SERVER'])
    nagios_server_name = str(nagios_server['nagios_server'])
    
#    nagios_server_ip = HOST_LIST[nagios_server_name]

    server_list = [(host, ip) for (host, ip) in HOST_LIST.items() if host != nagios_server_name]
    
    loaded_dict = dict()
    for (server,ip) in server_list:
        write_config_file(template_dir=vm_template_dir,file_dir=nagios_objects_dir,name=server,vm_ip=ip)
        loaded_dict[server] = ip
    write_ip_list(loaded_dict)    
    
def main(): 
    vm_config_files()

if __name__ == "__main__": 
    vm_config_files()      
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
        
