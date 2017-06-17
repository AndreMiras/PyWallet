# Troubleshooting


## Android

### ???????????? no permissions
```
buildozer android adb -- devices
...
List of devices attached 
????????????    no permissions
```
You need to add the udev rule of your device.
Here is a rule example you can update and copy to udev rules.d directory.
```
cp root/etc/udev/rules.d/51-android.rules /etc/udev/rules.d/
```
