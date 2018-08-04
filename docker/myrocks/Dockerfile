# TODO: Clean up the directory structure, it's a mess.

# Warning: Requires at least 3.5GB to build, maybe a bit more.

#http://myrocks.io/docs/getting-started/
FROM lamdencalrissian/seneca-myrocks-test:0.6

# Warning: Requires at least 3.5GB to build, maybe a bit more.

#http://myrocks.io/docs/getting-started/

FROM centos:7.5.1804
#https://hub.docker.com/_/centos/
MAINTAINER Lamden Calrissian version: 0.1

# Yum prereqs for Docker
RUN yum clean all
RUN yum install -y yum-plugin-ovl
RUN yum install -y deltarpm

# Install Git
RUN yum install -y git

# Download Facebook's mysql git repo (includes myrocks)
RUN mkdir -p /opt/myrocks
RUN cd /opt/myrocks && git clone https://github.com/facebook/mysql-5.6.git
RUN cd /opt/myrocks/mysql-5.6 && git checkout fb-prod201801 && git submodule init && git submodule update

# Get build deps from package management
RUN yum install -y cmake gcc-c++ bzip2-devel libaio-devel bison zlib-devel snappy-devel
RUN yum install -y gflags-devel readline-devel ncurses-devel openssl-devel lz4-devel gdb git
# Deps missing from rocksdb documentation
RUN yum install -y make boost-devel

# Build
RUN cd /opt/myrocks/mysql-5.6 && cmake . -DCMAKE_BUILD_TYPE=Release \
-DWITH_SSL=system -DWITH_ZLIB=bundled -DMYSQL_MAINTAINER_MODE=0 \
-DENABLED_LOCAL_INFILE=1 -DENABLE_DTRACE=0
RUN cd /opt/myrocks/mysql-5.6 && make -j8
RUN cd /opt/myrocks/mysql-5.6 && make install

# Instal dependency for mysql install
RUN yum install -y "perl(Data::Dumper)"

# Clean Yum cache to reduce artifact size
RUN yum clean all

# Copy config and install db
COPY ./my.cnf /etc/my.cnf

# Copy latest start_mysql
COPY ./start_mysql.sh /usr/local/bin/start_mysql.sh
RUN chmod +x /usr/local/bin/start_mysql.sh

#RUN cd /usr/local/mysql/ && ./scripts/mysql_install_db
RUN cd /usr/local/mysql/ && ./scripts/mysql_install_db

# Open mysql daemon port
EXPOSE 3306

RUN useradd -ms /bin/bash mysql
RUN chown -R mysql:mysql /usr/local/mysql/data

ENTRYPOINT ["/usr/local/bin/start_mysql.sh"]
