# TODO

 * with Kivy
   * Try to open a wallet
   * Try to send a transaction
     * https://github.com/ethereum/pyethapp/wiki/Account-Management
 * Take a look at:
   * https://github.com/ethereum/pyethereum
   * https://github.com/ethereum/pyethapp
 * use the test net
 * perform a transaction:
   * https://github.com/ethereum/pyethapp/wiki/Account-Management
 * pyethapp & pyethereum compilation recipe
   * https://stackoverflow.com/a/22268636/185510
   * checking from requirements:
     * [ok]   bitcoin
     * [FIXED]  pysha3>=1.0.1
     * [ok] PyYAML
     * [ok] repoze.lru
     * [ok] pbkdf2
     * [FIXED] pycryptodome>=3.3.1
     * [error] scrypt -> TODO this is the next up as in 2017/05/28
       * It could be skipped in a way that it doesn't seem totally mandatory, see:
         https://github.com/ethereum/pyethereum/blob/v1.6.1/ethereum/keys.py
     * [ok] rlp>=0.4.7
     * [FIXED] https://github.com/ethereum/ethash/tarball/master
     * [ok] secp256k1
 * Automate / Document dev requirements
   * Automate VM or Docker
   * https://developer.android.com/studio/run/device.html
   * https://stackoverflow.com/a/5510745/185510
   * https://buildozer.readthedocs.io/en/latest/installation.html
   * https://kivy.org/docs/guide/packaging-android.html#packaging-your-application-into-apk
   * https://python-for-android.readthedocs.io/en/latest/quickstart/#installing-dependencies
   * https://kivy.org/docs/guide/packaging-android.html
