import sys

def test_pyethash():
    import pyethash
    result = pyethash.get_seedhash(0)
    print("result:", result)

def test_hashlib_sha3():
    import hashlib
    import sha3
    print("hashlib:", hashlib)
    print("sha3:", sha3)
    print("hashlib.sha3_512():", hashlib.sha3_512())
    print("sha3.keccak_512():", sha3.keccak_512())

def test_scrypt():
    import scrypt
    print("scrypt")
    data = scrypt.encrypt('a secret message', 'password', maxtime=0.1) # This will take at least 0.1 seconds
    print("data[:20]:", data[:20])
    # 'scrypt\x00\r\x00\x00\x00\x08\x00\x00\x00\x01RX9H'
    scrypt.decrypt(data, 'password', maxtime=0.1) # This will also take at least 0.1 seconds
    # 'a secret message'

def main():
    print("sys.version_info:", sys.version_info)
    test_pyethash()
    test_hashlib_sha3()
    test_scrypt()
    print("end")


if __name__ == '__main__':
    main()
