import os
import sys

def onMayaDroppedPythonFile(*args, **kwargs):
    """
    This function is automatically called by Maya when this file is dragged and dropped into the viewport.
    """
    import maya.cmds as cmds
    
    # Get the directory of this install file
    install_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Maya module paths can be found using the MAYA_APP_DIR environment variable
    maya_app_dir = os.environ.get('MAYA_APP_DIR')
    if not maya_app_dir:
        # Fallback for Windows if MAYA_APP_DIR is not set
        maya_app_dir = os.path.expanduser("~/Documents/maya")
        
    modules_dir = os.path.join(maya_app_dir, "modules")
    
    # Create the modules directory if it doesn't exist
    if not os.path.exists(modules_dir):
        os.makedirs(modules_dir)
        
    mod_file_path = os.path.join(modules_dir, "jimboRigging.mod")
    
    # Write the .mod file
    # Replace backslashes with forward slashes for Maya compatibility
    install_dir_clean = install_dir.replace("\\", "/")
    
    mod_content = "+ jimboRigging 1.0 {}\nMAYA_SHELF_PATH +:= shelves\n".format(install_dir_clean)
    
    try:
        with open(mod_file_path, "w") as f:
            f.write(mod_content)
        
        cmds.inViewMessage(
            amg="<hl>JimboRigging Installed</hl> successfully! Please restart Maya.",
            pos='midCenter',
            fade=True,
            fadeStayTime=3000
        )
        sys.stdout.write("JimboRigging successfully installed. Mod file written to: {}\n".format(mod_file_path))
    except Exception as e:
        cmds.error("Failed to write .mod file: {}".format(e))
