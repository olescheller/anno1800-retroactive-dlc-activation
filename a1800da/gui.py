import tkinter as tk
from tkinter import filedialog
import os
from typing import List, Tuple

from a1800da import lib
from a1800da.lib import DLC


class CheckboxesGuiModel:
    def __init__(self, dlc: DLC, row: int, column: int, label: str):
        self.dlc = dlc
        self.row = row
        self.column = column
        self.label = label


def get_checkboxes_gui_models() -> List[CheckboxesGuiModel]:
    """Create a gui model for the dlc checkboxes."""
    return [
        CheckboxesGuiModel(DLC.THE_ANARCHIST, 0, 0, DLC.THE_ANARCHIST.name),
        CheckboxesGuiModel(DLC.S1_SUNKEN_TREASURES, 1, 0, DLC.S1_SUNKEN_TREASURES.name),
        CheckboxesGuiModel(DLC.S1_BOTANICA, 1, 1, DLC.S1_BOTANICA.name),
        CheckboxesGuiModel(DLC.S1_THE_PASSAGE, 1, 2, DLC.S1_THE_PASSAGE.name),
        CheckboxesGuiModel(DLC.S2_SEAT_OF_POWER, 2, 0, DLC.S2_SEAT_OF_POWER.name),
        CheckboxesGuiModel(DLC.S2_BRIGHT_HARVEST, 2, 1, DLC.S2_BRIGHT_HARVEST.name),
        CheckboxesGuiModel(DLC.S2_LAND_OF_LIONS, 2, 2, DLC.S2_LAND_OF_LIONS.name),
        CheckboxesGuiModel(DLC.S3_DOCKLANDS, 3, 0, DLC.S3_DOCKLANDS.name),
        CheckboxesGuiModel(DLC.S3_TOURIST_SEASON, 3, 1, DLC.S3_TOURIST_SEASON.name),
        CheckboxesGuiModel(DLC.S3_HIGH_LIFE, 3, 2, DLC.S3_HIGH_LIFE.name),
        CheckboxesGuiModel(DLC.S4_SEEDS_OF_CHANGE, 4, 0, DLC.S4_SEEDS_OF_CHANGE.name),
        CheckboxesGuiModel(DLC.S4_EMPIRE_OF_THE_SKIES, 4, 1, DLC.S4_EMPIRE_OF_THE_SKIES.name),
        CheckboxesGuiModel(DLC.S4_NEW_WORLD_RISING, 4, 2, DLC.S4_NEW_WORLD_RISING.name),
    ]


priorly_active_dlcs: List[DLC] = []


