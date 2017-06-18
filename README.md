# PyWallet

[![Build Status](https://secure.travis-ci.org/AndreMiras/PyWallet.png?branch=develop)](http://travis-ci.org/AndreMiras/PyWallet)

Cross platform Ethereum Wallet built with Python and Kivy.

![Screenshot](https://raw.githubusercontent.com/AndreMiras/PyWallet/develop/docs/images/preview_nexus_6p.png)

## Features

  * Show balance
  * Show transaction history
  * Receive Ethers via QR code
  * Send Ethers (TODO)
  * Handle multi keystores (TODO)

## Buildozer

### Debug
```
buildozer android debug deploy run logcat
buildozer android adb -- logcat
```

## Ubuntu dependencies
```
sudo apt install zlib1g-dev default-jdk
```

## Documentation

* Miscellaneous documentation in the [docs](docs/) directory
* Recipes documentation in the [python-for-android](python-for-android/) directory
