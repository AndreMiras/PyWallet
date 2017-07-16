# How to release

This is documenting the release process.


## Git flow & CHANGELOG.md

Make sure the CHANGELOG.md is up to date and follows the http://keepachangelog.com guidelines.
Start the release with git flow:
```
git flow release start vYYYYMMDD
```
Now update the CHANGELOG.md `[Unreleased]` section to match the new release version.
Eventually also update the `buildozer.spec` `version` section. Then commit and finish release.
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
  * MyProject - The name of your project, and APK
  * version - The version of this APK (not Kivy version)

### Commands
```
export P4A_RELEASE_KEYSTORE=~/.android/<ALIAS>.keystore
export P4A_RELEASE_KEYSTORE_PASSWD=android
export P4A_RELEASE_KEYALIAS_PASSWD=android
export P4A_RELEASE_KEYALIAS=<ALIAS>

keytool -genkey -v -keystore ~/.android/<my-new-key>.keystore -alias <my-alias> -keyalg RSA -keysize 2048 -validity 10000
buildozer android release
```

## GitHub

Got to GitHub [Release/Tags](https://github.com/AndreMiras/PyWallet/tags), click "Add release notes" for the tag just created.
Add the tag name in the "Release title" field and the relevant CHANGELOG.md section in the "Describe this release" textarea field.
Finally, attach the generated APK release file and click "Publish release".
