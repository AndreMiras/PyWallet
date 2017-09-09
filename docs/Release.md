# How to release

This is documenting the release process.


## Git flow & CHANGELOG.md

Make sure the CHANGELOG.md is up to date and follows the http://keepachangelog.com guidelines.
Start the release with git flow:
```
git flow release start vYYYYMMDD
```
Now update the CHANGELOG.md `[Unreleased]` section to match the new release version.
Also update the `__version__` string of the [version.py](/src/version.py) file. Then commit and finish release.
```
git commit -a -m "vYYYYMMDD"
git flow release finish
```
Push everything, make sure tags are also pushed:
```
git push
git push --tags
```

## Android

Useful links:

  * https://developer.android.com/studio/publish/app-signing.html
  * https://github.com/kivy/kivy/wiki/Creating-a-Release-APK

### Fields

  * my-project - The directory for your project
  * my-new-key - The name of the key you generate
  * my-alias - A short alias name for the key

### Commands
Prepare the environment variables:
```
export P4A_RELEASE_KEYSTORE=~/.android/<my-alias>.keystore
export P4A_RELEASE_KEYSTORE_PASSWD=android
export P4A_RELEASE_KEYALIAS_PASSWD=android
export P4A_RELEASE_KEYALIAS=<my-alias>
```
Generate a keystore if not yet generated:
```
keytool -genkey -v -keystore ~/.android/<my-new-key>.keystore -alias <my-alias> -keyalg RSA -keysize 2048 -validity 10000
```
Run buildozer:
```
buildozer android release
```

### Play Store

<https://play.google.com/apps/publish/>

## GitHub

Got to GitHub [Release/Tags](https://github.com/AndreMiras/PyWallet/tags), click "Add release notes" for the tag just created.
Add the tag name in the "Release title" field and the relevant CHANGELOG.md section in the "Describe this release" textarea field.
Finally, attach the generated APK release file and click "Publish release".
