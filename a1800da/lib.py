import io
import struct
import sys
import zlib
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
from typing import List, Self


def print(content):
    """Hack to disable print output"""
    pass


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


class Reader:
    """Supply utility methods for reading bytes from a bytearray."""

    def __init__(self, initial_bytes: bytearray):
        self.initial_bytes: bytearray = initial_bytes
        self.initial_bytes_buffer = io.BytesIO(initial_bytes)
        self.size = len(initial_bytes)

    def read_utf8(self, pos: int, size: int) -> str:
        """Read bytes from the initial bytes.

        Interpret bytes as UTF-8 string."""
        buffer = BytesIO(self.initial_bytes)
        buffer.seek(pos)
        return buffer.read(size).decode("utf-8")

    def read(self, pos: int, size: int) -> int:
        """Read bytes from the initial bytes.

        Interpret bytes as little endian."""
        buffer = BytesIO(self.initial_bytes)
        buffer.seek(pos)
        value = int.from_bytes(buffer.read(size), "little")
        print(f"DEBUG: read() value {value} (0x{value:x}), {size} bytes from position (0x{pos:x})")
        return value

    def read_sequentially(self, size: int) -> int:
        """Read bytes from the given buffer.

        Interpret bytes as little endian."""
        buffer = self.initial_bytes_buffer
        value = int.from_bytes(buffer.read(size), "little")
        print(
            f"DEBUG: read_sequentially() value {value} (0x{value:x}), {size} bytes from position (0x{buffer.tell():x})")
        return value

    def read_sequentially_big(self, size: int) -> int:
        """Read bytes from the given buffer.

        Interpret bytes as little endian."""
        buffer = self.initial_bytes_buffer
        value = int.from_bytes(buffer.read(size), "big")
        print(
            f"DEBUG: read_sequentially_big() value {value} (0x{value:x}), {size} bytes from position (0x{buffer.tell():x})")
        return value

    def read_bytes(self, pos: int, size: int) -> bytes:
        """Read bytes from the initial bytes."""
        buffer = BytesIO(self.initial_bytes)
        buffer.seek(pos)
        value = buffer.read(size)
        print(f"DEBUG: read_bytes() {size} bytes from position (0x{pos:x})")
        return value

    def read_big(self, pos: int, size: int) -> int:
        """Read bytes from the initial  bytes.

        Interpret bytes as big endian."""
        byio = BytesIO(self.initial_bytes)
        byio.seek(pos)
        return int.from_bytes(byio.read(size), "big")


class GameSetupNodeTypes(Enum):
    OPENING = 1,
    ATTRIBUTE = 2,
    CLOSING = 3


@dataclass()
class GameSetupNode:
    node_id: int | None
    node_name: str | None
    parent: Self | None


class GameSetupReader(Reader):
    def __init__(self, initial_bytes: bytearray):
        super().__init__(initial_bytes)

        self.existing_dlcs: List[DLC] = []
        self.existing_count_node_ptr: int = -1

        # debug:
        self._parse_enclosing_nodes_block(self.get_enclosing_nodes_block_ptr())
        self._parse_attribute_nodes_block(self.get_attribute_nodes_block_ptr())
        self._parse_active_dlcs()

    def get_activated_dlcs(self):
        return self.existing_dlcs

    def get_enclosing_nodes_block_ptr(self) -> int:
        """Get the pointer to where the enclosing nodes block is saved."""
        return self.read(self.size - 16, 4)

    def get_attribute_nodes_block_ptr(self) -> int:
        """Get the pointer to where the attribute nodes block is saved."""
        return self.read(self.size - 12, 4)

    def _parse_enclosing_nodes_block(self, ptr):
        self.initial_bytes_buffer.seek(ptr)
        enclosing_tags_count = self.read_sequentially(4)
        self.enclosing_tag_ids = [self.read_sequentially(2) for _ in range(0, enclosing_tags_count)]
        self.enclosing_tag_names = [self._collect_single_chars_until_empty_byte() for _ in
                                    range(0, enclosing_tags_count)]
        self.enclosing_tags_combined = dict(zip(self.enclosing_tag_ids, self.enclosing_tag_names))
        print(self.enclosing_tags_combined)

    def _parse_attribute_nodes_block(self, ptr):
        self.initial_bytes_buffer.seek(ptr)
        attribute_tags_count = self.read_sequentially(4)
        self.attribute_tag_ids = [self.read_sequentially(2) for _ in range(0, attribute_tags_count)]
        self.attribute_tag_names = [self._collect_single_chars_until_empty_byte() for _ in
                                    range(0, attribute_tags_count)]
        self.attribute_node_to_id = dict(zip(self.attribute_tag_names, self.attribute_tag_ids))
        print(self.attribute_node_to_id)
        self.attribute_tags_combined = dict(zip(self.attribute_tag_ids, self.attribute_tag_names))
        print(self.attribute_tags_combined)

    @staticmethod
    def get_node_type(number):
        if number >= 32768:
            return GameSetupNodeTypes.ATTRIBUTE
        if 0 < number < 32768:
            return GameSetupNodeTypes.OPENING
        if number <= 0:
            return GameSetupNodeTypes.CLOSING

    def _parse_active_dlcs(self):
        self.initial_bytes_buffer.seek(0)
        xml_nested_level = 0
        current_opening_node: GameSetupNode = GameSetupNode(None, None, None)

        while xml_nested_level >= 0:
            node_content_size = self.read_sequentially(4)
            node_id = self.read_sequentially(4)
            node_type = self.get_node_type(node_id)

            if node_type == GameSetupNodeTypes.OPENING:
                current_opening_node = GameSetupNode(node_id, self.enclosing_tags_combined[node_id],
                                                     current_opening_node)
                xml_nested_level += 1
                if self.enclosing_tags_combined[node_id] == "ActiveDLCs":
                    self.new_dlc_insertion_ptr = self.initial_bytes_buffer.tell()
                    print(f"SAVED new_dlc_insertion_ptr = 0x{self.new_dlc_insertion_ptr:x}")

            if node_type == GameSetupNodeTypes.ATTRIBUTE:
                content_block_size = 8
                node_content = self.read_sequentially_big(node_content_size)
                if self.attribute_tags_combined[node_id] == "count" and current_opening_node.node_name == "ActiveDLCs":
                    self.existing_count_node_ptr: int = self.initial_bytes_buffer.tell() - node_content_size
                    print(
                        f"FOUND COUNT the <ActiveDLC><count> tag. Write value to: 0x{self.existing_count_node_ptr:x}, {node_content_size} bytes, current content 0x{node_content:x}")
                if self.attribute_tags_combined[node_id] == "DLC":
                    self.existing_dlcs.append(DLC(node_content))
                rest_of_bytes_to_read = content_block_size - node_content_size % content_block_size
                if rest_of_bytes_to_read % content_block_size > 0:
                    self.read_sequentially(rest_of_bytes_to_read)

            if node_type == GameSetupNodeTypes.CLOSING:
                current_opening_node = current_opening_node.parent
                xml_nested_level -= 1

        return self.existing_dlcs

    def _collect_single_chars_until_empty_byte(self):
        character = ""
        collected_chars = ""
        while character != '\0':
            character = self.initial_bytes_buffer.read(1).decode()
            if character == '\0':
                return collected_chars
            collected_chars = collected_chars + character


