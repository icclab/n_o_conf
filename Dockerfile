FROM ubuntu
ENV NAGIOS_HOME /opt/nagios
ENV NAGIOS_USER nagios
ENV NAGIOS_GROUP nagios
ENV NAGIOS_CMDUSER nagios
ENV NAGIOS_CMDGROUP nagios
ENV NAGIOSADMIN_USER nagiosadmin
ENV NAGIOSADMIN_PASS nagios
ENV APACHE_RUN_USER nagios
ENV APACHE_RUN_GROUP nagios
ENV NAGIOS_TIMEZONE UTC

RUN groupadd nagios
RUN useradd -b /home/nagios -c "" -p "nagios" -g nagios nagios
RUN sed -i 's/universe/universe multiverse/' /etc/apt/sources.list
RUN apt-get update && apt-get install -y iputils-ping netcat build-essential snmp snmpd snmp-mibs-downloader php5-cli apache2 apache2-utils libapache2-mod-php5 runit bc postfix bsd-mailx git subversion libssl-dev librrds-perl rrdtool 
# RUN service apache2 start

RUN ( egrep -i  "^${NAGIOS_GROUP}" /etc/group || groupadd $NAGIOS_GROUP ) && ( egrep -i "^${NAGIOS_CMDGROUP}" /etc/group || groupadd $NAGIOS_CMDGROUP )

RUN ( id -u $NAGIOS_USER || useradd --system $NAGIOS_USER -g $NAGIOS_GROUP -d $NAGIOS_HOME ) && ( id -u $NAGIOS_CMDUSER || useradd --system -d $NAGIOS_HOME -g $NAGIOS_CMDGROUP $NAGIOS_CMDUSER )

ADD http://downloads.sourceforge.net/project/nagios/nagios-3.x/nagios-3.5.1/nagios-3.5.1.tar.gz?r=http%3A%2F%2Fwww.nagios.org%2Fdownload%2Fcore%2Fthanks%2F%3Ft%3D1398863696&ts=1398863718&use_mirror=superb-dca3 /tmp/nagios.tar.gz
RUN cd /tmp && tar -zxvf nagios.tar.gz && cd nagios  && ./configure --prefix=${NAGIOS_HOME} --exec-prefix=${NAGIOS_HOME} --enable-event-broker --with-nagios-command-user=${NAGIOS_CMDUSER} --with-command-group=${NAGIOS_CMDGROUP} --with-nagios-user=${NAGIOS_USER} --with-nagios-group=${NAGIOS_GROUP} && make all && make install && make install-config && make install-init && make install-commandmode && cp sample-config/httpd.conf /etc/apache2/conf-enabled/nagios.conf
ADD http://www.nagios-plugins.org/download/nagios-plugins-1.5.tar.gz /tmp/
RUN cd /tmp && tar -zxvf nagios-plugins-1.5.tar.gz && cd nagios-plugins-1.5 && ./configure --prefix=${NAGIOS_HOME} && make && make install

RUN sed -i.bak 's/.*\=www\-data//g' /etc/apache2/envvars
RUN export DOC_ROOT="DocumentRoot $(echo $NAGIOS_HOME/share)"; sed -i "s,DocumentRoot.*,$DOC_ROOT," /etc/apache2/sites-enabled/000-default.conf

RUN ln -s ${NAGIOS_HOME}/bin/nagios /usr/local/bin/nagios && mkdir -p /usr/share/snmp/mibs && chmod 0755 /usr/share/snmp/mibs && touch /usr/share/snmp/mibs/.foo

RUN echo "use_timezone=$NAGIOS_TIMEZONE" >> ${NAGIOS_HOME}/etc/nagios.cfg && echo "SetEnv TZ \"${NAGIOS_TIMEZONE}\"" >> /etc/apache2/conf-enabled/nagios.conf

RUN mkdir -p ${NAGIOS_HOME}/etc/conf.d && mkdir -p ${NAGIOS_HOME}/etc/monitor && ln -s /usr/share/snmp/mibs ${NAGIOS_HOME}/libexec/mibs
RUN echo "cfg_dir=${NAGIOS_HOME}/etc/conf.d" >> ${NAGIOS_HOME}/etc/nagios.cfg
RUN echo "cfg_dir=${NAGIOS_HOME}/etc/monitor" >> ${NAGIOS_HOME}/etc/nagios.cfg
RUN download-mibs && echo "mibs +ALL" > /etc/snmp/snmp.conf

RUN sed -i 's,/bin/mail,/usr/bin/mail,' /opt/nagios/etc/objects/commands.cfg && \
  sed -i 's,/usr/usr,/usr,' /opt/nagios/etc/objects/commands.cfg

RUN apt-get update && apt-get install -y runit

RUN cp /etc/services /var/spool/postfix/etc/

