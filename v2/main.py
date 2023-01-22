import io
import os.path
import zlib
from enum import Enum
from io import BytesIO
from typing import List
import struct


class DLC(Enum):
    THE_ANARCHIST = 2861514240  # 0xaa8f3e00
    S1_SUNKEN_TREASURES = 3091269120  # 0xb8410600
    S1_BOTANICA = 3108046336  # 0xb9410600
    S1_THE_PASSAGE = 3124823552  # 0xba410600
    S2_SEAT_OF_POWER = 3410036224  # 0xcb410600
    S2_BRIGHT_HARVEST = 3594585600  # 0xd6410600
    S2_LAND_OF_LIONS = 3611362816  # 0xd7410600
    S3_DOCKLANDS = 3812689408  # 0xe3410600
    S3_TOURIST_SEASON = 3829466624  # 0xe4410600
    S3_HIGH_LIFE = 3846243840  # 0xe5410600
    S4_SEEDS_OF_CHANGE = 2170617856  # 0x81610000
    S4_EMPIRE_OF_THE_SKIES = 2187395072  # 0x82610000
    S4_NEW_WORLD_RISING = 2204172288  # 0x83610000


# Path to the savefile, relative to this script file
SAVE_GAME_PATH = "Autosave.a7s"

# Insert the DLCs to add to the save game
DLCS_TO_ADD = [DLC.S3_HIGH_LIFE, DLC.S4_NEW_WORLD_RISING]


def get_dlc_name_by_id(id: int):
    [name] = [dlc.name for dlc in DLC if dlc.value == id]
    return name


class TagNode(object):
    def __init__(self, element_id: int, tag_name: str, parent_tag: "TagNode"):
        self.element_id = element_id
        self.name = tag_name
        self.parent_tag_node: TagNode = parent_tag
        self.attributes: List[AttributeNode] = []
        self.child_tag_nodes: List[TagNode] = []

    def add_attribute(self, attribute):
        self.attributes.append(attribute)

    def add_child_tag(self, tag):
        self.child_tag_nodes.append(tag)

    def __repr__(self):
        return f"<{self.name}/>"


class AttributeNode(object):
    def __init__(self, element_id: int, name: str, content_size: int, parent_tag_node: TagNode, content: int):
        self.element_id = element_id
        self.name = name
        self.content_size = content_size
        self.parent_tag: TagNode = parent_tag_node
        self.content = content

    def __repr__(self):
        return f"<{self.name}/>"


def open_save_file(save_file_path):
    f = open(save_file_path, "br")
    if not is_file_valid(f):
        return None
    print("Resource File V2.2 ✔")
    return f


def is_file_valid(f):
    """ Check for proper resource file version. """
    return f.read(len("Resource File V2.2".encode("UTF-8"))).decode("UTF-8") == "Resource File V2.2"


def get_gamesetup_a7s_bytes(f):
    # Skip a magic number of bytes
    f.seek(766 + len("Resource File V2.2"))

    print(f"File directory start block offset:      {hex(f.tell())}")
    directory_metadata_offset = read_int(f, 8)
    f.seek(directory_metadata_offset)

    return find_gamesetup_block(f, f.tell())


def find_gamesetup_block(f, block_offset):
    f.seek(block_offset)

    print(f"meta data position:      {hex(f.tell())}")
    flags = read_int(f, 4)
    file_count = read_int(f, 4)
    directory_size = read_int(f, 8)
    decompressed_size = read_int(f, 8)
    print(f"reading next block at:      {hex(f.tell())}")
    next_block_offset = read_int(f, 8)
    print(f"Flags:      {hex(flags)}")
    print(f"file_count:      {file_count}")
    print(f"next_block offset:      {hex(next_block_offset)}")

    f.seek(block_offset - directory_size)
    directory_bytes = f.read(directory_size)

    # Find gamesetup.a7s in the directory and extract its bytes
    gamesetup_offset, gamesetup_size = search_directory_block_for_gamesetup_a7s(directory_bytes, file_count)

    if gamesetup_offset is None:
        return find_gamesetup_block(f, next_block_offset)
    # Extract the binary contents of gamesetup.a7s
    f.seek(gamesetup_offset)
    return f.read(gamesetup_size)


