# anno1800-retroactive-dlc-activation
Description of how to retroactively activate one or more Anno 1800 DLCs in a savegame.
# Steps (new)
1. Install most recent version of Python 3 from https://www.python.org/downloads/
2. Download this repository, open command line into `v2`
3. Copy a Anno 1800 save game file you want additional DLCs activated into the `v2` directory. Save games can be found in `%userprofile%\Documents\Anno 1800\accounts`.
4. Edit the script `main.py` in line 27 and put in the file name of the save game file.
5. Edit the script `main.py` in line 30 and put in one or multiple DLCs that you want activated. See line 11-23 for possible values. The value must have `DLC.` as a prefix (as shown in the existing code). Save file.
6. Run `python main.py`
7. A file `gamesetup.a7s` is created in the same folder `v2`
8. Get the latest release of RDA Explorer here: https://github.com/lysannschlegel/RDAExplorer/releases and use it to load your save game from `v2`. Remove the existing gamesetup.a7s inside RDA Explorer (Right click - Delete). Add the generated `gamesetup.a7s` (Right click - Add files ...). Then save it (File - Save).
9. Copy the save game back to your Anno 1800 save games in `%userprofile%\Documents\Anno 1800\accounts`.
10. Launch Anno 1800 and pick the exact save game to load.


# Steps (old, more complicated, still working)
1. Get the latest release of RDA Explorer here: https://github.com/lysannschlegel/RDAExplorer/releases
   - Load the desired Anno 1800 save game into RDA Explorer (Save games are stored in `%userprofile%\Documents\Anno 1800\accounts`)
   - Export gamesetup.a7s to a local folder
2. Use a zlib library (e.g. Python zlib.decompress) to decompress `gamesetup.a7s` to ` gamesetup_zlib_decompressed`
3. Clone https://github.com/anno-mods/FileDBReader.git and open it in Visual Studio (the Community version is free).
    - Run FileDBReader with command line parameters in the working directory of ` gamesetup_zlib_decompressed`: `decompress -f gamesetup_zlib_decompressed`. You'll get a `gamesetup_zlib_decompressed.xml` as output.
4. Open the xml file and find the section `<ActiveDLCs>`. Add the desired DLCs to the list of DLCs and update the count accordingly.    
    Full list of DLCs as of Sept. 19th, 2022: ``` <ActiveDLCs>
      <count>0A00000000000000</count>
      <DLC>B8410600</DLC> <!--Sunken Treasures DLC-->
      <DLC>B9410600</DLC>
      <DLC>BA410600</DLC>
      <DLC>E3410600</DLC>
      <DLC>81610000</DLC>
      <DLC>CB410600</DLC>
      <DLC>D6410600</DLC>
      <DLC>D7410600</DLC>
      <DLC>E4410600</DLC>
      <DLC>E5410600</DLC>
      <DLC>82610000</DLC> <!--Reich der Lüfte-->
    </ActiveDLCs>```
5. Compress the xml file using FileDBReader: `compress -f gamesetup_zlib_decompressed.xml -o fdbr -c 2`
6. Use a zlib library (e.g. Python zlib.compress) to compress `gamesetup_zlib_decompressed.fdbr` to `gamesetup.a7s`
7. Use RDA Explorer to import the new `gamesetup.a7s` into your save game and save the file.
8. Run Anno 1800 and load that explicit save game.