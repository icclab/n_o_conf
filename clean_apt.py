# -*- coding: utf-8 -*-
"""
Created on Tue May 19 09:31:59 2015

@author: Konstantin
"""
import os, signal


def kill_process(pid):
    os.kill(int(pid), signal.SIGILL)
    

if __name__ == '__main__':
    pids = open('pids.txt','r')
    processes = [kill_process(pid) for pid in pids.readlines()]