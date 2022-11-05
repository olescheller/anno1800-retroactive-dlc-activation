import zlib

def main():
    with open("gamesetup_zlib.fdbr", "rb") as f:
        with open("gamesetup2.a7s", "wb") as fu:
            contents = f.read()
            compressed = zlib.compress(contents, level=9)
            fu.write(compressed)
            fu.write(b"xda030000000001f00000")

main()