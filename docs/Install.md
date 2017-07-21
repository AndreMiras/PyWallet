# Install

Project and dependencies are different depending on the host and target platform.

## Ubuntu host & target
To run the project on Ubuntu, you need to install the dependencies from using pip.
```
pip install --install-option="--no-cython-compile" $(grep Cython requirements/requirements.txt)
pip install -r requirements/test_requirements.txt
pip install -r requirements.txt
```
Cython needs to be installed explicitly because it's not in any sub-dependency `setup.py` `install_requires`.
Installing `test_requirements.txt` is only required if you want to contribute and run tests.

## Ubuntu host, Android target
```
sudo apt install zlib1g-dev default-jdk
```
