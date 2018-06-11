# Install

Project and dependencies are different depending on the host and target platform.

## Ubuntu host & target
```sh
make
```
This `Makefile` installs (`apt`) [system dependencies](https://kivy.org/docs/installation/installation-linux.html),
[compiles OpenCV](/docs/OpenCV.md), `pip` and `garden` dependencies. Python dependencies are installed in a virtualenv.

You can also install `test_requirements.txt` if you want to contribute and run tests.

You can also take a look at [.travis.yml](.travis.yml) and [dockerfiles/Dockerfile-linux](dockerfiles/Dockerfile-linux) to see how it's being automated in continuous integration testing.

## Ubuntu host, Android target
To be able to build the project for Android from Ubuntu, follow python-for-android official guide (for core dependencies):
https://python-for-android.readthedocs.io/en/latest/quickstart/#installing-dependencies

Before installing additional dependencies.
```
sudo apt install zlib1g-dev default-jdk
```
Check [.travis.yml](.travis.yml) or [dockerfiles/Dockerfile-android](dockerfiles/Dockerfile-android) to see Travis automated build in Docker.

## Gentoo 64 host, Android target
Build zlib in 32-bit:
```
echo 'sys-libs/zlib abi_x86_32' >> /etc/portage/package.use
emerge -1av sys-libs/zlib
```
Install buildozer outside the virtualenv:
```
pip install --user buildozer
```
