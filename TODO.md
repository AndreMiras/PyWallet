# TODO

 * with Kivy
   * Try to open a wallet
   * Try to send a transaction
     * https://github.com/ethereum/pyethapp/wiki/Account-Management
     * https://github.com/ethereum/pyethapp/issues/218
     * https://github.com/AndreMiras/PyWallet/issues/5
       * checklist
         * so make sure we have peers
         * so make sure we have ETH (or disable validate transaction method call)
         * make sure time is sync
       * next up
         * update PyWallet ticket with recent findings
         * findout why I get no peers
           * https://github.com/AndreMiras/PyWallet/issues/6
         * give it a try on the VM and latest develop branch
           * make sure TZ is correct and time is ntp sync
           * make sure it's running @develop branch
   * other way to broadcast transaction:
     * https://etherscan.io/pushTx
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
       # reduce key derivation iterations
       ethereum.keys.PBKDF2_CONSTANTS['c'] = 100
     * [FIXED] pycryptodome>=3.3.1
     * [FIXED] scrypt
     * [ok] rlp>=0.4.7
     * [FIXED] https://github.com/ethereum/ethash/tarball/master
     * [ok] secp256k1
 * Test
   * isort
   * flake8
   * pylint
 * Automate / Document dev requirements
   * Automate VM or Docker
   * https://developer.android.com/studio/run/device.html
   * https://stackoverflow.com/a/5510745/185510
   * https://buildozer.readthedocs.io/en/latest/installation.html
   * https://kivy.org/docs/guide/packaging-android.html#packaging-your-application-into-apk
   * https://python-for-android.readthedocs.io/en/latest/quickstart/#installing-dependencies
   * https://kivy.org/docs/guide/packaging-android.html
   * Upstream
     * pydevp2p
       * fix broken tests:
         * https://github.com/ethereum/pydevp2p/commit/8e1f2b2ef28ecba22bf27eac346bfa7007eaf0fe
