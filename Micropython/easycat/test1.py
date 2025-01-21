an_int = 0x5

a_bytes_big = an_int.to_bytes(2,'big')
print(a_bytes_big,a_bytes_big[0])

a_bytes_little = an_int.to_bytes(4,'little')
print(a_bytes_little)
DEB = const(True)
w=5
print(w>5 or not DEB)

a1 = bytearray(0x1 for _ in range(10)) 
print(a1)