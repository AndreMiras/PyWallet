import json
import os

import eth_account
from eth_keyfile import create_keyfile_json, decode_keyfile_json
from eth_keys import keys
from eth_utils import decode_hex, encode_hex, remove_0x_prefix


def to_string(value):
    if isinstance(value, bytes):
        return value
    if isinstance(value, str):
        return bytes(value, 'utf-8')
    if isinstance(value, int):
        return bytes(str(value), 'utf-8')


class Account:
    """
    Represents an account.
    :ivar keystore: the key store as a dictionary (as decoded from json)
    :ivar locked: `True` if the account is locked and neither private nor
    public keys can be accessed, otherwise `False`
    :ivar path: absolute path to the associated keystore file (`None` for
    in-memory accounts)
    """

    def __init__(self, keystore: dict, password: bytes = None, path=None):
        self.keystore = keystore
        try:
            self._address = decode_hex(self.keystore['address'])
        except KeyError:
            self._address = None
        self.locked = True
        if password is not None:
            password = to_string(password)
            self.unlock(password)
        if path is not None:
            self.path = os.path.abspath(path)
        else:
            self.path = None

    @classmethod
    def new(cls, password: bytes, key: bytes = None, uuid=None, path=None,
            iterations=None):
        """
        Create a new account.
        Note that this creates the account in memory and does not store it on
        disk.
        :param password: the password used to encrypt the private key
        :param key: the private key, or `None` to generate a random one
        :param uuid: an optional id
        """
        if key is None:
            account = eth_account.Account.create()
            key = account.privateKey

        # [NOTE]: key and password should be bytes
        password = str.encode(password)

        # encrypted = eth_account.Account.encrypt(account.privateKey, password)
        keystore = create_keyfile_json(key, password, iterations=iterations)
        keystore['id'] = uuid
        return Account(keystore, password, path)

    @classmethod
    def load(cls, path, password: bytes = None):
        """
        Load an account from a keystore file.
        :param path: full path to the keyfile
        :param password: the password to decrypt the key file or `None` to
        leave it encrypted
        """
        with open(path) as f:
            keystore = json.load(f)
        # if not keys.check_keystore_json(keystore):
        #     raise ValueError('Invalid keystore file')
        return Account(keystore, password, path=path)

    def dump(self, include_address=True, include_id=True):
        """
        Dump the keystore for later disk storage.
        The result inherits the entries `'crypto'` and `'version`' from
        `account.keystore`, and adds `'address'` and `'id'` in accordance with
        the parameters `'include_address'` and `'include_id`'.
        If address or id are not known, they are not added, even if requested.
        :param include_address: flag denoting if the address should be included
        or not
        :param include_id: flag denoting if the id should be included or not
        """
        d = {}
        d['crypto'] = self.keystore['crypto']
        d['version'] = self.keystore['version']
        if include_address and self.address is not None:
            d['address'] = encode_hex(self.address)
        if include_id and self.uuid is not None:
            d['id'] = str(self.uuid)
        return json.dumps(d)

    def unlock(self, password: bytes):
        """
        Unlock the account with a password.
        If the account is already unlocked, nothing happens, even if the
        password is wrong.
        :raises: :exc:`ValueError` (originating in ethereum.keys) if the
        password is wrong (and the account is locked)
        """
        if self.locked:
            password = to_string(password)
            self._privkey = decode_keyfile_json(self.keystore, password)
            self.locked = False
            # get address such that it stays accessible after a subsequent lock
            self.address

    def lock(self):
        """
        Relock an unlocked account.
        This method sets `account.privkey` to `None` (unlike `account.address`
        which is preserved).
        After calling this method, both `account.privkey` and `account.pubkey`
        are `None.
        `account.address` stays unchanged, even if it has been derived from the
        private key.
        """
        self._privkey = None
        self.locked = True

    @property
    def privkey(self):
        """
        The account's private key or `None` if the account is locked
        """
        if not self.locked:
            return self._privkey
        else:
            return None

    @property
    def pubkey(self):
        """
        The account's public key or `None` if the account is locked
        """
        if not self.locked:
            pk = keys.PrivateKey(self.privkey)
            return remove_0x_prefix(pk.public_key.to_address())
        else:
            return None

    @property
    def address(self):
        """
        The account's address or `None` if the address is not stored in the key
        file and cannot be reconstructed (because the account is locked)
        """
        if self._address:
            pass
        elif 'address' in self.keystore:
            self._address = decode_hex(self.keystore['address'])
        elif not self.locked:
            pk = keys.PrivateKey(self.privkey)
            self._address = decode_hex(pk.public_key.to_address())
        else:
            return None
        return self._address

    @property
    def uuid(self):
        """
        An optional unique identifier, formatted according to UUID version 4,
        or `None` if the account does not have an id
        """
        try:
            return self.keystore['id']
        except KeyError:
            return None

    @uuid.setter
    def uuid(self, value):
        """
        Set the UUID. Set it to `None` in order to remove it.
        """
        if value is not None:
            self.keystore['id'] = value
        elif 'id' in self.keystore:
            self.keystore.pop('id')

    # TODO: not yet migrated
    # def sign_tx(self, tx):
    #     """
    #     Sign a Transaction with the private key of this account.
    #     If the account is unlocked, this is equivalent to
    #     `tx.sign(account.privkey)`.
    #     :param tx: the :class:`ethereum.transactions.Transaction` to sign
    #     :raises: :exc:`ValueError` if the account is locked
    #     """
    #     if self.privkey:
    #         tx.sign(self.privkey)
    #     else:
    #         raise ValueError('Locked account cannot sign tx')

    def __repr__(self):
        if self.address is not None:
            address = encode_hex(self.address)
        else:
            address = '?'
        return f'<Account(address={address}, id={self.uuid})>'
