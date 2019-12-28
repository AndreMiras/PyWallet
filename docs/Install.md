# Install

Project and dependencies are different depending on the host and target platform.

## Ubuntu host & target
```sh
sudo make system_dependencies/linux
```
This `Makefile` installs (`apt`) [system dependencies](https://kivy.org/docs/installation/installation-linux.html).
The rest of the dependencies are Python packages and can be installed in a virtualenv via:
```sh
make virtualenv
```
Then run the project with:
```sh
make run
```

You can also take a look at [.travis.yml](.travis.yml) and [dockerfiles/Dockerfile-linux](dockerfiles/Dockerfile-linux) to see how it's being automated in continuous integration testing.

## Ubuntu host, Android target
To be able to build the project for Android from Ubuntu, follow python-for-android official guide (for core dependencies):
https://python-for-android.readthedocs.io/en/latest/quickstart/#installing-dependencies

Before installing additional dependencies.
```sh
sudo make system_dependencies/android
```
Check [.travis.yml](.travis.yml) or [dockerfiles/Dockerfile-android](dockerfiles/Dockerfile-android) to see Travis automated build in Docker.

## Gentoo 64 host, Android target
Build zlib in 32-bit:
```sh
echo 'sys-libs/zlib abi_x86_32' >> /etc/portage/package.use
emerge -1av sys-libs/zlib
```
Install buildozer outside the virtualenv:
```sh
pip install --user buildozer
```
