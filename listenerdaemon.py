# -*- coding: utf-8 -*-
"""
Created on Tue May 26 14:38:04 2015

@author: Konstantin
"""
import sys, time
from daemon import Daemon
import cloud_vm_change_listener as cvl

class ListenerDaemon(Daemon):
        def run(self):
                while True:
                        cvl.main()
                        time.sleep(1)

if __name__ == "__main__":
        daemon = ListenerDaemon('/var/run/listener-daemon.pid')
        if len(sys.argv) == 2:
                if 'start' == sys.argv[1]:
                        daemon.start()
                elif 'stop' == sys.argv[1]:
                        daemon.stop()
                elif 'restart' == sys.argv[1]:
                        daemon.restart()
                else:
                        print "Unknown command"
                        sys.exit(2)
                sys.exit(0)
        else:
                print "usage: %s start|stop|restart" % sys.argv[0]
                sys.exit(2)
