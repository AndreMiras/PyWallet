# Testnet

Some notes about the Testnet.


## Mine on the Testnet (geth)

Sync first:
```
geth --networkid 3 --testnet --fast --cache=512 console
```
Latest Testnet is Ropsten (networkid 3):
```
geth --networkid 3 --testnet --mine
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
Or using faucets:
```
curl -X POST  -H "Content-Type: application/json" -d '{"toWhom":"0x04bf6cdab64affdf50c634e14d88c376f2391d7e"}' https://ropsten.faucet.b9lab.com/tap
```
Then check your balance on:
https://ropsten.etherscan.io/address/0x04bf6cdab64affdf50c634e14d88c376f2391d7e

## Run on the Testnet (pyethapp)
Currently only Morden seems supported.
```
pyethapp --profile testnet run
```
