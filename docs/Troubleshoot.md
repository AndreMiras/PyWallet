# Troubleshoot


## Android

### Devices no permission
When running the adb devices command, if you're getting a "no permissions" error message like below:
```
buildozer android adb -- devices
...
List of devices attached 
????????????    no permissions
```

Update your udev rules, there's an example to adapt to your Android device here:
```
sudo cp root/etc/udev/rules.d/51-android.rules /etc/udev/rules.d/
```
Then replug your device and rerun the command.


### Devices unauthorized
When running the adb devices command, if you're getting a "unauthorized" error message like below:
```
buildozer android adb -- devices
...
List of devices attached 
X9LDU14B18003251        unauthorized
```
Then you simply need to allow your dev computer from your Android device.


### Buildozer run

Buildozer fails with the error below when installing dependencies:
```
urllib.error.URLError: <urlopen error unknown url type: https>
```
First install `libssl-dev`:
```
sudo apt install libssl-dev
```
Then clean openssl recipe build and retry:
```
buildozer android p4a -- clean_recipe_build openssl
buildozer android debug
```


Buildozer fails when building libffi:
```
configure.ac:41: error: possibly undefined macro: AC_PROG_LIBTOOL
      If this token and others are legitimate, please use m4_pattern_allow.
      See the Autoconf documentation.
autoreconf: /usr/bin/autoconf failed with exit status: 1
```
Fix it by installing autogen autoconf and libtool:
```
sudo apt install autogen autoconf libtool
```

Buildozer fails with when building cffi:
```
c/_cffi_backend.c:13:17: fatal error: ffi.h: No such file or directory
```
See upstream ticket: https://github.com/kivy/python-for-android/issues/1148


## Kivy

### Debugging widget sizes

<https://github.com/kivy/kivy/wiki/Debugging-widget-sizes>
