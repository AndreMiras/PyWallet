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
     * [TODO]   bitcoin
     * [error]  pysha3>=1.0.1
       * it uses a ASM/C package https://github.com/gvanas/KeccakCodePackage
       * maybe try to use pycryptodome sha3 module:
         https://github.com/ethereum/pyethereum/commit/6d6324bf3e99e15f3613990376555db970406534
     * [ok] PyYAML
     * [ok] repoze.lru
     * [ok] pbkdf2
     * [error] pycryptodome>=3.3.1
     * [error] scrypt
     * [ok] rlp>=0.4.7
     * [error] https://github.com/ethereum/ethash/tarball/master
     * [TODO] secp256k1
 * Automate / Document dev requirements
   * Automate VM or Docker
   * https://developer.android.com/studio/run/device.html
   * https://stackoverflow.com/a/5510745/185510
   * https://buildozer.readthedocs.io/en/latest/installation.html
   * https://kivy.org/docs/guide/packaging-android.html#packaging-your-application-into-apk
   * https://python-for-android.readthedocs.io/en/latest/quickstart/#installing-dependencies
   * https://kivy.org/docs/guide/packaging-android.html
