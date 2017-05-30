from pythonforandroid.recipe import PythonRecipe


class PyethereumRecipe(PythonRecipe):

    # using custom fork, for fixing a pyethereum upstream bug:
    # https://github.com/ethereum/pyethereum/pull/731
    # url = 'https://github.com/ethereum/pyethereum/archive/develop.zip'
    url = 'https://github.com/AndreMiras/pyethereum/archive/patch-1.zip'

    depends = [
        'python2','setuptools', 'pycryptodome', 'pysha3', 'ethash', 'scrypt'
    ]

    call_hostpython_via_targetpython = False

recipe = PyethereumRecipe()
