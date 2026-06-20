#**ClipCrop**

ClipCrop is a high-performance, keyboard-driven image cropping utility designed for speed and productivity. It automatically handles large images, provides precise cropping handles, and uses a simplified workflow for capturing and saving conte

##Features

*Keyboard-First Workflow: Execute all actions without touching your mouse.
*Smart Saving: Files are automatically named with a YYYYMMDDHHMMSS timestamp.
*Single-Instance Enforcement: Prevents duplicate processes from running simultaneously.
*Clean UI: Automatically centers and scales images to fit your screen with perfect padding.

##Keyboard Shortcuts

###Action:          ###Shortcut:

Paste Image         Ctrl + V
Save Crop           Ctrl + S
Clear Canvas        Ctrl + X
Minimize App        Esc
Quit App            Ctrl + Shift + X

##Setup and Build

1. Dependencies
Ensure you have the required libraries installed by running this command in your terminal:

'pip install pillow'

2. Prepare Icon
Place your icon.ico file in the same directory as main.py.

3. Create Executable
Use PyInstaller to build the distributable by running this command in your terminal:

'pyinstaller --noconsole --onefile --icon=icon.ico --name=ClipCrop main.py'