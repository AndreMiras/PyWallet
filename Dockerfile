FROM ubuntu:16.04

# install Buildozer requirements
# https://buildozer.readthedocs.io/en/latest/installation.html#android-on-ubuntu-16-04-64bit
RUN dpkg --add-architecture i386
RUN apt update -q
RUN apt install -y build-essential ccache git libncurses5:i386 libstdc++6:i386 libgtk2.0-0:i386 libpangox-1.0-0:i386 libpangoxft-1.0-0:i386 libidn11:i386 python2.7 python2.7-dev openjdk-8-jdk unzip zlib1g-dev zlib1g:i386
RUN apt install -y python-pip
RUN pip install --upgrade cython==0.21

# install Buildozer
RUN pip install --upgrade buildozer

# install PyWallet Android build dependencies
RUN apt install -y libffi-dev
RUN apt install -y autogen autoconf libtool
RUN apt install -y libssl-dev
# this is required by secp256k1 recipe, but should really be patched
# because pkg-config may not be available on other platforms
# https://github.com/AndreMiras/PyWallet/issues/39
RUN apt install -y pkg-config

# build preparation
RUN mkdir -p /src/
WORKDIR /src/
COPY . /src/
RUN cd /src
# TODO: do not build as root
RUN sed s/"warn_on_root = 1"/"warn_on_root = 0"/ -i buildozer.spec

# build
RUN buildozer android debug

# TODO cleanup
