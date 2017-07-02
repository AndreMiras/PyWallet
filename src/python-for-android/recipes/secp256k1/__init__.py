from os.path import join
from pythonforandroid.recipe import PythonRecipe


class Secp256k1Recipe(PythonRecipe):

    url = 'https://github.com/ludbb/secp256k1-py/archive/master.zip'

    call_hostpython_via_targetpython = False

    depends = [
        'openssl', 'hostpython2', 'python2', 'setuptools',
        'libffi', 'cffi', 'libffi', 'libsecp256k1']

    patches = [
        "cross_compile.patch", "drop_setup_requires.patch",
        "pkg-config.patch", "find_lib.patch"]


recipe = Secp256k1Recipe()
