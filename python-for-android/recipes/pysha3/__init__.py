from pythonforandroid.recipe import PythonRecipe



class Pysha3Recipe(PythonRecipe):
    # TODO take a look at:
    # https://github.com/tiran/pysha3/blob/master/Makefile
    # we may need "build_ext -i" (--inplace flag)

    url = 'https://github.com/ethereum/ethash/archive/master.zip'

    depends = ['python2','setuptools']

recipe = Pysha3Recipe()
