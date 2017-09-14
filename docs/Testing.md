# Testing

## Tox
All the tests are ran via `tox` exept the user interface tests.
```
tox
```

## User interface tests
UI tests are ran using [KeyWeeUsr/KivyUnitTest](https://github.com/KeyWeeUsr/KivyUnitTest).
```
python -m kivyunittest --folder src/tests/ui/ --pythonpath src/
```