def search_directory_block_for_gamesetup_a7s(directory_bytes, file_count):
    directory_bytes_io = BytesIO(directory_bytes)
    for _ in range(0, file_count):
        file_name = directory_bytes_io.read(520).decode("UTF-16").replace("\0", "")
        offset = read_int(directory_bytes_io, 8)
        compressed = read_int(directory_bytes_io, 8)
        file_size = read_int(directory_bytes_io, 8)
        timestamp = read_int(directory_bytes_io, 8)
        unknown = read_int(directory_bytes_io, 8)
        print(f"File:       {file_name} ✔")
        if file_name == "gamesetup.a7s":
            print(f"File:       {file_name} ✔")
            print(f"At offset:  {offset} ({offset:x})")
            print(f"Compressed: {compressed}")
            print(f"File size:  {file_size}")
            print(f"File until:  {offset + file_size:x}")
            return offset, file_size
    return None, None


def read_int(f, number_bytes):
    return int.from_bytes(f.read(number_bytes), "little")


def read_int_big(f, number_bytes):
    return int.from_bytes(f.read(number_bytes), "big")


def export_gamesetup_a7s(save_file_path):
    f = open_save_file(save_file_path)
    gamesetup_a7s_bytes = get_gamesetup_a7s_bytes(f)
    f.close()
    return gamesetup_a7s_bytes


def decompress_gamesetup_a7s(gamesetup_a7s_compressed_bytes):
    return zlib.decompress(gamesetup_a7s_compressed_bytes)


def compress_gamesetup_a7s(gamesetup_a7s_decompressed_bytes):
    return zlib.compress(gamesetup_a7s_decompressed_bytes, level=9)


def get_tags_and_attributes_addresses_header(gamesetup_a7s_decompressed_bytes):
    handle = BytesIO(gamesetup_a7s_decompressed_bytes)
    file_size = handle.seek(0, io.SEEK_END)
    offset_to_offsets = 16
    tags_offset = file_size - offset_to_offsets
    attributes_offset = tags_offset + 4
    return tags_offset, attributes_offset


