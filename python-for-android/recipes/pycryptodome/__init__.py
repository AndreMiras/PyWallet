from pythonforandroid.recipe import PythonRecipe


class Pysha3Recipe(PythonRecipe):
    url = 'https://github.com/Legrandin/pycryptodome/archive/master.zip'

    depends = ['python2','setuptools']

recipe = Pysha3Recipe()
