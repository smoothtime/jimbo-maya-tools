# Jimbo Maya Tools

A collection of custom Python scripts and tools for Autodesk Maya, specifically geared towards rigging and other pipeline tasks.

## Directory Structure

* **`scripts/`**: Contains all the core Python scripts and modules.
  * **`jimboRigging/`**: Python module dedicated to custom rigging tools. 
* **`plug-ins/`**: Directory for Maya plugins (using the OpenMaya API, typically `.py` or `.mll`/`.so`).
* **`shelves/`**: Custom Maya shelf files (`.mel`) to load UI buttons for the tools.
* **`icons/`**: Custom icons used in Maya shelves or tool UIs.

## Installation

> **Important Note for School/Studio Computers:** 
> If you are working on a machine that wipes its local drives regularly (like the Downloads or Desktop folders), make sure to extract this toolset to a persistent network drive or external drive *before* installing. The `.mod` installation relies on the folder staying exactly where it was when you installed it!

There are three ways to install this toolset.

### Method 1: Drag-and-Drop Installer (Easiest)
1. Clone or download this repository and extract it anywhere on your computer.
2. Open Maya.
3. Drag and drop the `install.py` file from the repository folder directly into the Maya viewport.
4. Restart Maya. 

### Method 2: Manual Maya Module (.mod)
This method is non-destructive and doesn't require scattering files across your Maya preferences.
1. Clone or download this repository and place the `jimbo-maya-tools` folder anywhere on your computer.
2. Copy the `jimboRigging.mod` template file from this repository into your Maya modules directory:
   - **Windows:** `C:\Users\<YourUsername>\Documents\maya\modules\`
3. Add the following lines to the `jimboRigging.mod` file, replacing the path with the actual location where you saved the repository:
   ```text
   + jimboRigging 1.0 C:/Path/To/Your/jimbo-maya-tools
   MAYA_SHELF_PATH +:= shelves
   ```
4. Restart Maya.

### Method 3: Manual Installation
If you prefer to install files directly into your Maya user preferences:
1. Clone or download this repository.
2. Copy the `jimboRigging` folder from inside `scripts/` into your Maya user scripts directory:
   - **Windows:** `C:\Users\<YourUsername>\Documents\maya\scripts\`
3. Copy the shelf file from `shelves/` into your Maya user shelves directory:
   - **Windows:** `C:\Users\<YourUsername>\Documents\maya\<version>\prefs\shelves\`
4. Copy the icon files from `icons/` into your Maya user icons directory:
   - **Windows:** `C:\Users\<YourUsername>\Documents\maya\<version>\prefs\icons\`

## Usage

The shelf .mel script will give you a button to launch the Auto Control Rig UI.

If you want to add the command to an existing shelf the script is below

```python
import importlib
import jimboRigging.autoRig
importlib.reload(jimboRigging.autoRig)
from jimboRigging.autoRig import ControlRigUI

my_ui = ControlRigUI()
my_ui.show()
```

## Uninstallation

If you installed via **Method 1** or **Method 2 (Maya Module)**:
1. Navigate to your Maya modules directory (e.g., `C:\Users\<YourUsername>\Documents\maya\modules\`).
2. Delete the `jimboRigging.mod` file.
3. Restart Maya. 
4. You can now safely delete the `jimbo-maya-tools` folder from your hard drive.

If you installed via **Method 3 (Manual Installation)**:
You will need to manually delete the copied `jimboRigging` folder, the shelf `.mel` file, and the icon files from your local Maya preferences.