def parse_decompressed_gamesetup_a7s(gamesetup_a7s_decompressed_bytes: bytearray) -> TagNode:
    handle = BytesIO(gamesetup_a7s_decompressed_bytes)
    initial_tags_offset_address, attributes_offset_address = get_tags_and_attributes_addresses_header(
        gamesetup_a7s_decompressed_bytes)

    handle.seek(initial_tags_offset_address)
    print(f"Reading tags_offset_address (4byte) at {handle.tell():x}")
    # read tags/attribute offsets
    initial_tags_address = read_int(handle, 4)
    print(f"Reading attributes_offset_address (4byte) at {handle.tell():x}")
    initial_attributes_address = read_int(handle, 4)
    print(hex(initial_tags_address))
    print(hex(initial_attributes_address))

    # read xml tags
    handle.seek(initial_tags_address)
    tags_count = read_int(handle, 4)
    print(f"XMl tags count: {tags_count}")
    tag_ids = [read_int(handle, 2) for _ in range(0, tags_count)]
    print(tag_ids)
    tag_names = [read_chars_until_space(handle) for _ in range(0, tags_count)]
    print(tag_names)
    tags = dict(zip(tag_ids, tag_names))

    # read xml attributes
    handle.seek(initial_attributes_address)
    attribute_count = read_int(handle, 4)
    print(f"XMl attributes count: {attribute_count}")
    attribute_ids = [read_int(handle, 2) for _ in range(0, attribute_count)]
    print(attribute_ids)
    attribute_names = [read_chars_until_space(handle) for _ in range(0, attribute_count)]
    print(attribute_names)
    attributes = dict(zip(attribute_ids, attribute_names))

    handle.seek(0)
    current_depth = 0
    root_tag_node: TagNode = None
    parent_tag_node: TagNode = None
    tag_node: TagNode = None

    active_dlcs = []
    last_dlc_found_offset = 0
    dlc_content_size = 0
    dlc_element_id = 0

    dlc_count_element_id = 0
    dlc_count_offset = 0
    dlc_count_content = 0
    dlc_count_content_size = 0

    while current_depth >= 0:
        start_read_at_offset = handle.tell()
        content_size = read_int(handle, 4)
        element_id = read_int(handle, 4)
        print(f"\nsize {content_size}, element_id {element_id} at {hex(handle.tell())}")

        if get_node_type(element_id) == "tag":
            print(f"Found tag: <{tags[element_id]}> ({element_id}) at {hex(handle.tell())}")
            if tag_node is not None:
                parent_tag_node = tag_node

            tag_node = TagNode(element_id, tags[element_id], parent_tag_node)

            if root_tag_node is None:
                root_tag_node = tag_node
            if parent_tag_node is not None:
                parent_tag_node.add_child_tag(tag_node)

            current_depth += 1

        elif get_node_type(element_id) == "attr":
            content_block_size = 8
            content = read_int_big(handle, content_size)
            current_attribute = AttributeNode(content_size, attributes[element_id], element_id,
                                              tag_node, content)

            tag_node.add_attribute(current_attribute)

            content_in_hex = f"{content:x}"

            if tag_node.name == "ActiveDLCs" and attributes[element_id] == "count":
                dlc_count_element_id = element_id
                dlc_count_offset = start_read_at_offset
                dlc_count_content = content
                dlc_count_content_size = content_size

            if attributes[element_id] == "DLC":
                dlc_element_id = element_id
                active_dlcs.append(content)
                dlc_content_size = content_size
                last_dlc_found_offset = start_read_at_offset

            print(
                f"Found attr: <{attributes[element_id]}>{content_in_hex}</{attributes[element_id]}> at {hex(handle.tell())} (read {content_size} bytes)")
            rest_of_bytes_to_read = content_block_size - content_size % content_block_size
            if rest_of_bytes_to_read % content_block_size > 0:
                read_int_big(handle, rest_of_bytes_to_read)
                print(f"Reading the rest of the block ({rest_of_bytes_to_read} bytes)")

        elif get_node_type(element_id) == "terminator":
            print(f"Found terminator at {hex(handle.tell())}")

            if current_depth > 0:
                tag_node = tag_node.parent_tag_node
            else:
                tag_node = None

            current_depth -= 1

    active_dlcs_count_prior = len(active_dlcs)

    print([get_dlc_name_by_id(i) for i in sorted(active_dlcs)])
    print([hex(i) for i in sorted(active_dlcs)])
    print([i for i in sorted(active_dlcs)])
    print(last_dlc_found_offset, dlc_element_id, dlc_content_size)
    print(dlc_count_element_id, hex(dlc_count_offset), dlc_count_content, hex(dlc_count_content),
          dlc_count_content_size)

    for dlc_to_add in DLCS_TO_ADD:
        # add dlc: calculate insert position
        new_dlc_insert_position = last_dlc_found_offset + 4 + 4 + 8
        # add dlc: insert dlc block
        bytes_to_insert = (struct.pack("<i", dlc_content_size)
                           + struct.pack("<i", dlc_element_id)
                           + struct.pack(">I", dlc_to_add.value)
                           + b"\x00\x00\x00\x00")

        # Required for writing the new dlc count later on
        active_dlcs.append(dlc_to_add.value)

        print(f"inserting {bytes_to_insert} at {new_dlc_insert_position} ({new_dlc_insert_position:x})")
        # insert
        gamesetup_a7s_decompressed_bytes[new_dlc_insert_position:new_dlc_insert_position] = bytes_to_insert

    # update count
    new_handle = BytesIO(gamesetup_a7s_decompressed_bytes)
    new_count = struct.pack("<q", len(active_dlcs))
    print(f"Updating DLC count at {dlc_count_offset:x} to {new_count}")
    new_handle.seek(dlc_count_offset + 8)  # skip size and elementid
    new_handle.write(new_count)

    # get new header positions for new file size
    new_tags_address_reference, new_attributes_address_reference = get_tags_and_attributes_addresses_header(
        gamesetup_a7s_decompressed_bytes)
    # update tag and attributes offsets
    active_dlcs_count = len(active_dlcs)
    print(f"Active and prior DLC counts: {active_dlcs_count}, {active_dlcs_count_prior})")

    new_tags_start_address = initial_tags_address + (len(active_dlcs) - active_dlcs_count_prior) * 16
    print(
        f"Changing tags offset from {initial_tags_address} to {new_tags_start_address} ({initial_tags_address:x} to {new_tags_start_address:x}), writing to {new_tags_address_reference:x}")
    new_attributes_start_address = initial_attributes_address + (len(active_dlcs) - active_dlcs_count_prior) * 16
    print(
        f"Changing attribtutes offset from {initial_attributes_address} to {new_attributes_start_address} ({initial_attributes_address:x} to {new_attributes_start_address:x}), writing to {new_attributes_address_reference:x}")

    new_handle.seek(new_tags_address_reference)
    new_handle.write(struct.pack("<i", new_tags_start_address))
    new_handle.seek(new_attributes_address_reference)
    new_handle.write(struct.pack("<i", new_attributes_start_address))
    new_handle.seek(0)

    return root_tag_node, bytearray(new_handle.read())


