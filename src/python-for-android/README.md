# Python for Android Recipes

This directory contains custom recipes used by the application.

## Debug
To debug custom recipes, it's possible to link them to the buildozer recipes directory.
For example for `ethash` recipe:
```
ln -sfn \
$PWD/python-for-android/recipes/ethash \
$PWD/.buildozer/android/platform/python-for-android-master/pythonforandroid/recipes/
```
That way commands likes `clean_recipe_build` will also be available for the custom recipe.


## Recipes
List all:
```
buildozer android p4a -- recipes
```

Clean all:
```
buildozer android p4a -- clean_dists
```

Clean a specific recipe, e.g. ethash:
```
buildozer android p4a -- clean_recipe_build ethash
```