class ParseError(Exception):
    pass


class SaveGameReader(Reader):
    def __init__(self, initial_bytes: bytearray):
        super().__init__(initial_bytes)

    def get_gamesetup_bytes(self) -> bytearray:
        """Extract the gamesetup.a7s bytes from the save file.

        The file is returned decompressed. Save the file header pointers for bytes, file size and compressed for
        later usage.
        """
        if self.read_utf8(0, 18) != "Resource File V2.2":
            raise ParseError("Not a Resource File V2.2")
        magic_bytes = 784
        first_block_ptr = self.read(magic_bytes, 8)
        return bytearray(zlib.decompress(self._find_gamesetup_bytes(first_block_ptr)))

    def _find_gamesetup_bytes(self, block_ptr) -> bytes:
        """Find the gamesetup.a7s bytes by looking through each file header of each directory of each block."""

        # Scan through block headers
        file_count = self.read(block_ptr + 4, 4)
        directory_size = self.read(block_ptr + 8, 8)
        next_block_ptr = self.read(block_ptr + 24, 8)

        directory_block_size = 560
        for i in range(0, file_count):
            # Scan through file headers
            directory_block_ptr = block_ptr - directory_size + i * directory_block_size
            file_name = self.read_utf8(directory_block_ptr, 520).replace("\0", "")
            if file_name == "gamesetup.a7s":
                self.gamesetup_bytes_ptr_ptr = directory_block_ptr + 520 + 0 * 8
                gamesetup_bytes_ptr = self.read(self.gamesetup_bytes_ptr_ptr, 8)
                self.gamesetup_compressed_ptr = directory_block_ptr + 520 + 1 * 8
                self.gamesetup_file_size_ptr = directory_block_ptr + 520 + 2 * 8
                gamesetup_file_size = self.read(self.gamesetup_file_size_ptr, 8)
                return self.read_bytes(gamesetup_bytes_ptr, gamesetup_file_size)
        return self._find_gamesetup_bytes(next_block_ptr)


class Writer:
    def __init__(self, base_bytes: bytearray):
        self.base_bytes: bytearray = base_bytes.copy()
        self.added_bytes = 0

    @property
    def _base_bytes_buffer(self):
        return io.BytesIO(self.base_bytes)

    @property
    def size(self):
        return len(self.base_bytes)

    def insert(self, ptr: int, content: bytes):
        print(f"Inserting at 0x{ptr:x}, {len(content)} bytes")
        self.base_bytes[ptr:ptr] = content
        self.added_bytes += len(content)

    def overwrite(self, ptr: int, content: bytes):
        print(f"Overwriting at 0x{ptr:x}, {len(content)} bytes")
        buffer = self._base_bytes_buffer
        buffer.seek(ptr)
        buffer.write(content)
        buffer.seek(0)
        self.base_bytes = bytearray(buffer.read())
        buffer.close()


