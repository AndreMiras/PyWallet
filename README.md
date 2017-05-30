# README

Just trying to build a Ethereum wallet with Kivy.

## Debug

### Mine on the Testnet (geth)

Latest Testnet is Ropsten (networkid 3):
```
geth --networkid 3 --mine
```
Also you need to make sure you have at least one wallet, since it will take the first one
for reward by default:
```
geth --networkid 3 account list
```

To set the reward address to a different account use the `--etherbase` flag:
```
geth --networkid 3 --mine --etherbase value
```

### Run on the Testnet (pyethapp)

```
pyethapp --profile testnet run
```


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
