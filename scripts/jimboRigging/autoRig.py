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
        build_legs_btn = cmds.button(label="Build Legs", height=35, command=self.buildLeftLeg)
        
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
        self.step5_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 10))
        
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
        cmds.button(label="Record Max Leg Extent", height=40, backgroundColor=(0.2, 0.6, 0.3), command=self.programLeftLegStretch)
        cmds.setParent('..') # exit step5_layout
        cmds.setParent('..') # exit step5_frame

        # CHAPTER 6: Foot Controls
        self.step6_frame = cmds.frameLayout(label="Step 6: Foot Controls", collapsable=True, collapse=True, marginWidth=5, marginHeight=5)
        self.step6_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 10))
        
        cmds.text(label="\nPrerequisite Nodes (Auto-Populated):", font="boldLabelFont")
        
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(200, 50, 50), adjustableColumn=1)
        self.step6_foot_ctrl_field = cmds.textField(placeholderText="Foot Controller", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadObject, self.step6_foot_ctrl_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.step6_foot_ctrl_field))
        cmds.setParent('..')
        
        cmds.separator(height=10, style='in')
        
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
        
        cmds.button(label="Build Foot Controls", height=40, backgroundColor=(0.2, 0.6, 0.3), command=self.buildLeftFootControls)
        
        cmds.setParent('..') # exit step6_layout
        cmds.setParent('..') # exit step6_frame
        
        # CHAPTER 7: Mirror Leg
        self.step7_frame = cmds.frameLayout(label="Step 7: Mirror Leg", collapsable=True, collapse=True, marginWidth=5, marginHeight=5)
        self.step7_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 10))
        
        cmds.text(label="\nRight Leg Joints (Auto-Populated):", font="boldLabelFont")
        
        # Right Thigh Joint
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.r_thigh_joint_text_field = cmds.textField(placeholderText="Right Thigh Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.r_thigh_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.r_thigh_joint_text_field))
        cmds.setParent('..')

        # Right Ankle Joint
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.r_ankle_joint_text_field = cmds.textField(placeholderText="Right Ankle Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.r_ankle_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.r_ankle_joint_text_field))
        cmds.setParent('..')

        # Right Ball Joint
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.r_ball_joint_text_field = cmds.textField(placeholderText="Right Ball Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.r_ball_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.r_ball_joint_text_field))
        cmds.setParent('..')

        # Right Toe Tip Joint
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.r_toe_joint_text_field = cmds.textField(placeholderText="Right Toe Tip Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.r_toe_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.r_toe_joint_text_field))
        cmds.setParent('..')
        
        cmds.text(label="\n*** IMPORTANT ***\nModify controller CVs on the left leg to your liking to fit the geometry before continuing.\n", wordWrap=True, align="center", font="boldLabelFont")
        cmds.button(label="Mirror Leg", height=40, backgroundColor=(0.2, 0.5, 0.6), command=self.mirrorLeg)
        
        cmds.setParent('..') # exit step7_layout
        cmds.setParent('..') # exit step7_frame
        
        # CHAPTER 8: Build Left Arm
        self.step8_frame = cmds.frameLayout(label="Step 8: Build Left Arm", collapsable=True, collapse=True, marginWidth=5, marginHeight=5)
        self.step8_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 10))
        
        cmds.text(label="Specify the joints for the left arm:", font="boldLabelFont")
        cmds.button(label="Analyze Rig", height=30, backgroundColor=(0.4, 0.4, 0.4), command=self.analyzeRig)
        
        # Spine Tip Joint
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.arm_spine_tip_text_field = cmds.textField(placeholderText="Spine Tip Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.arm_spine_tip_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.arm_spine_tip_text_field))
        cmds.setParent('..')
        
        # Left Clavicle Joint
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.l_clavicle_joint_text_field = cmds.textField(placeholderText="Left Clavicle Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.l_clavicle_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.l_clavicle_joint_text_field))
        cmds.setParent('..')

        # Left Shoulder Joint
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.l_shoulder_joint_text_field = cmds.textField(placeholderText="Left Shoulder Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.l_shoulder_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.l_shoulder_joint_text_field))
        cmds.setParent('..')

        # Left Wrist Joint
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.l_wrist_joint_text_field = cmds.textField(placeholderText="Left Wrist Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.l_wrist_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.l_wrist_joint_text_field))
        cmds.setParent('..')
        
        cmds.separator(height=15, style='in')
        
        cmds.button(label="Build Left Arm", height=40, backgroundColor=(0.6, 0.4, 0.2), command=self.buildLeftArm)
        
        cmds.setParent('..') # exit step8_layout
        cmds.setParent('..') # exit step8_frame
        
        # CHAPTER 9: Arm Stretch
        self.step9_frame = cmds.frameLayout(label="Step 9: Arm Stretch", collapsable=True, collapse=True, marginWidth=5, marginHeight=5)
        self.step9_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 10))
        
        cmds.text(label="Specify the nodes for the arm stretch:", font="boldLabelFont")
        cmds.button(label="Analyze Rig", height=30, backgroundColor=(0.4, 0.4, 0.4), command=self.analyzeRig)
        
        fields = [
            ("arm_top_loc_text_field", "L_armIKTop_LOC", self.loadObject),
            ("arm_bot_loc_text_field", "L_armIKBot_LOC", self.loadObject),
            ("arm_dist_text_field", "L_armIK_DIST", self.loadObject),
            ("arm_ik_shld_text_field", "L_shoulderIK_JNT", self.loadJointHierarchy),
            ("arm_ik_ctrl_text_field", "L_armIK_CTRL", self.loadObject),
            ("arm_global_scale_text_field", "all_CTRL", self.loadObject),
        ]
        
        for attr, placeholder, load_func in fields:
            cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
            setattr(self, attr, cmds.textField(placeholderText=placeholder, height=24))
            cmds.button(label="Load", height=24, command=partial(load_func, getattr(self, attr)))
            cmds.button(label="Clear", height=24, command=partial(self.clearSelection, getattr(self, attr)))
            cmds.setParent('..')
            
        cmds.text(label="\n*** IMPORTANT ***\nPosition the arm IK control to its maximum desired extent before running.\n", wordWrap=True, align="center", font="boldLabelFont")
        cmds.button(label="Record Max Arm Extent", height=40, backgroundColor=(0.8, 0.4, 0.2), command=self.programLeftArmStretch)
        
        cmds.setParent('..') # exit step9_layout
        cmds.setParent('..') # exit step9_frame
        
        # CHAPTER 10: Hand Controls
        self.step10_frame = cmds.frameLayout(label="Step 10: Build Hand Controls", collapsable=True, collapse=True, marginWidth=5, marginHeight=5)
        self.step10_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 10))
        
        cmds.text(label="Specify the wrist joint for the hand:", font="boldLabelFont")
        cmds.button(label="Analyze Rig", height=30, backgroundColor=(0.4, 0.4, 0.4), command=self.analyzeRig)
        
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.hand_wrist_joint_text_field = cmds.textField(placeholderText="Left Wrist Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.hand_wrist_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.hand_wrist_joint_text_field))
        cmds.setParent('..')
        
        cmds.separator(height=15, style='in')
        cmds.button(label="Build Left Hand Controls", height=40, backgroundColor=(0.6, 0.4, 0.2), command=self.buildLeftHandControls)
        
        cmds.setParent('..') # exit step10_layout
        cmds.setParent('..') # exit step10_frame
        
        # CHAPTER 11: Finger Presets
        self.step11_frame = cmds.frameLayout(label="Step 11: Finger Presets", collapsable=True, collapse=True, marginWidth=5, marginHeight=5)
        self.step11_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 10))
        
        cmds.text(label="Specify the preset control and finger control parent group:", font="boldLabelFont")
        
        # Preset Control
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.finger_preset_ctrl_field = cmds.textField(placeholderText="Left Finger Preset Control", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadObject, self.finger_preset_ctrl_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.finger_preset_ctrl_field))
        cmds.setParent('..')

        # Finger Control Parent Group
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.finger_sdk_grp_field = cmds.textField(placeholderText="Left Finger Control Group", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadObject, self.finger_sdk_grp_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.finger_sdk_grp_field))
        cmds.setParent('..')
        
        cmds.text(label="\nPose the finger control ***SDK GROUPS*** (not the finger controls themselves), then click a button below to record the pose with SetDrivenKey.\n", wordWrap=True, align="center")
        
        # Record Buttons
        form = cmds.formLayout(numberOfDivisions=100)
        b1 = cmds.button(label="Curl", height=30, backgroundColor=(0.6, 0.2, 0.2), command=partial(self._recordFingerPreset, "curl"))
        b2 = cmds.button(label="Scrunch", height=30, backgroundColor=(0.6, 0.3, 0.2), command=partial(self._recordFingerPreset, "scrunch"))
        b3 = cmds.button(label="Relax", height=30, backgroundColor=(0.6, 0.4, 0.2), command=partial(self._recordFingerPreset, "relax"))
        b4 = cmds.button(label="Spread", height=30, backgroundColor=(0.6, 0.5, 0.2), command=partial(self._recordFingerPreset, "spread"))
        b5 = cmds.button(label="ThumbSpread", height=30, backgroundColor=(0.5, 0.6, 0.2), command=partial(self._recordFingerPreset, "thumbSpread"))
        
        cmds.formLayout(form, edit=True,
            attachPosition=[
                (b1, 'left', 0, 0), (b1, 'right', 1, 20),
                (b2, 'left', 1, 20), (b2, 'right', 1, 40),
                (b3, 'left', 1, 40), (b3, 'right', 1, 60),
                (b4, 'left', 1, 60), (b4, 'right', 1, 80),
                (b5, 'left', 1, 80), (b5, 'right', 0, 100)
            ],
            attachForm=[
                (b1, 'top', 0), (b1, 'bottom', 0),
                (b2, 'top', 0), (b2, 'bottom', 0),
                (b3, 'top', 0), (b3, 'bottom', 0),
                (b4, 'top', 0), (b4, 'bottom', 0),
                (b5, 'top', 0), (b5, 'bottom', 0)
            ]
        )
        cmds.setParent('..')

        cmds.separator(height=10, style='none')
        
        cmds.setParent('..') # exit step11_layout
        cmds.setParent('..') # exit step11_frame
        
        # CHAPTER 12: Mirror Arm
        self.step12_frame = cmds.frameLayout(label="Step 12: Mirror Arm", collapsable=True, collapse=True, marginWidth=5, marginHeight=5)
        self.step12_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 10))
        
        cmds.text(label="\nRight Arm Joints (Auto-Populated):", font="boldLabelFont")
        
        # Spine Tip Control
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.r_arm_spine_tip_text_field = cmds.textField(placeholderText="Spine Tip Control", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadObject, self.r_arm_spine_tip_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.r_arm_spine_tip_text_field))
        cmds.setParent('..')

        # Right Clavicle Joint
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.r_clavicle_joint_text_field = cmds.textField(placeholderText="Right Clavicle Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.r_clavicle_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.r_clavicle_joint_text_field))
        cmds.setParent('..')

        # Right Shoulder Joint
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.r_shoulder_joint_text_field = cmds.textField(placeholderText="Right Shoulder Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.r_shoulder_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.r_shoulder_joint_text_field))
        cmds.setParent('..')

        # Right Wrist Joint
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(260, 50, 50), adjustableColumn=1, columnAttach3=['both', 'both', 'both'], columnOffset3=[2, 2, 2])
        self.r_wrist_joint_text_field = cmds.textField(placeholderText="Right Wrist Joint", height=24)
        cmds.button(label="Load", height=24, command=partial(self.loadJointHierarchy, self.r_wrist_joint_text_field))
        cmds.button(label="Clear", height=24, command=partial(self.clearSelection, self.r_wrist_joint_text_field))
        cmds.setParent('..')
        
        cmds.text(label="\n*** IMPORTANT ***\nEnsure the left arm and hand are perfectly positioned before mirroring.\n", wordWrap=True, align="center", font="boldLabelFont")
        cmds.button(label="Mirror Arm", height=40, backgroundColor=(0.2, 0.5, 0.6), command=self.mirrorArm)
        
        cmds.setParent('..') # exit step12_layout
        cmds.setParent('..') # exit step12_frame

        cmds.separator(height=20, style='none')
        
        cmds.setParent('..') # exit main columnLayout
        cmds.setParent('..') # exit main scrollLayout
        cmds.setParent('..') # exit window
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
        spine_tip_ctrl = None
        global_scale = None
        neck = None
        head = None
        l_thigh = None
        l_ankle = None
        l_ball = None
        l_toe = None
        r_thigh = None
        r_ankle = None
        r_ball = None
        r_toe = None
        l_clavicle = None
        l_shoulder = None
        l_wrist = None
        r_clavicle = None
        r_shoulder = None
        r_wrist = None
        hip_ctrl = None
        foot_ctrl = None
        arm_top_loc = None
        arm_bot_loc = None
        arm_dist = None
        arm_ik_shld = None
        arm_ik_ctrl = None
        
        for node in descendants:
            short_name = node.split('|')[-1]
            if short_name == "COG_bridgeJNT" and not cog:
                cog = node
            elif short_name == "spine1_bridgeJNT" and not spine_base:
                spine_base = node
            elif short_name == "chest_bridgeJNT" and not spine_tip:
                spine_tip = node
            elif short_name == "spineTip_CTRL" and not spine_tip_ctrl:
                spine_tip_ctrl = node
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
            elif short_name == "R_thigh_bridgeJNT" and not r_thigh:
                r_thigh = node
            elif short_name == "R_ankle_bridgeJNT" and not r_ankle:
                r_ankle = node
            elif short_name == "R_ball_bridgeJNT" and not r_ball:
                r_ball = node
            elif short_name == "R_toeTip_bridgeJNT" and not r_toe:
                r_toe = node
            elif short_name == "L_clavicle_bridgeJNT" and not l_clavicle:
                l_clavicle = node
            elif short_name == "L_shoulder_bridgeJNT" and not l_shoulder:
                l_shoulder = node
            elif short_name == "L_wrist_bridgeJNT" and not l_wrist:
                l_wrist = node
            elif short_name == "R_clavicle_bridgeJNT" and not r_clavicle:
                r_clavicle = node
            elif short_name == "R_shoulder_bridgeJNT" and not r_shoulder:
                r_shoulder = node
            elif short_name == "R_wrist_bridgeJNT" and not r_wrist:
                r_wrist = node
            elif short_name == "chacha_CTRL" and not hip_ctrl:
                hip_ctrl = node
            elif short_name == "L_footIK_CTRL" and not foot_ctrl:
                foot_ctrl = node
            elif short_name == "L_armIKTop_LOC" and not arm_top_loc:
                arm_top_loc = node
            elif short_name == "L_armIKBot_LOC" and not arm_bot_loc:
                arm_bot_loc = node
            elif short_name == "L_armIK_DIST" and not arm_dist:
                arm_dist = node
            elif short_name == "L_shoulderIK_JNT" and not arm_ik_shld:
                arm_ik_shld = node
            elif short_name == "L_armIK_CTRL" and not arm_ik_ctrl:
                arm_ik_ctrl = node
                
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
        if r_thigh:
            cmds.textField(self.r_thigh_joint_text_field, edit=True, text=r_thigh)
            populated.append("R Thigh")
        if r_ankle:
            cmds.textField(self.r_ankle_joint_text_field, edit=True, text=r_ankle)
            populated.append("R Ankle")
        if r_ball:
            cmds.textField(self.r_ball_joint_text_field, edit=True, text=r_ball)
            populated.append("R Ball")
        if r_toe:
            cmds.textField(self.r_toe_joint_text_field, edit=True, text=r_toe)
            populated.append("R Toe Tip")
        if spine_tip_ctrl:
            cmds.textField(self.arm_spine_tip_text_field, edit=True, text=spine_tip_ctrl)
            populated.append("Arm Spine Tip")
        if l_clavicle:
            cmds.textField(self.l_clavicle_joint_text_field, edit=True, text=l_clavicle)
            populated.append("L Clavicle")
        if l_shoulder:
            cmds.textField(self.l_shoulder_joint_text_field, edit=True, text=l_shoulder)
            populated.append("L Shoulder")
        if l_wrist:
            cmds.textField(self.l_wrist_joint_text_field, edit=True, text=l_wrist)
            cmds.textField(self.hand_wrist_joint_text_field, edit=True, text=l_wrist)
            populated.append("L Wrist")
        if r_clavicle:
            cmds.textField(self.r_clavicle_joint_text_field, edit=True, text=r_clavicle)
            populated.append("R Clavicle")
        if r_shoulder:
            cmds.textField(self.r_shoulder_joint_text_field, edit=True, text=r_shoulder)
            populated.append("R Shoulder")
        if r_wrist:
            cmds.textField(self.r_wrist_joint_text_field, edit=True, text=r_wrist)
            populated.append("R Wrist")
        if spine_tip_ctrl:
            cmds.textField(self.arm_spine_tip_text_field, edit=True, text=spine_tip_ctrl)
            cmds.textField(self.r_arm_spine_tip_text_field, edit=True, text=spine_tip_ctrl)
            populated.append("Arm Spine Tip")
        if hip_ctrl:
            cmds.textField(self.hip_ctrl_text_field, edit=True, text=hip_ctrl)
            populated.append("Hip Control")
        if foot_ctrl:
            cmds.textField(self.stretch_foot_ctrl_field, edit=True, text=foot_ctrl)
            cmds.textField(self.step6_foot_ctrl_field, edit=True, text=foot_ctrl)
            populated.append("Foot Control")
        if arm_top_loc:
            cmds.textField(self.arm_top_loc_text_field, edit=True, text=arm_top_loc)
            populated.append("Arm Top LOC")
        if arm_bot_loc:
            cmds.textField(self.arm_bot_loc_text_field, edit=True, text=arm_bot_loc)
            populated.append("Arm Bot LOC")
        if arm_dist:
            cmds.textField(self.arm_dist_text_field, edit=True, text=arm_dist)
            populated.append("Arm Dist Node")
        if arm_ik_shld:
            cmds.textField(self.arm_ik_shld_text_field, edit=True, text=arm_ik_shld)
            populated.append("Arm IK Shoulder")
        if arm_ik_ctrl:
            cmds.textField(self.arm_ik_ctrl_text_field, edit=True, text=arm_ik_ctrl)
            populated.append("Arm IK Control")
        if global_scale:
            cmds.textField(self.arm_global_scale_text_field, edit=True, text=global_scale)
            
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

    def _getLocalAxisToWorld(self, node, world_dir):
        m = cmds.xform(node, query=True, worldSpace=True, matrix=True)
        x_world = [m[0], m[1], m[2]]
        y_world = [m[4], m[5], m[6]]
        z_world = [m[8], m[9], m[10]]
        
        x_dot = x_world[0]*world_dir[0] + x_world[1]*world_dir[1] + x_world[2]*world_dir[2]
        y_dot = y_world[0]*world_dir[0] + y_world[1]*world_dir[1] + y_world[2]*world_dir[2]
        z_dot = z_world[0]*world_dir[0] + z_world[1]*world_dir[1] + z_world[2]*world_dir[2]
        
        dots = [(abs(x_dot), x_dot, (1,0,0)), 
                (abs(y_dot), y_dot, (0,1,0)), 
                (abs(z_dot), z_dot, (0,0,1))]
                
        dots.sort(key=lambda item: item[0], reverse=True)
        
        best_axis = dots[0][2]
        is_positive = dots[0][1] > 0
        
        if is_positive:
            return best_axis
        else:
            return (-best_axis[0], -best_axis[1], -best_axis[2])

    def _getDynamicRotation(self, target_axis):
        if target_axis == (0, 1, 0):   return (0, 0, 0)
        elif target_axis == (0, -1, 0):return (180, 0, 0)
        elif target_axis == (0, 0, 1): return (90, 0, 0)
        elif target_axis == (0, 0, -1):return (-90, 0, 0)
        elif target_axis == (1, 0, 0): return (0, 0, -90)
        elif target_axis == (-1, 0, 0):return (0, 0, 90)
        return (0, 0, 0)

    def _lockAndHideAttrs(self, ctrl, attrs):
        if not cmds.objExists(ctrl):
            return
        for attr in attrs:
            try:
                cmds.setAttr(f"{ctrl}.{attr}", lock=True, keyable=False, channelBox=False)
            except Exception:
                pass

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

    def _createArrowCurve(self, name, size=1.0):
        pts = [
            (0, 1*size, 0),      # Tip
            (0.5*size, 0, 0),    # Right wing
            (0.2*size, 0, 0),    # Right inner corner
            (0.2*size, -1*size, 0), # Right bottom
            (-0.2*size, -1*size, 0),# Left bottom
            (-0.2*size, 0, 0),   # Left inner corner
            (-0.5*size, 0, 0),   # Left wing
            (0, 1*size, 0)       # Back to tip
        ]
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

    def _createSphereCurve(self, name, radius=1.0):
        # Create 3 circles in X, Y, Z planes
        cx = cmds.circle(name=f"{name}_cx", normal=(1, 0, 0), radius=radius, sections=8, degree=3, constructionHistory=False)[0]
        cy = cmds.circle(name=f"{name}_cy", normal=(0, 1, 0), radius=radius, sections=8, degree=3, constructionHistory=False)[0]
        cz = cmds.circle(name=f"{name}_cz", normal=(0, 0, 1), radius=radius, sections=8, degree=3, constructionHistory=False)[0]
        
        cx_shape = cmds.listRelatives(cx, shapes=True)[0]
        cy_shape = cmds.listRelatives(cy, shapes=True)[0]
        cz_shape = cmds.listRelatives(cz, shapes=True)[0]
        
        cmds.parent(cy_shape, cz_shape, cx, shape=True, relative=True)
        cmds.delete(cy, cz)
        
        return cmds.rename(cx, name)

    def _createHandCurve(self, name, normal=(0, 1, 0), radius=1.0):
        r = radius
        if normal == (1, 0, 0) or normal == (-1, 0, 0):
            pts = [
                (0, r*0.8, r*1.0), (0, r*1.0, r*0.6), (0, r*1.8, -r*0.2),
                (0, r*1.6, -r*0.5), (0, r*0.8, -r*0.1),
                (0, r*0.8, -r*1.0), (0, r*0.8, -r*2.1), (0, r*0.4, -r*2.1), (0, r*0.4, -r*1.1),
                (0, r*0.4, -r*2.3), (0, 0, -r*2.3), (0, 0, -r*1.1), (0, 0, -r*2.1),
                (0, -r*0.4, -r*2.1), (0, -r*0.4, -r*1.0), (0, -r*0.4, -r*1.7), (0, -r*0.8, -r*1.7),
                (0, -r*0.8, r*0.2), (0, -r*0.8, r*1.0), (0, r*0.8, r*1.0)
            ]
        elif normal == (0, 0, 1) or normal == (0, 0, -1):
            pts = [
                (-r*0.8, -r*1.0, 0), (-r*1.0, -r*0.6, 0), (-r*1.8, r*0.2, 0),
                (-r*1.6, r*0.5, 0), (-r*0.8, r*0.1, 0),
                (-r*0.8, r*1.0, 0), (-r*0.8, r*2.1, 0), (-r*0.4, r*2.1, 0), (-r*0.4, r*1.1, 0),
                (-r*0.4, r*2.3, 0), (0, r*2.3, 0), (0, r*1.1, 0), (0, r*2.1, 0),
                (r*0.4, r*2.1, 0), (r*0.4, r*1.0, 0), (r*0.4, r*1.7, 0), (r*0.8, r*1.7, 0),
                (r*0.8, -r*0.2, 0), (r*0.8, -r*1.0, 0), (-r*0.8, -r*1.0, 0)
            ]
        else: # Default Y normal
            pts = [
                (-r*0.8, 0, r*1.0), (-r*1.0, 0, r*0.6), (-r*1.8, 0, -r*0.2),
                (-r*1.6, 0, -r*0.5), (-r*0.8, 0, -r*0.1),
                (-r*0.8, 0, -r*1.0), (-r*0.8, 0, -r*2.1), (-r*0.4, 0, -r*2.1), (-r*0.4, 0, -r*1.1),
                (-r*0.4, 0, -r*2.3), (0, 0, -r*2.3), (0, 0, -r*1.1), (0, 0, -r*2.1),
                (r*0.4, 0, -r*2.1), (r*0.4, 0, -r*1.0), (r*0.4, 0, -r*1.7), (r*0.8, 0, -r*1.7),
                (r*0.8, 0, r*0.2), (r*0.8, 0, r*1.0), (-r*0.8, 0, r*1.0)
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
            
        # Auto-populate Step 8's Spine Tip Control if it exists
        if cmds.objExists(spine_tip_ctrl):
            cmds.textField(self.arm_spine_tip_text_field, edit=True, text=spine_tip_ctrl)
            
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
            cmds.setAttr(head_locator + ".v", 0)
            
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
            cmds.setAttr(neck_locator + ".v", 0)
            
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

    def buildLeftLeg(self, *args):
        hip_ctrl = cmds.textField(self.hip_ctrl_text_field, query=True, text=True)
        l_thigh_joint = cmds.textField(self.l_thigh_joint_text_field, query=True, text=True)
        l_ankle_joint = cmds.textField(self.l_ankle_joint_text_field, query=True, text=True)
        l_ball_joint = cmds.textField(self.l_ball_joint_text_field, query=True, text=True)
        l_toe_joint = cmds.textField(self.l_toe_joint_text_field, query=True, text=True)
        
        if not (l_thigh_joint and l_ankle_joint and l_ball_joint and l_toe_joint and hip_ctrl):
            cmds.error("Please specify Hip Control, Left Thigh, Ankle, Ball, and Toe Tip joints.")
            return
            
        self._buildLegLogic("L", l_thigh_joint, l_ankle_joint, l_ball_joint, l_toe_joint, hip_ctrl)

    def _buildLegLogic(self, side, thigh_joint, ankle_joint, ball_joint, toe_joint, hip_ctrl):
        cmds.undoInfo(openChunk=True)
        try:
            # Resolve to full paths
            thigh_joint = cmds.ls(thigh_joint, long=True)[0]
            ankle_joint = cmds.ls(ankle_joint, long=True)[0]
            ball_joint = cmds.ls(ball_joint, long=True)[0]
            toe_joint = cmds.ls(toe_joint, long=True)[0]
            
            # 1. Duplicate and unparent
            dupe_joints = cmds.duplicate(thigh_joint)
            if not dupe_joints:
                cmds.error("Failed to duplicate left thigh hierarchy.")
                return
            main_thigh_dup = dupe_joints[0]
            if cmds.listRelatives(main_thigh_dup, parent=True):
                main_thigh_dup = cmds.parent(main_thigh_dup, world=True)[0]
                
            # Rename _bridgeJNT to Main_JNT
            main_hierarchy = cmds.listRelatives(main_thigh_dup, allDescendents=True, fullPath=True) or []
            main_hierarchy.append(main_thigh_dup)
            main_thigh_dup = self._renameHierarchy(main_hierarchy, "_bridgeJNT", "Main_JNT")
            
            # Use short names for ease after this point
            main_thigh_short = thigh_joint.split('|')[-1].replace("_bridgeJNT", "Main_JNT")
            main_ankle_short = ankle_joint.split('|')[-1].replace("_bridgeJNT", "Main_JNT")
            main_ball_short = ball_joint.split('|')[-1].replace("_bridgeJNT", "Main_JNT")
            main_toe_short = toe_joint.split('|')[-1].replace("_bridgeJNT", "Main_JNT")
            
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
            all_main_joints = path_to_thigh + [desc.split('|')[-1] for desc in ankle_descendants]
            for jnt in all_main_joints:
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
            ik_thigh_jnt = self._renameHierarchy(ik_hierarchy, "FK_JNT", "IK_JNT")
            
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

            ankle_normal, ankle_length = self._getPrimaryAxis(main_ankle, target_child=ball_joint.split('|')[-1].replace("_bridgeJNT", "_Main_JNT"))
            legFKIK_ctrl = self._createPlusCurve(f"{side}_LegFKIK_CTRL", (1,0,0))
            legFKIK_ctrl_zero, legFKIK_ctrl_sdk = self._groupOverAlign(legFKIK_ctrl, main_ankle)
            cmds.move(-0.5 * ankle_length, 0, 0, legFKIK_ctrl + '.cv[*]', relative=True, objectSpace=True)
            self._orientCVsUpright(legFKIK_ctrl, main_ankle, aim_axis=(1,0,0))
            
            # Constrain FK/IK switch to the ankle so it moves with the foot
            cmds.parentConstraint(main_ankle, legFKIK_ctrl_zero, maintainOffset=True)
            if not cmds.attributeQuery("FKIK", node=legFKIK_ctrl, exists=True):
                cmds.addAttr(legFKIK_ctrl, longName="FKIK", niceName= "FK/IK", attributeType="float", minValue=0, maxValue=1, defaultValue=1.0, keyable=True)
                
            # Connect FKIK switch to thigh parent constraint
            if thigh_constraint and ik_thigh_short and fk_thigh_short:
                ik_weight_attr = "{}.{}W1".format(thigh_constraint, ik_thigh_short)
                fk_weight_attr = "{}.{}W0".format(thigh_constraint, fk_thigh_short)
                
                # 1. Connect IK weight directly (0 = FK, 1 = IK)
                cmds.connectAttr(legFKIK_ctrl + ".FKIK", ik_weight_attr, force=True)
                
                # 2. Create a reverse node for the FK weight
                leg_rev_node = cmds.createNode("reverse", name=legFKIK_ctrl + "_FK_REV")
                
                # 3. Connect FKIK attr into the reverse node's inputX
                cmds.connectAttr(legFKIK_ctrl + ".FKIK", leg_rev_node + ".inputX", force=True)
                
                # 4. Connect the reverse node's outputX into the FK weight
                cmds.connectAttr(leg_rev_node + ".outputX", fk_weight_attr, force=True)
            else:
                cmds.error("Unable to connect FK/IK switch to thigh parent constraint")
                return

            # Create groups for the leg controls
            legFK_CTRL_GRP = cmds.group(empty=True, name=f"{side}_legFK_CTRL_GRP", world=True)
            legIK_CTRL_GRP = cmds.group(empty=True, name=f"{side}_legIK_CTRL_GRP", world=True)

            cmds.connectAttr(leg_rev_node + ".outputX", legFK_CTRL_GRP + ".visibility", force=True)
            cmds.connectAttr(legFKIK_ctrl + ".FKIK", legIK_CTRL_GRP + ".visibility", force=True)

            # Create FK controls
            fk_thigh_jnt = main_thigh.replace("Main_JNT", "FK_JNT")
            fk_knee_jnt = main_knee.replace("Main_JNT", "FK_JNT")
            fk_ankle_jnt = main_ankle.replace("Main_JNT", "FK_JNT")
            fk_ball_jnt = main_ball_short.replace("Main_JNT", "FK_JNT")
            
            # Thigh FK
            thigh_normal, thigh_length = self._getPrimaryAxis(fk_thigh_jnt, target_child=fk_knee_jnt)
            thigh_length = thigh_length if thigh_length > 0.1 else 2.0
            thigh_fk_ctrl = cmds.circle(constructionHistory=False, name=f"{side}_thighFK_CTRL", normal=thigh_normal, radius=(thigh_length * 0.25))[0]
            thigh_fk_zero, _ = self._groupOverAlign(thigh_fk_ctrl, fk_thigh_jnt)
            
            # Move thigh controller slightly down thigh to not intersect groin
            if cmds.objExists(fk_knee_jnt):
                tx = cmds.getAttr(fk_knee_jnt + ".translateX")
                ty = cmds.getAttr(fk_knee_jnt + ".translateY")
                tz = cmds.getAttr(fk_knee_jnt + ".translateZ")
                cmds.move(tx * 0.25, ty * 0.25, tz * 0.25, thigh_fk_ctrl + '.cv[*]', relative=True, objectSpace=True)
            cmds.parentConstraint(thigh_fk_ctrl, fk_thigh_jnt, maintainOffset=False)
            cmds.addAttr(thigh_fk_ctrl, longName="length", attributeType="float", defaultValue=1, keyable=True)
            
            # Knee FK
            knee_normal, knee_length = self._getPrimaryAxis(fk_knee_jnt, target_child=fk_ankle_jnt)
            knee_length = knee_length if knee_length > 0.1 else 2.0
            knee_fk_ctrl = cmds.circle(constructionHistory=False, name=f"{side}_kneeFK_CTRL", normal=knee_normal, radius=(knee_length * 0.25))[0]
            knee_fk_zero, knee_fk_sdk = self._groupOverAlign(knee_fk_ctrl, fk_knee_jnt)
            cmds.parentConstraint(knee_fk_ctrl, fk_knee_jnt, maintainOffset=False)
            cmds.addAttr(knee_fk_ctrl, longName="length", attributeType="float", defaultValue=1, keyable=True)
            
            # Ankle FK
            ankle_normal, ankle_length = self._getPrimaryAxis(fk_ankle_jnt, target_child=ball_joint.split('|')[-1].replace("_bridgeJNT", "_FK_JNT"))
            ankle_length = ankle_length if ankle_length > 0.1 else 2.0
            ankle_fk_ctrl = cmds.circle(constructionHistory=False, name=f"{side}_ankleFK_CTRL", normal=ankle_normal, radius=(ankle_length * 0.5))[0]
            ankle_fk_zero, ankle_fk_sdk = self._groupOverAlign(ankle_fk_ctrl, fk_ankle_jnt)
            cmds.parentConstraint(ankle_fk_ctrl, fk_ankle_jnt, maintainOffset=False)
            
            # Ball FK
            ball_normal, ball_length = self._getPrimaryAxis(fk_ball_jnt)
            ball_length = ball_length if ball_length > 0.1 else 2.0
            ball_fk_ctrl = cmds.circle(constructionHistory=False, name=f"{side}_ballFK_CTRL", normal=ball_normal, radius=(ball_length * 0.75))[0]
            ball_fk_zero, _ = self._groupOverAlign(ball_fk_ctrl, fk_ball_jnt)
            cmds.parentConstraint(ball_fk_ctrl, fk_ball_jnt, maintainOffset=False)
            
            # Parent FK chain
            cmds.parent(ball_fk_zero, ankle_fk_ctrl)
            cmds.parent(ankle_fk_zero, knee_fk_ctrl)
            cmds.parent(knee_fk_zero, thigh_fk_ctrl)
            cmds.parent(thigh_fk_zero, legFK_CTRL_GRP)

            # Set up SDK for length of thigh and knee
            self._setupLengthSDK(thigh_fk_ctrl, knee_fk_sdk, fk_thigh_jnt)
            self._setupLengthSDK(knee_fk_ctrl, ankle_fk_sdk, fk_knee_jnt)

            # Space switching for thigh
            thigh_locator = cmds.spaceLocator(name=f"{side}_thighFK_CTRL_LOC")[0]
            cmds.setAttr(thigh_locator + ".v", 0)
            # Snap locator to thigh main joint
            temp_const = cmds.parentConstraint(main_thigh, thigh_locator, maintainOffset=False)
            cmds.delete(temp_const)

            # Parent locator to hip control
            cmds.parent(thigh_locator, hip_ctrl)

            # Constrain thigh zero group to locator
            cmds.pointConstraint(thigh_locator, thigh_fk_zero, maintainOffset=False)
            thigh_orient_constraint = cmds.orientConstraint(thigh_locator, thigh_fk_zero, maintainOffset=False)[0]

            # Add custom attribute for space switching
            cmds.addAttr(thigh_fk_ctrl, longName="orient", attributeType="enum", enumName="<none>:Hips", keyable=True)

            # Connect the orient attribute to the orient constraint weight
            cmds.connectAttr(thigh_fk_ctrl + ".orient", thigh_orient_constraint + "." + thigh_locator.split('|')[-1] + "W0", force=True)

            # Default to Hip Orientation
            cmds.setAttr(thigh_fk_ctrl + ".orient", 1)

            # ------------------------------------------------------------------
            # IK Chain Setup
            # ------------------------------------------------------------------
            ik_ankle_jnt = main_ankle_short.replace("Main_JNT", "IK_JNT")
            ik_ball_jnt = main_ball_short.replace("Main_JNT", "IK_JNT")
            ik_toe_jnt = main_toe_short.replace("Main_JNT", "IK_JNT")
            
            # Thigh to Ankle (Rotate Plane Solver)
            foot_ikh, foot_eff = cmds.ikHandle(startJoint=ik_thigh_jnt, endEffector=ik_ankle_jnt, solver="ikRPsolver", sticky="sticky", name=f"{side}_foot_IKH")
            cmds.rename(foot_eff, f"{side}_foot_EFF")
            
            # Ankle to Ball (Single Chain Solver)
            ball_ikh, ball_eff = cmds.ikHandle(startJoint=ik_ankle_jnt, endEffector=ik_ball_jnt, solver="ikSCsolver", sticky="sticky", name=f"{side}_ball_IKH")
            cmds.rename(ball_eff, f"{side}_ball_EFF")
            
            # Ball to Toe (Single Chain Solver)
            toe_ikh, toe_eff = cmds.ikHandle(startJoint=ik_ball_jnt, endEffector=ik_toe_jnt, solver="ikSCsolver", sticky="sticky", name=f"{side}_toe_IKH")
            cmds.rename(toe_eff, f"{side}_toe_EFF")

            cmds.parentConstraint(hip_ctrl, ik_thigh_jnt, maintainOffset=True)


            # ------------------------------------------------------------------
            # IK Controls
            # ------------------------------------------------------------------
            # Foot IK Control
            _, ankle_length = self._getPrimaryAxis(ik_ankle_jnt, target_child=ball_joint.split('|')[-1].replace("_bridgeJNT", "_IK_JNT"))
            ankle_length = ankle_length if ankle_length > 0.1 else 2.0
            foot_ik_ctrl = cmds.circle(constructionHistory=False, name=f"{side}_footIK_CTRL", normal=(0,1,0), sections=12, radius=(ankle_length * 1.5))[0]
            foot_ik_sdk = cmds.group(foot_ik_ctrl, name=foot_ik_ctrl + "_SDK")
            foot_ik_zero = cmds.group(foot_ik_sdk, name=foot_ik_ctrl + "_0")
            
            # Snap position to ankle
            temp_const = cmds.pointConstraint(ik_ankle_jnt, foot_ik_zero, maintainOffset=False)
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
            cmds.xform(foot_ik_zero, rotation=(0, y_rot, 0), worldSpace=True)
            
            # Move CVs close to the ground (90% of the way down from ankle to world Y 0) and halfway up the ankle bone
            ankle_y = cmds.xform(ik_ankle_jnt, query=True, translation=True, worldSpace=True)[1]
            cmds.move(0.5 * dx, -ankle_y * 0.9, 0.5 * dz, foot_ik_ctrl + '.cv[*]', relative=True, worldSpace=True)
            cmds.scale(0.5, 1, 1, foot_ik_ctrl + '.cv[*]', relative=True, objectSpace=True)
            
            # Parent IKs to Foot Control
            cmds.parent(foot_ikh, foot_ik_ctrl)
            cmds.parent(ball_ikh, foot_ik_ctrl)
            cmds.parent(toe_ikh, foot_ik_ctrl)
            cmds.parent(foot_ik_zero, legIK_CTRL_GRP)
            
            # Pole Vector Control
            ik_knee_jnt = main_knee.split('|')[-1].replace("Main_JNT", "IK_JNT")
            knee_ik_ctrl = self._createDiamondCurve(f"{side}_kneeIK_CTRL", radius=0.5)
            knee_ik_sdk = cmds.group(knee_ik_ctrl, name=knee_ik_ctrl + "_SDK")
            knee_ik_zero = cmds.group(knee_ik_sdk, name=knee_ik_ctrl + "_0")
            
            # Calculate and set PV position perfectly perpendicular to the hip-ankle line
            pv_pos = self._calculatePoleVectorPos(ik_thigh_jnt, ik_knee_jnt, ik_ankle_jnt, multiplier=thigh_length)
            cmds.xform(knee_ik_zero, translation=pv_pos, worldSpace=True)
            
            # Orient the zero group so its local Z axis points directly away from the knee
            pv_aim = cmds.aimConstraint(ik_knee_jnt, knee_ik_zero, aimVector=(0,0,-1), upVector=(0,1,0), worldUpType="vector", worldUpVector=(0,1,0))[0]
            cmds.delete(pv_aim)
            
            # Install Pole Vector constraint
            cmds.poleVectorConstraint(knee_ik_ctrl, foot_ikh)
            
            # Space Switching
            cmds.addAttr(knee_ik_ctrl, longName="follow", attributeType="enum", enumName="<none>:Foot", keyable=True)
            pv_space_constraint = cmds.parentConstraint(foot_ik_ctrl, knee_ik_zero, maintainOffset=True)[0]
            
            cmds.connectAttr(f"{knee_ik_ctrl}.follow", f"{pv_space_constraint}.{foot_ik_ctrl}W0", force=True)

            # Grouping and organizing
            cmds.parent(knee_ik_zero, legIK_CTRL_GRP)
            leg_common_CTRL_GRP = cmds.group(legFKIK_ctrl_zero, name=f"{side}_legCommon_CTRL_GRP")
            side_leg_CTRL_GRP = cmds.group(leg_common_CTRL_GRP, legIK_CTRL_GRP, legFK_CTRL_GRP, name=f"{side}_leg_CTRL_GRP")
            
            if cmds.objExists("leg_CTRL_GRP"):
                cmds.parent(side_leg_CTRL_GRP, "leg_CTRL_GRP")
            else:
                global_leg_grp = cmds.group(side_leg_CTRL_GRP, name="leg_CTRL_GRP")
                master_ctrl_grp = cmds.ls("CTRL_GRP")
                if master_ctrl_grp:
                    cmds.parent(global_leg_grp, master_ctrl_grp[0])

            # ------------------------------------------------------------------
            # Squash and stretch
            # ------------------------------------------------------------------
            cmds.connectAttr(f"{ik_thigh_jnt}.scaleX", f"{ik_knee_jnt}.scaleX", force=True)
            # create measure distance tools
            thigh_pos = cmds.xform(ik_thigh_jnt, query=True, translation=True, worldSpace=True)
            ankle_pos = cmds.xform(ik_ankle_jnt, query=True, translation=True, worldSpace=True)
            
            cmds.select(clear=True) # Prevent Maya from auto-parenting locators to the active selection
            dist_shape = cmds.distanceDimension(startPoint=thigh_pos, endPoint=ankle_pos)
            dist_node = cmds.listRelatives(dist_shape, parent=True)[0]
            
            locs = cmds.listConnections(dist_shape + ".startPoint")
            legIKTop_LOC = cmds.rename(locs[0], f"{side}_legIKTop_LOC")
            
            locs = cmds.listConnections(dist_shape + ".endPoint")
            legIKBot_LOC = cmds.rename(locs[0], f"{side}_legIKBot_LOC")
            
            legIK_DIST = cmds.rename(dist_node, f"{side}_legIK_DIST")
            
            # Explicitly force them to World Space to override any lingering Maya auto-parenting quirks
            for node in [legIKTop_LOC, legIKBot_LOC, legIK_DIST]:
                try:
                    if cmds.listRelatives(node, parent=True):
                        cmds.parent(node, world=True)
                except Exception:
                    pass
            
            # Constrain locators to drivers to avoid cycles
            cmds.parentConstraint(hip_ctrl, legIKTop_LOC, maintainOffset=True)
            cmds.parentConstraint(foot_ik_ctrl, legIKBot_LOC, maintainOffset=True)
            
            # Group the distance components to keep the outliner clean
            legIK_dist_grp = cmds.group(legIKTop_LOC, legIKBot_LOC, legIK_DIST, name=f"{side}_legIK_DIST_GRP")
            cmds.parent(legIK_dist_grp, legIK_CTRL_GRP)
            
            # --- LOCK & HIDE ATTRIBUTES ---
            t = ['tx', 'ty', 'tz']
            r = ['rx', 'ry', 'rz']
            s = ['sx', 'sy', 'sz']
            v = ['v']
            
            # knee pole vector controls should have rotations, scales, and visibility locked and hidden
            self._lockAndHideAttrs(f"{side}_kneeIK_CTRL", r + s + v)
            
            # FKIK switch controls should have translations, rotations, scales, and visibility locked and hidden
            self._lockAndHideAttrs(f"{side}_LegFKIK_CTRL", t + r + s + v)
            
            # Foot IK control should have scales and visibility locked and hidden.
            self._lockAndHideAttrs(foot_ik_ctrl, s + v)
            
            # Leg FK controls should have scales and visibility locked and hidden.
            for fk_ctrl in [f"{side}_thighFK_CTRL", f"{side}_kneeFK_CTRL", f"{side}_ankleFK_CTRL", f"{side}_ballFK_CTRL"]:
                self._lockAndHideAttrs(fk_ctrl, s + v)
            
            # --- JOINT ORGANIZATION ---
            side_leg_jnt_grp = f"{side}_leg_JNT_GRP"
            if not cmds.objExists(side_leg_jnt_grp):
                cmds.group(empty=True, name=side_leg_jnt_grp)
                
            chains_to_group = [main_thigh_short, fk_thigh, ik_thigh_jnt]
            for j in chains_to_group:
                if cmds.objExists(j):
                    try: cmds.parent(j, side_leg_jnt_grp)
                    except Exception: pass
                        
            if not cmds.objExists("leg_JNT_GRP"):
                cmds.group(empty=True, name="leg_JNT_GRP")
                
            if cmds.objExists(side_leg_jnt_grp):
                try: cmds.parent(side_leg_jnt_grp, "leg_JNT_GRP")
                except Exception: pass
                    
            if not cmds.objExists("JNT_GRP"):
                cmds.group(empty=True, name="JNT_GRP")
                
            if cmds.objExists("leg_JNT_GRP"):
                try: cmds.parent("leg_JNT_GRP", "JNT_GRP")
                except Exception: pass
            
            # Auto-populate Step 5 fields
            if side == 'L':
                cmds.textField(self.stretch_top_loc_field, edit=True, text=legIKTop_LOC)
                cmds.textField(self.stretch_bot_loc_field, edit=True, text=legIKBot_LOC)
                cmds.textField(self.stretch_dist_field, edit=True, text=legIK_DIST)
                cmds.textField(self.stretch_foot_ctrl_field, edit=True, text=foot_ik_ctrl)
                cmds.textField(self.step6_foot_ctrl_field, edit=True, text=foot_ik_ctrl)
                cmds.textField(self.stretch_thigh_ik_field, edit=True, text=ik_thigh_jnt)

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

    def programLeftLegStretch(self, *args):
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
            
            self._programLegStretchLogic("L", top_loc, bot_loc, dist_node, foot_ctrl, thigh_ik, global_scale, recordedMaxLegExtent)
            
            print(f"Recorded Max Leg Extent: {recordedMaxLegExtent}")
            
            # Reset the foot controller back to bind pose
            cmds.setAttr(f"{foot_ctrl}.translate", 0, 0, 0)
            cmds.setAttr(f"{foot_ctrl}.rotate", 0, 0, 0)
            
        except Exception as e:
            full_traceback = traceback.format_exc()
            cmds.error(f"Error programming left leg stretch: {e}\n\nFull Traceback:\n{full_traceback}")

    def _programLegStretchLogic(self, side, top_loc, bot_loc, dist_node, foot_ctrl, thigh_ik, global_scale, recordedMaxLegExtent):
        dist_shape = cmds.listRelatives(dist_node, shapes=True)[0]
        
        # MD for global scale * max extent
        max_scale_md = cmds.createNode("multiplyDivide", name=f"{side}_legIK_maxScale_MD")
        cmds.connectAttr(f"{global_scale}.globalScale", f"{max_scale_md}.input1X", force=True)
        cmds.setAttr(f"{max_scale_md}.input2X", recordedMaxLegExtent)
        
        # MD for distance / (global scale * max extent)
        stretch_ratio_md = cmds.createNode("multiplyDivide", name=f"{side}_legIK_stretchRatio_MD")
        cmds.setAttr(f"{stretch_ratio_md}.operation", 2) # Divide
        cmds.connectAttr(f"{dist_shape}.distance", f"{stretch_ratio_md}.input1X", force=True)
        cmds.connectAttr(f"{max_scale_md}.outputX", f"{stretch_ratio_md}.input2X", force=True)
        
        # Condition node
        stretch_cond = cmds.createNode("condition", name=f"{side}_legIK_stretch_COND")
        cmds.setAttr(f"{stretch_cond}.operation", 3) # Greater or Equal
        cmds.connectAttr(f"{dist_shape}.distance", f"{stretch_cond}.firstTerm", force=True)
        cmds.connectAttr(f"{max_scale_md}.outputX", f"{stretch_cond}.secondTerm", force=True)
        
        cmds.connectAttr(f"{stretch_ratio_md}.outputX", f"{stretch_cond}.colorIfTrueR", force=True)
        cmds.setAttr(f"{stretch_cond}.colorIfFalseR", 1.0)
        
        # Connect result to the thigh IK scaleX
        cmds.connectAttr(f"{stretch_cond}.outColorR", f"{thigh_ik}.scaleX", force=True)
            
    def programLeftArmStretch(self, *args):
        try:
            top_loc = cmds.textField(self.arm_top_loc_text_field, query=True, text=True)
            bot_loc = cmds.textField(self.arm_bot_loc_text_field, query=True, text=True)
            dist_node = cmds.textField(self.arm_dist_text_field, query=True, text=True)
            arm_ctrl = cmds.textField(self.arm_ik_ctrl_text_field, query=True, text=True)
            shld_ik = cmds.textField(self.arm_ik_shld_text_field, query=True, text=True)
            global_scale = cmds.textField(self.arm_global_scale_text_field, query=True, text=True)
            
            if not all([top_loc, bot_loc, dist_node, arm_ctrl, shld_ik, global_scale]):
                cmds.warning("Please populate all fields in Step 9 before running this.")
                return
                
            dist_shape = cmds.listRelatives(dist_node, shapes=True)[0]
            recordedMaxArmExtent = cmds.getAttr(f"{dist_shape}.distance")
            
            self._programArmStretchLogic("L", top_loc, bot_loc, dist_node, arm_ctrl, shld_ik, global_scale, recordedMaxArmExtent)
            
            print(f"Recorded Max Arm Extent: {recordedMaxArmExtent}")
            
            # Reset the arm controller back to bind pose
            cmds.setAttr(f"{arm_ctrl}.translate", 0, 0, 0)
            cmds.setAttr(f"{arm_ctrl}.rotate", 0, 0, 0)
            
        except Exception as e:
            full_traceback = traceback.format_exc()
            cmds.error(f"Error programming left arm stretch: {e}\n\nFull Traceback:\n{full_traceback}")

    def _programArmStretchLogic(self, side, top_loc, bot_loc, dist_node, arm_ctrl, shld_ik, global_scale, recordedMaxArmExtent):
        dist_shape = cmds.listRelatives(dist_node, shapes=True)[0]
        
        # MD for global scale * max extent
        max_scale_md = cmds.createNode("multiplyDivide", name=f"{side}_armIK_maxScale_MD")
        cmds.connectAttr(f"{global_scale}.globalScale", f"{max_scale_md}.input1X", force=True)
        cmds.setAttr(f"{max_scale_md}.input2X", recordedMaxArmExtent)
        
        # MD for distance / (global scale * max extent)
        stretch_ratio_md = cmds.createNode("multiplyDivide", name=f"{side}_armIK_stretchRatio_MD")
        cmds.setAttr(f"{stretch_ratio_md}.operation", 2) # Divide
        cmds.connectAttr(f"{dist_shape}.distance", f"{stretch_ratio_md}.input1X", force=True)
        cmds.connectAttr(f"{max_scale_md}.outputX", f"{stretch_ratio_md}.input2X", force=True)
        
        # Condition node
        stretch_cond = cmds.createNode("condition", name=f"{side}_armIK_stretch_COND")
        cmds.setAttr(f"{stretch_cond}.operation", 3) # Greater or Equal
        cmds.connectAttr(f"{dist_shape}.distance", f"{stretch_cond}.firstTerm", force=True)
        cmds.connectAttr(f"{max_scale_md}.outputX", f"{stretch_cond}.secondTerm", force=True)
        
        cmds.connectAttr(f"{stretch_ratio_md}.outputX", f"{stretch_cond}.colorIfTrueR", force=True)
        cmds.setAttr(f"{stretch_cond}.colorIfFalseR", 1.0)
        
        # Connect result to the shoulder IK scaleX
        cmds.connectAttr(f"{stretch_cond}.outColorR", f"{shld_ik}.scaleX", force=True)
            



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

    def buildLeftFootControls(self, *args):
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
                
            foot_ik_ctrl = cmds.textField(self.step6_foot_ctrl_field, query=True, text=True)
            if not foot_ik_ctrl:
                cmds.warning("Please populate the Foot Controller field in Step 6 before building foot controls.")
                return
                
            heel_pos = cmds.xform(heel_loc, query=True, worldSpace=True, translation=True)
            toe_pos = cmds.xform(toe_loc, query=True, worldSpace=True, translation=True)
            ankle_out_pos = cmds.xform(ankle_out_loc, query=True, worldSpace=True, translation=True)
            ankle_in_pos = cmds.xform(ankle_in_loc, query=True, worldSpace=True, translation=True)
            ball_pos = cmds.xform(ball_loc, query=True, worldSpace=True, translation=True)
            ball_floor_pos = cmds.xform(ball_floor_loc, query=True, worldSpace=True, translation=True)
                
            self._buildFootControlsLogic("L", foot_ik_ctrl, heel_pos, toe_pos, ankle_out_pos, ankle_in_pos, ball_pos, ball_floor_pos)
            
            # --- CLEANUP ---
            # 1. Delete pivot placement locators
            gen_locs = [heel_loc, toe_loc, ankle_out_loc, ankle_in_loc, ball_loc, ball_floor_loc]
            for loc in gen_locs:
                if loc and cmds.objExists(loc):
                    cmds.delete(loc)
            
            print("Foot Control Hierarchy Built Successfully!")

        except Exception as e:
            full_traceback = traceback.format_exc()
            cmds.error(f"Error building left foot controls: {e}\n\nFull Traceback:\n{full_traceback}")
        finally:
            cmds.undoInfo(closeChunk=True)

    def _buildFootControlsLogic(self, side, foot_ik_ctrl, heel_pos, toe_pos, ankle_out_pos, ankle_in_pos, ball_pos, ball_floor_pos):
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
                
            heel_ctrl, heel_sdk, heel_zero = create_ctrl(f"{side}_heel_CTRL", 1.0, crescent=True, rotate_cvs=(0, 180, 0))
            toe_ctrl, toe_sdk, toe_zero = create_ctrl(f"{side}_toePivot_CTRL", 0.75, crescent=True, translate_cvs=(0, 0, 0))
            ankle_out_ctrl, ankle_out_sdk, ankle_out_zero = create_ctrl(f"{side}_ankleOut_CTRL", 0.75, crescent=True, rotate_cvs=(0, 90, 0))
            ankle_in_ctrl, ankle_in_sdk, ankle_in_zero = create_ctrl(f"{side}_ankleIn_CTRL", 0.75, crescent=True, rotate_cvs=(0, -90, 0))
            ball_floor_ctrl, ball_floor_sdk, ball_floor_zero = create_ctrl(f"{side}_ballPivot_CTRL", 0.25, crescent=False, rotate_cvs=(-90, 0, 0), translate_cvs=(0, 1.5, 0))
            foot_roll_ctrl, foot_roll_sdk, foot_roll_zero = create_ctrl(f"{side}_footRoll_CTRL", 0.6, crescent=True, rotate_cvs=(-90, 0, 0), translate_cvs=(0, 0.3, 0))
            toe_wiggle_ctrl, toe_wiggle_sdk, toe_wiggle_zero = create_ctrl(f"{side}_toeWiggle_CTRL", 0.25, crescent=False, translate_cvs=(0, 0, 2.0))
            
            def snap_zero(zero_grp, pos):
                pos_list = list(pos)
                if side == "R":
                    pos_list[0] = -pos_list[0]
                    
                cmds.xform(zero_grp, worldSpace=True, translation=pos_list)
                
                # Match orientation perfectly to the Foot Controller
                temp_const = cmds.orientConstraint(foot_ik_ctrl, zero_grp, maintainOffset=False)
                cmds.delete(temp_const)
                
            snap_zero(heel_zero, heel_pos)
            snap_zero(toe_zero, toe_pos)
            snap_zero(ankle_out_zero, ankle_out_pos)
            snap_zero(ankle_in_zero, ankle_in_pos)
            snap_zero(ball_floor_zero, ball_floor_pos)
            snap_zero(foot_roll_zero, ball_pos)
            snap_zero(toe_wiggle_zero, ball_pos)

            cmds.parent(heel_zero, foot_ik_ctrl)
            cmds.parent(ball_floor_zero, heel_ctrl)
            cmds.parent(toe_zero, ball_floor_ctrl)
            cmds.parent(ankle_out_zero, toe_ctrl)
            cmds.parent(ankle_in_zero, ankle_out_ctrl)
            cmds.parent(foot_roll_zero, ankle_in_ctrl)
            cmds.parent(toe_wiggle_zero, ankle_in_ctrl)
            
            try:
                cmds.parent(f"{side}_foot_IKH", foot_roll_ctrl)
                cmds.parent(f"{side}_ball_IKH", ankle_in_ctrl)
                cmds.parent(f"{side}_toe_IKH", toe_wiggle_ctrl)
                
                cmds.setAttr(f"{side}_foot_IKH.v", 0)
                cmds.setAttr(f"{side}_ball_IKH.v", 0)
                cmds.setAttr(f"{side}_toe_IKH.v", 0)
            except Exception as e:
                cmds.warning(f"Could not re-parent or hide IK handles directly. Ensure they exist with standard names: {e}")
                
            print("Foot Control Hierarchy Built Successfully!")

            if not cmds.attributeQuery("footCTRLVIS", node=foot_ik_ctrl, exists=True):
                cmds.addAttr(foot_ik_ctrl, longName="footCTRLVIS", attributeType="enum", enumName="Off:On", keyable=False)
            cmds.setAttr(f"{foot_ik_ctrl}.footCTRLVIS", channelBox=True)
            
            # foot controls are parented to only need to connectr top level visibility
            cmds.connectAttr(f"{foot_ik_ctrl}.footCTRLVIS", f"{heel_zero}.v")

            # Add foot control attributes
            foot_attrs = ["footRoll", "ankleRoll", "toeRoll", "heelPivot", "ballPivot", "toePivot", "toeWiggle"]
            for attr in foot_attrs:
                if not cmds.attributeQuery(attr, node=foot_ik_ctrl, exists=True):
                    cmds.addAttr(foot_ik_ctrl, longName=attr, attributeType="float", keyable=True)
            
            # Setup SetDrivenKeys for foot attributes
            # Format: (driver_attr, target_node, target_attr, keys_list, pre_infinity, post_infinity)
            sdks = [
                ("footRoll", foot_roll_sdk, "rx", [(0, 0), (10, 40)], "constant", "cycleRelative"),
                ("footRoll", heel_sdk, "rx", [(-10, -40), (0, 0)], "cycleRelative", "constant"),
                ("ankleRoll", ankle_out_sdk, "rz", [(0, 0), (10, -40)], "constant", "cycleRelative"),
                ("ankleRoll", ankle_in_sdk, "rz", [(-10, 40), (0, 0)], "cycleRelative", "constant"),
                ("toeRoll", toe_sdk, "rx", [(0, 0), (10, 40)], "cycleRelative", "cycleRelative"),
                ("heelPivot", heel_sdk, "ry", [(0, 0), (10, 40)], "cycleRelative", "cycleRelative"),
                ("ballPivot", ball_floor_sdk, "ry", [(0, 0), (10, 40)], "cycleRelative", "cycleRelative"),
                ("toePivot", toe_sdk, "ry", [(0, 0), (10, 40)], "cycleRelative", "cycleRelative"),
                ("toeWiggle", toe_wiggle_sdk, "rx", [(0, 0), (10, 40)], "cycleRelative", "cycleRelative"),
            ]
            
            cmds.select(clear=True)
            attrs_to_invert = ["ankleRoll", "heelPivot", "ballPivot", "toePivot"]
            for driver_attr, target_node, target_attr, keys, pre_inf, post_inf in sdks:
                for drv_val, target_val in keys:
                    
                    if side == "R" and driver_attr in attrs_to_invert:
                        target_val = -target_val
                        
                    cmds.setDrivenKeyframe(
                        f"{target_node}.{target_attr}", 
                        currentDriver=f"{foot_ik_ctrl}.{driver_attr}", 
                        driverValue=drv_val, 
                        value=target_val, 
                        inTangentType="linear", 
                        outTangentType="linear"
                    )
                # Apply explicit pre and post infinity bounds
                cmds.setInfinity(target_node, attribute=target_attr, preInfinite=pre_inf, postInfinite=post_inf)

            # Re-parent LegIKBot_LOC if it exists to allow leg stretch during foot roll
            if cmds.objExists(f"{side}_legIKBot_LOC"):
                # Find existing parent constraints on the locator and delete them
                existing_constraints = cmds.listRelatives(f"{side}_legIKBot_LOC", type="parentConstraint")
                if existing_constraints:
                    cmds.delete(existing_constraints)
                
                # Add new parent constraint to footRoll control
                cmds.parentConstraint(foot_roll_ctrl, f"{side}_legIKBot_LOC", maintainOffset=True)

            # --- LOCK & HIDE ATTRIBUTES ---
            t = ['tx', 'ty', 'tz']
            r = ['rx', 'ry', 'rz']
            s = ['sx', 'sy', 'sz']
            v = ['v']
            
            # The heel control should have translations, rotateZ, scales, and visibility locked and hidden
            self._lockAndHideAttrs(f"{side}_heel_CTRL", t + ['rz'] + s + v)
            
            # The ankle in and out should both have translations, rotateX, rotateY, scales and visibility locked and hidden.
            self._lockAndHideAttrs(f"{side}_ankleIn_CTRL", t + ['rx', 'ry'] + s + v)
            self._lockAndHideAttrs(f"{side}_ankleOut_CTRL", t + ['rx', 'ry'] + s + v)
            
            # The foot roll control should have translations, rotateY, rotateZ, scales and visibility locked and hidden.
            self._lockAndHideAttrs(f"{side}_footRoll_CTRL", t + ['ry', 'rz'] + s + v)
            
            # The ball floor pivot control should have translations rotateX, rotateZ, scales, and visiblity locked and hidden
            self._lockAndHideAttrs(f"{side}_ballPivot_CTRL", t + ['rx', 'rz'] + s + v)
            
            # The toe pivot control should have translations, rotateX, rotateZ, scales, and visibility locked and hidden.
            self._lockAndHideAttrs(f"{side}_toePivot_CTRL", t + ['rx', 'rz'] + s + v)
            
            # The toe wiggle control should have translations, rotateY, rotateZ, scales and visibility locked and hidden
            self._lockAndHideAttrs(f"{side}_toeWiggle_CTRL", t + ['ry', 'rz'] + s + v)

            # --- ORGANIZATION ---
            # 1. Organize Leg IK Distance nodes
            if cmds.objExists(f"{side}_legIK_DIST_GRP"):
                if not cmds.objExists("legIK_DIST_GRP"):
                    cmds.group(empty=True, name="legIK_DIST_GRP")
                try: cmds.parent(f"{side}_legIK_DIST_GRP", "legIK_DIST_GRP")
                except: pass

            if not cmds.objExists("leg_MISC_GRP"):
                cmds.group(empty=True, name="leg_MISC_GRP")
            if cmds.objExists("legIK_DIST_GRP"):
                try: cmds.parent("legIK_DIST_GRP", "leg_MISC_GRP")
                except: pass

            if not cmds.objExists("MISC_GRP"):
                cmds.group(empty=True, name="MISC_GRP")
            if cmds.objExists("leg_MISC_GRP"):
                try: cmds.parent("leg_MISC_GRP", "MISC_GRP")
                except: pass
                
            # 3. Organize Joint Chains
            chains_to_group = [f"{side}_upLeg_Main_JNT", f"{side}_upLeg_FK_JNT", f"{side}_upLeg_IK_JNT"]
            if any(cmds.objExists(j) for j in chains_to_group):
                if not cmds.objExists(f"{side}_leg_JNT_GRP"):
                    cmds.group(empty=True, name=f"{side}_leg_JNT_GRP")
                for j in chains_to_group:
                    if cmds.objExists(j):
                        try: cmds.parent(j, f"{side}_leg_JNT_GRP")
                        except: pass
                        
            if not cmds.objExists("leg_JNT_GRP"):
                cmds.group(empty=True, name="leg_JNT_GRP")
            if cmds.objExists(f"{side}_leg_JNT_GRP"):
                try: cmds.parent(f"{side}_leg_JNT_GRP", "leg_JNT_GRP")
                except: pass
                
            if not cmds.objExists("JNT_GRP"):
                cmds.group(empty=True, name="JNT_GRP")
            if cmds.objExists("leg_JNT_GRP"):
                try: cmds.parent("leg_JNT_GRP", "JNT_GRP")
                except: pass

    def _buildArmLogic(self, side, spine_tip, clavicle, shoulder, wrist):
        # 0. Clavicle Setup
        clav_pos = cmds.xform(clavicle, query=True, worldSpace=True, translation=True)
        shoulder_pos = cmds.xform(shoulder, query=True, worldSpace=True, translation=True)
        diff_x = shoulder_pos[0] - clav_pos[0]
        diff_y = shoulder_pos[1] - clav_pos[1]
        diff_z = shoulder_pos[2] - clav_pos[2]
        clav_len = math.sqrt(diff_x**2 + diff_y**2 + diff_z**2)
        
        clav_ctrl = self._createArrowCurve(f"{side}_clavicle_CTRL", size=clav_len * 0.5)
        clav_zero, clav_sdk = self._groupOverAlign(clav_ctrl, clavicle)
        
        up_vec = self._getLocalAxisToWorld(clavicle, (0, 1, 0)) # World Up
        
        rot_offset = self._getDynamicRotation(up_vec)
        cmds.xform(clav_ctrl + ".cv[*]", rotation=rot_offset, relative=True)
        
        cmds.xform(clav_ctrl + ".cv[*]", translation=(diff_x, diff_y, diff_z), relative=True, worldSpace=True)
        
        offset_x = up_vec[0] * clav_len
        offset_y = up_vec[1] * clav_len
        offset_z = up_vec[2] * clav_len
        cmds.xform(clav_ctrl + ".cv[*]", translation=(offset_x, offset_y, offset_z), relative=True, objectSpace=True)
        
        cmds.parentConstraint(clav_ctrl, clavicle, maintainOffset=False)
        self._lockAndHideAttrs(clav_ctrl, ['sx', 'sy', 'sz', 'v'])
        
        clav_locator = cmds.spaceLocator(name=clav_ctrl + "_spaceLOC")[0]
        cmds.setAttr(clav_locator + ".v", 0)
        temp_const = cmds.parentConstraint(clavicle, clav_locator, maintainOffset=False)
        cmds.delete(temp_const)
        
        cmds.parent(clav_locator, spine_tip)
        
        cmds.pointConstraint(clav_locator, clav_zero, maintainOffset=False)
        orient_const_clav = cmds.orientConstraint(clav_locator, clav_zero, maintainOffset=False)[0]
        
        cmds.addAttr(clav_ctrl, longName="orient", attributeType="enum", enumName="<none>:Chest", keyable=True)
        cmds.connectAttr(clav_ctrl + ".orient", orient_const_clav + "." + clav_locator.split('|')[-1] + "W0", force=True)
        cmds.setAttr(clav_ctrl + ".orient", 1)
        
        if cmds.objExists("clavicle_CTRL_GRP"):
            cmds.parent(clav_zero, "clavicle_CTRL_GRP")
        else:
            global_clav_grp = cmds.group(clav_zero, name="clavicle_CTRL_GRP")
            master_ctrl_grp = cmds.ls("CTRL_GRP")
            if master_ctrl_grp:
                cmds.parent(global_clav_grp, master_ctrl_grp[0])

        # 1. Duplicate shoulder to wrist
        shoulder_dupes = cmds.duplicate(shoulder)
        top_arm_node = shoulder_dupes[0]
        
        # Clean up the duplicated hierarchy to only include joints
        arm_hierarchy = cmds.listRelatives(top_arm_node, allDescendents=True, fullPath=True) or []
        arm_hierarchy.append(top_arm_node)
        
        # Rename to Main_JNT
        main_shoulder_long = self._renameHierarchy(arm_hierarchy, "_bridgeJNT", "Main_JNT")
        main_shoulder_short = shoulder.split('|')[-1].replace("_bridgeJNT", "Main_JNT")
        main_wrist_short = wrist.split('|')[-1].replace("_bridgeJNT", "Main_JNT")
        
        # Delete any children below the wrist (like fingers) so they don't propagate into FK/IK chains
        wrist_children = cmds.listRelatives(main_wrist_short, children=True, fullPath=True) or []
        if wrist_children:
            cmds.delete(wrist_children)
        
        # Get path from wrist to shoulder
        curr = main_wrist_short
        path_to_shoulder = [curr]
        safe_count = 0
        while curr != main_shoulder_short and safe_count < 100:
            parent = cmds.listRelatives(curr, parent=True)
            if not parent:
                cmds.error("Wrist is not a descendant of Shoulder")
                return
            curr = parent[0].split('|')[-1]
            path_to_shoulder.append(curr)
            safe_count += 1
            
        path_to_shoulder.reverse() # [shoulder, midShoulder, elbow, forearm, wrist]
        
        if len(path_to_shoulder) != 5:
            cmds.warning("Expected exactly 5 joints from Shoulder to Wrist. Found {} joints.".format(len(path_to_shoulder)))
            
        main_shoulder = path_to_shoulder[0]
        main_mid_shoulder = path_to_shoulder[1]
        main_elbow = path_to_shoulder[2]
        main_forearm = path_to_shoulder[3]
        main_wrist = path_to_shoulder[4]
        
        # Reorganize Main chain
        cmds.parent(main_elbow, main_shoulder)
        cmds.parent(main_wrist, main_elbow)
        
        main_joints_no_mid = [main_shoulder, main_elbow, main_wrist]
        # Any child of the wrist gets brought along
        wrist_descendants = cmds.listRelatives(main_wrist, allDescendents=True, type="joint") or []
        for desc in wrist_descendants:
            main_joints_no_mid.append(desc.split('|')[-1])
            
        # Point constrain mid joints
        cmds.pointConstraint(main_shoulder, main_elbow, main_mid_shoulder, maintainOffset=False)
        cmds.pointConstraint(main_elbow, main_wrist, main_forearm, maintainOffset=False)
        
        # Parent constrain & scale bridge joints to main joints
        # We use path_to_shoulder here to ensure the mid joints are included
        for jnt in path_to_shoulder:
            bridge_jnt = jnt.replace("Main_JNT", "_bridgeJNT")
            if cmds.objExists(bridge_jnt):
                self._parentConstraintAndScale(jnt, bridge_jnt)
                
        # Create FK chain
        fk_dupes = cmds.duplicate(main_shoulder)
        fk_shoulder = fk_dupes[0]
        
        fk_hierarchy = cmds.listRelatives(fk_shoulder, allDescendents=True, fullPath=True) or []
        fk_hierarchy.append(fk_shoulder)
        fk_shoulder = self._renameHierarchy(fk_hierarchy, "Main_JNT", "FK_JNT")
        
        # Delete mid joints from FK chain
        fk_mid_shoulder = main_mid_shoulder.replace("Main_JNT", "FK_JNT")
        fk_forearm = main_forearm.replace("Main_JNT", "FK_JNT")
        if cmds.objExists(fk_mid_shoulder):
            cmds.delete(fk_mid_shoulder)
        if cmds.objExists(fk_forearm):
            cmds.delete(fk_forearm)
            
        # Create IK chain
        ik_dupes = cmds.duplicate(fk_shoulder)
        ik_shoulder = ik_dupes[0]
        
        ik_hierarchy = cmds.listRelatives(ik_shoulder, allDescendents=True, fullPath=True) or []
        ik_hierarchy.append(ik_shoulder)
        ik_shoulder_jnt = self._renameHierarchy(ik_hierarchy, "FK_JNT", "IK_JNT")
        
        # Parent constrain Main to FK and IK
        shoulder_constraint = None
        fk_shoulder_short = None
        ik_shoulder_short = None
        
        for main_jnt in main_joints_no_mid:
            fk_jnt = main_jnt.replace("Main_JNT", "FK_JNT")
            ik_jnt = main_jnt.replace("Main_JNT", "IK_JNT")
            
            if cmds.objExists(fk_jnt) and cmds.objExists(ik_jnt):
                constraint = cmds.parentConstraint(fk_jnt, ik_jnt, main_jnt, maintainOffset=False)[0]
                
                fk_short = fk_jnt.split('|')[-1]
                ik_short = ik_jnt.split('|')[-1]
                
                if not shoulder_constraint:
                    shoulder_constraint = constraint
                    fk_shoulder_short = fk_short
                    ik_shoulder_short = ik_short
                else:
                    fk_src = "{}.{}W0".format(shoulder_constraint, fk_shoulder_short)
                    ik_src = "{}.{}W1".format(shoulder_constraint, ik_shoulder_short)
                    
                    fk_dst = "{}.{}W0".format(constraint, fk_short)
                    ik_dst = "{}.{}W1".format(constraint, ik_short)
                    
                    cmds.connectAttr(fk_src, fk_dst, force=True)
                    cmds.connectAttr(ik_src, ik_dst, force=True)

        # FKIK Switch Controller
        armFKIK_ctrl = self._createPlusCurve(f"{side}_armFKIK_CTRL", (0,1,0), 0.5)
        armFKIK_ctrl_zero, armFKIK_ctrl_sdk = self._groupOverAlign(armFKIK_ctrl, main_wrist)
        
        # Move CVs back an amount in object space Y
        cmds.move(0, -3, 0, armFKIK_ctrl + '.cv[*]', relative=True, objectSpace=True)
        
        # Constrain FK/IK switch to the wrist so it moves with the hand
        cmds.parentConstraint(main_wrist, armFKIK_ctrl_zero, maintainOffset=True)
        if not cmds.attributeQuery("FKIK", node=armFKIK_ctrl, exists=True):
            cmds.addAttr(armFKIK_ctrl, longName="FKIK", niceName= "FK/IK", attributeType="float", minValue=0, maxValue=1, defaultValue=1.0, keyable=True)
            
        # Connect FKIK switch to shoulder parent constraint
        if shoulder_constraint and ik_shoulder_short and fk_shoulder_short:
            ik_weight_attr = "{}.{}W1".format(shoulder_constraint, ik_shoulder_short)
            fk_weight_attr = "{}.{}W0".format(shoulder_constraint, fk_shoulder_short)
            
            cmds.connectAttr(armFKIK_ctrl + ".FKIK", ik_weight_attr, force=True)
            
            arm_rev_node = cmds.createNode("reverse", name=armFKIK_ctrl + "_FK_REV")
            cmds.connectAttr(armFKIK_ctrl + ".FKIK", arm_rev_node + ".inputX", force=True)
            cmds.connectAttr(arm_rev_node + ".outputX", fk_weight_attr, force=True)
        else:
            cmds.error("Unable to connect FK/IK switch to shoulder parent constraint")
            return
            
        # Lock and hide attributes on FKIK switch
        t = ['tx', 'ty', 'tz']
        r = ['rx', 'ry', 'rz']
        s = ['sx', 'sy', 'sz']
        v = ['v']
        self._lockAndHideAttrs(armFKIK_ctrl, t + r + s + v)
        
        # Create visibility groups for arm
        armCommon_CTRL_GRP = cmds.group(empty=True, name=f"{side}_armCommon_CTRL_GRP", world=True)
        armFK_CTRL_GRP = cmds.group(empty=True, name=f"{side}_armFK_CTRL_GRP", world=True)
        armIK_CTRL_GRP = cmds.group(empty=True, name=f"{side}_armIK_CTRL_GRP", world=True)
        
        cmds.parent(armFKIK_ctrl_zero, armCommon_CTRL_GRP)
        
        cmds.connectAttr(arm_rev_node + ".outputX", armFK_CTRL_GRP + ".visibility", force=True)
        cmds.connectAttr(armFKIK_ctrl + ".FKIK", armIK_CTRL_GRP + ".visibility", force=True)
        
        side_arm_CTRL_GRP = cmds.group(armCommon_CTRL_GRP, armIK_CTRL_GRP, armFK_CTRL_GRP, name=f"{side}_arm_CTRL_GRP")
        
        if cmds.objExists("arm_CTRL_GRP"):
            cmds.parent(side_arm_CTRL_GRP, "arm_CTRL_GRP")
        else:
            global_arm_grp = cmds.group(side_arm_CTRL_GRP, name="arm_CTRL_GRP")
            master_ctrl_grp = cmds.ls("CTRL_GRP")
            if master_ctrl_grp:
                cmds.parent(global_arm_grp, master_ctrl_grp[0])
        
        # Create FK Controls
        fk_shoulder_jnt = main_shoulder.replace("Main_JNT", "FK_JNT")
        fk_elbow_jnt = main_elbow.replace("Main_JNT", "FK_JNT")
        fk_wrist_jnt = main_wrist.replace("Main_JNT", "FK_JNT")
        
        # Shoulder FK
        shld_normal, shld_len = self._getPrimaryAxis(fk_shoulder_jnt, target_child=fk_elbow_jnt)
        shld_len = shld_len if shld_len > 0.1 else 2.0
        shld_fk_ctrl = cmds.circle(constructionHistory=False, name=f"{side}_shoulderFK_CTRL", normal=shld_normal, radius=(shld_len * 0.25))[0]
        shld_fk_zero, shld_fk_sdk = self._groupOverAlign(shld_fk_ctrl, fk_shoulder_jnt)
        cmds.parentConstraint(shld_fk_ctrl, fk_shoulder_jnt, maintainOffset=False)
        cmds.addAttr(shld_fk_ctrl, longName="length", attributeType="float", defaultValue=1, keyable=True)
        
        # Shoulder Space Switching
        shld_locator = cmds.spaceLocator(name=f"{side}_shoulderFK_CTRL_LOC")[0]
        cmds.setAttr(shld_locator + ".v", 0)
        temp_const = cmds.parentConstraint(fk_shoulder_jnt, shld_locator, maintainOffset=False)
        cmds.delete(temp_const)
        
        cmds.parent(shld_locator, clav_ctrl)
        
        cmds.pointConstraint(shld_locator, shld_fk_zero, maintainOffset=False)
        orient_const_shld = cmds.orientConstraint(shld_locator, shld_fk_zero, maintainOffset=False)[0]
        
        cmds.addAttr(shld_fk_ctrl, longName="orient", attributeType="enum", enumName="<none>:Clavicle", keyable=True)
        cmds.connectAttr(shld_fk_ctrl + ".orient", orient_const_shld + "." + shld_locator.split('|')[-1] + "W0", force=True)
        cmds.setAttr(shld_fk_ctrl + ".orient", 1)
        
        # Elbow FK
        elbow_normal, elbow_len = self._getPrimaryAxis(fk_elbow_jnt, target_child=fk_wrist_jnt)
        elbow_len = elbow_len if elbow_len > 0.1 else 2.0
        elbow_fk_ctrl = cmds.circle(constructionHistory=False, name=f"{side}_elbowFK_CTRL", normal=elbow_normal, radius=(elbow_len * 0.25))[0]
        elbow_fk_zero, elbow_fk_sdk = self._groupOverAlign(elbow_fk_ctrl, fk_elbow_jnt)
        cmds.parentConstraint(elbow_fk_ctrl, fk_elbow_jnt, maintainOffset=False)
        cmds.addAttr(elbow_fk_ctrl, longName="length", attributeType="float", defaultValue=1, keyable=True)
        
        # Wrist FK
        # Since the wrist has no children anymore, we explicitly orient it down X 
        # and size it relative to the elbow so it doesn't become tiny.
        wrist_normal = (1, 0, 0)
        wrist_fk_ctrl = cmds.circle(constructionHistory=False, name=f"{side}_wristFK_CTRL", normal=wrist_normal, radius=(elbow_len * 0.25))[0]
        wrist_fk_zero, wrist_fk_sdk = self._groupOverAlign(wrist_fk_ctrl, fk_wrist_jnt)
        cmds.parentConstraint(wrist_fk_ctrl, fk_wrist_jnt, maintainOffset=False)
        
        # Parent FK controls
        cmds.parent(wrist_fk_zero, elbow_fk_ctrl)
        cmds.parent(elbow_fk_zero, shld_fk_ctrl)
        cmds.parent(shld_fk_zero, armFK_CTRL_GRP)
        
        # Set up SDK for length
        self._setupLengthSDK(shld_fk_ctrl, elbow_fk_sdk, fk_shoulder_jnt)
        self._setupLengthSDK(elbow_fk_ctrl, wrist_fk_sdk, fk_elbow_jnt)
        
        # Lock and hide scale and visibility
        for ctrl in [shld_fk_ctrl, elbow_fk_ctrl, wrist_fk_ctrl]:
            self._lockAndHideAttrs(ctrl, ['sx', 'sy', 'sz', 'v'])
            
        # ------------------------------------------------------------------
        # IK Chain Setup
        # ------------------------------------------------------------------
        ik_shoulder_jnt = main_shoulder.replace("Main_JNT", "IK_JNT")
        ik_elbow_jnt = main_elbow.replace("Main_JNT", "IK_JNT")
        ik_wrist_jnt = main_wrist.replace("Main_JNT", "IK_JNT")
        
        # Shoulder to Wrist (Rotate Plane Solver)
        arm_ikh, arm_eff = cmds.ikHandle(startJoint=ik_shoulder_jnt, endEffector=ik_wrist_jnt, solver="ikRPsolver", sticky="sticky", name=f"{side}_arm_IKH")
        cmds.rename(arm_eff, f"{side}_arm_EFF")
        cmds.setAttr(f"{arm_ikh}.v", 0)
        
        # Clavicle drives IK shoulder
        cmds.parentConstraint(clav_ctrl, ik_shoulder_jnt, maintainOffset=True)
        
        # ------------------------------------------------------------------
        # IK Controls
        # ------------------------------------------------------------------
        # Wrist IK Control (Cube)
        wrist_ik_ctrl = self._createCubeCurve(f"{side}_armIK_CTRL", radius=(elbow_len * 0.25))
        wrist_ik_zero, wrist_ik_sdk = self._groupOverAlign(wrist_ik_ctrl, ik_wrist_jnt)
        # scale wrist down in X to be more narrow along wrist
        cmds.scale(0.5, 1, 1, wrist_ik_ctrl + '.cv[*]', relative=True, objectSpace=True)
        
        cmds.parent(arm_ikh, wrist_ik_ctrl)
        cmds.orientConstraint(wrist_ik_ctrl, ik_wrist_jnt, maintainOffset=False)
        cmds.parent(wrist_ik_zero, armIK_CTRL_GRP)
        
        # Space Switching for Wrist IK -> Clavicle
        cmds.addAttr(wrist_ik_ctrl, longName="follow", attributeType="enum", enumName="<none>:Clavicle", keyable=True)
        armIK_space_constraint = cmds.parentConstraint(clav_ctrl, wrist_ik_zero, maintainOffset=True)[0]
        cmds.connectAttr(f"{wrist_ik_ctrl}.follow", f"{armIK_space_constraint}.{clav_ctrl}W0", force=True)
        
        # Pole Vector Control (Elbow)
        elbow_ik_ctrl = self._createDiamondCurve(f"{side}_elbowIK_CTRL", radius=(0.25))
        elbow_ik_sdk = cmds.group(elbow_ik_ctrl, name=elbow_ik_ctrl + "_SDK")
        elbow_ik_zero = cmds.group(elbow_ik_sdk, name=elbow_ik_ctrl + "_0")
        
        pv_pos = self._calculatePoleVectorPos(ik_shoulder_jnt, ik_elbow_jnt, ik_wrist_jnt, multiplier=shld_len)
        cmds.xform(elbow_ik_zero, translation=pv_pos, worldSpace=True)
        
        pv_aim = cmds.aimConstraint(ik_elbow_jnt, elbow_ik_zero, aimVector=(0,0,-1), upVector=(0,1,0), worldUpType="vector", worldUpVector=(0,1,0))[0]
        cmds.delete(pv_aim)
        
        cmds.poleVectorConstraint(elbow_ik_ctrl, arm_ikh)
        cmds.parent(elbow_ik_zero, armIK_CTRL_GRP)
        
        # Space Switching for Elbow PV -> Wrist IK
        cmds.addAttr(elbow_ik_ctrl, longName="follow", attributeType="enum", enumName="<none>:Wrist", keyable=True)
        pv_space_constraint = cmds.parentConstraint(wrist_ik_ctrl, elbow_ik_zero, maintainOffset=True)[0]
        cmds.connectAttr(f"{elbow_ik_ctrl}.follow", f"{pv_space_constraint}.{wrist_ik_ctrl}W0", force=True)
        
        # Lock and hide attributes
        self._lockAndHideAttrs(wrist_ik_ctrl, ['sx', 'sy', 'sz', 'v'])
        self._lockAndHideAttrs(elbow_ik_ctrl, ['rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v'])

        # ------------------------------------------------------------------
        # Squash and stretch preparation
        # ------------------------------------------------------------------
        cmds.connectAttr(f"{ik_shoulder_jnt}.scaleX", f"{ik_elbow_jnt}.scaleX", force=True)
        # create measure distance tools
        shld_pos = cmds.xform(ik_shoulder_jnt, query=True, translation=True, worldSpace=True)
        wrist_pos = cmds.xform(ik_wrist_jnt, query=True, translation=True, worldSpace=True)
        
        cmds.select(clear=True) # Prevent Maya from auto-parenting locators to the active selection
        dist_shape = cmds.distanceDimension(startPoint=shld_pos, endPoint=wrist_pos)
        dist_node = cmds.listRelatives(dist_shape, parent=True)[0]
        
        locs = cmds.listConnections(dist_shape + ".startPoint")
        armIKTop_LOC = cmds.rename(locs[0], f"{side}_armIKTop_LOC")
        
        locs = cmds.listConnections(dist_shape + ".endPoint")
        armIKBot_LOC = cmds.rename(locs[0], f"{side}_armIKBot_LOC")
        
        armIK_DIST = cmds.rename(dist_node, f"{side}_armIK_DIST")
        
        # Explicitly force them to World Space to override any lingering Maya auto-parenting quirks
        for node in [armIKTop_LOC, armIKBot_LOC, armIK_DIST]:
            try:
                if cmds.listRelatives(node, parent=True):
                    cmds.parent(node, world=True)
            except Exception:
                pass
        
        # Constrain locators to drivers to avoid cycles
        cmds.parentConstraint(clav_ctrl, armIKTop_LOC, maintainOffset=True)
        cmds.parentConstraint(wrist_ik_ctrl, armIKBot_LOC, maintainOffset=True)
        
        # Group the distance components to keep the outliner clean
        armIK_dist_grp = cmds.group(armIKTop_LOC, armIKBot_LOC, armIK_DIST, name=f"{side}_armIK_DIST_GRP")
        
        # Organize into MISC_GRP
        if not cmds.objExists("armIK_DIST_GRP"):
            cmds.group(empty=True, name="armIK_DIST_GRP")
        try: cmds.parent(armIK_dist_grp, "armIK_DIST_GRP")
        except Exception: pass
            
        if not cmds.objExists("arm_MISC_GRP"):
            cmds.group(empty=True, name="arm_MISC_GRP")
        
        if "arm_MISC_GRP" not in (cmds.listRelatives("armIK_DIST_GRP", parent=True) or []):
            try: cmds.parent("armIK_DIST_GRP", "arm_MISC_GRP")
            except Exception: pass
            
        if not cmds.objExists("MISC_GRP"):
            cmds.group(empty=True, name="MISC_GRP")
            
        if "MISC_GRP" not in (cmds.listRelatives("arm_MISC_GRP", parent=True) or []):
            try: cmds.parent("arm_MISC_GRP", "MISC_GRP")
            except Exception: pass
            
        # Optional: ensure MISC_GRP is under all_GRP
        if cmds.objExists("all_GRP") and "all_GRP" not in (cmds.listRelatives("MISC_GRP", parent=True) or []):
            try: cmds.parent("MISC_GRP", "all_GRP")
            except Exception: pass


        # ------------------------------------------------------------------
        # Joint Grouping
        # ------------------------------------------------------------------
        side_arm_jnt_grp = f"{side}_arm_JNT_GRP"
        if not cmds.objExists(side_arm_jnt_grp):
            cmds.group(empty=True, name=side_arm_jnt_grp)
            
        for j in [main_shoulder, fk_shoulder_jnt, ik_shoulder_jnt]:
            if cmds.objExists(j):
                try: cmds.parent(j, side_arm_jnt_grp)
                except Exception: pass
                
        if not cmds.objExists("arm_JNT_GRP"):
            cmds.group(empty=True, name="arm_JNT_GRP")
            
        if cmds.objExists(side_arm_jnt_grp):
            try: cmds.parent(side_arm_jnt_grp, "arm_JNT_GRP")
            except Exception: pass
            
        if not cmds.objExists("JNT_GRP"):
            cmds.group(empty=True, name="JNT_GRP")
            
        if cmds.objExists("arm_JNT_GRP"):
            try: cmds.parent("arm_JNT_GRP", "JNT_GRP")
            except Exception: pass

    def buildLeftArm(self, *args):
        spine_tip = cmds.textField(self.arm_spine_tip_text_field, query=True, text=True)
        l_clavicle = cmds.textField(self.l_clavicle_joint_text_field, query=True, text=True)
        l_shoulder = cmds.textField(self.l_shoulder_joint_text_field, query=True, text=True)
        l_wrist = cmds.textField(self.l_wrist_joint_text_field, query=True, text=True)
        
        if not all([spine_tip, l_clavicle, l_shoulder, l_wrist]):
            cmds.warning("Please populate all fields in Step 8 before building the left arm.")
            return
            
        cmds.undoInfo(openChunk=True)
        try:
            self._buildArmLogic("L", spine_tip, l_clavicle, l_shoulder, l_wrist)
            
            # Auto populate Step 9 fields
            if cmds.objExists("L_armIKTop_LOC"):
                cmds.textField(self.arm_top_loc_text_field, edit=True, text="L_armIKTop_LOC")
            if cmds.objExists("L_armIKBot_LOC"):
                cmds.textField(self.arm_bot_loc_text_field, edit=True, text="L_armIKBot_LOC")
            if cmds.objExists("L_armIK_DIST"):
                cmds.textField(self.arm_dist_text_field, edit=True, text="L_armIK_DIST")
            if cmds.objExists("L_shoulderIK_JNT"):
                cmds.textField(self.arm_ik_shld_text_field, edit=True, text="L_shoulderIK_JNT")
            if cmds.objExists("L_armIK_CTRL"):
                cmds.textField(self.arm_ik_ctrl_text_field, edit=True, text="L_armIK_CTRL")
            if cmds.objExists("all_CTRL"):
                cmds.textField(self.arm_global_scale_text_field, edit=True, text="all_CTRL")
        except Exception as e:
            full_traceback = traceback.format_exc()
            cmds.error(f"Error building arm: {e}\n\nFull Traceback:\n{full_traceback}")
        finally:
            cmds.undoInfo(closeChunk=True)

    def buildLeftHandControls(self, *args):
        try:
            cmds.undoInfo(openChunk=True)
            l_wrist = cmds.textField(self.hand_wrist_joint_text_field, query=True, text=True)
            if not l_wrist:
                cmds.warning("Please populate the wrist joint field in Step 10.")
                return
            
            self._buildHandControlsLogic("L", l_wrist)
            
        except Exception as e:
            full_traceback = traceback.format_exc()
            cmds.error(f"Error building hand controls: {e}\n\nFull Traceback:\n{full_traceback}")
        finally:
            cmds.undoInfo(closeChunk=True)

    def _buildHandControlsLogic(self, side, wrist_joint):
        # Gather all descendants
        descendants = cmds.listRelatives(wrist_joint, allDescendents=True, fullPath=True) or []
        
        # Filter for bridge joints and ignore tips
        finger_joints = []
        for d in descendants:
            short_name = d.split('|')[-1]
            if short_name.endswith("_bridgeJNT") and "Tip" not in short_name:
                finger_joints.append(d)
                
        # Sort by depth to ensure parents are processed before children
        finger_joints.sort(key=lambda x: x.count('|'))

        side_finger_ctrl_grp = cmds.group(empty=True, name=f"{side}_finger_CTRL_GRP")
        cmds.parentConstraint(wrist_joint, side_finger_ctrl_grp, maintainOffset=False)
        if cmds.objExists("finger_CTRL_GRP"):
            cmds.parent(side_finger_ctrl_grp, "finger_CTRL_GRP")
        else:
            global_finger__grp = cmds.group(side_finger_ctrl_grp, name="finger_CTRL_GRP")
            master_ctrl_grp = cmds.ls("CTRL_GRP")
            if master_ctrl_grp:
                cmds.parent(global_finger__grp, master_ctrl_grp[0])
                
        # Mapping joint full path to its controller transform
        ctrl_mapping = {}
        
        for jnt in finger_joints:
            short_name = jnt.split('|')[-1]
            base_name = short_name.replace("_bridgeJNT", "")
            ctrl_name = f"{base_name}_CTRL"
            
            # Determine length (distance to first child)
            children = cmds.listRelatives(jnt, children=True, fullPath=True) or []
            length = 1.0
            if children:
                pos1 = cmds.xform(jnt, query=True, worldSpace=True, translation=True)
                pos2 = cmds.xform(children[0], query=True, worldSpace=True, translation=True)
                diff_x = pos2[0] - pos1[0]
                diff_y = pos2[1] - pos1[1]
                diff_z = pos2[2] - pos1[2]
                length = math.sqrt(diff_x**2 + diff_y**2 + diff_z**2)
                
            radius = length * 0.6
            
            is_base = "Base" in base_name
            if is_base:
                ctrl = self._createSphereCurve(ctrl_name, radius=(radius * 0.6))
            else:
                ctrl = cmds.circle(name=ctrl_name, normal=(1, 0, 0), radius=radius, constructionHistory=False)[0]
                
            ctrl_zero, ctrl_sdk = self._groupOverAlign(ctrl, jnt)
            
            if is_base:
                cmds.xform(ctrl + ".cv[*]", translation=(0, 0, length * -1.25), relative=True, objectSpace=True)
                
            # Parent constraint to joint
            cmds.parentConstraint(ctrl, jnt, maintainOffset=False)
            self._lockAndHideAttrs(ctrl, ['tx', 'ty', 'tz', 'sx', 'sy', 'sz', 'v'])
            
            # FK parenting
            parent_jnt = cmds.listRelatives(jnt, parent=True, fullPath=True)
            if parent_jnt and parent_jnt[0] in ctrl_mapping:
                cmds.parent(ctrl_zero, ctrl_mapping[parent_jnt[0]])
            else:
                cmds.parent(ctrl_zero, side_finger_ctrl_grp)
                
            ctrl_mapping[jnt] = ctrl
            
        # Create Finger Preset Controller
        preset_ctrl_name = f"{side}_fingerPreset_CTRL"
        preset_ctrl = self._createHandCurve(preset_ctrl_name, normal=(1, 0, 0), radius=1.0)
        preset_zero, preset_sdk = self._groupOverAlign(preset_ctrl, wrist_joint)
        
        # Move away in object -Z
        cmds.move(0, 0, -3.0, preset_ctrl + '.cv[*]', relative=True, objectSpace=True)
        
        # Constrain zero group to wrist
        cmds.parentConstraint(wrist_joint, preset_zero, maintainOffset=True)
        
        # Add attributes
        preset_attrs = ['curl', 'scrunch', 'relax', 'spread', 'thumbSpread']
        for attr in preset_attrs:
            cmds.addAttr(preset_ctrl, longName=attr, attributeType="float", keyable=True)
            
        # Lock and hide transforms
        self._lockAndHideAttrs(preset_ctrl, ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v'])
        
        cmds.parent(preset_zero, side_finger_ctrl_grp)
        
        # Auto populate step 11 fields
        cmds.textField(self.finger_preset_ctrl_field, edit=True, text=preset_ctrl_name)
        cmds.textField(self.finger_sdk_grp_field, edit=True, text=side_finger_ctrl_grp)
        

    def _recordFingerPreset(self, attribute, *args):
        preset_ctrl = cmds.textField(self.finger_preset_ctrl_field, query=True, text=True)
        finger_grp = cmds.textField(self.finger_sdk_grp_field, query=True, text=True)
        
        if not preset_ctrl or not cmds.objExists(preset_ctrl):
            cmds.warning("Preset Control not found. Please populate Step 11.")
            return
            
        if not finger_grp or not cmds.objExists(finger_grp):
            cmds.warning("Finger SDK Group not found. Please populate Step 11.")
            return
            
        if not cmds.attributeQuery(attribute, node=preset_ctrl, exists=True):
            cmds.warning(f"Attribute '{attribute}' does not exist on {preset_ctrl}.")
            return
            
        # Find all _SDK groups under finger_grp
        descendants = cmds.listRelatives(finger_grp, allDescendents=True, type="transform") or []
        sdk_groups = [d for d in descendants if d.endswith("_SDK")]
        
        if not sdk_groups:
            cmds.warning(f"No _SDK groups found under {finger_grp}.")
            return
            
        cmds.undoInfo(openChunk=True)
        try:
            pose_data = {}
            for sdk in sdk_groups:
                ctrls = cmds.listRelatives(sdk, children=True, type="transform") or []
                if not ctrls: continue
                ctrl = ctrls[0]
                
                # Add control and SDK transforms together so the user can pose either one.
                pose_data[sdk] = {
                    'tx': cmds.getAttr(f"{ctrl}.tx") + cmds.getAttr(f"{sdk}.tx"),
                    'ty': cmds.getAttr(f"{ctrl}.ty") + cmds.getAttr(f"{sdk}.ty"),
                    'tz': cmds.getAttr(f"{ctrl}.tz") + cmds.getAttr(f"{sdk}.tz"),
                    'rx': cmds.getAttr(f"{ctrl}.rx") + cmds.getAttr(f"{sdk}.rx"),
                    'ry': cmds.getAttr(f"{ctrl}.ry") + cmds.getAttr(f"{sdk}.ry"),
                    'rz': cmds.getAttr(f"{ctrl}.rz") + cmds.getAttr(f"{sdk}.rz")
                }
                
            # Key rest pose at 0.0
            cmds.setAttr(f"{preset_ctrl}.{attribute}", 0.0)
            for sdk in sdk_groups:
                for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
                    cmds.setDrivenKeyframe(f"{sdk}.{attr}", currentDriver=f"{preset_ctrl}.{attribute}", driverValue=0.0, value=0.0)
                    
            # Key max pose at 10.0
            cmds.setAttr(f"{preset_ctrl}.{attribute}", 10.0)
            for sdk in sdk_groups:
                ctrls = cmds.listRelatives(sdk, children=True, type="transform") or []
                ctrl = ctrls[0] if ctrls else None
                
                for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
                    val = pose_data[sdk][attr]
                    cmds.setDrivenKeyframe(f"{sdk}.{attr}", currentDriver=f"{preset_ctrl}.{attribute}", driverValue=10.0, value=val)
                    
                    # Zero out the control since the pose is now driven by the SDK!
                    if ctrl:
                        try:
                            cmds.setAttr(f"{ctrl}.{attr}", 0.0)
                        except Exception:
                            pass
                            
            # Set pre and post infinity to cycle with offset
            anim_curves = cmds.listConnections(f"{preset_ctrl}.{attribute}", type="animCurve")
            if anim_curves:
                cmds.setInfinity(anim_curves, pri="cycleRelative", poi="cycleRelative")
                            
            # Restore to 0.0
            cmds.setAttr(f"{preset_ctrl}.{attribute}", 0.0)
            
            cmds.inViewMessage(amg=f'<hl>Recorded</hl>: {attribute.capitalize()} preset recorded successfully.', pos='midCenter', fade=True)
            
        except Exception as e:
            full_traceback = traceback.format_exc()
            cmds.error(f"Failed to record finger preset: {e}\n\nFull Traceback:\n{full_traceback}")
        finally:
            cmds.undoInfo(closeChunk=True)

    def mirrorLeg(self, *args):
        hip_ctrl = cmds.textField(self.hip_ctrl_text_field, query=True, text=True)
        r_thigh_joint = cmds.textField(self.r_thigh_joint_text_field, query=True, text=True)
        r_ankle_joint = cmds.textField(self.r_ankle_joint_text_field, query=True, text=True)
        r_ball_joint = cmds.textField(self.r_ball_joint_text_field, query=True, text=True)
        r_toe_joint = cmds.textField(self.r_toe_joint_text_field, query=True, text=True)
        
        if not (r_thigh_joint and r_ankle_joint and r_ball_joint and r_toe_joint and hip_ctrl):
            cmds.error("Please specify Hip Control, Right Thigh, Ankle, Ball, and Toe Tip joints in Step 7.")
            return

        try:
            cmds.undoInfo(openChunk=True)
            
            # 1. Build the base right leg joints and FK/IK rig
            self._buildLegLogic("R", r_thigh_joint, r_ankle_joint, r_ball_joint, r_toe_joint, hip_ctrl)
            
            # 2. Mirror CV shapes from Left to Right
            controls_to_mirror = [
                "thighFK_CTRL", "kneeFK_CTRL", "ankleFK_CTRL", "ballFK_CTRL",
                "LegFKIK_CTRL", "footIK_CTRL", "kneeIK_CTRL"
            ]
            for ctrl in controls_to_mirror:
                self._mirrorControlShape(f"L_{ctrl}", f"R_{ctrl}")
                
            # 3. Program Leg Stretch
            left_max_scale_md = "L_legIK_maxScale_MD"
            if cmds.objExists(left_max_scale_md):
                recorded_max_extent = cmds.getAttr(f"{left_max_scale_md}.input2X")
                
                r_top_loc = "R_legIKTop_LOC"
                r_bot_loc = "R_legIKBot_LOC"
                r_dist_node = "R_legIK_DIST"
                r_foot_ctrl = "R_footIK_CTRL"
                r_thigh_ik = r_thigh_joint.split('|')[-1].replace("_bridgeJNT", "IK_JNT")
                global_scale = cmds.textField(self.stretch_global_scale_field, query=True, text=True)
                
                self._programLegStretchLogic("R", r_top_loc, r_bot_loc, r_dist_node, r_foot_ctrl, r_thigh_ik, global_scale, recorded_max_extent)
            else:
                cmds.warning("Could not find L_legIK_maxScale_MD. Skipping right leg stretch programming.")
                
            # 4. Build Foot Controls
            l_heel_ctrl = "L_heel_CTRL"
            l_toe_ctrl = "L_toePivot_CTRL"
            l_ankle_out_ctrl = "L_ankleOut_CTRL"
            l_ankle_in_ctrl = "L_ankleIn_CTRL"
            l_ball_ctrl = "L_footRoll_CTRL"
            l_ball_floor_ctrl = "L_ballPivot_CTRL"
            
            if cmds.objExists(l_heel_ctrl):
                heel_pos = cmds.xform(l_heel_ctrl, query=True, worldSpace=True, rotatePivot=True)
                toe_pos = cmds.xform(l_toe_ctrl, query=True, worldSpace=True, rotatePivot=True)
                ankle_out_pos = cmds.xform(l_ankle_out_ctrl, query=True, worldSpace=True, rotatePivot=True)
                ankle_in_pos = cmds.xform(l_ankle_in_ctrl, query=True, worldSpace=True, rotatePivot=True)
                ball_pos = cmds.xform(l_ball_ctrl, query=True, worldSpace=True, rotatePivot=True)
                ball_floor_pos = cmds.xform(l_ball_floor_ctrl, query=True, worldSpace=True, rotatePivot=True)
                
                self._buildFootControlsLogic("R", "R_footIK_CTRL", heel_pos, toe_pos, ankle_out_pos, ankle_in_pos, ball_pos, ball_floor_pos)
                
                # Mirror CV shapes for foot controls
                foot_controls_to_mirror = [
                    "heel_CTRL", "toePivot_CTRL", "ankleOut_CTRL", "ankleIn_CTRL",
                    "ballPivot_CTRL", "footRoll_CTRL", "toeWiggle_CTRL"
                ]
                for ctrl in foot_controls_to_mirror:
                    self._mirrorControlShape(f"L_{ctrl}", f"R_{ctrl}")
            else:
                cmds.warning("Left side foot controls missing. Skipping right foot controls.")
                
        except Exception as e:
            full_traceback = traceback.format_exc()
            cmds.error(f"Error mirroring leg: {e}\n\nFull Traceback:\n{full_traceback}")
        finally:
            cmds.undoInfo(closeChunk=True)

    def mirrorArm(self, *args):
        spine_tip = cmds.textField(self.r_arm_spine_tip_text_field, query=True, text=True)
        r_clavicle = cmds.textField(self.r_clavicle_joint_text_field, query=True, text=True)
        r_shoulder = cmds.textField(self.r_shoulder_joint_text_field, query=True, text=True)
        r_wrist = cmds.textField(self.r_wrist_joint_text_field, query=True, text=True)
        
        if not all([spine_tip, r_clavicle, r_shoulder, r_wrist]):
            cmds.warning("Please populate all fields in Step 12 before mirroring the arm.")
            return
            
        try:
            cmds.undoInfo(openChunk=True)
            
            # 1. Build Base Arm Logic
            self._buildArmLogic("R", spine_tip, r_clavicle, r_shoulder, r_wrist)
            
            # 2. Mirror Control Shapes
            controls_to_mirror = [
                "clavicle_CTRL", "shoulderFK_CTRL", "elbowFK_CTRL", "wristFK_CTRL",
                "armFKIK_CTRL", "armIK_CTRL", "elbowIK_CTRL"
            ]
            for ctrl in controls_to_mirror:
                self._mirrorControlShape(f"L_{ctrl}", f"R_{ctrl}")
                
            # 3. Program Arm Stretch
            left_max_scale_md = "L_armIK_maxScale_MD"
            if cmds.objExists(left_max_scale_md):
                recorded_max_extent = cmds.getAttr(f"{left_max_scale_md}.input2X")
                
                r_top_loc = "R_armIKTop_LOC"
                r_bot_loc = "R_armIKBot_LOC"
                r_dist_node = "R_armIK_DIST"
                r_arm_ctrl = "R_armIK_CTRL"
                r_shld_ik = "R_shoulderIK_JNT"
                global_scale = cmds.textField(self.arm_global_scale_text_field, query=True, text=True)
                
                self._programArmStretchLogic("R", r_top_loc, r_bot_loc, r_dist_node, r_arm_ctrl, r_shld_ik, global_scale, recorded_max_extent)
            else:
                cmds.warning("Could not find L_armIK_maxScale_MD. Skipping right arm stretch programming.")
                
            # 4. Build Hand Controls
            self._buildHandControlsLogic("R", r_wrist)
            
            # 5. Mirror Hand Control Shapes
            # Get all finger controls on left side
            left_finger_grp = "L_finger_CTRL_GRP"
            if cmds.objExists(left_finger_grp):
                descendants = cmds.listRelatives(left_finger_grp, allDescendents=True, type="transform") or []
                left_ctrls = [d for d in descendants if d.endswith("_CTRL")]
                for l_ctrl in left_ctrls:
                    r_ctrl = l_ctrl.replace("L_", "R_", 1)
                    if cmds.objExists(r_ctrl):
                        self._mirrorControlShape(l_ctrl, r_ctrl)
            
            # 6. Copy SDK values from left to right
            l_preset_ctrl = "L_fingerPreset_CTRL"
            r_preset_ctrl = "R_fingerPreset_CTRL"
            if cmds.objExists(l_preset_ctrl) and cmds.objExists(r_preset_ctrl):
                preset_attrs = ['curl', 'scrunch', 'relax', 'spread', 'thumbSpread']
                
                for attr in preset_attrs:
                    # Key rest pose at 0
                    cmds.setAttr(f"{r_preset_ctrl}.{attr}", 0.0)
                    r_sdk_groups = [d for d in cmds.listRelatives("R_finger_CTRL_GRP", allDescendents=True, type="transform") or [] if d.endswith("_SDK")]
                    for r_sdk in r_sdk_groups:
                        for transform_attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
                            cmds.setDrivenKeyframe(f"{r_sdk}.{transform_attr}", currentDriver=f"{r_preset_ctrl}.{attr}", driverValue=0.0, value=0.0)
                
                for attr in preset_attrs:
                    # Temporarily evaluate left preset at 10 to grab poses
                    original_val = cmds.getAttr(f"{l_preset_ctrl}.{attr}")
                    cmds.setAttr(f"{l_preset_ctrl}.{attr}", 10.0)
                    
                    # Read left SDK poses
                    l_sdk_groups = [d for d in cmds.listRelatives("L_finger_CTRL_GRP", allDescendents=True, type="transform") or [] if d.endswith("_SDK")]
                    pose_data = {}
                    for l_sdk in l_sdk_groups:
                        pose_data[l_sdk] = {
                            'tx': cmds.getAttr(f"{l_sdk}.tx"),
                            'ty': cmds.getAttr(f"{l_sdk}.ty"),
                            'tz': cmds.getAttr(f"{l_sdk}.tz"),
                            'rx': cmds.getAttr(f"{l_sdk}.rx"),
                            'ry': cmds.getAttr(f"{l_sdk}.ry"),
                            'rz': cmds.getAttr(f"{l_sdk}.rz")
                        }
                    
                    # Restore left preset
                    cmds.setAttr(f"{l_preset_ctrl}.{attr}", original_val)
                    
                    # Set right preset to 10.0 and apply mirrored poses
                    cmds.setAttr(f"{r_preset_ctrl}.{attr}", 10.0)
                    
                    for r_sdk in r_sdk_groups:
                        l_sdk = r_sdk.replace("R_", "L_", 1)
                        if l_sdk in pose_data:
                            # Apply the specific mirroring math: negate translations, keep rotations
                            mirrored_tx = pose_data[l_sdk]['tx'] * -1
                            mirrored_ty = pose_data[l_sdk]['ty'] * -1
                            mirrored_tz = pose_data[l_sdk]['tz'] * -1
                            mirrored_rx = pose_data[l_sdk]['rx']
                            mirrored_ry = pose_data[l_sdk]['ry']
                            mirrored_rz = pose_data[l_sdk]['rz']
                            
                            cmds.setDrivenKeyframe(f"{r_sdk}.tx", currentDriver=f"{r_preset_ctrl}.{attr}", driverValue=10.0, value=mirrored_tx)
                            cmds.setDrivenKeyframe(f"{r_sdk}.ty", currentDriver=f"{r_preset_ctrl}.{attr}", driverValue=10.0, value=mirrored_ty)
                            cmds.setDrivenKeyframe(f"{r_sdk}.tz", currentDriver=f"{r_preset_ctrl}.{attr}", driverValue=10.0, value=mirrored_tz)
                            cmds.setDrivenKeyframe(f"{r_sdk}.rx", currentDriver=f"{r_preset_ctrl}.{attr}", driverValue=10.0, value=mirrored_rx)
                            cmds.setDrivenKeyframe(f"{r_sdk}.ry", currentDriver=f"{r_preset_ctrl}.{attr}", driverValue=10.0, value=mirrored_ry)
                            cmds.setDrivenKeyframe(f"{r_sdk}.rz", currentDriver=f"{r_preset_ctrl}.{attr}", driverValue=10.0, value=mirrored_rz)
                            
                    # Set cycleRelative infinity
                    anim_curves = cmds.listConnections(f"{r_preset_ctrl}.{attr}", type="animCurve")
                    if anim_curves:
                        cmds.setInfinity(anim_curves, pri="cycleRelative", poi="cycleRelative")
                                    
                    # Restore right preset to 0
                    cmds.setAttr(f"{r_preset_ctrl}.{attr}", 0.0)
                    
            cmds.inViewMessage(amg='<hl>Right Arm</hl>: Mirrored Successfully.', pos='midCenter', fade=True)
            
        except Exception as e:
            full_traceback = traceback.format_exc()
            cmds.error(f"Error mirroring arm: {e}\n\nFull Traceback:\n{full_traceback}")
        finally:
            cmds.undoInfo(closeChunk=True)

    def _mirrorControlShape(self, l_ctrl, r_ctrl):
        if not cmds.objExists(l_ctrl) or not cmds.objExists(r_ctrl):
            cmds.warning(f"Skipping shape mirror: {l_ctrl} or {r_ctrl} does not exist.")
            return
            
        l_shapes = cmds.listRelatives(l_ctrl, shapes=True) or []
        r_shapes = cmds.listRelatives(r_ctrl, shapes=True) or []
        
        for s_idx, l_shape in enumerate(l_shapes):
            if s_idx >= len(r_shapes):
                break
                
            r_shape = r_shapes[s_idx]
            num_cvs = cmds.getAttr(l_shape + ".cp", size=True)
            
            if not num_cvs:
                continue
                
            for i in range(num_cvs):
                # Get world space position of left CV
                l_pos = cmds.xform(f"{l_shape}.cv[{i}]", query=True, translation=True, worldSpace=True)
                # Mirror across YZ plane (invert world X)
                r_pos = (-l_pos[0], l_pos[1], l_pos[2])
                # Set world space position of right CV
                cmds.xform(f"{r_shape}.cv[{i}]", translation=r_pos, worldSpace=True)

if __name__ == "__main__":
    ui = ControlRigUI()
    ui.show()
