import maya.cmds as cmds
import string
from functools import partial

class ControlRigUI:
    
    def __init__(self):
        self.window_name = "vfx356_rig_companion_window"
        self.window_title = "Auto Rig"
        self.min_width = 300
        self.min_height = 200
        
    def show(self):
    
        if (cmds.window(self.window_name, exists=True)):
            cmds.deleteUI(self.window_name)
        if (cmds.windowPref(self.window_name, exists=True)):
            cmds.windowPref(self.window_name, remove=True)
            
        # calculate fractional dimensions
        try:
            main_width = cmds.window("MayaWindow", query=True, width=True)
            main_height = cmds.window("MayaWindow", query=True, height=True)
            target_width = max(self.min_width, main_width * 0.2)
            target_height = max(self.min_height, main_height * 0.2)
        except RuntimeError:
            # fallback to defaults
            target_width, target_height = self.min_width, self.min_height
        
        self.window = cmds.window(self.window_name, title=self.window_title, widthHeight = (target_width, target_height), sizeable = True)        
        
        
        self.connect_object_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 10))
        cmds.separator(height=10, style='none')

        # bind joint selection
        self.bind_joint_row = cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        
        self.bind_joint_text_field = cmds.textField(placeholderText="Bind joint hierarchy", height=24)
        
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.bind_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.bind_joint_text_field))


        cmds.setParent('..')
        
        # bridge joint selection
        self.bridge_joint_row = cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])

        self.bridge_joint_text_field = cmds.textField(placeholderText="Bridge joint hierarchy", height=24)

        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.bridge_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.bridge_joint_text_field))

        # step out to bridge row parent layout
        cmds.setParent('..')

        # create bridge hierarchy optional setup
        cmds.button(label="Create Bridge Hierarchy", height=30, command=self.createBridgeHierarchy)
        
        cmds.separator(height=15, style='in')
        
        # attribute selection checkboxes
        self.attr_checkboxes = cmds.checkBoxGrp(
            numberOfCheckBoxes=3, 
            label='Connect Attributes: ', 
            labelArray3=['Translate', 'Rotate', 'Scale'],
            valueArray3=[True, True, True]
        )
        
        cmds.separator(height=15, style='in')
        
        # main connection actions
        self.action_layout = cmds.formLayout(numberOfDivisions=100)
        connectBtn = cmds.button(label="Connect Hierarchies", height=35, command=self.connectHierarchies)
        disconnectBtn = cmds.button(label="Disconnect Hierarchies", height=35, command=self.disconnectHierarchies)
        
        cmds.formLayout(self.action_layout, edit=True,
            attachForm=[(connectBtn, 'left', 0), (connectBtn, 'top', 0), (connectBtn, 'bottom', 0),
                        (disconnectBtn, 'right', 0), (disconnectBtn, 'top', 0), (disconnectBtn, 'bottom', 0)],
            attachPosition=[(connectBtn, 'right', 2, 50), (disconnectBtn, 'left', 2, 50)]
        )
        cmds.setParent('..')
        
        cmds.showWindow(self.window)
        
    def loadJointHierarchy(self, target_field, *args):
        # grab hierachy from selection
        selection = cmds.ls(selection=True, type="joint")
        
        if selection:
            # update text field
            cmds.textField(target_field, edit=True, text=selection[0])
        else:
            cmds.warning("No joints selected")
            
    def clearSelection(self, target_field, *args):
        cmds.textField(target_field, edit=True, text="")

    def createBridgeHierarchy(self, *args):
        existing_bridge_root = cmds.textField(self.bridge_joint_text_field, query=True, text=True)
        if (existing_bridge_root):
            cmds.error("A bridge hierarchy already exists. Please delete it before creating a new one.")
            return

        bind_root = cmds.textField(self.bind_joint_text_field, query=True, text=True)
        if not bind_root:
            cmds.error("No bind joint selected. Please load a bind joint hierarchy.")
            return

        cmds.undoInfo(openChunk=True)
        # duplicate bind hierarchy
        dupe_joints = cmds.duplicate(bind_root)
        if not dupe_joints:
            cmds.error("Failed to duplicate bind hierarchy.")
            cmds.undoInfo(closeChunk=True)
            return
        
        bridge_root = dupe_joints[0]
        bridge_root = cmds.ls(bridge_root, long=True)[0]

        bridge_hierarchy = cmds.listRelatives(bridge_root, allDescendents=True, fullPath=True) or []
        bridge_hierarchy.append(bridge_root)
        for node in bridge_hierarchy:
            if (cmds.nodeType(node) != "joint"):
                cmds.delete(node)
                continue
            node_short_name = node.split('|')[-1]
            # clean up digits on suffix
            clean_short_name = node_short_name.rstrip(string.digits)
            new_name = clean_short_name.replace("_bindJNT", "_bridgeJNT")
            final_name = cmds.rename(node, new_name)
        
        # update tool UI
        cmds.textField(self.bridge_joint_text_field, edit=True, text=final_name)

        cmds.undoInfo(closeChunk=True)
        
    def connectHierarchies(self, *args):
        self._modifyConnections(connect=True)
        
        
    def disconnectHierarchies(self, *args):
        self._modifyConnections(connect=False)

    def _modifyConnections(self, connect=True):
        bind_root = cmds.textField(self.bind_joint_text_field, query=True, text=True)
        bridge_root = cmds.textField(self.bridge_joint_text_field, query=True, text=True)

        if (not (bind_root and bridge_root)):
            cmds.error("Need both a bind joint hierarchy and a bridge joint hierarchy to connect")
            return
        
        connect_translate = cmds.checkBoxGrp(self.attr_checkboxes, query=True, value1=True)
        connect_rotate = cmds.checkBoxGrp(self.attr_checkboxes, query=True, value2=True)
        connect_scale = cmds.checkBoxGrp(self.attr_checkboxes, query=True, value3=True)

        active_attributes = []
        if connect_translate: active_attributes.append(".translate")
        if connect_rotate: active_attributes.append(".rotate")
        if connect_scale: active_attributes.append(".scale")

        if not active_attributes:
            cmds.error("No attributes selected to connect")
            return
        
        bind_joints = cmds.listRelatives(bind_root, allDescendents=True, fullPath=True, type='joint') or []
        bind_joints.append(cmds.ls(bind_root, long=True)[0])
        bridge_joints = cmds.listRelatives(bridge_root, allDescendents=True, fullPath=True, type='joint') or []
        bridge_joints.append(cmds.ls(bridge_root, long=True)[0])

        if len(bind_joints) != len(bridge_joints):
            cmds.error("Bind and bridge joint hierarchies must have the same number of joints")
            return
        
        cmds.undoInfo(openChunk=True)
        for bridge_joint, bind_joint in zip(bridge_joints, bind_joints):
            for attribute in active_attributes:
                src = bridge_joint + attribute
                dst = bind_joint + attribute
                if connect:
                    cmds.connectAttr(src, dst, force=True)
                else:
                    if (cmds.isConnected(src, dst)):
                        cmds.disconnectAttr(src, dst)
        cmds.undoInfo(closeChunk=True)


if __name__ == "__main__":
    ui = ControlRigUI()
    ui.show()