class GameSetupWriter(Writer):
    def __init__(self, game_setup_reader: GameSetupReader, base_bytes: bytearray):
        super().__init__(base_bytes)
        self.game_setup_reader = game_setup_reader

    def insert_dlcs(self, dlcs: List[DLC]):
        for dlc in dlcs:
            self.insert_dlc(dlc)
        self.update_dlc_count(len(dlcs))
        self.update_node_block_pointers()

    def update_dlc_count(self, added_dlc_count):
        count = len(self.game_setup_reader.existing_dlcs) + added_dlc_count
        count_bytes = struct.pack("<q", count)
        # count is shifted down by inserted dlcs by 16 bytes each dlc
        ptr = self.game_setup_reader.existing_count_node_ptr + added_dlc_count * 16
        print(f"Update DLC count {len(self.game_setup_reader.existing_dlcs)}, to {count_bytes} at 0x{ptr:x}")
        self.overwrite(ptr, count_bytes)

    def insert_dlc(self, dlc: DLC):
        dlc_content_size = 4
        dlc_element_id = self.game_setup_reader.attribute_node_to_id["DLC"]
        dlc_content = dlc.value
        dlc_bytes_to_insert = (struct.pack("<i", dlc_content_size)
                               + struct.pack("<i", dlc_element_id)
                               + struct.pack(">I", dlc_content)
                               + b"\x00\x00\x00\x00")

        print(f"INSERTING {dlc.name} ...")
        ptr = self.game_setup_reader.new_dlc_insertion_ptr
        self.insert(ptr, dlc_bytes_to_insert)
        print(f"INSERTED {dlc_bytes_to_insert} at {ptr} ({ptr:x})")

    def update_node_block_pointers(self):
        new_enclosing_node_block_ptr = self.game_setup_reader.get_enclosing_nodes_block_ptr() + self.added_bytes
        new_enclosing_node_block_ptr_bytes = struct.pack("<i", new_enclosing_node_block_ptr)
        new_attribute_node_block_ptr = self.game_setup_reader.get_attribute_nodes_block_ptr() + self.added_bytes
        new_attribute_node_block_ptr_bytes = struct.pack("<i", new_attribute_node_block_ptr)
        self.overwrite(self.size - 16, new_enclosing_node_block_ptr_bytes)
        self.overwrite(self.size - 12, new_attribute_node_block_ptr_bytes)

    def get_compressed_gamesetup_a7s(self) -> bytearray:
        gamesetup_a7s = zlib.compress(self.base_bytes, level=9)
        # gamesetup_a7s.extend(b"xda030000000001f00000")
        return gamesetup_a7s

    def get_uncompressed_gamesetup_a7s(self) -> bytearray:
        gamesetup_a7s = self.base_bytes
        return gamesetup_a7s


class SaveGameWriter(Writer):
    def __init__(self, save_game_reader: SaveGameReader, base_bytes: bytearray):
        super().__init__(base_bytes)
        self.save_game_reader = save_game_reader

    def add_gamesetup_a7s(self, gamesetup_bytes: bytearray):
        file_suffix_bytes = self.base_bytes[-80:]
        gamesetup_bytes_ptr = self.size

        self.insert(gamesetup_bytes_ptr, gamesetup_bytes)

        # self.added_bytes += len(gamesetup_bytes)
        self._update_gamesetup_block_file_header(sys.getsizeof(gamesetup_bytes), gamesetup_bytes_ptr)
        self.insert(self.size, b"xda030000000001f00000")
        self._add_new_file_suffix_bytes(file_suffix_bytes)

    def _update_gamesetup_block_file_header(self, gamesetup_size: int, gamesetup_bytes_ptr: int):
        gamesetup_size_bytes = struct.pack("<i", gamesetup_size)
        print(f"gamesetup_file_size_ptr {self.save_game_reader.gamesetup_file_size_ptr}")
        self.overwrite(self.save_game_reader.gamesetup_file_size_ptr, gamesetup_size_bytes)
        print(f"gamesetup_compressed_ptr {self.save_game_reader.gamesetup_compressed_ptr}")
        self.overwrite(self.save_game_reader.gamesetup_compressed_ptr, gamesetup_size_bytes)
        gamesetup_bytes_ptr_bytes = struct.pack("<i", gamesetup_bytes_ptr)
        print(f"Gamesetup bytes ptr at {self.save_game_reader.gamesetup_bytes_ptr_ptr}")
        print(f"Gamesetup bytes now at {gamesetup_bytes_ptr}")
        self.overwrite(self.save_game_reader.gamesetup_bytes_ptr_ptr, gamesetup_bytes_ptr_bytes)

        # original 55928
        # neu 1122169

    def _add_new_file_suffix_bytes(self, file_suffix_bytes: bytes):
        self.insert(self.size, file_suffix_bytes)

    def write_save_game(self, filepath):
        print(f"Writing {filepath}")
        with open(filepath, "w+b") as f:
            f.write(self.base_bytes)
