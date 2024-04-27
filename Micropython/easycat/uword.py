import uctypes

UWORD = {
    "bytes": (0 | uctypes.ARRAY, 2 | uctypes.UINT8),
    "word": 0 | uctypes.UINT16
}
addr = bytearray([0x0,0x1])
struct1 = uctypes.struct(uctypes.addressof(addr), UWORD, uctypes.NATIVE)

struct1.word=0xffff
print(struct1.word)
print(struct1.bytes[0])
print(struct1.bytes[1])
print('-----')
struct1.bytes[0]=1
struct1.bytes[1]=1
print(struct1.word)
print(struct1.bytes[0])
print(struct1.bytes[1])

STRUCT2 = {
    "bytes": (0 | uctypes.ARRAY, 4 | uctypes.UINT8),
    "long": 0 | uctypes.UINT32
}
addr1 = bytearray([0x0,0x1,0x02,0x03])
struct2 = uctypes.struct(uctypes.addressof(addr1), STRUCT2, uctypes.NATIVE)
print('-------------long')
struct2.long=0x01020304
print(struct2.long)
print(struct2.bytes[0])
print(struct2.bytes[1])
print(struct2.bytes[2])
print(struct2.bytes[3])
print('-----')
struct2.bytes[0]=10
struct2.bytes[1]=11
struct2.bytes[2]=12
struct2.bytes[3]=13

print(struct2.long)
print(struct2.bytes[0])
print(struct2.bytes[1])
print(struct2.bytes[2])
print(struct2.bytes[3])