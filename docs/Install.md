# Install

Project and dependencies are different depending on the host and target platform.

## Ubuntu host & target
To run the project on Ubuntu, you first need to install system dependencies. See Kivy guide: https://kivy.org/docs/installation/installation-linux.html.

Then install project dependencies using pip (in a virtualenv).
```
pip install --install-option="--no-cython-compile" $(grep Cython requirements/requirements.txt)
pip install -r requirements/test_requirements.txt
pip install -r requirements.txt
```
Cython needs to be installed explicitly because it's not in any sub-dependency `setup.py` `install_requires`.

Installing `test_requirements.txt` is only required if you want to contribute and run tests.

You can also take a look at [script_linux.sh](/travis/script_linux.sh) to see how it's being automated for Travis.

### Linux Camera support (optional)
See [OpenCV.md](/docs/OpenCV.md).
You also need to install `garden.xcamera` as it's a `garden.zbarcam` requirement.
```
garden install garden.xcamera
```

## Ubuntu host, Android target
To be able to build the project for Android from Ubuntu, follow python-for-android official guide (for core dependencies):
https://python-for-android.readthedocs.io/en/latest/quickstart/#installing-dependencies

Before installing additional dependencies.
```
sudo apt install zlib1g-dev default-jdk
```
Check [script_android.sh](/travis/script_android.sh) or [Dockerfile](https://github.com/AndreMiras/PyWallet/blob/feature/ticket37_travis_docker/Dockerfile) to see two different ways to do it in Travis.

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
