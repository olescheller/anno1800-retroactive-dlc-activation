import zlib

def main():
    filename = "gamesetup"
    suffix = "a7s"
    suffix2 = "zlib"
    with open(f"{filename}.{suffix}", "rb") as f:
        with open(f"{filename}_{suffix2}", "wb") as fu:
            contents = f.read()
            decompressed = zlib.decompress(contents)
            fu.write(decompressed)

main()