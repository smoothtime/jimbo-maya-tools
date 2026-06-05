import maya.cmds as cmds
import string
from functools import partial
import math
import maya.api.OpenMaya as om
import traceback

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
        # CHAPTER 0: Rig Structure
        # ----------------------------------------------------------------------
        self.step0_frame = cmds.frameLayout(label="Step 0: Rig Structure", collapsable=True, collapse=False, marginWidth=5, marginHeight=5)
        self.rig_structure_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 10))
        cmds.separator(height=10, style='none')

        # bind skeleton selection
        self.bind_skeleton_row = cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.bind_skeleton_text_field = cmds.textField(placeholderText="Bind skeleton root", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.bind_skeleton_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.bind_skeleton_text_field))
        cmds.setParent('..')
        
        cmds.separator(height=15, style='in')
        
        # main structure actions
        self.structure_action_layout = cmds.formLayout(numberOfDivisions=100)
        build_structure_btn = cmds.button(label="Build Rig Structure", height=35, command=self.buildRigStructure)
        
        cmds.formLayout(self.structure_action_layout, edit=True,
            attachForm=[(build_structure_btn, 'left', 0), (build_structure_btn, 'top', 0), (build_structure_btn, 'bottom', 0),
                        (build_structure_btn, 'right', 0)]
        )
        cmds.setParent('..')
        cmds.setParent('..')
        cmds.setParent('..')

        # ----------------------------------------------------------------------
        # CHAPTER 1: Bind and Bridge
        # ----------------------------------------------------------------------
        self.step1_frame = cmds.frameLayout(label="Step 1: Bind and Bridge", collapsable=True, collapse=True, marginWidth=5, marginHeight=5)
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

        # Analyze Rig Instruction and Button
        cmds.text(label="Select the 'all_GRP' in Maya and click 'Analyze Rig'\nto auto-populate fields from a standard skeleton.", align="left", font="obliqueLabelFont")
        cmds.button(label="Analyze Rig", height=30, backgroundColor=(0.3, 0.4, 0.5), command=self.analyzeRig)
        cmds.separator(height=10, style='in')

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
        # CHAPTER 3: Neck and Head
        # ----------------------------------------------------------------------
        self.step3_frame = cmds.frameLayout(label="Step 3: Neck and Head", collapsable=True, collapse=True, marginWidth=5, marginHeight=5)
        self.neck_head_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 10))
        cmds.separator(height=10, style='none')

        # Neck Joint
        self.neck_joint_row = cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.neck_joint_text_field = cmds.textField(placeholderText="Neck Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.neck_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.neck_joint_text_field))
        cmds.setParent('..')

        # Head Joint
        self.head_joint_row = cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.head_joint_text_field = cmds.textField(placeholderText="Head Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.head_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.head_joint_text_field))
        cmds.setParent('..')

        # Spine Tip Joint (for Neck hookup)
        self.neck_spine_tip_row = cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.neck_spine_tip_text_field = cmds.textField(placeholderText="Spine Tip Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.neck_spine_tip_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.neck_spine_tip_text_field))
        cmds.setParent('..')

        cmds.separator(height=15, style='in')
        
        # main neck/head actions
        self.neck_head_action_layout = cmds.formLayout(numberOfDivisions=100)
        build_neck_head_btn = cmds.button(label="Build Neck and Head", height=35, command=self.buildNeckAndHead)
        
        cmds.formLayout(self.neck_head_action_layout, edit=True,
            attachForm=[(build_neck_head_btn, 'left', 0), (build_neck_head_btn, 'top', 0), (build_neck_head_btn, 'bottom', 0),
                        (build_neck_head_btn, 'right', 0)]
        )
        cmds.setParent('..')
        cmds.setParent('..')
        cmds.setParent('..')
        

        # ----------------------------------------------------------------------
        # CHAPTER 4: Legs
        # ----------------------------------------------------------------------
        self.step4_frame = cmds.frameLayout(label="Step 4: Legs", collapsable=True, collapse=True, marginWidth=5, marginHeight=5)
        self.legs_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 10))
        cmds.separator(height=10, style='none')

        # Analyze Rig Button
        cmds.button(label="Analyze Rig", height=30, backgroundColor=(0.3, 0.4, 0.5), command=self.analyzeRig)
        cmds.separator(height=10, style='none')

        # Hip Control
        self.hip_ctrl_row = cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.hip_ctrl_text_field = cmds.textField(placeholderText="Hip Control (Chacha)", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.hip_ctrl_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.hip_ctrl_text_field))
        cmds.setParent('..')

        # Left Thigh Joint
        self.l_thigh_joint_row = cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.l_thigh_joint_text_field = cmds.textField(placeholderText="Left Thigh Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.l_thigh_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.l_thigh_joint_text_field))
        cmds.setParent('..')

        # Left Ankle Joint
        self.l_ankle_joint_row = cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.l_ankle_joint_text_field = cmds.textField(placeholderText="Left Ankle Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.l_ankle_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.l_ankle_joint_text_field))
        cmds.setParent('..')

        # Left Ball Joint
        self.l_ball_joint_row = cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.l_ball_joint_text_field = cmds.textField(placeholderText="Left Ball Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.l_ball_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.l_ball_joint_text_field))
        cmds.setParent('..')

        # Left Toe Tip Joint
        self.l_toe_joint_row = cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.l_toe_joint_text_field = cmds.textField(placeholderText="Left Toe Tip Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.l_toe_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.l_toe_joint_text_field))
        cmds.setParent('..')

        cmds.separator(height=15, style='in')
        
        # main legs actions
        self.legs_action_layout = cmds.formLayout(numberOfDivisions=100)
        build_legs_btn = cmds.button(label="Build Legs", height=35, command=self.buildLegs)
        
        cmds.formLayout(self.legs_action_layout, edit=True,
            attachForm=[(build_legs_btn, 'left', 0), (build_legs_btn, 'top', 0), (build_legs_btn, 'bottom', 0),
                        (build_legs_btn, 'right', 0)]
        )
        cmds.setParent('..')
        cmds.setParent('..')
        cmds.setParent('..')

        # ----------------------------------------------------------------------
        # CHAPTER 5: Control Objects
        # ----------------------------------------------------------------------
        self.step5_frame = cmds.frameLayout(label="Step 5: Leg Stretch", collapsable=True, collapse=True, marginWidth=5, marginHeight=5)
        
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(200, 50, 50), adjustableColumn=1)
        self.stretch_top_loc_field = cmds.textField(placeholderText="Top Locator", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadObject, self.stretch_top_loc_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.stretch_top_loc_field))
        cmds.setParent('..')
        
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(200, 50, 50), adjustableColumn=1)
        self.stretch_bot_loc_field = cmds.textField(placeholderText="Bottom Locator", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadObject, self.stretch_bot_loc_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.stretch_bot_loc_field))
        cmds.setParent('..')
        
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(200, 50, 50), adjustableColumn=1)
        self.stretch_dist_field = cmds.textField(placeholderText="Distance Node", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadObject, self.stretch_dist_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.stretch_dist_field))
        cmds.setParent('..')
        
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(200, 50, 50), adjustableColumn=1)
        self.stretch_foot_ctrl_field = cmds.textField(placeholderText="Foot Controller", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadObject, self.stretch_foot_ctrl_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.stretch_foot_ctrl_field))
        cmds.setParent('..')
        
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(200, 50, 50), adjustableColumn=1)
        self.stretch_thigh_ik_field = cmds.textField(placeholderText="IK Thigh Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadObject, self.stretch_thigh_ik_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.stretch_thigh_ik_field))
        cmds.setParent('..')
        
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(200, 50, 50), adjustableColumn=1)
        self.stretch_global_scale_field = cmds.textField(placeholderText="Global Scale Node", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadObject, self.stretch_global_scale_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.stretch_global_scale_field))
        cmds.setParent('..')
        
        cmds.text(label="\n*** IMPORTANT ***\nPlace the foot controller at the maximum leg extent BEFORE recording.\n", wordWrap=True, align="center", font="boldLabelFont")
        cmds.button(label="Record Max Leg Extent", height=40, backgroundColor=(0.2, 0.6, 0.3), command=self.programLegStretch)
        cmds.setParent('..')

        # CHAPTER 6: Foot Controls
        cmds.separator(height=10, style='none')
        
        self.step6_frame = cmds.frameLayout(label="Step 6: Foot Controls", collapsable=True, collapse=True, marginWidth=5, marginHeight=5)
        
        cmds.text(label="\nClick 'Generate Pivot Locators' to spawn templates. Move them to perfectly border your geometry, then hit 'Build Foot Controls'.\n", wordWrap=True, align="center")
        
        cmds.button(label="Generate Pivot Locators", height=35, command=self.generateFootPivotLocators)
        cmds.button(label="Scan For Locators", height=30, command=self.scanFootPivotLocators)
        cmds.separator(height=10, style='none')
        
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(200, 50, 50), adjustableColumn=1)
        self.heel_loc_field = cmds.textField(placeholderText="Heel Locator", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadObject, self.heel_loc_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.heel_loc_field))
        cmds.setParent('..')
        
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(200, 50, 50), adjustableColumn=1)
        self.toe_loc_field = cmds.textField(placeholderText="Toe Locator", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadObject, self.toe_loc_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.toe_loc_field))
        cmds.setParent('..')
        
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(200, 50, 50), adjustableColumn=1)
        self.ankle_out_loc_field = cmds.textField(placeholderText="Ankle Out Locator", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadObject, self.ankle_out_loc_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.ankle_out_loc_field))
        cmds.setParent('..')
        
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(200, 50, 50), adjustableColumn=1)
        self.ankle_in_loc_field = cmds.textField(placeholderText="Ankle In Locator", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadObject, self.ankle_in_loc_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.ankle_in_loc_field))
        cmds.setParent('..')
        
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(200, 50, 50), adjustableColumn=1)
        self.ball_loc_field = cmds.textField(placeholderText="Ball Joint Locator", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadObject, self.ball_loc_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.ball_loc_field))
        cmds.setParent('..')
        
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(200, 50, 50), adjustableColumn=1)
        self.ball_floor_loc_field = cmds.textField(placeholderText="Ball Floor Locator", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadObject, self.ball_floor_loc_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.ball_floor_loc_field))
        cmds.setParent('..')
        
        cmds.separator(height=15, style='in')
        
        cmds.button(label="Build Foot Controls", height=40, backgroundColor=(0.2, 0.6, 0.3), command=self.buildFootControls)
        
        cmds.setParent('..')
        cmds.setParent('..')
        cmds.setParent('..')

        cmds.showWindow(self.window)

    def analyzeRig(self, *args):
        selection = cmds.ls(selection=True)
        if not selection:
            cmds.warning("Please select the 'all_GRP' node to analyze the rig.")
            return
            
        all_grp = selection[0]
        if all_grp.split('|')[-1] != "all_GRP":
            cmds.warning("Selected node is not 'all_GRP'. Please select the 'all_GRP' node.")
            return
            
        descendants = cmds.listRelatives(all_grp, allDescendents=True, fullPath=True) or []
        
        cog = None
        spine_base = None
        spine_tip = None
        global_scale = None
        neck = None
        head = None
        l_thigh = None
        l_ankle = None
        l_ball = None
        l_toe = None
        hip_ctrl = None
        
        for node in descendants:
            short_name = node.split('|')[-1]
            if short_name == "COG_bridgeJNT" and not cog:
                cog = node
            elif short_name == "spine1_bridgeJNT" and not spine_base:
                spine_base = node
            elif short_name == "chest_bridgeJNT" and not spine_tip:
                spine_tip = node
            elif short_name == "neck_bridgeJNT" and not neck:
                neck = node
            elif short_name == "head_bridgeJNT" and not head:
                head = node
            elif short_name == "all_CTRL" and not global_scale:
                global_scale = node
            elif short_name == "L_thigh_bridgeJNT" and not l_thigh:
                l_thigh = node
            elif short_name == "L_ankle_bridgeJNT" and not l_ankle:
                l_ankle = node
            elif short_name == "L_ball_bridgeJNT" and not l_ball:
                l_ball = node
            elif short_name == "L_toeTip_bridgeJNT" and not l_toe:
                l_toe = node
            elif short_name == "chacha_CTRL" and not hip_ctrl:
                hip_ctrl = node
                
        populated = []
        if cog:
            cmds.textField(self.cog_joint_text_field, edit=True, text=cog)
            populated.append("COG")
        if spine_base:
            cmds.textField(self.spine_base_text_field, edit=True, text=spine_base)
            populated.append("Spine Base")
        if spine_tip:
            cmds.textField(self.spine_tip_text_field, edit=True, text=spine_tip)
            cmds.textField(self.neck_spine_tip_text_field, edit=True, text=spine_tip)
            populated.append("Spine Tip")
        if neck:
            cmds.textField(self.neck_joint_text_field, edit=True, text=neck)
            populated.append("Neck")
        if head:
            cmds.textField(self.head_joint_text_field, edit=True, text=head)
            populated.append("Head")
        if global_scale:
            cmds.textField(self.global_scale_text_field, edit=True, text=global_scale)
            cmds.textField(self.stretch_global_scale_field, edit=True, text=global_scale)
            populated.append("Global Scale")
        if l_thigh:
            cmds.textField(self.l_thigh_joint_text_field, edit=True, text=l_thigh)
            populated.append("L Thigh")
        if l_ankle:
            cmds.textField(self.l_ankle_joint_text_field, edit=True, text=l_ankle)
            populated.append("L Ankle")
        if l_ball:
            cmds.textField(self.l_ball_joint_text_field, edit=True, text=l_ball)
            populated.append("L Ball")
        if l_toe:
            cmds.textField(self.l_toe_joint_text_field, edit=True, text=l_toe)
            populated.append("L Toe Tip")
        if hip_ctrl:
            cmds.textField(self.hip_ctrl_text_field, edit=True, text=hip_ctrl)
            populated.append("Hip Control")
            
        if populated:
            cmds.inViewMessage(amg='<hl>Rig Analyzed</hl>: Found and populated {}.'.format(", ".join(populated)), pos='midCenter', fade=True)
        else:
            cmds.warning("Analyze Rig: Could not find any standard named joints/controls in 'all_GRP'.")
        
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

    def _orientCVsUpright(self, ctrl, align_target, aim_axis=(1,0,0)):
        loc_base = cmds.spaceLocator()[0]
        loc_aim = cmds.spaceLocator()[0]
        
        temp_const1 = cmds.parentConstraint(align_target, loc_base, maintainOffset=False)
        temp_const2 = cmds.parentConstraint(align_target, loc_aim, maintainOffset=False)
        cmds.delete(temp_const1)
        cmds.delete(temp_const2)
        
        cmds.parent(loc_aim, align_target)
        cmds.move(aim_axis[0]*10, aim_axis[1]*10, aim_axis[2]*10, loc_aim, relative=True, objectSpace=True)
        loc_aim = cmds.parent(loc_aim, world=True)[0]
        
        base_pos = cmds.xform(loc_base, query=True, translation=True, worldSpace=True)
        aim_pos = cmds.xform(loc_aim, query=True, translation=True, worldSpace=True)
        
        dist_xz = math.sqrt((aim_pos[0] - base_pos[0])**2 + (aim_pos[2] - base_pos[2])**2)
        
        if dist_xz > 0.001:
            cmds.xform(loc_aim, translation=(aim_pos[0], base_pos[1], aim_pos[2]), worldSpace=True)
            
            loc_target = cmds.spaceLocator()[0]
            temp_const3 = cmds.pointConstraint(loc_base, loc_target, maintainOffset=False)
            cmds.delete(temp_const3)
            
            temp_const4 = cmds.aimConstraint(loc_aim, loc_target, aimVector=aim_axis, upVector=(0,1,0), worldUpType="scene", maintainOffset=False)
            cmds.delete(temp_const4)
            
            # By parenting the upright loc_target to the target joint, we get the corrective rotation needed to straighten the controller
            loc_target = cmds.parent(loc_target, align_target)[0]
            corrective_rot = cmds.getAttr(loc_target + ".rotate")[0]
            
            self._rotateCVs(ctrl, corrective_rot)
            cmds.delete(loc_target)
        else:
            cmds.warning("Cannot orient CVs upright: target is pointing perfectly vertically.")
            
        cmds.delete([loc_base, loc_aim])

    def _getPrimaryAxis(self, joint_node, target_child=None):
        # A joint's child translation is essentially a local vector pointing down the bone
        if target_child and cmds.objExists(target_child):
            target_node = target_child
        else:
            children = cmds.listRelatives(joint_node, children=True, type="joint")
            if children:
                target_node = children[0]
            else:
                target_node = None
                
        if target_node:
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
    def _createDiamondCurve(self, name, radius=1.0):
        s1 = self._createSquareCurve(name + "_s1", normal=(1,0,0), radius=radius)
        s2 = self._createSquareCurve(name + "_s2", normal=(0,1,0), radius=radius)
        s3 = self._createSquareCurve(name + "_s3", normal=(0,0,1), radius=radius)
        
        cmds.xform(s1, rotation=(45, 0, 0), objectSpace=True)
        cmds.xform(s2, rotation=(0, 45, 0), objectSpace=True)
        cmds.xform(s3, rotation=(0, 0, 45), objectSpace=True)
        
        cmds.makeIdentity([s1, s2, s3], apply=True, t=1, r=1, s=1, n=0)
        
        shapes = cmds.listRelatives([s2, s3], shapes=True)
        cmds.parent(shapes, s1, shape=True, relative=True)
        cmds.delete(s2, s3)
        
        return cmds.rename(s1, name)

    def _createCubeCurve(self, name, radius=1.0):
        r = radius
        # 16-point path that traces all 12 edges of a cube without lifting the pen
        pts = [
            (r, r, r), (r, r, -r), (-r, r, -r), (-r, r, r), (r, r, r),          # Top face
            (r, -r, r), (r, -r, -r), (-r, -r, -r), (-r, -r, r), (r, -r, r),     # Bottom face
            (-r, -r, r), (-r, r, r), (-r, r, -r), (-r, -r, -r), (r, -r, -r), (r, r, -r) # Connecting pillars
        ]
        return cmds.curve(name=name, degree=1, point=pts)

    def _createPlusCurve(self, name, normal=(0, 1, 0), radius=1.0):
        r = radius
        t = radius * 0.333
        
        if normal == (1, 0, 0) or normal == (-1, 0, 0):
            pts = [
                (0, -r, -t), (0, -t, -t), (0, -t, -r), (0, t, -r),
                (0, t, -t), (0, r, -t), (0, r, t), (0, t, t),
                (0, t, r), (0, -t, r), (0, -t, t), (0, -r, t),
                (0, -r, -t)
            ]
        elif normal == (0, 0, 1) or normal == (0, 0, -1):
            pts = [
                (-t, -r, 0), (-t, -t, 0), (-r, -t, 0), (-r, t, 0),
                (-t, t, 0), (-t, r, 0), (t, r, 0), (t, t, 0),
                (r, t, 0), (r, -t, 0), (t, -t, 0), (t, -r, 0),
                (-t, -r, 0)
            ]
        else: # Default Y normal
            pts = [
                (-t, 0, -r), (-t, 0, -t), (-r, 0, -t), (-r, 0, t),
                (-t, 0, t), (-t, 0, r), (t, 0, r), (t, 0, t),
                (r, 0, t), (r, 0, -t), (t, 0, -t), (t, 0, -r),
                (-t, 0, -r)
            ]
            
        return cmds.curve(name=name, degree=1, point=pts)

    def buildRigStructure(self, *args):
        skeleton_root = cmds.textField(self.bind_skeleton_text_field, query=True, text=True)
        if not skeleton_root:
            cmds.error("No bind skeleton selected.")
            return
            
        if not cmds.objExists(skeleton_root):
            cmds.error("Selected skeleton does not exist.")
            return

        cmds.undoInfo(openChunk=True)
        try:
            # Helper to ensure parenting
            def ensure_parent(child, parent):
                current = cmds.listRelatives(child, parent=True)
                if not current or current[0].split('|')[-1] != parent:
                    cmds.parent(child, parent)

            # Check structure from root downwards
            if not cmds.objExists("all_GRP"):
                cmds.group(empty=True, name="all_GRP")
                    
            if not cmds.objExists("GEO_GRP"):
                cmds.group(empty=True, name="GEO_GRP")
            ensure_parent("GEO_GRP", "all_GRP")
            
            if not cmds.objExists("all_CTRL"):
                cmds.circle(constructionHistory=False, name="all_CTRL", normal=(0, 1, 0), radius=10.0)
            ensure_parent("all_CTRL", "all_GRP")
                
            if not cmds.attributeQuery("globalScale", node="all_CTRL", exists=True):
                cmds.addAttr("all_CTRL", longName="globalScale", attributeType="float", defaultValue=1.0, keyable=True)
                
            # Connect globalScale to all_CTRL's scale so it drives the physical transform
            for attr in ['scaleX', 'scaleY', 'scaleZ']:
                # Unlock just in case it was locked by previous runs
                cmds.setAttr("all_CTRL." + attr, lock=False)
                if not cmds.isConnected("all_CTRL.globalScale", "all_CTRL." + attr):
                    cmds.connectAttr("all_CTRL.globalScale", "all_CTRL." + attr, force=True)
                
            if not cmds.objExists("offset_CTRL"):
                cmds.circle(constructionHistory=False, name="offset_CTRL", normal=(0, 1, 0), radius=8.0)
            ensure_parent("offset_CTRL", "all_CTRL")
                
            if not cmds.objExists("JNT_GRP"):
                cmds.group(empty=True, name="JNT_GRP")
            ensure_parent("JNT_GRP", "offset_CTRL")
                
            if not cmds.objExists("bindJNT_GRP"):
                cmds.group(empty=True, name="bindJNT_GRP")
            ensure_parent("bindJNT_GRP", "JNT_GRP")
                
            if not cmds.objExists("CTRL_GRP"):
                cmds.group(empty=True, name="CTRL_GRP")
            ensure_parent("CTRL_GRP", "offset_CTRL")
                
            if not cmds.objExists("settings_CTRL_GRP"):
                cmds.group(empty=True, name="settings_CTRL_GRP")
            ensure_parent("settings_CTRL_GRP", "CTRL_GRP")
            
            # TODO: the settings control is useless atm. Need to add the bendy control toggle and the render/proxy geometry toggle later if we care
            if not cmds.objExists("setting_CTRL"):
                setting_ctrl = cmds.circle(constructionHistory=False, name="setting_CTRL", normal=(0, 1, 0), radius=2.0)[0]
                cmds.move(15, 0, 0, setting_ctrl)
                ensure_parent(setting_ctrl, "settings_CTRL_GRP")
            else:
                ensure_parent("setting_CTRL", "settings_CTRL_GRP")
                
            if not cmds.objExists("MISC_GRP"):
                cmds.group(empty=True, name="MISC_GRP")
            ensure_parent("MISC_GRP", "offset_CTRL")
                
            # Finally, parent the skeleton to bindJNT_GRP if it's not already
            ensure_parent(skeleton_root, "bindJNT_GRP")
            
            # Lock and hide attributes
            for ctrl in ["all_CTRL", "offset_CTRL", "setting_CTRL"]:
                if cmds.objExists(ctrl):
                    for attr in ['v', 'sx', 'sy', 'sz']:
                        cmds.setAttr(ctrl + "." + attr, lock=True, keyable=False, channelBox=False)
                        
            if cmds.objExists("setting_CTRL"):
                for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
                    cmds.setAttr("setting_CTRL." + attr, lock=True, keyable=False, channelBox=False)
            
        except Exception as e:
            full_traceback = traceback.format_exc()
            cmds.error(f"Error building rig structure: {e}\n\nFull Traceback:\n{full_traceback}")
        finally:
            cmds.undoInfo(closeChunk=True)

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
        
        # move bridge skeleton to bridgeJNT_GRP
        if not cmds.objExists("bridgeJNT_GRP"):
            if cmds.objExists("JNT_GRP"):
                cmds.group(empty=True, name="bridgeJNT_GRP", parent="JNT_GRP")
            else:
                cmds.group(empty=True, name="bridgeJNT_GRP")
                
        current_parent = cmds.listRelatives(final_name, parent=True)
        if not current_parent or current_parent[0].split('|')[-1] != "bridgeJNT_GRP":
            cmds.parent(final_name, "bridgeJNT_GRP")

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
        spine_tip_ctrl = cmds.circle(constructionHistory=False, name="spineTip_CTRL", normal=tip_normal, radius=(tip_length * 2.0))[0]
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
        
        chacha_ctrl = cmds.circle(constructionHistory=False, name="chacha_CTRL", normal=base_normal, radius=(cog_length * 2.0))[0]
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
        
        # TODO consider finding a place in the IK chain that is about halfway along its length. Also maybe have >1 FK joints for long enough spines
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
        fk_mid_ctrl = cmds.circle(constructionHistory=False, name="spineMid_FK_CTRL", normal=(1, 0, 0), radius=(base_length * 2.0))[0]
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
        
        # Drive the first spine IK joint's scaleX
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
            
        # Auto-populate Step 4's Hip Control if it exists
        if cmds.objExists(chacha_ctrl):
            cmds.textField(self.hip_ctrl_text_field, edit=True, text=chacha_ctrl)
            
        cmds.select(clear=True)
    
    def buildNeckAndHead(self, *args):
        neck_joint = cmds.textField(self.neck_joint_text_field, query=True, text=True)
        if not neck_joint:
            cmds.error("No neck joint specified")
            return
            
        head_joint = cmds.textField(self.head_joint_text_field, query=True, text=True)
        if not head_joint:
            cmds.error("No head joint specified")
            return
            
        spine_tip_joint = cmds.textField(self.neck_spine_tip_text_field, query=True, text=True)
        if not spine_tip_joint:
            cmds.error("No spine tip joint specified")
            return

        cmds.undoInfo(openChunk=True)
        try:
            neck_joint = cmds.ls(neck_joint, long=True)[0]
            head_joint = cmds.ls(head_joint, long=True)[0]
            spine_tip_joint = cmds.ls(spine_tip_joint, long=True)[0]

            # Find the path from neck to head
            neck_chain = [neck_joint]
            current_joint = head_joint
            head_parents = []
            while current_joint and current_joint != neck_joint:
                parent = cmds.listRelatives(current_joint, parent=True, fullPath=True)
                if not parent:
                    break
                current_joint = parent[0]
                if current_joint != neck_joint:
                    head_parents.append(current_joint)
                    
            head_parents.reverse()
            neck_chain.extend(head_parents)

            neck_ctrls = []
            
            # Build Neck Controls
            previous_ctrl = None
            last_neck_joint = neck_chain[-1]
            
            for i, jnt in enumerate(neck_chain):
                short_name = jnt.split('|')[-1]
                ctrl_name = short_name.replace("_bridgeJNT", "_CTRL")
                if "_CTRL" not in ctrl_name:
                    ctrl_name += "_CTRL"
                    
                normal, length = self._getPrimaryAxis(jnt, target_child=neck_chain[i+1] if i < len(neck_chain)-1 else head_joint)
                ctrl = cmds.circle(constructionHistory=False, name=ctrl_name, normal=normal, radius=(length * 1.5))[0]
                neck_ctrls.append(ctrl)
                
                zero_grp, sdk_grp = self._groupOverAlign(ctrl, jnt)
                cmds.parentConstraint(ctrl, jnt, maintainOffset=False)
                
                if previous_ctrl:
                    cmds.parent(zero_grp, previous_ctrl)
                
                previous_ctrl = ctrl
                
            # Build Head Control
            head_short_name = head_joint.split('|')[-1]
            head_ctrl_name = head_short_name.replace("_bridgeJNT", "_CTRL")
            if "_CTRL" not in head_ctrl_name:
                head_ctrl_name += "_CTRL"
                
            head_normal, head_length = self._getPrimaryAxis(head_joint)
            head_ctrl = cmds.circle(constructionHistory=False, name=head_ctrl_name, normal=head_normal, radius=(head_length * 0.5))[0]
            
            head_zero_grp, head_sdk_grp = self._groupOverAlign(head_ctrl, head_joint)
            cmds.parentConstraint(head_ctrl, head_joint, maintainOffset=False)

            # push head control up to be more halo-like
            move_length = head_length * 0.75
            cmds.move(head_normal[0] * move_length, head_normal[1] * move_length, head_normal[2] * move_length, head_ctrl + '.cv[*]', relative=True, objectSpace=True)
            
            # Space Switching Setup for Head
            head_locator = cmds.spaceLocator(name=head_ctrl_name + "_spaceLOC")[0]
            
            # Snap locator to head joint
            temp_const = cmds.parentConstraint(head_joint, head_locator, maintainOffset=False)
            cmds.delete(temp_const)
            
            # Parent locator to last neck ctrl
            cmds.parent(head_locator, previous_ctrl)
            
            # Constrain head zero group to locator
            cmds.pointConstraint(head_locator, head_zero_grp, maintainOffset=False)
            orient_const = cmds.orientConstraint(head_locator, head_zero_grp, maintainOffset=False)[0]
            
            # Add custom attribute for space switching
            cmds.addAttr(head_ctrl, longName="orient", attributeType="enum", enumName="<none>:Neck", keyable=True)
            
            # Connect the orient attribute to the orient constraint weight
            cmds.connectAttr(head_ctrl + ".orient", orient_const + "." + head_locator.split('|')[-1] + "W0", force=True)
            
            # Default to Neck orientation
            cmds.setAttr(head_ctrl + ".orient", 1)

            # Connect scale of head ctrl to head joint
            cmds.connectAttr(head_ctrl + ".scaleX", head_joint + ".scaleX", force=True)
            cmds.connectAttr(head_ctrl + ".scaleY", head_joint + ".scaleY", force=True)
            cmds.connectAttr(head_ctrl + ".scaleZ", head_joint + ".scaleZ", force=True)
            
            # Space Switching Setup for Base Neck
            base_neck_ctrl = neck_ctrls[0]
            base_neck_zero_grp = base_neck_ctrl + "_0"
            
            neck_locator = cmds.spaceLocator(name=base_neck_ctrl + "_spaceLOC")[0]
            
            # Snap locator to base neck joint
            temp_const = cmds.parentConstraint(neck_joint, neck_locator, maintainOffset=False)
            cmds.delete(temp_const)
            
            # Parent locator to spine tip ctrl
            if cmds.objExists("spineTip_CTRL"):
                cmds.parent(neck_locator, "spineTip_CTRL")
            else:
                cmds.warning("spineTip_CTRL does not exist. Space switching locator left unparented.")
            
            # Constrain base neck zero group to locator
            cmds.pointConstraint(neck_locator, base_neck_zero_grp, maintainOffset=False)
            orient_const_neck = cmds.orientConstraint(neck_locator, base_neck_zero_grp, maintainOffset=False)[0]
            
            # Add custom attribute for space switching
            cmds.addAttr(base_neck_ctrl, longName="orient", attributeType="enum", enumName="<none>:Chest", keyable=True)
            
            # Connect the orient attribute to the orient constraint weight
            cmds.connectAttr(base_neck_ctrl + ".orient", orient_const_neck + "." + neck_locator.split('|')[-1] + "W0", force=True)
            
            # Default to Chest orientation
            cmds.setAttr(base_neck_ctrl + ".orient", 1)

            
            # Lock and hide scaling/visibility on neck controls
            for c in neck_ctrls:
                if cmds.objExists(c):
                    for attr in ['sx', 'sy', 'sz', 'v']:
                        cmds.setAttr(c + "." + attr, lock=True, keyable=False, channelBox=False)
            
            # Lock and hide visiblity on head control
            cmds.setAttr(head_ctrl + ".v", lock=True, keyable=False, channelBox=False)
            
            # Grouping and Organization
            neck_ctrl_grp = cmds.group(empty=True, name="neck_CTRL_GRP")
            head_ctrl_grp = cmds.group(empty=True, name="head_CTRL_GRP")
            
            cmds.parent(base_neck_zero_grp, neck_ctrl_grp)
            cmds.parent(head_zero_grp, head_ctrl_grp)
            
            master_ctrl_grp = cmds.ls("CTRL_GRP")
            if master_ctrl_grp:
                cmds.parent(neck_ctrl_grp, master_ctrl_grp[0])
                cmds.parent(head_ctrl_grp, master_ctrl_grp[0])
                        
        except Exception as e:
            full_traceback = traceback.format_exc()
            cmds.error(f"Error building neck and head: {e}\n\nFull Traceback:\n{full_traceback}")
        finally:
            cmds.undoInfo(closeChunk=True)
    
    def _parentConstraintAndScale(self, driver, driven):
        cmds.parentConstraint(driver, driven, maintainOffset=True)
        for attr in ['scaleX', 'scaleY', 'scaleZ']:
            cmds.connectAttr(driver + "." + attr, driven + "." + attr, force=True)



    def _setupLengthSDK(self, driver_ctrl, driven_sdk, snap_target):
        # Calculate the local translation needed to be at snap_target
        # We use a temporary locator parented under the SDK group's parent 
        # so it lives in the exact same local space as the SDK group.
        parent_grp = cmds.listRelatives(driven_sdk, parent=True)[0]
        temp_loc = cmds.spaceLocator()[0]
        cmds.parent(temp_loc, parent_grp)
        
        # Snap the locator to the target to get the required local translation
        temp_const = cmds.pointConstraint(snap_target, temp_loc, maintainOffset=False)
        cmds.delete(temp_const)
        
        local_tx = cmds.getAttr(temp_loc + ".tx")
        local_ty = cmds.getAttr(temp_loc + ".ty")
        local_tz = cmds.getAttr(temp_loc + ".tz")
        cmds.delete(temp_loc)
        
        # Key Length = 0 (snapped to parent joint)
        cmds.setDrivenKeyframe(driven_sdk + ".tx", currentDriver=driver_ctrl + ".length", driverValue=0, value=local_tx)
        cmds.setDrivenKeyframe(driven_sdk + ".ty", currentDriver=driver_ctrl + ".length", driverValue=0, value=local_ty)
        cmds.setDrivenKeyframe(driven_sdk + ".tz", currentDriver=driver_ctrl + ".length", driverValue=0, value=local_tz)
        
        # Key Length = 1 (current default position, which is 0,0,0 local)
        cmds.setDrivenKeyframe(driven_sdk + ".tx", currentDriver=driver_ctrl + ".length", driverValue=1, value=0)
        cmds.setDrivenKeyframe(driven_sdk + ".ty", currentDriver=driver_ctrl + ".length", driverValue=1, value=0)
        cmds.setDrivenKeyframe(driven_sdk + ".tz", currentDriver=driver_ctrl + ".length", driverValue=1, value=0)
        
        # Set animation curves to Cycle with Offset
        cmds.setInfinity(driven_sdk, attribute=["tx", "ty", "tz"], preInfinite="cycleRelative", postInfinite="cycleRelative")
        
        # Restore default length to visually confirm
        cmds.setAttr(driver_ctrl + ".length", 1)

    def buildLegs(self, *args):
        hip_ctrl = cmds.textField(self.hip_ctrl_text_field, query=True, text=True)
        l_thigh_joint = cmds.textField(self.l_thigh_joint_text_field, query=True, text=True)
        l_ankle_joint = cmds.textField(self.l_ankle_joint_text_field, query=True, text=True)
        l_ball_joint = cmds.textField(self.l_ball_joint_text_field, query=True, text=True)
        l_toe_joint = cmds.textField(self.l_toe_joint_text_field, query=True, text=True)
        
        if not (l_thigh_joint and l_ankle_joint and l_ball_joint and l_toe_joint and hip_ctrl):
            cmds.error("Please specify Hip Control, Left Thigh, Ankle, Ball, and Toe Tip joints.")
            return
            
        cmds.undoInfo(openChunk=True)
        try:
            # Resolve to full paths
            l_thigh_joint = cmds.ls(l_thigh_joint, long=True)[0]
            l_ankle_joint = cmds.ls(l_ankle_joint, long=True)[0]
            l_ball_joint = cmds.ls(l_ball_joint, long=True)[0]
            l_toe_joint = cmds.ls(l_toe_joint, long=True)[0]
            
            # 1. Duplicate and unparent
            dupe_joints = cmds.duplicate(l_thigh_joint)
            if not dupe_joints:
                cmds.error("Failed to duplicate left thigh hierarchy.")
                return
            main_l_thigh = dupe_joints[0]
            if cmds.listRelatives(main_l_thigh, parent=True):
                main_l_thigh = cmds.parent(main_l_thigh, world=True)[0]
                
            # Rename _bridgeJNT to Main_JNT
            main_hierarchy = cmds.listRelatives(main_l_thigh, allDescendents=True, fullPath=True) or []
            main_hierarchy.append(main_l_thigh)
            main_l_thigh = self._renameHierarchy(main_hierarchy, "_bridgeJNT", "Main_JNT")
            
            # Use short names for ease after this point
            main_thigh_short = l_thigh_joint.split('|')[-1].replace("_bridgeJNT", "Main_JNT")
            main_ankle_short = l_ankle_joint.split('|')[-1].replace("_bridgeJNT", "Main_JNT")
            main_ball_short = l_ball_joint.split('|')[-1].replace("_bridgeJNT", "Main_JNT")
            main_toe_short = l_toe_joint.split('|')[-1].replace("_bridgeJNT", "Main_JNT")
            
            # Get path from ankle to thigh
            curr = main_ankle_short
            path_to_thigh = [curr]
            safe_count = 0
            while curr != main_thigh_short and safe_count < 100:
                parent = cmds.listRelatives(curr, parent=True)
                if not parent:
                    cmds.error("Ankle is not a descendant of Thigh")
                    return
                curr = parent[0].split('|')[-1]
                path_to_thigh.append(curr)
                safe_count += 1
                
            path_to_thigh.reverse() # [thigh, midThigh, knee, midKnee, ankle]
            
            if len(path_to_thigh) != 5:
                cmds.warning("Expected exactly 5 joints from Thigh to Ankle. Found {} joints.".format(len(path_to_thigh)))
                
            main_thigh = path_to_thigh[0]
            main_mid_thigh = path_to_thigh[1]
            main_knee = path_to_thigh[2]
            main_mid_knee = path_to_thigh[3]
            main_ankle = path_to_thigh[4]
            
            cmds.warning("main_thigh: " + main_thigh)
            cmds.warning("main_mid_thigh: " + main_mid_thigh)
            cmds.warning("main_knee: " + main_knee)
            cmds.warning("main_mid_knee: " + main_mid_knee)
            cmds.warning("main_ankle: " + main_ankle)

            # Reorganize Main chain
            cmds.parent(main_knee, main_thigh)
            cmds.parent(main_ankle, main_knee)
            
            # Array of joints NOT including mid joints
            main_joints_no_mid = [main_thigh, main_knee, main_ankle]
            # Joints past the ankle will be in a weird order but atm this doesn't matter
            ankle_descendants = cmds.listRelatives(main_ankle, allDescendents=True, type="joint") or []
            for desc in ankle_descendants:
                main_joints_no_mid.append(desc.split('|')[-1])
                
            # Point constrain mid joints
            cmds.pointConstraint(main_thigh, main_knee, main_mid_thigh, maintainOffset=False)
            cmds.pointConstraint(main_knee, main_ankle, main_mid_knee, maintainOffset=False)
            
            # Parent constrain & scale bridge joints to main joints
            for jnt in main_joints_no_mid:
                bridge_jnt = jnt.replace("Main_JNT", "_bridgeJNT")
                if cmds.objExists(bridge_jnt):
                    self._parentConstraintAndScale(jnt, bridge_jnt)
                    
            # Create FK chain
            fk_dupes = cmds.duplicate(main_thigh)
            fk_thigh = fk_dupes[0]
            
            fk_hierarchy = cmds.listRelatives(fk_thigh, allDescendents=True, fullPath=True) or []
            fk_hierarchy.append(fk_thigh)
            fk_thigh = self._renameHierarchy(fk_hierarchy, "Main_JNT", "FK_JNT")
            
            # Delete mid joints from FK chain
            fk_mid_thigh = main_mid_thigh.replace("Main_JNT", "FK_JNT")
            fk_mid_knee = main_mid_knee.replace("Main_JNT", "FK_JNT")
            if cmds.objExists(fk_mid_thigh):
                cmds.delete(fk_mid_thigh)
            if cmds.objExists(fk_mid_knee):
                cmds.delete(fk_mid_knee)
                
            # Create IK chain
            ik_dupes = cmds.duplicate(fk_thigh)
            ik_thigh = ik_dupes[0]
            
            ik_hierarchy = cmds.listRelatives(ik_thigh, allDescendents=True, fullPath=True) or []
            ik_hierarchy.append(ik_thigh)
            l_ik_thigh_jnt = self._renameHierarchy(ik_hierarchy, "FK_JNT", "IK_JNT")
            
            # Parent constrain Main to FK and IK
            thigh_constraint = None
            fk_thigh_short = None
            ik_thigh_short = None
            
            for main_jnt in main_joints_no_mid:
                fk_jnt = main_jnt.replace("Main_JNT", "FK_JNT")
                ik_jnt = main_jnt.replace("Main_JNT", "IK_JNT")
                
                if cmds.objExists(fk_jnt) and cmds.objExists(ik_jnt):
                    constraint = cmds.parentConstraint(fk_jnt, ik_jnt, main_jnt, maintainOffset=False)[0]
                    
                    fk_short = fk_jnt.split('|')[-1]
                    ik_short = ik_jnt.split('|')[-1]
                    
                    if not thigh_constraint:
                        thigh_constraint = constraint
                        fk_thigh_short = fk_short
                        ik_thigh_short = ik_short
                    else:
                        fk_src = "{}.{}W0".format(thigh_constraint, fk_thigh_short)
                        ik_src = "{}.{}W1".format(thigh_constraint, ik_thigh_short)
                        
                        fk_dst = "{}.{}W0".format(constraint, fk_short)
                        ik_dst = "{}.{}W1".format(constraint, ik_short)
                        
                        cmds.connectAttr(fk_src, fk_dst, force=True)
                        cmds.connectAttr(ik_src, ik_dst, force=True)

            l_ankle_normal, l_ankle_length = self._getPrimaryAxis(main_ankle, target_child=l_ball_joint.split('|')[-1].replace("_bridgeJNT", "_Main_JNT"))
            l_legFKIK_ctrl = self._createPlusCurve("L_LegFKIK_CTRL", (1,0,0))
            l_legFKIK_ctrl_zero, l_legFKIK_ctrl_sdk = self._groupOverAlign(l_legFKIK_ctrl, main_ankle)
            cmds.move(-0.5 * l_ankle_length, 0, 0, l_legFKIK_ctrl + '.cv[*]', relative=True, objectSpace=True)
            self._orientCVsUpright(l_legFKIK_ctrl, main_ankle, aim_axis=(1,0,0))
            if not cmds.attributeQuery("FKIK", node=l_legFKIK_ctrl, exists=True):
                cmds.addAttr(l_legFKIK_ctrl, longName="FKIK", niceName= "FK/IK", attributeType="float", minValue=0, maxValue=1, defaultValue=1.0, keyable=True)
                
            # Connect FKIK switch to thigh parent constraint
            if thigh_constraint and ik_thigh_short and fk_thigh_short:
                ik_weight_attr = "{}.{}W1".format(thigh_constraint, ik_thigh_short)
                fk_weight_attr = "{}.{}W0".format(thigh_constraint, fk_thigh_short)
                
                # 1. Connect IK weight directly (0 = FK, 1 = IK)
                cmds.connectAttr(l_legFKIK_ctrl + ".FKIK", ik_weight_attr, force=True)
                
                # 2. Create a reverse node for the FK weight
                l_leg_rev_node = cmds.createNode("reverse", name=l_legFKIK_ctrl + "_FK_REV")
                
                # 3. Connect FKIK attr into the reverse node's inputX
                cmds.connectAttr(l_legFKIK_ctrl + ".FKIK", l_leg_rev_node + ".inputX", force=True)
                
                # 4. Connect the reverse node's outputX into the FK weight
                cmds.connectAttr(l_leg_rev_node + ".outputX", fk_weight_attr, force=True)
            else:
                cmds.error("Unable to connect FK/IK switch to thigh parent constraint")
                return

            # Create groups for the leg controls
            l_legFK_CTRL_GRP = cmds.group(empty=True, name="L_legFK_CTRL_GRP", world=True)
            l_legIK_CTRL_GRP = cmds.group(empty=True, name="L_legIK_CTRL_GRP", world=True)

            cmds.connectAttr(l_leg_rev_node + ".outputX", l_legFK_CTRL_GRP + ".visibility", force=True)
            cmds.connectAttr(l_legFKIK_ctrl + ".FKIK", l_legIK_CTRL_GRP + ".visibility", force=True)

            # Create FK controls
            fk_thigh_jnt = main_thigh.replace("Main_JNT", "FK_JNT")
            fk_knee_jnt = main_knee.replace("Main_JNT", "FK_JNT")
            fk_ankle_jnt = main_ankle.replace("Main_JNT", "FK_JNT")
            fk_ball_jnt = main_ball_short.replace("Main_JNT", "FK_JNT")
            
            # Thigh FK
            thigh_normal, thigh_length = self._getPrimaryAxis(fk_thigh_jnt, target_child=fk_knee_jnt)
            thigh_length = thigh_length if thigh_length > 0.1 else 2.0
            l_thigh_fk_ctrl = cmds.circle(constructionHistory=False, name="L_thighFK_CTRL", normal=thigh_normal, radius=(thigh_length * 0.25))[0]
            l_thigh_fk_zero, _ = self._groupOverAlign(l_thigh_fk_ctrl, fk_thigh_jnt)
            
            # Move thigh controller slightly down thigh to not intersect groin
            if cmds.objExists(fk_knee_jnt):
                tx = cmds.getAttr(fk_knee_jnt + ".translateX")
                ty = cmds.getAttr(fk_knee_jnt + ".translateY")
                tz = cmds.getAttr(fk_knee_jnt + ".translateZ")
                cmds.move(tx * 0.25, ty * 0.25, tz * 0.25, l_thigh_fk_ctrl + '.cv[*]', relative=True, objectSpace=True)
            cmds.parentConstraint(l_thigh_fk_ctrl, fk_thigh_jnt, maintainOffset=False)
            cmds.addAttr(l_thigh_fk_ctrl, longName="length", attributeType="float", defaultValue=1, keyable=True)
            
            # Knee FK
            knee_normal, knee_length = self._getPrimaryAxis(fk_knee_jnt, target_child=fk_ankle_jnt)
            knee_length = knee_length if knee_length > 0.1 else 2.0
            l_knee_fk_ctrl = cmds.circle(constructionHistory=False, name="L_kneeFK_CTRL", normal=knee_normal, radius=(knee_length * 0.25))[0]
            l_knee_fk_zero, l_knee_fk_sdk = self._groupOverAlign(l_knee_fk_ctrl, fk_knee_jnt)
            cmds.parentConstraint(l_knee_fk_ctrl, fk_knee_jnt, maintainOffset=False)
            cmds.addAttr(l_knee_fk_ctrl, longName="length", attributeType="float", defaultValue=1, keyable=True)
            
            # Ankle FK
            ankle_normal, ankle_length = self._getPrimaryAxis(fk_ankle_jnt, target_child=l_ball_joint.split('|')[-1].replace("_bridgeJNT", "_FK_JNT"))
            ankle_length = ankle_length if ankle_length > 0.1 else 2.0
            l_ankle_fk_ctrl = cmds.circle(constructionHistory=False, name="L_ankleFK_CTRL", normal=ankle_normal, radius=(ankle_length * 0.5))[0]
            l_ankle_fk_zero, l_ankle_fk_sdk = self._groupOverAlign(l_ankle_fk_ctrl, fk_ankle_jnt)
            cmds.parentConstraint(l_ankle_fk_ctrl, fk_ankle_jnt, maintainOffset=False)
            
            # Ball FK
            ball_normal, ball_length = self._getPrimaryAxis(fk_ball_jnt)
            ball_length = ball_length if ball_length > 0.1 else 2.0
            l_ball_fk_ctrl = cmds.circle(constructionHistory=False, name="L_ballFK_CTRL", normal=ball_normal, radius=(ball_length * 0.75))[0]
            l_ball_fk_zero, _ = self._groupOverAlign(l_ball_fk_ctrl, fk_ball_jnt)
            cmds.parentConstraint(l_ball_fk_ctrl, fk_ball_jnt, maintainOffset=False)
            
            # Parent FK chain
            cmds.parent(l_ball_fk_zero, l_ankle_fk_ctrl)
            cmds.parent(l_ankle_fk_zero, l_knee_fk_ctrl)
            cmds.parent(l_knee_fk_zero, l_thigh_fk_ctrl)
            cmds.parent(l_thigh_fk_zero, l_legFK_CTRL_GRP)

            # Set up SDK for length of thigh and knee
            self._setupLengthSDK(l_thigh_fk_ctrl, l_knee_fk_sdk, fk_thigh_jnt)
            self._setupLengthSDK(l_knee_fk_ctrl, l_ankle_fk_sdk, fk_knee_jnt)

            # Space switching for thigh
            l_thigh_locator = cmds.spaceLocator(name="L_thighFK_CTRL_LOC")[0]
            # Snap locator to thigh main joint
            temp_const = cmds.parentConstraint(main_thigh, l_thigh_locator, maintainOffset=False)
            cmds.delete(temp_const)

            # Parent locator to hip control
            cmds.parent(l_thigh_locator, hip_ctrl)

            # Constrain thigh zero group to locator
            cmds.pointConstraint(l_thigh_locator, l_thigh_fk_zero, maintainOffset=False)
            l_thigh_orient_constraint = cmds.orientConstraint(l_thigh_locator, l_thigh_fk_zero, maintainOffset=False)[0]

            # Add custom attribute for space switching
            cmds.addAttr(l_thigh_fk_ctrl, longName="orient", attributeType="enum", enumName="<none>:Hips", keyable=True)

            # Connect the orient attribute to the orient constraint weight
            cmds.connectAttr(l_thigh_fk_ctrl + ".orient", l_thigh_orient_constraint + "." + l_thigh_locator.split('|')[-1] + "W0", force=True)

            # Default to Hip Orientation
            cmds.setAttr(l_thigh_fk_ctrl + ".orient", 1)

            # ------------------------------------------------------------------
            # IK Chain Setup
            # ------------------------------------------------------------------
            ik_ankle_jnt = main_ankle_short.replace("Main_JNT", "IK_JNT")
            ik_ball_jnt = main_ball_short.replace("Main_JNT", "IK_JNT")
            ik_toe_jnt = main_toe_short.replace("Main_JNT", "IK_JNT")
            
            # Thigh to Ankle (Rotate Plane Solver)
            l_foot_ikh, l_foot_eff = cmds.ikHandle(startJoint=l_ik_thigh_jnt, endEffector=ik_ankle_jnt, solver="ikRPsolver", sticky="sticky", name="L_foot_IKH")
            cmds.rename(l_foot_eff, "L_foot_EFF")
            
            # Ankle to Ball (Single Chain Solver)
            l_ball_ikh, l_ball_eff = cmds.ikHandle(startJoint=ik_ankle_jnt, endEffector=ik_ball_jnt, solver="ikSCsolver", sticky="sticky", name="L_ball_IKH")
            cmds.rename(l_ball_eff, "L_ball_EFF")
            
            # Ball to Toe (Single Chain Solver)
            l_toe_ikh, l_toe_eff = cmds.ikHandle(startJoint=ik_ball_jnt, endEffector=ik_toe_jnt, solver="ikSCsolver", sticky="sticky", name="L_toe_IKH")
            cmds.rename(l_toe_eff, "L_toe_EFF")

            cmds.parentConstraint(hip_ctrl, l_ik_thigh_jnt, maintainOffset=True)


            # ------------------------------------------------------------------
            # IK Controls
            # ------------------------------------------------------------------
            # Foot IK Control
            _, ankle_length = self._getPrimaryAxis(ik_ankle_jnt, target_child=l_ball_joint.split('|')[-1].replace("_bridgeJNT", "_IK_JNT"))
            ankle_length = ankle_length if ankle_length > 0.1 else 2.0
            l_foot_ik_ctrl = cmds.circle(constructionHistory=False, name="L_footIK_CTRL", normal=(0,1,0), sections=12, radius=(ankle_length * 1.5))[0]
            l_foot_ik_sdk = cmds.group(l_foot_ik_ctrl, name=l_foot_ik_ctrl + "_SDK")
            l_foot_ik_zero = cmds.group(l_foot_ik_sdk, name=l_foot_ik_ctrl + "_0")
            
            # Snap position to ankle
            temp_const = cmds.pointConstraint(ik_ankle_jnt, l_foot_ik_zero, maintainOffset=False)
            cmds.delete(temp_const)
            # Capture the XZ heading using the vector from ankle to ball
            ankle_pos = cmds.xform(ik_ankle_jnt, query=True, translation=True, worldSpace=True)
            ball_pos = cmds.xform(ik_ball_jnt, query=True, translation=True, worldSpace=True)
            
            # Project vector onto XZ plane
            dx = ball_pos[0] - ankle_pos[0]
            dz = ball_pos[2] - ankle_pos[2]
            
            # Calculate rotation around Y axis in degrees
            # math.atan2(dx, dz) gives the angle from Z axis towards X axis
            y_rot = math.degrees(math.atan2(dx, dz))
            
            # Apply heading rotation directly
            cmds.xform(l_foot_ik_zero, rotation=(0, y_rot, 0), worldSpace=True)
            
            # Move CVs close to the ground (90% of the way down from ankle to world Y 0) and halfway up the ankle bone
            ankle_y = cmds.xform(ik_ankle_jnt, query=True, translation=True, worldSpace=True)[1]
            cmds.move(0.5 * dx, -ankle_y * 0.9, 0.5 * dz, l_foot_ik_ctrl + '.cv[*]', relative=True, worldSpace=True)
            cmds.scale(0.5, 1, 1, l_foot_ik_ctrl + '.cv[*]', relative=True, objectSpace=True)
            
            # Parent IKs to Foot Control
            cmds.parent(l_foot_ikh, l_foot_ik_ctrl)
            cmds.parent(l_ball_ikh, l_foot_ik_ctrl)
            cmds.parent(l_toe_ikh, l_foot_ik_ctrl)
            cmds.parent(l_foot_ik_zero, l_legIK_CTRL_GRP)
            
            # Pole Vector Control
            ik_knee_jnt = main_knee.split('|')[-1].replace("Main_JNT", "IK_JNT")
            l_knee_ik_ctrl = self._createDiamondCurve("L_kneeIK_CTRL", radius=0.5)
            l_knee_ik_sdk = cmds.group(l_knee_ik_ctrl, name=l_knee_ik_ctrl + "_SDK")
            l_knee_ik_zero = cmds.group(l_knee_ik_sdk, name=l_knee_ik_ctrl + "_0")
            
            # Calculate and set PV position perfectly perpendicular to the hip-ankle line
            pv_pos = self._calculatePoleVectorPos(l_ik_thigh_jnt, ik_knee_jnt, ik_ankle_jnt, multiplier=thigh_length)
            cmds.xform(l_knee_ik_zero, translation=pv_pos, worldSpace=True)
            
            # Orient the zero group so its local Z axis points directly away from the knee
            pv_aim = cmds.aimConstraint(ik_knee_jnt, l_knee_ik_zero, aimVector=(0,0,-1), upVector=(0,1,0), worldUpType="vector", worldUpVector=(0,1,0))[0]
            cmds.delete(pv_aim)
            
            # Install Pole Vector constraint
            cmds.poleVectorConstraint(l_knee_ik_ctrl, l_foot_ikh)
            
            # Space Switching
            cmds.addAttr(l_knee_ik_ctrl, longName="follow", attributeType="enum", enumName="<none>:Foot", keyable=True)
            pv_space_constraint = cmds.parentConstraint(l_foot_ik_ctrl, l_knee_ik_zero, maintainOffset=True)[0]
            
            cmds.connectAttr(f"{l_knee_ik_ctrl}.follow", f"{pv_space_constraint}.{l_foot_ik_ctrl}W0", force=True)

            # Grouping and organizing
            cmds.parent(l_knee_ik_zero, l_legIK_CTRL_GRP)
            l_leg_common_CTRL_GRP = cmds.group(l_legFKIK_ctrl_zero, name="L_legCommon_CTRL_GRP")
            l_leg_CTRL_GRP = cmds.group(l_leg_common_CTRL_GRP, l_legIK_CTRL_GRP, l_legFK_CTRL_GRP, name="L_leg_CTRL_GRP")
            leg_CTRL_GRP = cmds.group(l_leg_CTRL_GRP, name="leg_CTRL_GRP")
            
            master_ctrl_grp = cmds.ls("CTRL_GRP")
            if master_ctrl_grp:
                cmds.parent(leg_CTRL_GRP, master_ctrl_grp[0])

            # ------------------------------------------------------------------
            # Squash and stretch
            # ------------------------------------------------------------------
            cmds.connectAttr(f"{l_ik_thigh_jnt}.scaleX", f"{ik_knee_jnt}.scaleX", force=True)
            # create measure distance tools
            thigh_pos = cmds.xform(l_ik_thigh_jnt, query=True, translation=True, worldSpace=True)
            ankle_pos = cmds.xform(ik_ankle_jnt, query=True, translation=True, worldSpace=True)
            
            cmds.select(clear=True) # Prevent Maya from auto-parenting locators to the active selection
            dist_shape = cmds.distanceDimension(startPoint=thigh_pos, endPoint=ankle_pos)
            dist_node = cmds.listRelatives(dist_shape, parent=True)[0]
            
            locs = cmds.listConnections(dist_shape + ".startPoint")
            l_legIKTop_LOC = cmds.rename(locs[0], "L_legIKTop_LOC")
            
            locs = cmds.listConnections(dist_shape + ".endPoint")
            l_legIKBot_LOC = cmds.rename(locs[0], "L_legIKBot_LOC")
            
            l_legIK_DIST = cmds.rename(dist_node, "L_legIK_DIST")
            
            # Explicitly force them to World Space to override any lingering Maya auto-parenting quirks
            for node in [l_legIKTop_LOC, l_legIKBot_LOC, l_legIK_DIST]:
                try:
                    if cmds.listRelatives(node, parent=True):
                        cmds.parent(node, world=True)
                except Exception:
                    pass
            
            # Constrain locators to drivers to avoid cycles
            cmds.parentConstraint(hip_ctrl, l_legIKTop_LOC, maintainOffset=True)
            cmds.parentConstraint(l_foot_ik_ctrl, l_legIKBot_LOC, maintainOffset=True)
            
            # Group the distance components to keep the outliner clean
            l_legIK_dist_grp = cmds.group(l_legIKTop_LOC, l_legIKBot_LOC, l_legIK_DIST, name="L_legIK_DIST_GRP")
            cmds.parent(l_legIK_dist_grp, l_legIK_CTRL_GRP)
            
            # Auto-populate Step 5 fields
            cmds.textField(self.stretch_top_loc_field, edit=True, text=l_legIKTop_LOC)
            cmds.textField(self.stretch_bot_loc_field, edit=True, text=l_legIKBot_LOC)
            cmds.textField(self.stretch_dist_field, edit=True, text=l_legIK_DIST)
            cmds.textField(self.stretch_foot_ctrl_field, edit=True, text=l_foot_ik_ctrl)
            cmds.textField(self.stretch_thigh_ik_field, edit=True, text=l_ik_thigh_jnt)

        except Exception as e:
            full_traceback = traceback.format_exc()
            cmds.error(f"Error building legs: {e}\n\nFull Traceback:\n{full_traceback}")
        finally:
            cmds.undoInfo(closeChunk=True)

    def _calculatePoleVectorPos(self, start_jnt, mid_jnt, end_jnt, multiplier=1.0):
        start_pos = cmds.xform(start_jnt, query=True, worldSpace=True, translation=True)
        mid_pos = cmds.xform(mid_jnt, query=True, worldSpace=True, translation=True)
        end_pos = cmds.xform(end_jnt, query=True, worldSpace=True, translation=True)
        
        start_vec = om.MVector(start_pos)
        mid_vec = om.MVector(mid_pos)
        end_vec = om.MVector(end_pos)
        
        # hipAnkle or shoulderWrist
        line = end_vec - start_vec
        # hipKnee or shoulderElbow
        point = mid_vec - start_vec
        projection = (point * line.normal()) * line.normal()
        pv_pos = start_vec + projection + ((point - projection).normal() * multiplier)
        
        return [pv_pos.x, pv_pos.y, pv_pos.z]

    def programLegStretch(self, *args):
        try:
            top_loc = cmds.textField(self.stretch_top_loc_field, query=True, text=True)
            bot_loc = cmds.textField(self.stretch_bot_loc_field, query=True, text=True)
            dist_node = cmds.textField(self.stretch_dist_field, query=True, text=True)
            foot_ctrl = cmds.textField(self.stretch_foot_ctrl_field, query=True, text=True)
            thigh_ik = cmds.textField(self.stretch_thigh_ik_field, query=True, text=True)
            global_scale = cmds.textField(self.stretch_global_scale_field, query=True, text=True)
            
            if not all([top_loc, bot_loc, dist_node, foot_ctrl, thigh_ik, global_scale]):
                cmds.warning("Please populate all fields in Step 5 before running this.")
                return
                
            dist_shape = cmds.listRelatives(dist_node, shapes=True)[0]
            recordedMaxLegExtent = cmds.getAttr(f"{dist_shape}.distance")
            
            # MD for global scale * max extent
            max_scale_md = cmds.createNode("multiplyDivide", name="L_legIK_maxScale_MD")
            cmds.connectAttr(f"{global_scale}.globalScale", f"{max_scale_md}.input1X", force=True)
            cmds.setAttr(f"{max_scale_md}.input2X", recordedMaxLegExtent)
            
            # MD for distance / (global scale * max extent)
            stretch_ratio_md = cmds.createNode("multiplyDivide", name="L_legIK_stretchRatio_MD")
            cmds.setAttr(f"{stretch_ratio_md}.operation", 2) # Divide
            cmds.connectAttr(f"{dist_shape}.distance", f"{stretch_ratio_md}.input1X", force=True)
            cmds.connectAttr(f"{max_scale_md}.outputX", f"{stretch_ratio_md}.input2X", force=True)
            
            # Condition node
            stretch_cond = cmds.createNode("condition", name="L_legIK_stretch_COND")
            cmds.setAttr(f"{stretch_cond}.operation", 3) # Greater or Equal
            cmds.connectAttr(f"{dist_shape}.distance", f"{stretch_cond}.firstTerm", force=True)
            cmds.connectAttr(f"{max_scale_md}.outputX", f"{stretch_cond}.secondTerm", force=True)
            
            cmds.connectAttr(f"{stretch_ratio_md}.outputX", f"{stretch_cond}.colorIfTrueR", force=True)
            cmds.setAttr(f"{stretch_cond}.colorIfFalseR", 1.0)
            
            # Connect result to the thigh IK scaleX
            cmds.connectAttr(f"{stretch_cond}.outColorR", f"{thigh_ik}.scaleX", force=True)
            
            print(f"Recorded Max Leg Extent: {recordedMaxLegExtent}")
            
            # Reset the foot controller back to bind pose
            cmds.setAttr(f"{foot_ctrl}.translate", 0, 0, 0)
            cmds.setAttr(f"{foot_ctrl}.rotate", 0, 0, 0)
            
        except Exception as e:
            full_traceback = traceback.format_exc()
            cmds.error(f"Error programming leg stretch: {e}\n\nFull Traceback:\n{full_traceback}")


    def generateFootPivotLocators(self, *args):
        try:
            cmds.undoInfo(openChunk=True)
            
            l_ankle = cmds.textField(self.l_ankle_joint_text_field, query=True, text=True)
            l_ball = cmds.textField(self.l_ball_joint_text_field, query=True, text=True)
            l_toe = cmds.textField(self.l_toe_joint_text_field, query=True, text=True)
            
            if not all([l_ankle, l_ball, l_toe]):
                cmds.warning("Please make sure Ankle, Ball, and Toe joints are loaded in Step 4.")
                return
                
            ankle_pos = cmds.xform(l_ankle, query=True, worldSpace=True, translation=True)
            ball_pos = cmds.xform(l_ball, query=True, worldSpace=True, translation=True)
            toe_pos = cmds.xform(l_toe, query=True, worldSpace=True, translation=True)
            
            offset = 5.0 # Rough offset for templates
            
            locs = {}
            locs['jimbo_L_Heel_Pivot_LOC'] = [ankle_pos[0], 0, ankle_pos[2] - offset]
            locs['jimbo_L_Toe_Pivot_LOC'] = [toe_pos[0], 0, toe_pos[2] + offset]
            locs['jimbo_L_AnkleIn_Pivot_LOC'] = [ankle_pos[0] - offset, 0, ball_pos[2]]
            locs['jimbo_L_AnkleOut_Pivot_LOC'] = [ankle_pos[0] + offset, 0, ball_pos[2]]
            locs['jimbo_L_Ball_Pivot_LOC'] = [ball_pos[0], ball_pos[1], ball_pos[2]]
            locs['jimbo_L_BallFloor_Pivot_LOC'] = [ball_pos[0], 0, ball_pos[2]]
            
            created_locs = {}
            for name, pos in locs.items():
                if cmds.objExists(name):
                    cmds.delete(name)
                loc = cmds.spaceLocator(name=name)[0]
                cmds.xform(loc, worldSpace=True, translation=pos)
                created_locs[name] = loc
                
            cmds.textField(self.heel_loc_field, edit=True, text=created_locs['jimbo_L_Heel_Pivot_LOC'])
            cmds.textField(self.toe_loc_field, edit=True, text=created_locs['jimbo_L_Toe_Pivot_LOC'])
            cmds.textField(self.ankle_in_loc_field, edit=True, text=created_locs['jimbo_L_AnkleIn_Pivot_LOC'])
            cmds.textField(self.ankle_out_loc_field, edit=True, text=created_locs['jimbo_L_AnkleOut_Pivot_LOC'])
            cmds.textField(self.ball_loc_field, edit=True, text=created_locs['jimbo_L_Ball_Pivot_LOC'])
            cmds.textField(self.ball_floor_loc_field, edit=True, text=created_locs['jimbo_L_BallFloor_Pivot_LOC'])
            
            cmds.select(clear=True)
            print("Foot pivot locators generated! Please adjust them to match your foot geometry.")
            
        except Exception as e:
            full_traceback = traceback.format_exc()
            cmds.error(f"Error generating pivot locators: {e}\n\nFull Traceback:\n{full_traceback}")
        finally:
            cmds.undoInfo(closeChunk=True)

    def scanFootPivotLocators(self, *args):
        try:
            expected_locs = {
                'jimbo_L_Heel_Pivot_LOC': self.heel_loc_field,
                'jimbo_L_Toe_Pivot_LOC': self.toe_loc_field,
                'jimbo_L_AnkleIn_Pivot_LOC': self.ankle_in_loc_field,
                'jimbo_L_AnkleOut_Pivot_LOC': self.ankle_out_loc_field,
                'jimbo_L_Ball_Pivot_LOC': self.ball_loc_field,
                'jimbo_L_BallFloor_Pivot_LOC': self.ball_floor_loc_field
            }
            
            found_count = 0
            for name, field in expected_locs.items():
                if cmds.objExists(name):
                    cmds.textField(field, edit=True, text=name)
                    found_count += 1
                    
            if found_count > 0:
                print(f"Scanned and successfully loaded {found_count} foot pivot locators!")
            else:
                cmds.warning("No locators found with the 'jimbo_' prefix.")
                
        except Exception as e:
            cmds.error(f"Error scanning for locators: {e}")

    def buildFootControls(self, *args):
        try:
            cmds.undoInfo(openChunk=True)
            
            heel_loc = cmds.textField(self.heel_loc_field, query=True, text=True)
            toe_loc = cmds.textField(self.toe_loc_field, query=True, text=True)
            ankle_out_loc = cmds.textField(self.ankle_out_loc_field, query=True, text=True)
            ankle_in_loc = cmds.textField(self.ankle_in_loc_field, query=True, text=True)
            ball_loc = cmds.textField(self.ball_loc_field, query=True, text=True)
            ball_floor_loc = cmds.textField(self.ball_floor_loc_field, query=True, text=True)
            
            if not all([heel_loc, toe_loc, ankle_out_loc, ankle_in_loc, ball_loc, ball_floor_loc]):
                cmds.warning("Please populate all 6 pivot locators.")
                return
                
            foot_ik_ctrl = cmds.textField(self.stretch_foot_ctrl_field, query=True, text=True)
            if not foot_ik_ctrl:
                cmds.warning("Please populate the Foot Controller field in Step 5 before building foot controls.")
                return
            
            def create_ctrl(name, radius=2.0, crescent=False, rotate_cvs=(0, 0, 0), translate_cvs=(0, 0, 0)):
                ctrl = cmds.circle(name=name, normal=(0, 1, 0), radius=radius, constructionHistory=False)[0]
                
                if crescent:
                    # Pushing the back 3 CVs (0, 1, 2) inward (+Z) to form a crescent moon shape
                    cmds.xform(f"{ctrl}.cv[0:2]", relative=True, translation=(0, 0, radius * 1.2))
                    # Push cv[1] slightly more to form a nicer, sharper arc
                    cmds.xform(f"{ctrl}.cv[1]", relative=True, translation=(0, 0, radius * 0.4))
                    
                if rotate_cvs != (0, 0, 0):
                    # Rotate the CVs directly around the local origin, avoiding transform modifications entirely
                    cmds.rotate(rotate_cvs[0], rotate_cvs[1], rotate_cvs[2], f"{ctrl}.cv[*]", pivot=(0,0,0), relative=True)
                    
                if translate_cvs != (0, 0, 0):
                    # Move the CVs directly so the actual transform pivot remains perfectly untouched at (0,0,0)
                    cmds.xform(f"{ctrl}.cv[*]", relative=True, translation=translate_cvs)
                    
                sdk_grp = cmds.group(ctrl, name=f"{name}_sdk")
                cmds.xform(sdk_grp, pivots=(0,0,0), worldSpace=True) # Force pivot to origin
                zero_grp = cmds.group(sdk_grp, name=f"{name}_0")
                cmds.xform(zero_grp, pivots=(0,0,0), worldSpace=True) # Force pivot to origin
                return ctrl, sdk_grp, zero_grp
                
            heel_ctrl, heel_sdk, heel_zero = create_ctrl("L_heel_CTRL", 1.0, crescent=True, rotate_cvs=(0, 180, 0))
            toe_ctrl, toe_sdk, toe_zero = create_ctrl("L_toePivot_CTRL", 0.75, crescent=True)
            ankle_out_ctrl, ankle_out_sdk, ankle_out_zero = create_ctrl("L_ankleOut_CTRL", 0.75, crescent=True, rotate_cvs=(0, 90, 0))
            ankle_in_ctrl, ankle_in_sdk, ankle_in_zero = create_ctrl("L_ankleIn_CTRL", 0.75, crescent=True, rotate_cvs=(0, -90, 0))
            ball_floor_ctrl, ball_floor_sdk, ball_floor_zero = create_ctrl("L_ballPivot_CTRL", 0.25, crescent=False, rotate_cvs=(-90, 0, 0), translate_cvs=(0, 1.5, 0))
            foot_roll_ctrl, foot_roll_sdk, foot_roll_zero = create_ctrl("L_footRoll_CTRL", 0.6, crescent=True, rotate_cvs=(-90, 0, 0), translate_cvs=(0, 0.3, 0))
            toe_wiggle_ctrl, toe_wiggle_sdk, toe_wiggle_zero = create_ctrl("L_toeWiggle_CTRL", 0.25, crescent=False, translate_cvs=(0, 0, 2.0))
            
            def snap_zero(zero_grp, loc):
                pos = cmds.xform(loc, query=True, worldSpace=True, translation=True)
                cmds.xform(zero_grp, worldSpace=True, translation=pos)
                
            snap_zero(heel_zero, heel_loc)
            snap_zero(toe_zero, toe_loc)
            snap_zero(ankle_out_zero, ankle_out_loc)
            snap_zero(ankle_in_zero, ankle_in_loc)
            snap_zero(ball_floor_zero, ball_floor_loc)
            snap_zero(foot_roll_zero, ball_loc)
            snap_zero(toe_wiggle_zero, ball_loc)
            
            cmds.parent(toe_zero, heel_ctrl)
            cmds.parent(ankle_out_zero, toe_ctrl)
            cmds.parent(ankle_in_zero, ankle_out_ctrl)
            cmds.parent(ball_floor_zero, ankle_in_ctrl)
            
            cmds.parent(foot_roll_zero, ball_floor_ctrl)
            cmds.parent(toe_wiggle_zero, ball_floor_ctrl)
            
            cmds.parent(heel_zero, foot_ik_ctrl)
            
            try:
                cmds.parent("L_foot_IKH", foot_roll_ctrl)
                cmds.parent("L_ball_IKH", ball_floor_ctrl)
                cmds.parent("L_toe_IKH", toe_wiggle_ctrl)
            except Exception as e:
                cmds.warning(f"Could not re-parent IK handles directly. Ensure they exist with standard names: {e}")
                
            print("Foot Reverse Hierarchy Built Successfully!")
            
        except Exception as e:
            full_traceback = traceback.format_exc()
            cmds.error(f"Error building foot controls: {e}\n\nFull Traceback:\n{full_traceback}")
        finally:
            cmds.undoInfo(closeChunk=True)

if __name__ == "__main__":
    ui = ControlRigUI()
    ui.show()