RUN mkdir -p /etc/sv/nagios && mkdir -p /etc/sv/apache2 && rm -rf /etc/sv/getty-5 && mkdir -p /etc/sv/postfix
ADD nagios.init /etc/sv/nagios/run
ADD apache.init /etc/sv/apache2/run
ADD postfix.init /etc/sv/postfix/run
ADD postfix.stop /etc/sv/postfix/finish

#RUN mkdir -p /service && mkdir -p /etc/service && cd / && ln -s /etc/services && cd /service && ln -s /etc/sv/apache && ln -s /etc/sv/nagios && ln -s /etc/sv/postfix

RUN chmod +x /etc/sv/nagios/run


RUN chmod +x /etc/sv/apache2/run
RUN chmod +x /etc/default/apache2
RUN chmod +x /usr/sbin/apache2

RUN chmod +x /etc/sv/postfix/run
RUN chmod +x /etc/sv/postfix/finish

RUN mkdir -p /usr/local
RUN mkdir -p /usr/local/bin
ADD start.sh /usr/local/bin/start_nagios
RUN chmod 755 /usr/local/bin
RUN chmod a+x /usr/local/bin/start_nagios

Run a2enmod cgi

ENV APACHE_LOCK_DIR /var/run
ENV APACHE_LOG_DIR /var/log/apache2

EXPOSE 80

VOLUME /opt/nagios/var
VOLUME /opt/nagios/etc
VOLUME /opt/nagios/libexec
VOLUME /var/log/apache2
VOLUME /usr/share/snmp/mibs

RUN cd /tmp && git clone git://git.code.sf.net/p/nagios/nagiosbpi nagios-nagiosbpi && cd nagios-nagiosbpi && cp -R nagiosbpi ${NAGIOS_HOME}/share && cd ${NAGIOS_HOME}/share/nagiosbpi/ && mkdir -p ${NAGIOS_HOME}/share/nagiosbpi/tmp && chmod o+rx config_functions functions images tmp && chmod o+rxw tmp
ADD constants.conf ${NAGIOS_HOME}/share/nagiosbpi/constants.conf
RUN cd ${NAGIOS_HOME}/share/nagiosbpi/ && chmod +x set_bpi_perms.sh && ./set_bpi_perms.sh

RUN cd /tmp && svn checkout http://svn.code.sf.net/p/nagiosgraph/code/trunk nagiosgraph-code && cd nagiosgraph-code/nagiosgraph && mkdir -p /opt/nagiosgraph/etc && cp lib/insert.pl ${NAGIOS_HOME}/libexec && chown ${NAGIOS_USER}.${NAGIOS_GROUP} ${NAGIOS_HOME}/libexec/insert.pl && cp cgi/*.cgi ${NAGIOS_HOME}/sbin && chown -R ${NAGIOS_USER}.${NAGIOS_GROUP} ${NAGIOS_HOME}/sbin && cp share/nagiosgraph.css ${NAGIOS_HOME}/share && cp share/nagiosgraph.js ${NAGIOS_HOME}/share && chown -R ${NAGIOS_USER}.${NAGIOS_GROUP} ${NAGIOS_HOME}/share 

ADD nagiosgraph.conf /opt/nagiosgraph/etc/nagiosgraph.conf
ADD nagios.cfg ${NAGIOS_HOME}etc/nagios.cfg
ADD commands.cfg ${NAGIOS_HOME}etc/objects/commands.cfg
ADD graphed_service.cfg ${NAGIOS_HOME}etc/objects/graphed_service.cfg

RUN mkdir -p /var/nagios/rrd && chown ${NAGIOS_USER}.${NAGIOS_GROUP} /var/nagios/rrd && chmod 755 /var/nagios/rrd 
RUN touch /var/log/nagiosgraph.log && chown ${NAGIOS_USER}.${NAGIOS_GROUP} /var/log/nagiosgraph.log && chmod 664 /var/log/nagiosgraph.log
RUN touch /var/log/nagiosgraph-cgi.log && chown ${NAGIOS_USER}.${NAGIOS_GROUP} /var/log/nagiosgraph-cgi.log && chmod 664 /var/log/nagiosgraph-cgi.log

RUN cd /tmp/nagiosgraph-code/nagiosgraph && cp share/graph.gif ${NAGIOS_HOME}/share/images/action.gif

ADD common-header.ssi ${NAGIOS_HOME}share/ssi/common-header.ssi
ADD side.php ${NAGIOS_HOME}share/side.php


RUN cd /tmp && wget http://sourceforge.net/projects/nagios/files/nrpe-2.x/nrpe-2.15/nrpe-2.15.tar.gz && tar xzf nrpe-2.15.tar.gz && cd nrpe-2.15 && ./configure --with-ssl=/usr/bin/openssl --with-ssl-lib=/usr/lib/x86_64-linux-gnu && make all && make install-plugin

EXPOSE 5666

ENTRYPOINT ["/usr/local/bin/start_nagios"]
CMD ["/bin/bash"]
