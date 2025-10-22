import hashlib


data = "Transaccion Aylin"
prev_hash = "0000"
hash = hashlib.sha256((data + prev_hash) .encode()) .hexdigest()
print(hash)