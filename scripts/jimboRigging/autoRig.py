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
    
        # ----------------------------------------------------------------------
        # WINDOW SETUP
        # ----------------------------------------------------------------------
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

        # top level layout
        self.scroll_layout = cmds.scrollLayout(childResizable=True)
        self.chapter_layout = cmds.columnLayout(adjustableColumn=True)
        
        # ----------------------------------------------------------------------
        # CHAPTER 1: Bind and Bridge
        # ----------------------------------------------------------------------
        self.step1_frame = cmds.frameLayout(label="Step 1: Bind and Bridge", collapsable=True, collapse=False, marginWidth=5, marginHeight=5)
        self.connect_object_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 10))
        cmds.separator(height=10, style='none')

        # bind joint selection
        self.bind_joint_row = cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        
        self.bind_joint_text_field = cmds.textField(placeholderText="Bind joint hierarchy", height=24)
        
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.bind_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.bind_joint_text_field))

        # step out to bind row parent layout
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
        cmds.setParent('..')
        cmds.setParent('..')

        # ----------------------------------------------------------------------
        # CHAPTER 2: Spine and Hip
        # ----------------------------------------------------------------------
        self.step2_frame = cmds.frameLayout(label="Step 2: Spine and Hip", collapsable=True, collapse=True, marginWidth=5, marginHeight=5)
        self.spine_hip_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 10))
        cmds.separator(height=10, style='none')

        # COG Joint
        self.cog_joint_row = cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.cog_joint_text_field = cmds.textField(placeholderText="COG Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.cog_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.cog_joint_text_field))
        cmds.setParent('..')

        # Spine Base
        self.spine_base_row = cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.spine_base_text_field = cmds.textField(placeholderText="Spine Base Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.spine_base_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.spine_base_text_field))
        cmds.setParent('..')
        
        # Spine Tip
        self.spine_tip_row = cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.spine_tip_text_field = cmds.textField(placeholderText="Spine Tip Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.spine_tip_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.spine_tip_text_field))
        cmds.setParent('..')
        
        # Global Scale Node
        self.global_scale_row = cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.global_scale_text_field = cmds.textField(placeholderText="Global Scale Node", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadObject, self.global_scale_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.global_scale_text_field))
        cmds.setParent('..')

        cmds.separator(height=15, style='in')
        
        # main spine/hip actions
        self.spine_hip_action_layout = cmds.formLayout(numberOfDivisions=100)
        build_spine_hip_btn = cmds.button(label="Build Spine and Hip", height=35, command=self.buildSpineAndHip)
        
        cmds.formLayout(self.spine_hip_action_layout, edit=True,
            attachForm=[(build_spine_hip_btn, 'left', 0), (build_spine_hip_btn, 'top', 0), (build_spine_hip_btn, 'bottom', 0),
                        (build_spine_hip_btn, 'right', 0)]
        )
        cmds.setParent('..')
        cmds.setParent('..')
        cmds.setParent('..')

        # ----------------------------------------------------------------------
        # CHAPTER 3: FK Systems
        # ----------------------------------------------------------------------
        self.step3_frame = cmds.frameLayout(label="Step 3: FK Systems", collapsable=True, collapse=True, marginWidth=5, marginHeight=5)
        self.fk_system_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 10))
        cmds.separator(height=10, style='none')

        # fk system checkboxes
        self.fk_system_checkboxes = cmds.checkBoxGrp(
            numberOfCheckBoxes=3, 
            label='FK Systems: ', 
            labelArray3=['Spine', 'Legs', 'Arms'],
            valueArray3=[True, True, True]
        )

        cmds.separator(height=15, style='in')
        
        # main fk system actions
        self.fk_action_layout = cmds.formLayout(numberOfDivisions=100)
        create_fk_btn = cmds.button(label="Create FK Systems", height=35, command=self.createFKSystems)
        
        cmds.formLayout(self.fk_action_layout, edit=True,
            attachForm=[(create_fk_btn, 'left', 0), (create_fk_btn, 'top', 0), (create_fk_btn, 'bottom', 0),
                        (create_fk_btn, 'right', 0)]
        )
        cmds.setParent('..')
        cmds.setParent('..')
        cmds.setParent('..')
        

        # ----------------------------------------------------------------------
        # CHAPTER 4: Control Objects
        # ----------------------------------------------------------------------
        self.step4_frame = cmds.frameLayout(label="Step 4: Control Objects", collapsable=True, collapse=True, marginWidth=5, marginHeight=5)
        self.control_object_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 10))
        cmds.separator(height=10, style='none')

        # control object checkboxes
        self.control_object_checkboxes = cmds.checkBoxGrp(
            numberOfCheckBoxes=3, 
            label='Control Objects: ', 
            labelArray3=['Feet', 'Hands', 'Spine'],
            valueArray3=[True, True, True]
        )

        cmds.separator(height=15, style='in')
        
        # main control object actions
        self.control_action_layout = cmds.formLayout(numberOfDivisions=100)
        create_control_btn = cmds.button(label="Create Control Objects", height=35, command=self.createControlObjects)
        
        cmds.formLayout(self.control_action_layout, edit=True,
            attachForm=[(create_control_btn, 'left', 0), (create_control_btn, 'top', 0), (create_control_btn, 'bottom', 0),
                        (create_control_btn, 'right', 0)]
        )
        cmds.setParent('..')
        cmds.setParent('..')
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

    def loadObject(self, target_field, *args):
        selection = cmds.ls(selection=True)
        if selection:
            cmds.textField(target_field, edit=True, text=selection[0])
        else:
            cmds.warning("No objects selected")
            
    def clearSelection(self, target_field, *args):
        cmds.textField(target_field, edit=True, text="")

    def _renameHierarchy(self, hierarchy, old_suffix, new_suffix):
        last_renamed = None
        for node in hierarchy:
            if (cmds.nodeType(node) != "joint"):
                cmds.delete(node)
                continue
            node_short_name = node.split('|')[-1]
            # clean up digits on suffix
            clean_short_name = node_short_name.rstrip(string.digits)
            
            new_name = clean_short_name.replace(old_suffix, new_suffix)
            if new_suffix not in new_name:
                new_name = clean_short_name + new_suffix
                
            last_renamed = cmds.rename(node, new_name)
        return last_renamed

    def _groupOverAlign(self, ctrl, target):
        # Create the SDK group
        sdk_name = ctrl + "_SDK"
        sdk_grp = cmds.group(ctrl, name=sdk_name)
        
        # Create the outer zero offset group
        zero_name = ctrl + "_0"
        zero_grp = cmds.group(sdk_grp, name=zero_name)
        
        # Temporarily constrain to snap the group into place
        temp_constraint = cmds.parentConstraint(target, zero_grp, maintainOffset=False)
        cmds.delete(temp_constraint)
        
        return zero_grp, sdk_grp

    def _groupOverSnap(self, ctrl, target):
        # Create the SDK group
        sdk_name = ctrl + "_SDK"
        sdk_grp = cmds.group(ctrl, name=sdk_name)
        
        # Create the outer zero offset group
        zero_name = ctrl + "_0"
        zero_grp = cmds.group(sdk_grp, name=zero_name)
        
        # Temporarily point constrain to snap the group into place (position only)
        temp_constraint = cmds.pointConstraint(target, zero_grp, maintainOffset=False)
        cmds.delete(temp_constraint)
        
        return zero_grp, sdk_grp

    def _rotateCVs(self, ctrl, rotation=(0, 0, 0)):
        cmds.rotate(rotation[0], rotation[1], rotation[2], ctrl + '.cv[*]', relative=True, objectSpace=True)

    def _getPrimaryAxis(self, joint_node):
        # A joint's child translation is essentially a local vector pointing down the bone
        children = cmds.listRelatives(joint_node, children=True, type="joint")
        if children:
            target_node = children[0]
            tx = cmds.getAttr(target_node + ".translateX")
            ty = cmds.getAttr(target_node + ".translateY")
            tz = cmds.getAttr(target_node + ".translateZ")
        else:
            # If it's a tip joint, look at its own local vector relative to its parent
            tx = cmds.getAttr(joint_node + ".translateX")
            ty = cmds.getAttr(joint_node + ".translateY")
            tz = cmds.getAttr(joint_node + ".translateZ")
            
        abs_tx, abs_ty, abs_tz = abs(tx), abs(ty), abs(tz)
        max_val = max(abs_tx, abs_ty, abs_tz)
        
        if max_val == 0:
            return (1, 0, 0), 1.0 # default fallback length if joints are perfectly snapped
            
        # Return the normalized axis vector and the bone length (max_val)
        if max_val == abs_tx:
            return (1, 0, 0), max_val
        elif max_val == abs_ty:
            return (0, 1, 0), max_val
        else:
            return (0, 0, 1), max_val

    def _createSquareCurve(self, name, normal=(0, 1, 0), radius=1.0):
        r = radius
        if normal == (1, 0, 0) or normal == (-1, 0, 0):
            pts = [(0, -r, -r), (0, r, -r), (0, r, r), (0, -r, r), (0, -r, -r)]
        elif normal == (0, 0, 1) or normal == (0, 0, -1):
            pts = [(-r, -r, 0), (r, -r, 0), (r, r, 0), (-r, r, 0), (-r, -r, 0)]
        else: # Default to Y normal
            pts = [(-r, 0, -r), (r, 0, -r), (r, 0, r), (-r, 0, r), (-r, 0, -r)]
            
        # degree 1 creates a linear (straight edge) curve connecting the points
        return cmds.curve(name=name, degree=1, point=pts)

    def _createCubeCurve(self, name, radius=1.0):
        r = radius
        # 16-point path that traces all 12 edges of a cube without lifting the pen
        pts = [
            (r, r, r), (r, r, -r), (-r, r, -r), (-r, r, r), (r, r, r),          # Top face
            (r, -r, r), (r, -r, -r), (-r, -r, -r), (-r, -r, r), (r, -r, r),     # Bottom face
            (-r, -r, r), (-r, r, r), (-r, r, -r), (-r, -r, -r), (r, -r, -r), (r, r, -r) # Connecting pillars
        ]
        return cmds.curve(name=name, degree=1, point=pts)

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
        final_name = self._renameHierarchy(bridge_hierarchy, "_bindJNT", "_bridgeJNT")
        
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

    def buildSpineAndHip(self, *args):

        spine_base_joint = cmds.textField(self.spine_base_text_field, query=True, text=True)
        if (not spine_base_joint):
            cmds.error("No spine base joint specified")
            return

        spine_tip_joint = cmds.textField(self.spine_tip_text_field, query=True, text=True)
        if (not spine_tip_joint):
            cmds.error("No spine tip joint specified")
            return
        
        cog_joint = cmds.textField(self.cog_joint_text_field, query=True, text=True)
        if (not cog_joint):
            cmds.error("No COG joint specified")
            return
        
        global_scale_node = cmds.textField(self.global_scale_text_field, query=True, text=True)
        if (not global_scale_node):
            cmds.error("No global scale node specified")
            return

        cmds.undoInfo(openChunk=True)

        # Resolve UI inputs to absolute full paths BEFORE creating/duplicating any nodes.
        # This prevents newly duplicated nodes from stealing the short-name lookup.
        spine_base_joint = cmds.ls(spine_base_joint, long=True)[0]
        spine_tip_joint = cmds.ls(spine_tip_joint, long=True)[0]
        cog_joint = cmds.ls(cog_joint, long=True)[0]
        global_scale_node = cmds.ls(global_scale_node, long=True)[0]

        # ----------------------------------------------------------------------
        # 1. Duplicate out a section of the bridge spine for an IK joint chain
        # ----------------------------------------------------------------------
        dupe_joints = cmds.duplicate(spine_base_joint)
        if not dupe_joints:
            cmds.error("Failed to duplicate spine hierarchy.")
            cmds.undoInfo(closeChunk=True)
            return
        
        spine_IK_base_joint = dupe_joints[0]
        
        # Unparent the duplicated IK chain to prevent double transforms from the COG
        if cmds.listRelatives(spine_IK_base_joint, parent=True):
            spine_IK_base_joint = cmds.parent(spine_IK_base_joint, world=True)[0]
            
        spine_IK_base_joint = cmds.ls(spine_IK_base_joint, long=True)[0]

        # Find the duplicated tip using index matching
        base_long = cmds.ls(spine_base_joint, long=True)[0]
        tip_long = cmds.ls(spine_tip_joint, long=True)[0]

        orig_descendants = cmds.listRelatives(spine_base_joint, allDescendents=True, fullPath=True) or []
        dupe_descendants = cmds.listRelatives(spine_IK_base_joint, allDescendents=True, fullPath=True) or []

        ik_tip = None
        ik_tip_index = -1
        if base_long == tip_long:
            ik_tip = spine_IK_base_joint
        else:
            for i, (orig, dupe) in enumerate(zip(orig_descendants, dupe_descendants)):
                if orig == tip_long:
                    ik_tip = dupe
                    ik_tip_index = i
                    break

        if not ik_tip:
            print("--- DEBUG INFO ---")
            print("Looking for tip_long: {}".format(tip_long))
            print("Available orig_descendants:")
            for orig in orig_descendants:
                print("  - {}".format(orig))
            print("------------------")
            
            cmds.error("Could not find duplicated spine tip. Is the tip a descendant of the base?")
            cmds.undoInfo(closeChunk=True)
            return

        # Capture the relevant slice of bridge joints for Step 2
        if base_long == tip_long:
            bridge_hierarchy = []
        else:
            bridge_hierarchy = list(orig_descendants[ik_tip_index:])
        bridge_hierarchy.append(base_long)

        # Prune the excess hierarchy below the duplicated tip, children flag only returns immediate children
        tip_children = cmds.listRelatives(ik_tip, children=True, fullPath=True)
        if tip_children:
            cmds.delete(tip_children)

        # Now get the remaining hierarchy and rename it
        spine_IK_hierarchy = cmds.listRelatives(spine_IK_base_joint, allDescendents=True, fullPath=True) or []
        spine_IK_hierarchy.append(spine_IK_base_joint)

        spine_IK_base_joint = self._renameHierarchy(spine_IK_hierarchy, "_bridgeJNT", "_IK_JNT")

        # ----------------------------------------------------------------------
        # 2. Parent the relevant bridge joints to the IK chain
        # ----------------------------------------------------------------------
        spine_IK_base_joint = cmds.ls(spine_IK_base_joint, long=True)[0]
        spine_IK_hierarchy = cmds.listRelatives(spine_IK_base_joint, allDescendents=True, fullPath=True) or []
        spine_IK_hierarchy.append(spine_IK_base_joint)

        for ik_joint, bridge_joint in zip(spine_IK_hierarchy, bridge_hierarchy):
            cmds.parentConstraint(ik_joint, bridge_joint, maintainOffset=False)


        # ----------------------------------------------------------------------
        # 3. Install a spline IK handle
        # ----------------------------------------------------------------------
        spine_ik_tip = spine_IK_hierarchy[0]

        ik_nodes = cmds.ikHandle(startJoint=spine_IK_base_joint, 
                                 endEffector=spine_ik_tip, 
                                 solver='ikSplineSolver', 
                                 createCurve=True,
                                 parentCurve=False,
                                 simplifyCurve=False,
                                 name="spine_IKH")
                                 
        spine_ik_handle = ik_nodes[0]
        spine_ik_effector = cmds.rename(ik_nodes[1], "spine_EFF")
        spine_ik_curve = cmds.rename(ik_nodes[2], "spine_CUR")

        # ----------------------------------------------------------------------
        # 4. Create control joints at the spine tip and spine base
        # ----------------------------------------------------------------------
        spine_base_ctrl_jnt = cmds.duplicate(spine_IK_base_joint, parentOnly=True, name="spineBase_JNT")[0]
        if cmds.listRelatives(spine_base_ctrl_jnt, parent=True):
            spine_base_ctrl_jnt = cmds.parent(spine_base_ctrl_jnt, world=True)[0]
            
        spine_tip_ctrl_jnt = cmds.duplicate(spine_ik_tip, parentOnly=True, name="spineTip_JNT")[0]
        if cmds.listRelatives(spine_tip_ctrl_jnt, parent=True):
            spine_tip_ctrl_jnt = cmds.parent(spine_tip_ctrl_jnt, world=True)[0]

        # ----------------------------------------------------------------------
        # 5. Skin the curve of the IK spline to these control joints
        # ----------------------------------------------------------------------
        cmds.skinCluster(
            spine_base_ctrl_jnt, 
            spine_tip_ctrl_jnt, 
            spine_ik_curve, 
            toSelectedBones=True, 
            bindMethod=0, 
            skinMethod=0, 
            normalizeWeights=1, 
            weightDistribution=0, 
            maximumInfluences=2, 
            ignoreBindPose=True
        )

        # ----------------------------------------------------------------------
        # 6. Disable inherit transforms on the curve
        # ----------------------------------------------------------------------
        cmds.setAttr(spine_ik_curve + ".inheritsTransform", 0)

        # ----------------------------------------------------------------------
        # 7. Replace the parent constraint of the top of the spine from the ik joint to the control joint
        # ----------------------------------------------------------------------
        bridge_spine_tip = bridge_hierarchy[0]
        
        # Find and delete the parent constraint created in step 2
        existing_constraints = cmds.listRelatives(bridge_spine_tip, type="parentConstraint", fullPath=True) or []
        if existing_constraints:
            cmds.delete(existing_constraints)
            
        # Add the new constraint from the control joint to the bridge tip
        cmds.parentConstraint(spine_tip_ctrl_jnt, bridge_spine_tip, maintainOffset=False)

        # ----------------------------------------------------------------------
        # 8. Create controllers with Maya curves, group over align them to the right spot, parent constrain the control joints to the controllers
        # ----------------------------------------------------------------------
        # TODO: Investigate using OpenMaya MFnMesh.allIntersections raycasting against character mesh to dynamically calculate radius instead of bone length heuristic.

        # Spine Base Controller
        base_normal, base_length = self._getPrimaryAxis(spine_IK_base_joint)
        spine_base_ctrl = self._createSquareCurve(name="spineBase_CTRL", normal=base_normal, radius=(base_length * 2.0))
        self._groupOverAlign(spine_base_ctrl, spine_base_ctrl_jnt)
        cmds.parentConstraint(spine_base_ctrl, spine_base_ctrl_jnt, maintainOffset=False)

        # Spine Tip Controller
        tip_normal, tip_length = self._getPrimaryAxis(spine_ik_tip)
        spine_tip_ctrl = cmds.circle(name="spineTip_CTRL", normal=tip_normal, radius=(tip_length * 2.0))[0]
        self._groupOverAlign(spine_tip_ctrl, spine_tip_ctrl_jnt)
        cmds.parentConstraint(spine_tip_ctrl, spine_tip_ctrl_jnt, maintainOffset=False)

        # ----------------------------------------------------------------------
        # 9. Enable twist controls on the IK handle
        # ----------------------------------------------------------------------
        cmds.setAttr(spine_ik_handle + ".dTwistControlEnable", 1)
        
        # 4 corresponds to 'Object Rotation Up (Start/End)'
        cmds.setAttr(spine_ik_handle + ".dWorldUpType", 4)
        
        # Connect the world matrices of our controllers to the twist matrices
        cmds.connectAttr(spine_base_ctrl + ".worldMatrix[0]", spine_ik_handle + ".dWorldUpMatrix", force=True)
        cmds.connectAttr(spine_tip_ctrl + ".worldMatrix[0]", spine_ik_handle + ".dWorldUpMatrixEnd", force=True)

        # ----------------------------------------------------------------------
        # 10. Install a "chacha" controller for the hip (aligned to the base of the spine, but influences the cog joint)
        # ----------------------------------------------------------------------
        base_normal, base_length = self._getPrimaryAxis(spine_IK_base_joint)
        cog_normal, cog_length = self._getPrimaryAxis(cog_joint)
        
        chacha_ctrl = cmds.circle(name="chacha_CTRL", normal=base_normal, radius=(cog_length * 2.0))[0]
        self._groupOverAlign(chacha_ctrl, spine_base_ctrl_jnt)
        
        # Move CVs "down" the object space primary axis by the COG bone length
        move_x = base_normal[0] * -cog_length
        move_y = base_normal[1] * -cog_length
        move_z = base_normal[2] * -cog_length
        cmds.move(move_x, move_y, move_z, chacha_ctrl + '.cv[*]', relative=True, objectSpace=True)
        
        # Drive the COG bridge joint with offset
        cmds.parentConstraint(chacha_ctrl, cog_joint, maintainOffset=True)

        # ----------------------------------------------------------------------
        # 11. Make a body controller that is snapped to the cog joint, but axis aligned to the world
        # ----------------------------------------------------------------------
        body_ctrl = self._createCubeCurve(name="body_CTRL", radius=(cog_length * 1.5))
        
        # Use _groupOverSnap so the zero group only snaps position, staying aligned to the world
        self._groupOverSnap(body_ctrl, cog_joint)
        
        # Flatten the cube by scaling its CVs in world Y
        cmds.scale(1, 0.25, 1, body_ctrl + '.cv[*]', relative=True, worldSpace=True)
        
        # Move the CVs up in world Y by half the COG bone's length
        cmds.move(0, cog_length * 0.5, 0, body_ctrl + '.cv[*]', relative=True, worldSpace=True)

        # ----------------------------------------------------------------------
        # 12. Parenting organization
        # ----------------------------------------------------------------------
        # Parent the primary zero groups under the body controller to establish hierarchy
        cmds.parent(spine_base_ctrl + "_0", spine_tip_ctrl + "_0", body_ctrl)
        
        # Parent the chacha zero group under the spine base controller
        cmds.parent(chacha_ctrl + "_0", spine_base_ctrl)
        
        # ----------------------------------------------------------------------
        # 13. Set up the FK spine
        # ----------------------------------------------------------------------
        cmds.select(clear=True)
        
        # Calculate programmatic joint positions
        base_pos = cmds.xform(spine_IK_base_joint, query=True, translation=True, worldSpace=True)
        tip_pos = cmds.xform(spine_ik_tip, query=True, translation=True, worldSpace=True)
        
        # Find the midpoint of the second IK bone by averaging world pos of 2nd and 3rd joints
        forward_ik = spine_IK_hierarchy[::-1]
        pos2 = cmds.xform(forward_ik[1], query=True, translation=True, worldSpace=True)
        pos3 = cmds.xform(forward_ik[2], query=True, translation=True, worldSpace=True)
        mid_pos = [(p2 + p3) / 2.0 for p2, p3 in zip(pos2, pos3)]
        
        # Create the FK joints in world space
        fk_base_jnt = cmds.joint(name="spine1FK_JNT", position=base_pos)
        cmds.select(clear=True)
        fk_mid_jnt = cmds.joint(name="spine2FK_JNT", position=mid_pos)
        cmds.select(clear=True)
        fk_tip_jnt = cmds.joint(name="spine3FK_JNT", position=tip_pos)
        cmds.select(clear=True)
        
        # Orient the FK joints using Aim Constraints to match IK twist
        # Base FK: Aim at Mid FK, Up vector matches IK Base
        temp_aim = cmds.aimConstraint(fk_mid_jnt, fk_base_jnt, aimVector=(1, 0, 0), upVector=(0, 1, 0), 
                                      worldUpType="objectrotation", worldUpVector=(0, 1, 0), worldUpObject=spine_IK_base_joint)
        cmds.delete(temp_aim)
        cmds.makeIdentity(fk_base_jnt, apply=True, rotate=True)
        
        # Mid FK: Aim at Tip FK, Up vector matches IK median joint
        median_ik_jnt = spine_IK_hierarchy[len(spine_IK_hierarchy) // 2]
        temp_aim = cmds.aimConstraint(fk_tip_jnt, fk_mid_jnt, aimVector=(1, 0, 0), upVector=(0, 1, 0), 
                                      worldUpType="objectrotation", worldUpVector=(0, 1, 0), worldUpObject=median_ik_jnt)
        cmds.delete(temp_aim)
        cmds.makeIdentity(fk_mid_jnt, apply=True, rotate=True)
        
        # Tip FK: Copy orientation from IK Tip
        temp_orient = cmds.orientConstraint(spine_ik_tip, fk_tip_jnt)
        cmds.delete(temp_orient)
        cmds.makeIdentity(fk_tip_jnt, apply=True, rotate=True)
        
        # Parent the FK joints into a chain
        cmds.parent(fk_tip_jnt, fk_mid_jnt)
        cmds.parent(fk_mid_jnt, fk_base_jnt)
        
        # Create the Mid FK controller and constrain the Mid FK joint to it
        fk_mid_ctrl = cmds.circle(name="spineMid_FK_CTRL", normal=(1, 0, 0), radius=(base_length * 2.0))[0]
        self._groupOverAlign(fk_mid_ctrl, fk_mid_jnt)
        cmds.parentConstraint(fk_mid_ctrl, fk_mid_jnt, maintainOffset=True)
        
        # Build the hierarchy and drive the IK
        cmds.parentConstraint(body_ctrl, fk_base_jnt, maintainOffset=True)
        cmds.parent(fk_mid_ctrl + "_0", body_ctrl)
        
        # The FK tip drives the top of the IK Spline
        cmds.parentConstraint(fk_tip_jnt, spine_tip_ctrl + "_0", maintainOffset=True)
        
        # ----------------------------------------------------------------------
        # 14. Handle squash and stretch
        # ----------------------------------------------------------------------
        # Propagate scaleX down the IK chain (up to but not including tip)
        forward_ik = spine_IK_hierarchy[::-1]
        for i in range(len(forward_ik) - 2):
            cmds.connectAttr(forward_ik[i] + ".scaleX", forward_ik[i+1] + ".scaleX", force=True)
            
        # Create curveInfo node and connect the spline IK curve natively
        # Using cmds.arclen(ch=True) guarantees Maya hooks up the exact right evaluation plug
        curve_info = cmds.arclen(spine_ik_curve, ch=True)
        curve_info = cmds.rename(curve_info, "spine_curveInfo")
        
        # Query default arc length at bind pose
        default_length = cmds.getAttr(curve_info + ".arcLength")
        
        # Global Scale math: default_length * globalScale
        global_attr = global_scale_node + ".globalScale"
        
        global_length_md = cmds.createNode("multiplyDivide", name="spine_globalLength_MD")
        cmds.setAttr(global_length_md + ".operation", 1) # Multiply
        cmds.setAttr(global_length_md + ".input1X", default_length)
        
        if cmds.objExists(global_attr):
            cmds.connectAttr(global_attr, global_length_md + ".input2X", force=True)
        else:
            cmds.warning("Attribute '.globalScale' not found on '{}'. Using 1.0 fallback.".format(global_scale_node))
            cmds.setAttr(global_length_md + ".input2X", 1.0)
            
        # Ratio math: Current arcLength / Global Length
        ratio_md = cmds.createNode("multiplyDivide", name="spine_stretchRatio_MD")
        cmds.setAttr(ratio_md + ".operation", 2) # Divide
        cmds.connectAttr(curve_info + ".arcLength", ratio_md + ".input1X", force=True)
        cmds.connectAttr(global_length_md + ".outputX", ratio_md + ".input2X", force=True)
        
        # Drive the first IK joint's scaleX
        cmds.connectAttr(ratio_md + ".outputX", spine_IK_base_joint + ".scaleX", force=True)
        
        # ----------------------------------------------------------------------
        # 15. Outliner Cleanup & Organization
        # ----------------------------------------------------------------------
        # Lock and hide attributes on controllers to prevent accidental keyframes
        ctrls_to_clean = [spine_base_ctrl, spine_tip_ctrl, body_ctrl, chacha_ctrl, fk_mid_ctrl]
        for ctrl in ctrls_to_clean:
            for attr in ['sx', 'sy', 'sz', 'v']:
                cmds.setAttr(ctrl + "." + attr, lock=True, keyable=False, channelBox=False)
                
        # Additionally lock and hide translation on the chacha_CTRL
        for attr in ['tx', 'ty', 'tz']:
            cmds.setAttr(chacha_ctrl + "." + attr, lock=True, keyable=False, channelBox=False)
            
        # Create the local spine groups
        spine_jnt_grp = cmds.group(empty=True, name="spine_JNT_GRP")
        spine_ctrl_grp = cmds.group(empty=True, name="spine_CTRL_GRP")
        spine_misc_grp = cmds.group(empty=True, name="spine_MISC_GRP")
        
        # Sort the nodes into the local groups
        cmds.parent(spine_IK_base_joint, fk_base_jnt, spine_base_ctrl_jnt, spine_tip_ctrl_jnt, spine_jnt_grp)
        cmds.parent(body_ctrl + "_0", spine_ctrl_grp)
        cmds.parent(spine_ik_handle, spine_ik_curve, spine_misc_grp)
        
        # Integrate into Master Rig Hierarchy by searching for the short names
        master_jnt_grp = cmds.ls("JNT_GRP")
        if master_jnt_grp:
            cmds.parent(spine_jnt_grp, master_jnt_grp[0])
            
        master_ctrl_grp = cmds.ls("CTRL_GRP")
        if master_ctrl_grp:
            cmds.parent(spine_ctrl_grp, master_ctrl_grp[0])
            
        master_misc_grp = cmds.ls("MISC_GRP")
        if master_misc_grp:
            cmds.parent(spine_misc_grp, master_misc_grp[0])
            
        cmds.select(clear=True)
    
    def createFKSystems(self, *args):
        pass
    
    def createControlObjects(self, *args):
        pass

if __name__ == "__main__":
    ui = ControlRigUI()
    ui.show()
