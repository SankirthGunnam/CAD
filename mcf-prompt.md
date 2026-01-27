Prompt: Implement Windows File Association for .mcf Files with SDTS.exe
Goal: Enable "Double-Click to Open" functionality for files with the .mcf extension so they automatically launch and load within SDTS.exe.

Technical Context: The project uses a custom binary format (.mcf) managed by 
DatabaseMgr
. The database files consist of a 1024-byte plain-text header followed by encrypted and compressed binary data.

Requirements:

Command-Line Parameter Handling:
Update the main entry point of the application (e.g., 
gui_app.py
 or the script that becomes SDTS.exe).
The application must check sys.argv for a file path.
If a path is provided (from Windows shell), the app should automatically trigger the DatabaseMgr.load() logic for that specific path instead of the default database.mcf.
Windows Registry Association:
Provide or implement a mechanism to register the file association in the Windows Registry (HKCU).
The association should link .mcf to a Program ID (e.g., SDTS.Document.1).
The shell\open\command must be set to: "C:\Path\To\SDTS.exe" "%1", where %1 is the placeholder for the file path provided by Windows Explorer.
UI Feedback:
Ensure that when the app launches via double-click, the UI (PyQt) correctly displays the metadata and contents of the specific file that was opened.
Reference Files:

database_mgr.py
: Contains the logic for parsing the 1KB text header and decrypting the data.
setup.nsi
: Already contains the registry "WriteRegStr" logic needed for the installer.
gui_app.py
: A template that demonstrates how to parse sys.argv[1] and load the corresponding data.
Task for the Agent: "Please integrate the sys.argv handling into the main production GUI and ensure that the installation process (or a standalone utility) executes the registry entries defined in the NSIS script to bind .mcf files to SDTS.exe."
