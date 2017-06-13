# Troubleshoot


## Devices no permission
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


## Devices no permission
When running the adb devices command, if you're getting a "unauthorized" error message like below:
```
buildozer android adb -- devices
...
List of devices attached 
X9LDU14B18003251        unauthorized
```
Then you simply need to allow your dev computer from your Android device.
