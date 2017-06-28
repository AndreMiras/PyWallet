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
Install `libssl-dev` before rebuilding from scratch:
```
sudo apt install libssl-dev
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