def print_node_tree(tag_node: TagNode, result: str = ""):
    # opening tag
    result = f"{result}<{tag_node.name}>"
    # attributes
    for attr in tag_node.attributes:
        result = f"{result}<{attr.name}>{attr.content:x}</{attr.name}>"

    # children
    for child in tag_node.child_tag_nodes:
        child_tree = print_node_tree(child)
        result = f"{result}{child_tree}"
    # closing tag
    result = f"{result}</{tag_node.name}>"
    return result


def read_chars_until_space(f) -> str:
    current_character = ""
    collected_value = ""
    while current_character != '\0':
        current_character = f.read(1).decode()
        if current_character == '\0':
            return collected_value
        collected_value = collected_value + current_character

def get_node_type(number):
    if number >= 32768:
        return "attr"
    if 0 < number < 32768:
        return "tag"
    if number <= 0:
        return "terminator"

def main(save_game_path):
    save_game_file_name = save_game_path
    # Step 1: Export gamesetup.a7s from save game
    gamesetup_a7s_compressed_bytes = export_gamesetup_a7s(save_game_file_name)

    # with open(f"{save_game_file_name}_gamesetup_extracted", "wb+") as fe:
    #     fe.write(gamesetup_a7s_compressed_bytes)

    # Step 2: Decompress exported gamesetup.a7s
    gamesetup_a7s_decompressed_bytes = decompress_gamesetup_a7s(gamesetup_a7s_compressed_bytes)

    # with open(f"{save_game_file_name}_gamesetup_decompressed", "wb+") as fe:
    #     fe.write(gamesetup_a7s_decompressed_bytes)

    # Step 3: Parse and insert desired DLCs into decompressed gamesetup bytes
    # Step 3a: generate XML from bytes (optional)
    root_tag_node, decompressed_gamesetup_a7s_containing_new_dlcs = parse_decompressed_gamesetup_a7s(
        bytearray(gamesetup_a7s_decompressed_bytes))
    print(print_node_tree(root_tag_node))

    # with open(f"{save_game_file_name}_gamesetup_decompress_added_dlcs", "wb+") as fe:
    #     fe.write(decompressed_gamesetup_a7s_containing_new_dlcs)
    #
    # with open(f"{save_game_file_name}_gamesetup_a7s.xml", "wb+") as fe:
    #     fe.write(print_node_tree(root_tag_node).encode("utf-8"))

    # Step 4: Compress gamesetup with added dlcs
    compressed_gamesetup_containing_new_dlcs = compress_gamesetup_a7s(decompressed_gamesetup_a7s_containing_new_dlcs)
    with open(f"gamesetup.a7s", "wb+") as fe:
        fe.write(compressed_gamesetup_containing_new_dlcs)
        fe.write(b"xda030000000001f00000")
    print(f"Wrote gamesetup.a7s to {os.path.abspath('gamesetup.a7s')}")

    # Step 5: Import gamesetup back into save file
    # Use RDAExplorer for now!


def run_with_script_parameters():
    main(SAVE_GAME_PATH)


if __name__ == "__main__":
    run_with_script_parameters()
