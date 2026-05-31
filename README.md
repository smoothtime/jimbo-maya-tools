# Jimbo Maya Tools

A collection of custom Python scripts and tools for Autodesk Maya, specifically geared towards rigging and other pipeline tasks.

## Directory Structure

* **`scripts/`**: Contains all the core Python scripts and modules.
  * **`jimboRigging/`**: Python module dedicated to custom rigging tools. 
* **`plug-ins/`**: Directory for Maya plugins (using the OpenMaya API, typically `.py` or `.mll`/`.so`).
* **`shelves/`**: Custom Maya shelf files (`.mel`) to load UI buttons for the tools.
* **`icons/`**: Custom icons used in Maya shelves or tool UIs.

## Installation

1. Clone or download this repository.
2. Add the `scripts` folder to your Maya `PYTHONPATH`. You can do this in your `Maya.env` file or dynamically via Python inside Maya:

```python
import sys
sys.path.append(r"PATH_TO_YOUR_DIRECTORY/jimbo-maya-tools/scripts")
```

3. (Optional) If you have plugins or shelf files you want to use, ensure their respective paths are added to `MAYA_PLUG_IN_PATH` and `MAYA_SHELF_PATH`.

## Usage

To use the rigging tools in Maya's Script Editor (Python tab):

```python
import jimboRigging
# import specific rigging tools here
```