class Gui:

    def apply_changes(self):
        dlcs_to_activate = [dlc for dlc in self.selected_dlcs if dlc not in self.priorly_active_dlcs]
        if dlcs_to_activate:
            self.game_setup_writer.insert_dlcs(dlcs_to_activate)

            self.save_game_writer = lib.SaveGameWriter(self.save_game_reader, self.save_game_reader.initial_bytes)
            self.save_game_writer.add_gamesetup_a7s(self.game_setup_writer.get_compressed_gamesetup_a7s())

            old_filename = os.path.basename(self.save_game_file_path)
            new_filename = old_filename.split(".")[0] + "_dlc_activated.a7s"
            save_game_dir = os.path.dirname(self.save_game_file_path)

            # with open(os.path.join(save_game_dir, "gui_gamesetup_original.a7s"), "w+b") as f:
            #     f.write(self.save_game_reader.get_gamesetup_bytes())
            # with open(os.path.join(save_game_dir, "gui_gamesetup_uncompressed.a7s"), "w+b") as f:
            #     f.write(self.game_setup_writer.get_uncompressed_gamesetup_a7s())
            # with open(os.path.join(save_game_dir, "gui_gamesetup.a7s"), "w+b") as f:
            #     f.write(self.game_setup_writer.get_compressed_gamesetup_a7s())
            self.save_game_writer.write_save_game(os.path.join(save_game_dir, new_filename))
            self.status_message.set(f"New file '{new_filename}' created.")
        elif not self.save_game_file_path:
            self.status_message.set(f"Select an Anno 1800 save game using 'Open Save File'.")
        else:
            self.status_message.set(f"Pick at least one DLC to activate.")

    def update_selected_dlcs(self, dlc: DLC):
        if dlc in self.selected_dlcs:
            self.selected_dlcs.remove(dlc)
        else:
            self.selected_dlcs.append(dlc)
        print(self.selected_dlcs)

    def open_file(self):
        folder1 = os.path.join(os.getenv("USERPROFILE"), "Documents", "Anno 1800", "accounts")
        folder2 = os.path.join(os.getenv("USERPROFILE"), "OneDrive", "Documents", "Anno 1800", "accounts")

        initial_dir = None
        if os.path.isdir(folder1):
            initial_dir = folder1
        elif os.path.isdir(folder2):
            initial_dir = folder2

        accounts = os.listdir(initial_dir)
        if len(accounts) == 1:
            initial_dir = os.path.join(initial_dir, accounts[0])

        # Set the initial directory to the user's home directory

        # Open the file dialog and save the selected directory
        self.save_game_file_path = filedialog.askopenfilename(initialdir=initial_dir,
                                                              filetypes=(("Anno 1800 Savegame file", "*.a7s"),))
        self.selected_dir_label.set(os.path.basename(self.save_game_file_path))
        self.refresh_activated_dlcs()

    def refresh_activated_dlcs(self):
        self.selected_dlcs = []
        if self.save_game_file_path:
            f = open(self.save_game_file_path, "rb")

            self.save_game_reader = lib.SaveGameReader(bytearray(f.read()))
            print(f"Reading {self.save_game_file_path} ({self.save_game_reader.size} bytes) ")

            self.game_setup_reader = lib.GameSetupReader(self.save_game_reader.get_gamesetup_bytes())

            self.priorly_active_dlcs = self.game_setup_reader.get_activated_dlcs()

            self.game_setup_writer = lib.GameSetupWriter(self.game_setup_reader, self.game_setup_reader.initial_bytes)

            for (dlc, checkbox) in self.checkboxes:
                checkbox.config(state='active')
                checkbox.deselect()
                if self.priorly_active_dlcs and dlc in self.priorly_active_dlcs:
                    checkbox.select()
                    checkbox.config(state='disabled')

    def __init__(self):
        self.save_game_reader: lib.SaveGameReader | None = None
        self.game_setup_reader: lib.GameSetupReader | None = None
        self.game_setup_writer: lib.GameSetupWriter | None = None
        self.save_game_writer: lib.SaveGameWriter | None = None
        # DLCs selected by the checkboxes
        self.selected_dlcs: List[DLC] = []
        self.save_game_file_path: str | None = None
        self.priorly_active_dlcs: List[DLC] = []

        # Create the main window
        root = tk.Tk()
        root.title("Anno 1800 DLC Activator - ALPHA 1")
        root.resizable(False, False)

        # configure columns to fill available space
        for i in range(3):
            root.columnconfigure(i, weight=1)

        # configure rows to fill available space
        for i in range(4):
            root.rowconfigure(i, weight=1)

        current_row = 0
        version_disclaimer_label = tk.Label(root, text="Alpha version !")
        version_disclaimer_label.grid(row=current_row, column=0, columnspan=4)
        current_row+=1

        version_disclaimer_label = tk.Label(root, text="May contain bugs and might not work for your save game")
        version_disclaimer_label.grid(row=current_row, column=0, columnspan=4)
        current_row+=1

        open_file_button = tk.Button(root, text="Open Save File", command=self.open_file)
        open_file_button.grid(row=current_row, column=0, padx=16, pady=16, ipadx=16, columnspan=4)

        current_row += 1
        self.selected_dir_label = tk.StringVar()
        selected_dir_label = tk.Label(root, textvariable=self.selected_dir_label)
        selected_dir_label.grid(row=current_row, column=0, padx=16, pady=(0, 16), columnspan=4)

        current_row += 1
        self.checkboxes: List[Tuple[DLC, tk.Checkbutton]] = []
        for checkbox_gui_model in get_checkboxes_gui_models():
            cb = tk.Checkbutton(root, text=checkbox_gui_model.label,
                                command=lambda dlc=checkbox_gui_model.dlc: self.update_selected_dlcs(dlc))
            cb.grid(row=checkbox_gui_model.row + current_row, padx=16, column=checkbox_gui_model.column, sticky="w")
            self.checkboxes.append((checkbox_gui_model.dlc, cb))

        # Create an "Apply" button
        current_row += 5
        open_file_button = tk.Button(root, text="Apply", command=self.apply_changes)
        open_file_button.grid(row=current_row, column=0, padx=(32, 32), pady=(32, 16), ipadx=16, sticky="e",
                              columnspan=4)

        current_row += 1
        self.status_message = tk.StringVar()
        status_message_label = tk.Label(root, textvariable=self.status_message)
        status_message_label.grid(row=current_row, column=0, columnspan=4)

        root.mainloop()


if __name__ == '__main__':
    Gui()
