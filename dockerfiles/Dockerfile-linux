# Docker image for installing dependencies on Linux and running tests.
# Build with:
# docker build --tag=pywallet-linux --file=dockerfiles/Dockerfile-linux .
# Run with:
# docker run pywallet-linux /bin/sh -c 'make test'
# Or using the entry point shortcut:
# docker run pywallet-linux 'make test'
# Or for interactive shell:
# docker run -it --rm pywallet-linux
# TODO:
#	- delete archives to keep small the container small
#	- setup caching (for apt, and pip)
FROM ubuntu:18.04

# configure locale
RUN apt update -qq > /dev/null && apt install --yes --no-install-recommends \
    locales && \
    locale-gen en_US.UTF-8
ENV LANG="en_US.UTF-8" \
    LANGUAGE="en_US.UTF-8" \
    LC_ALL="en_US.UTF-8"

# install system dependencies
RUN apt update -qq > /dev/null && apt install --yes --no-install-recommends \
    make lsb-release sudo

# install kivy system dependencies
# https://kivy.org/docs/installation/installation-linux.html#dependencies-with-sdl2
RUN apt install --yes --no-install-recommends \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev

WORKDIR /app
COPY . /app
RUN make
ENTRYPOINT ["./dockerfiles/start.sh"]
