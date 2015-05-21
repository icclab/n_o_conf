# -*- coding: utf-8 -*-
"""
Created on Tue May 19 14:56:36 2015

@author: Konstantin
"""

import configparser, json

from fabric.api import task, local, execute
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
        :content: cfg_files which are added to configuration
'''
    file_dir = kwargs.pop('file_dir', '')
    template_dir = kwargs.pop('template_dir', '/usr/local/nagios/etc')
    content = kwargs.pop('content', '')
    target_config_file = open(str('%snagios.cfg' % file_dir), 'w')
    template_file_name = str('%s/nagios_template.cfg' % template_dir)
    with open(template_file_name, 'r') as template_file:
        for line in template_file:
            if re.search('cfg_files', line):
                param = _template(line)
                line = param.substitute(cfg_files=content)
            buf = str(line)
            target_config_file.write(buf)
    target_config_file.close()

def write_ip_list(address_dict):
    json.dump(address_dict,open('monitored_list','w'), encoding='utf-8')
    return 'monitored_list'

def vm_config_files(nagios_template_dir='/usr/local/nagios/etc',nagios_dir='/usr/local/nagios/etc/'):
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    HOST_LIST = json.load(open('loaded_list', 'r'))
    
    nagios_server = dict(config['NAGIOS_SERVER'])
    nagios_server_name = str(nagios_server['nagios_server'])
    
#    nagios_server_ip = HOST_LIST[nagios_server_name]

    server_list = [(host, ip) for (host, ip) in HOST_LIST.items() if host != nagios_server_name]
    
    monitored_dict = dict()
    cfg_file_string = str()
    for (server,ip) in server_list:
        cfg_file_string += str('cfg_file=/usr/local/nagios/etc/objects/%s_nagios.cfg\n' % server)
        monitored_dict[server] = ip
#    print(cfg_file_string)
    write_config_file(template_dir=nagios_template_dir,file_dir=nagios_dir,content=cfg_file_string) 
    write_ip_list(monitored_dict)

def main():
    vm_config_files() 
    execute(restart_nagios)

if __name__ == "__main__": 
    vm_config_files() 
    execute(restart_nagios)     
#    config = configparser.ConfigParser()
#    config.read('remote_config.ini')
#    
#    HOST_LIST = json.load(open('loaded_list', 'r'))
#    
#    nagios_server = dict(config['NAGIOS_SERVER'])
#    nagios_server_name = str(nagios_server['nagios_server'])
#    
##    nagios_server_ip = HOST_LIST[nagios_server_name]
#
#    server_list = [(host, ip) for (host, ip) in HOST_LIST.items() if host != nagios_server_name]
#    
#    monitored_dict = dict()
#    cfg_file_string = str()
#    for (server,ip) in server_list:
#        cfg_file_string += str('cfg_file=/usr/local/nagios/etc/objects/%s_nagios.cfg\n' % server)
#        monitored_dict[server] = ip
#    print(cfg_file_string)
#    write_config_file(template_dir='.',file_dir='',content=cfg_file_string)
    
    
    
    
    
#    execute(run_python_program, '~/clientside_monitoring_environment_installer.py')
        
