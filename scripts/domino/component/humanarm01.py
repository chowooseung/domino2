# domino
from domino import component
from domino.core import attribute, Name, Transform, Joint, rigkit, Surface
from domino.core.utils import build_log

# maya
from maya.api import OpenMaya as om
from maya import cmds

# built-ins
import logging

# gui
from PySide6 import QtWidgets


# region Initialize Settings
ORIGINMATRIX = om.MMatrix()
matrices = []
m = om.MMatrix()
tm0 = om.MTransformationMatrix(m)
tm0.setTranslation(
    om.MVector((0.2713483983280126, 14.817113835622706, -0.21733299595141725)),
    om.MSpace.kObject,
)
matrices.append(list(tm0.asMatrix()))

tm1 = om.MTransformationMatrix(m)
tm1.setTranslation(
    om.MVector((1.6375206610699022, -0.46228491902835245, 0.0)), om.MSpace.kObject
)
radians = [
    om.MAngle(x, om.MAngle.kDegrees).asRadians() for x in (0.0, 0.0, -64.38074188099554)
]
euler_rot = om.MEulerRotation(radians, om.MEulerRotation.kXYZ)
tm1.setRotation(euler_rot)
matrices.append(list(tm1.asMatrix() * tm0.asMatrix()))

tm2 = om.MTransformationMatrix(m)
tm2.setTranslation(
    om.MVector((2.986188866176552, 0.0, 0.0)),
    om.MSpace.kObject,
)
radians = [
    om.MAngle(x, om.MAngle.kDegrees).asRadians()
    for x in (0.0, -12.303827536691916, 0.0)
]
euler_rot = om.MEulerRotation(radians, om.MEulerRotation.kXYZ)
tm2.setRotation(euler_rot)
matrices.append(list(tm2.asMatrix() * tm1.asMatrix() * tm0.asMatrix()))

tm3 = om.MTransformationMatrix(m)
tm3.setTranslation(
    om.MVector((2.5550001731058107, 0.0, 0.0)),
    om.MSpace.kObject,
)
matrices.append(list(tm3.asMatrix() * tm2.asMatrix() * tm1.asMatrix() * tm0.asMatrix()))

tm4 = om.MTransformationMatrix(m)
tm4.setTranslation(om.MVector((0.7532275625127223, 0.0, 0.0)), om.MSpace.kObject)
matrices.append(
    list(
        tm4.asMatrix()
        * tm3.asMatrix()
        * tm2.asMatrix()
        * tm1.asMatrix()
        * tm0.asMatrix()
    )
)

matrices.append(list(tm0.asMatrix()))

tm6 = om.MTransformationMatrix(m)
tm6.setTranslation(
    om.MVector((1.383837182993473, -0.3763373064937685, -0.29592414776586956)),
    om.MSpace.kObject,
)
radians = [
    om.MAngle(x, om.MAngle.kDegrees).asRadians()
    for x in (3.596721910740145, 153.54807469808893, 8.032006443550973)
]
euler_rot = om.MEulerRotation(radians, om.MEulerRotation.kXYZ)
tm6.setRotation(euler_rot)
matrices.append(list(tm6.asMatrix() * tm0.asMatrix()))

tm7 = om.MTransformationMatrix(m)
tm7.setTranslation(om.MVector((2.0, 0.0, 0.0)), om.MSpace.kObject)
matrices.append(list(tm7.asMatrix() * tm6.asMatrix() * tm0.asMatrix()))

tm8 = om.MTransformationMatrix(m)
tm8.setTranslation(om.MVector((0.0, -2.0, 0.0)), om.MSpace.kObject)
matrices.append(list(tm8.asMatrix() * tm6.asMatrix() * tm0.asMatrix()))

DATA = [
    attribute.String(longName="component", value="humanarm01"),
    attribute.String(longName="name", value="humanArm"),
    attribute.Enum(longName="side", enumName=Name.side_list, value=0),
    attribute.Integer(longName="index", minValue=0),
    attribute.Matrix(longName="guide_matrix", multi=True, value=matrices),
    attribute.Matrix(longName="npo_matrix", multi=True, value=matrices[:9]),
    attribute.Matrix(
        longName="initialize_output_matrix",
        multi=True,
        value=matrices,
    ),
    attribute.Matrix(
        longName="initialize_output_inverse_matrix",
        multi=True,
        value=matrices,
    ),
    attribute.Integer(
        longName="guide_mirror_type", multi=True, value=[1, 1, 1, 1, 1, 1, 1, 1, 1]
    ),
    # 부모로 사용할 상위 component 의 output index
    attribute.Integer(
        longName="parent_output_index", minValue=-1, defaultValue=-1, value=-1
    ),
    # output joint 생성 option
    attribute.Bool(longName="create_output_joint", value=1),
    attribute.Integer(
        longName="twist_joint_count", minValue=1, defaultValue=2, value=2
    ),
    attribute.Float(
        longName="upper_output_u_values", multi=True, value=[0, 0.3333, 0.6666, 1]
    ),
    attribute.Float(
        longName="lower_output_u_values", multi=True, value=[0, 0.3333, 0.6666, 1]
    ),
    # offset output rotate
    attribute.DoubleAngle(
        longName="offset_output_rotate_x", minValue=-360, maxValue=360
    ),
    attribute.DoubleAngle(
        longName="offset_output_rotate_y", minValue=-360, maxValue=360
    ),
    attribute.DoubleAngle(
        longName="offset_output_rotate_z", minValue=-360, maxValue=360
    ),
    attribute.Float(longName="pole_vector_multiple", value=5),
    attribute.Matrix(longName="pole_vector_matrix", value=list(ORIGINMATRIX)),
    attribute.Bool(longName="align_last_transform_to_guide", defaultValue=0),
    attribute.Bool(longName="unlock_last_scale", defaultValue=0),
    attribute.Matrix(
        longName="driver_inverse_matrix",
        multi=True,
        value=[list(ORIGINMATRIX) for _ in range(6)],
    ),
    attribute.Matrix(
        longName="clavicle_bone_matrix",
        value=list(ORIGINMATRIX),
    ),
    attribute.Float(
        longName="clavicle_bone_distance",
        value=0,
    ),
    attribute.Float(
        longName="scapular_aim_axis_x",
    ),
    attribute.Float(
        longName="scapular_aim_axis_y",
    ),
    attribute.Float(
        longName="scapular_aim_axis_z",
    ),
    attribute.Float(
        longName="scapular_up_axis_x",
    ),
    attribute.Float(
        longName="scapular_up_axis_y",
    ),
    attribute.Float(
        longName="scapular_up_axis_z",
    ),
    attribute.Matrix(
        longName="scapular_aim_matrix",
        value=list(ORIGINMATRIX),
    ),
    attribute.Matrix(
        longName="scapular_up_matrix",
        value=list(ORIGINMATRIX),
    ),
    attribute.NurbsSurface(
        longName="upper_ribbon_surface",
        value={
            "parent_name": "",
            "surface_name": "upperRibbonTempSurface",
            "surface_matrix": [
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
            ],
            "surface": {
                "form_u": 0,
                "form_v": 0,
                "knot_u": [0.0, 0.5, 1.0],
                "knot_v": [0.0, 0.0, 0.0, 0.5, 1.0, 1.0, 1.0],
                "degree_u": 1,
                "degree_v": 3,
                "cvs": [
                    (1.9088690392914205, 14.354828892661422, -0.11733299595143254, 1.0),
                    (2.2316676896787655, 13.681676855189712, -0.11733299595143254, 1.0),
                    (2.5544663400661154, 13.00852481771799, -0.11733299595143253, 1.0),
                    (2.8772649904534626, 12.335372780246278, -0.11733299595143251, 1.0),
                    (3.20006364084081, 11.662220742774565, -0.11733299595143253, 1.0),
                    (1.9088690892002336, 14.354828916594348, -0.21733299595141722, 1.0),
                    (2.231667739587582, 13.681676879122632, -0.21733299595141722, 1.0),
                    (2.554466389974932, 13.008524841650933, -0.21733299595141747, 1.0),
                    (2.877265040362275, 12.33537280417921, -0.21733299595141722, 1.0),
                    (3.200063690749623, 11.662220766707494, -0.21733299595141722, 1.0),
                    (1.9088691391090464, 14.35482894052727, -0.31733299595140185, 1.0),
                    (2.2316677894963934, 13.681676903055562, -0.31733299595140196, 1.0),
                    (2.5544664398837416, 13.008524865583842, -0.31733299595140185, 1.0),
                    (2.877265090271087, 12.335372828112133, -0.31733299595140185, 1.0),
                    (3.200063740658436, 11.662220790640415, -0.31733299595140185, 1.0),
                ],
            },
        },
    ),
    attribute.NurbsSurface(
        longName="lower_ribbon_surface",
        value={
            "parent_name": "",
            "surface_name": "lowerRibbonTempSurface",
            "surface_matrix": [
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
            ],
            "surface": {
                "form_u": 0,
                "form_v": 0,
                "knot_u": [0.0, 0.5, 1.0],
                "knot_v": [0.0, 0.0, 0.0, 0.5, 1.0, 1.0, 1.0],
                "degree_u": 1,
                "degree_v": 3,
                "cvs": [
                    (3.190849749433228, 11.681435047807645, -0.11962986183530845, 1.0),
                    (3.4606944666280897, 11.118711144368435, 0.016484997330898452, 1.0),
                    (3.730539183822951, 10.55598724092923, 0.15259985649710447, 1.0),
                    (4.000383901017809, 9.993263337490019, 0.2887147156633093, 1.0),
                    (4.270228618212672, 9.430539434050807, 0.424829574829517, 1.0),
                    (3.200063817657159, 11.662220508243697, -0.21733299595141722, 1.0),
                    (3.469908534852017, 11.099496604804495, -0.08121813678521213, 1.0),
                    (3.739753252046883, 10.536772701365283, 0.054896722380995966, 1.0),
                    (4.009597969241742, 9.974048797926073, 0.1910115815472015, 1.0),
                    (4.279442686436603, 9.411324894486862, 0.32712644071340824, 1.0),
                    (3.20927788588109, 11.643005968679754, -0.315036130067526, 1.0),
                    (3.4791226030759472, 11.080282065240555, -0.17892127090132195, 1.0),
                    (3.7489673202708156, 10.517558161801338, -0.04280641173511264, 1.0),
                    (4.018812037465672, 9.954834258362128, 0.09330844743109216, 1.0),
                    (4.2886567546605345, 9.392110354922917, 0.22942330659729948, 1.0),
                ],
            },
        },
    ),
]

description = """## fkik01
---

2jnt fkik blend 를 생성합니다.

#### Settings"""

# endregion


class Rig(component.Rig):

    def input_data(self):
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Twist Joint Count")
        label = QtWidgets.QLabel("Twist Count : ")
        line_edit = QtWidgets.QLineEdit()
        ok_btn = QtWidgets.QPushButton("Ok")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)

        layout0 = QtWidgets.QVBoxLayout(dialog)
        layout1 = QtWidgets.QHBoxLayout()
        layout1.addWidget(label)
        layout1.addWidget(line_edit)
        layout2 = QtWidgets.QHBoxLayout()
        layout2.addWidget(ok_btn)
        layout2.addWidget(cancel_btn)
        layout0.addLayout(layout1)
        layout0.addLayout(layout2)

        result = dialog.exec()
        try:
            value = int(line_edit.text())
            self["twist_joint_count"]["value"] = value
            self["upper_output_u_values"]["value"] = [
                v / (value + 1) for v in range(value + 2)
            ]
            self["lower_output_u_values"]["value"] = [
                v / (value + 1) for v in range(value + 2)
            ]
            self["initialize_output_matrix"]["value"] = [
                list(ORIGINMATRIX) for _ in range((value * 2) + 5)
            ]
            self["initialize_output_inverse_matrix"]["value"] = [
                list(ORIGINMATRIX) for _ in range((value * 2) + 5)
            ]
        except:
            return False
        return result

    def __init__(self):
        super().__init__(DATA)

    def populate_controller(self):
        if not self["controller"]:
            self.add_controller(
                description="host",
                parent_controllers=[],
            )
            fk_descriptions = ["clavicle", "clavicleBone", "shoulder", "elbow", "wrist"]
            parent_controllers = [(self.identifier, "host")]
            for description in fk_descriptions:
                self.add_controller(
                    description=description,
                    parent_controllers=parent_controllers,
                )
                parent_controllers = [(self.identifier, description)]

            parent_controllers = [(self.identifier, "clavicleBone")]
            ik_descriptions = ["ikPos", "poleVec", "ik", "ikLocal"]
            for description in ik_descriptions:
                self.add_controller(
                    description=description,
                    parent_controllers=parent_controllers,
                )
                parent_controllers = [(self.identifier, description)]

            self.add_controller(
                description="pin",
                parent_controllers=[(self.identifier, "elbow")],
            )
            self.add_controller(
                description="upperBend",
                parent_controllers=[(self.identifier, "pin")],
            )
            self.add_controller(
                description="lowerBend",
                parent_controllers=[(self.identifier, "pin")],
            )
            self.add_controller(
                description="scapular",
                parent_controllers=[(self.identifier, "clavicleBone")],
            )

    def populate_output(self):
        if not self["output"]:
            self.add_output(description="clavicle", extension=Name.output_extension)
            self.add_output(description="shoulder", extension=Name.output_extension)
            for i in range(self["twist_joint_count"]["value"]):
                self.add_output(
                    description=f"upperTwist{i}", extension=Name.output_extension
                )
            self.add_output(description="elbow", extension=Name.output_extension)
            for i in range(self["twist_joint_count"]["value"]):
                self.add_output(
                    description=f"lowerTwist{i}", extension=Name.output_extension
                )
            self.add_output(description="wrist", extension=Name.output_extension)
            self.add_output(description="scapular", extension=Name.output_extension)

    def populate_output_joint(self):
        if not self["output_joint"]:
            self.add_output_joint(parent_description=None, description="clavicle")
            self.add_output_joint(parent_description="clavicle", description="shoulder")
            parent_description = "shoulder"
            for i in range(self["twist_joint_count"]["value"]):
                description = f"upperTwist{i}"
                self.add_output_joint(
                    parent_description=parent_description, description=description
                )
                parent_description = description
            self.add_output_joint(
                parent_description=parent_description, description="elbow"
            )
            parent_description = "elbow"
            for i in range(self["twist_joint_count"]["value"]):
                description = f"lowerTwist{i}"
                self.add_output_joint(
                    parent_description=parent_description, description=description
                )
                parent_description = description
            self.add_output_joint(
                parent_description=parent_description, description="wrist"
            )
            self.add_output_joint(parent_description="clavicle", description="scapular")

    # region RIG
    @build_log(logging.INFO)
    def rig(self):
        super().rig(description=description)

        name, side, index = self.identifier

        negate_condition = cmds.createNode("condition")
        cmds.connectAttr(f"{self.rig_root}.side", f"{negate_condition}.firstTerm")
        cmds.setAttr(f"{negate_condition}.secondTerm", 2)
        cmds.setAttr(f"{negate_condition}.colorIfTrueR", -1)
        cmds.setAttr(f"{negate_condition}.colorIfFalseR", 1)

        # region RIG - fk / ik
        host_npo, host_ctl = self["controller"][0].create(
            parent=self.rig_root,
            shape=(
                self["controller"][0]["shape"]
                if "shape" in self["controller"][0]
                else "host"
            ),
            color=12,
            host=True,
        )
        cmds.setAttr(f"{host_ctl}.tx", lock=True, keyable=False)
        cmds.setAttr(f"{host_ctl}.ty", lock=True, keyable=False)
        cmds.setAttr(f"{host_ctl}.tz", lock=True, keyable=False)
        cmds.setAttr(f"{host_ctl}.rx", lock=True, keyable=False)
        cmds.setAttr(f"{host_ctl}.ry", lock=True, keyable=False)
        cmds.setAttr(f"{host_ctl}.rz", lock=True, keyable=False)
        cmds.setAttr(f"{host_ctl}.rotateOrder", channelBox=False)
        cmds.setAttr(f"{host_ctl}.mirror_type", 1)
        cmds.addAttr(
            host_ctl,
            longName="_scapular",
            attributeType="enum",
            enumName="____________",
            keyable=False,
        )
        cmds.setAttr(f"{host_ctl}._scapular", channelBox=True)
        cmds.addAttr(
            host_ctl,
            longName="auto_scapular",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=0,
            keyable=True,
        )
        cmds.addAttr(
            host_ctl,
            longName="scapular_ctl_visibility",
            attributeType="enum",
            enumName="off:on",
            defaultValue=0,
            keyable=True,
        )
        cmds.addAttr(
            host_ctl,
            longName="_arm",
            attributeType="enum",
            enumName="____________",
            keyable=False,
        )
        cmds.setAttr(f"{host_ctl}._arm", channelBox=True)
        cmds.addAttr(
            host_ctl,
            longName="fkik",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=0,
            keyable=True,
        )
        cmds.addAttr(
            host_ctl,
            longName="armpit_roll",
            attributeType="float",
            defaultValue=0,
            keyable=True,
        )
        cmds.addAttr(
            host_ctl,
            longName="auto_volume",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=0,
            keyable=True,
        )
        cmds.addAttr(
            host_ctl,
            longName="sub_ctls_visibility",
            attributeType="enum",
            enumName="off:on",
            defaultValue=0,
            keyable=True,
        )
        cmds.addAttr(
            host_ctl,
            longName="stretch",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=1,
            keyable=False,
        )
        cmds.addAttr(
            host_ctl,
            longName="squash",
            attributeType="float",
            minValue=0.001,
            maxValue=1,
            defaultValue=1,
            keyable=False,
        )
        clavicle_npo, clavicle_ctl = self["controller"][1].create(
            parent=self.rig_root,
            shape=(
                self["controller"][1]["shape"]
                if "shape" in self["controller"][1]
                else "cube"
            ),
            color=12,
            npo_matrix_index=0,
        )
        cmds.addAttr(
            clavicle_ctl,
            longName="roll",
            attributeType="doubleAngle",
            minValue=-360,
            maxValue=360,
            defaultValue=0,
            keyable=True,
        )
        cmds.addAttr(
            clavicle_ctl,
            longName="clavicle_bone_ctl_visibility",
            attributeType="enum",
            enumName="off:on",
            defaultValue=0,
            keyable=True,
        )
        ins = Transform(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description="claviclePos",
            extension=Name.loc_extension,
        )
        clavicle_pos_loc = ins.create()
        cmds.pointConstraint(clavicle_ctl, clavicle_pos_loc, maintainOffset=False)
        ins = Transform(
            parent=clavicle_ctl,
            name=name,
            side=side,
            index=index,
            description="ikhDriver",
            extension=Name.loc_extension,
        )
        clavicle_ikh_driver = ins.create()
        cmds.setAttr(f"{clavicle_ikh_driver}.t", 0, 0, 0)
        cmds.setAttr(f"{clavicle_ikh_driver}.r", 0, 0, 0)
        cmds.connectAttr(
            f"{self.rig_root}.clavicle_bone_distance", f"{clavicle_ikh_driver}.tx"
        )
        ins = Joint(
            parent=clavicle_pos_loc,
            name=name,
            side=side,
            index=index,
            description="clavicleSC0",
            extension=Name.joint_extension,
            m=ORIGINMATRIX,
        )
        clavicle_sc0_joint = ins.create()
        ins = Joint(
            parent=clavicle_sc0_joint,
            name=name,
            side=side,
            index=index,
            description="clavicleSC1",
            extension=Name.joint_extension,
            m=ORIGINMATRIX,
        )
        clavicle_sc1_joint = ins.create()
        cmds.connectAttr(f"{negate_condition}.outColorR", f"{clavicle_sc1_joint}.tx")
        cmds.setAttr(f"{clavicle_sc0_joint}.t", 0, 0, 0)
        cmds.setAttr(f"{clavicle_sc0_joint}.r", 0, 0, 0)
        cmds.setAttr(f"{clavicle_sc0_joint}.jointOrient", 0, 0, 0)
        clavicle_sc_ikh, _ = cmds.ikHandle(
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="clavicleSC",
                extension=Name.ikh_extension,
            ),
            startJoint=clavicle_sc0_joint,
            endEffector=clavicle_sc1_joint,
            solver="ikSCsolver",
        )
        clavicle_sc_ikh = cmds.parent(clavicle_sc_ikh, self.rig_root)[0]
        cmds.setAttr(f"{clavicle_sc_ikh}.r", 0, 0, 0)
        clavicle_negate_condition = cmds.createNode("condition")
        cmds.connectAttr(
            f"{self.rig_root}.side", f"{clavicle_negate_condition}.firstTerm"
        )
        cmds.setAttr(f"{clavicle_negate_condition}.secondTerm", 2)
        cmds.setAttr(f"{clavicle_negate_condition}.colorIfTrueR", 180)
        cmds.setAttr(f"{clavicle_negate_condition}.colorIfFalseR", 0)
        cmds.hide(clavicle_sc0_joint, clavicle_sc_ikh)
        cmds.connectAttr(
            f"{self.rig_root}.clavicle_bone_matrix",
            f"{clavicle_sc0_joint}.offsetParentMatrix",
        )
        cmds.pointConstraint(clavicle_ikh_driver, clavicle_sc_ikh, maintainOffset=False)
        ins = Transform(
            clavicle_pos_loc,
            name=name,
            side=side,
            index=index,
            description="clavicleSC",
            extension="space",
        )
        clavicle_sc_space = ins.create()
        cmds.connectAttr(
            f"{self.rig_root}.clavicle_bone_matrix",
            f"{clavicle_sc_space}.offsetParentMatrix",
        )
        cmds.setAttr(f"{clavicle_sc_space}.t", 0, 0, 0)
        cmds.setAttr(f"{clavicle_sc_space}.s", 1, 1, 1)
        cmds.connectAttr(f"{clavicle_sc0_joint}.r", f"{clavicle_sc_space}.r")
        clavicle_bone_npo, clavicle_bone_ctl = self["controller"][2].create(
            parent=clavicle_sc_space,
            shape=(
                self["controller"][2]["shape"]
                if "shape" in self["controller"][2]
                else "square"
            ),
            color=12,
        )
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{self.rig_root}.npo_matrix[1]", f"{mult_m}.matrixIn[0]")

        inverse_m = cmds.createNode("inverseMatrix")
        cmds.connectAttr(
            f"{self.rig_root}.clavicle_bone_matrix", f"{inverse_m}.inputMatrix"
        )
        cmds.connectAttr(f"{inverse_m}.outputMatrix", f"{mult_m}.matrixIn[1]")

        pick_m = cmds.createNode("pickMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{pick_m}.inputMatrix")
        cmds.setAttr(f"{pick_m}.useTranslate", 0)
        cmds.connectAttr(
            f"{pick_m}.outputMatrix", f"{clavicle_bone_npo}.offsetParentMatrix"
        )

        multiply = cmds.createNode("multiply")
        cmds.connectAttr(f"{clavicle_ctl}.roll", f"{multiply}.input[0]")
        cmds.setAttr(f"{multiply}.input[1]", -1)
        cmds.connectAttr(f"{multiply}.output", f"{clavicle_bone_npo}.rx")
        for shape in cmds.listRelatives(clavicle_bone_ctl, shapes=True) or []:
            cmds.connectAttr(
                f"{clavicle_ctl}.clavicle_bone_ctl_visibility", f"{shape}.v"
            )

        ins = Transform(
            parent=clavicle_bone_ctl,
            name=name,
            side=side,
            index=index,
            description="clavicleBoneInverse",
            m=ORIGINMATRIX,
        )
        clavicle_bone_npo_inverse = ins.create()
        inverse_m = cmds.createNode("inverseMatrix")
        cmds.connectAttr(f"{self.rig_root}.npo_matrix[1]", f"{inverse_m}.inputMatrix")
        cmds.connectAttr(
            f"{inverse_m}.outputMatrix",
            f"{clavicle_bone_npo_inverse}.offsetParentMatrix",
        )
        cmds.setAttr(f"{clavicle_bone_npo_inverse}.t", 0, 0, 0)
        cmds.setAttr(f"{clavicle_bone_npo_inverse}.r", 0, 0, 0)
        shoulder_npo, shoulder_ctl = self["controller"][3].create(
            parent=clavicle_bone_ctl,
            shape=(
                self["controller"][3]["shape"]
                if "shape" in self["controller"][3]
                else "cube"
            ),
            color=12,
            npo_matrix_index=2,
        )
        cmds.setAttr(f"{shoulder_ctl}.mirror_type", 1)
        ins = Transform(
            parent=shoulder_ctl,
            name=name,
            side=side,
            index=index,
            description="fk0Length",
            m=ORIGINMATRIX,
        )
        shoulder_length_grp = ins.create()
        cmds.setAttr(f"{shoulder_length_grp}.t", 0, 0, 0)
        cmds.setAttr(f"{shoulder_length_grp}.r", 0, 0, 0)
        cmds.addAttr(
            shoulder_ctl,
            longName="length",
            attributeType="float",
            keyable=True,
            defaultValue=0,
        )
        multiply0 = cmds.createNode("multiply")
        cmds.connectAttr(f"{shoulder_ctl}.length", f"{multiply0}.input[0]")
        cmds.connectAttr(f"{negate_condition}.outColorR", f"{multiply0}.input[1]")
        cmds.connectAttr(f"{multiply0}.output", f"{shoulder_length_grp}.tx")

        elbow_npo, elbow_ctl = self["controller"][4].create(
            parent=shoulder_length_grp,
            shape=(
                self["controller"][4]["shape"]
                if "shape" in self["controller"][4]
                else "cube"
            ),
            color=12,
            npo_matrix_index=3,
        )
        cmds.setAttr(f"{elbow_ctl}.rx", lock=True, keyable=False)
        cmds.setAttr(f"{elbow_ctl}.rz", lock=True, keyable=False)
        cmds.setAttr(f"{elbow_ctl}.mirror_type", 1)
        ins = Transform(
            parent=elbow_ctl,
            name=name,
            side=side,
            index=index,
            description="fk1Length",
            m=ORIGINMATRIX,
        )
        elbow_length_grp = ins.create()
        cmds.setAttr(f"{elbow_length_grp}.t", 0, 0, 0)
        cmds.setAttr(f"{elbow_length_grp}.r", 0, 0, 0)
        cmds.addAttr(
            elbow_ctl,
            longName="length",
            attributeType="float",
            keyable=True,
            defaultValue=0,
        )
        multiply0 = cmds.createNode("multiply")
        cmds.connectAttr(f"{elbow_ctl}.length", f"{multiply0}.input[0]")
        cmds.connectAttr(f"{negate_condition}.outColorR", f"{multiply0}.input[1]")
        cmds.connectAttr(f"{multiply0}.output", f"{elbow_length_grp}.tx")

        wrist_npo, wrist_ctl = self["controller"][5].create(
            parent=elbow_length_grp,
            shape=(
                self["controller"][5]["shape"]
                if "shape" in self["controller"][5]
                else "cube"
            ),
            color=12,
            npo_matrix_index=4,
        )
        cmds.setAttr(f"{wrist_ctl}.mirror_type", 1)
        if self["unlock_last_scale"]["value"]:
            cmds.setAttr(f"{wrist_ctl}.sx", lock=False, keyable=True)
            cmds.setAttr(f"{wrist_ctl}.sy", lock=False, keyable=True)
            cmds.setAttr(f"{wrist_ctl}.sz", lock=False, keyable=True)
        else:
            cmds.setAttr(f"{wrist_ctl}.sx", lock=True, keyable=False)
            cmds.setAttr(f"{wrist_ctl}.sy", lock=True, keyable=False)
            cmds.setAttr(f"{wrist_ctl}.sz", lock=True, keyable=False)

        ik_pos_npo, ik_pos_ctl = self["controller"][6].create(
            parent=clavicle_bone_npo_inverse,
            shape=(
                self["controller"][6]["shape"]
                if "shape" in self["controller"][6]
                else "cube"
            ),
            color=12,
            npo_matrix_index=5,
        )
        cmds.setAttr(f"{ik_pos_ctl}.rx", lock=True, keyable=False)
        cmds.setAttr(f"{ik_pos_ctl}.ry", lock=True, keyable=False)
        cmds.setAttr(f"{ik_pos_ctl}.rz", lock=True, keyable=False)
        cmds.setAttr(f"{ik_pos_ctl}.mirror_type", 2)

        pole_vec_npo, pole_vec_ctl = self["controller"][7].create(
            parent=clavicle_bone_npo_inverse,
            shape=(
                self["controller"][7]["shape"]
                if "shape" in self["controller"][7]
                else "cube"
            ),
            color=12,
        )
        cmds.setAttr(f"{pole_vec_ctl}.rx", lock=True, keyable=False)
        cmds.setAttr(f"{pole_vec_ctl}.ry", lock=True, keyable=False)
        cmds.setAttr(f"{pole_vec_ctl}.rz", lock=True, keyable=False)
        cmds.setAttr(f"{pole_vec_ctl}.mirror_type", 2)
        cmds.connectAttr(
            f"{self.rig_root}.pole_vector_matrix", f"{pole_vec_npo}.offsetParentMatrix"
        )
        guideline = cmds.curve(point=((0, 0, 0), (0, 0, 0)), degree=1)
        guideline = cmds.rename(
            guideline,
            Name.create(
                convention=Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                extension="guideline",
            ),
        )
        guideline = cmds.parent(guideline, clavicle_bone_npo_inverse)[0]
        cmds.setAttr(f"{guideline}.overrideEnabled", 1)
        cmds.setAttr(f"{guideline}.overrideDisplayType", 1)
        cmds.setAttr(f"{guideline}.t", 0, 0, 0)
        cmds.setAttr(f"{guideline}.r", 0, 0, 0)

        ins = Joint(
            parent=clavicle_bone_npo_inverse,
            name=name,
            side=side,
            index=index,
            description="ik0",
            extension=Name.joint_extension,
            m=cmds.xform(shoulder_ctl, query=True, matrix=True, worldSpace=True),
            use_joint_convention=False,
        )
        ik0_jnt = ins.create()

        ins = Joint(
            parent=ik0_jnt,
            name=name,
            side=side,
            index=index,
            description="ik1",
            extension=Name.joint_extension,
            m=cmds.xform(elbow_ctl, query=True, matrix=True, worldSpace=True),
            use_joint_convention=False,
        )
        ik1_jnt = ins.create()

        ins = Joint(
            parent=ik1_jnt,
            name=name,
            side=side,
            index=index,
            description="ik2",
            extension=Name.joint_extension,
            m=cmds.xform(wrist_ctl, query=True, matrix=True, worldSpace=True),
            use_joint_convention=False,
        )
        ik2_jnt = ins.create()
        cmds.pointConstraint(ik_pos_ctl, ik0_jnt, maintainOffset=False)
        cmds.hide(ik0_jnt)

        ik_npo, ik_ctl = self["controller"][8].create(
            parent=clavicle_bone_npo_inverse,
            shape=(
                self["controller"][8]["shape"]
                if "shape" in self["controller"][8]
                else "cube"
            ),
            color=12,
            npo_matrix_index=6,
        )
        cmds.setAttr(f"{ik_ctl}.mirror_type", 0)
        if self["unlock_last_scale"]["value"]:
            cmds.setAttr(f"{ik_ctl}.sx", lock=False, keyable=True)
            cmds.setAttr(f"{ik_ctl}.sy", lock=False, keyable=True)
            cmds.setAttr(f"{ik_ctl}.sz", lock=False, keyable=True)
        else:
            cmds.setAttr(f"{ik_ctl}.sx", lock=True, keyable=False)
            cmds.setAttr(f"{ik_ctl}.sy", lock=True, keyable=False)
            cmds.setAttr(f"{ik_ctl}.sz", lock=True, keyable=False)

        cmds.addAttr(
            ik_ctl,
            longName="ik_scale",
            attributeType="float",
            minValue=0,
            defaultValue=1,
            keyable=True,
        )
        cmds.addAttr(
            ik_ctl,
            longName="slide",
            attributeType="float",
            minValue=-1,
            maxValue=1,
            defaultValue=0,
            keyable=True,
        )
        cmds.addAttr(
            ik_ctl,
            longName="soft_ik",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=0,
            keyable=True,
        )
        cmds.addAttr(
            ik_ctl,
            longName="max_stretch",
            attributeType="float",
            minValue=1,
            defaultValue=1,
            keyable=True,
        )
        cmds.addAttr(
            ik_ctl,
            longName="attach_to_PV",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=0,
            keyable=True,
        )

        ik_local_npo, ik_local_ctl = self["controller"][9].create(
            parent=ik_ctl,
            shape=(
                self["controller"][9]["shape"]
                if "shape" in self["controller"][9]
                else "cube"
            ),
            color=12,
            npo_matrix_index=7,
        )
        if self["unlock_last_scale"]["value"]:
            cmds.setAttr(f"{ik_local_ctl}.sx", lock=False, keyable=True)
            cmds.setAttr(f"{ik_local_ctl}.sy", lock=False, keyable=True)
            cmds.setAttr(f"{ik_local_ctl}.sz", lock=False, keyable=True)
        else:
            cmds.setAttr(f"{ik_local_ctl}.sx", lock=True, keyable=False)
            cmds.setAttr(f"{ik_local_ctl}.sy", lock=True, keyable=False)
            cmds.setAttr(f"{ik_local_ctl}.sz", lock=True, keyable=False)

        cmds.setAttr(f"{ik_local_ctl}.mirror_type", 1)
        cmds.orientConstraint(ik_local_ctl, ik2_jnt, maintainOffset=False)
        cmds.scaleConstraint(ik_local_ctl, ik2_jnt, maintainOffset=False)

        cmds.connectAttr(f"{host_ctl}.fkik", f"{ik_pos_npo}.v")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{pole_vec_npo}.v")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{ik_npo}.v")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{guideline}.v")

        rev = cmds.createNode("reverse")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{rev}.inputX")
        cmds.connectAttr(f"{rev}.outputX", f"{shoulder_npo}.v")

        ins = Transform(
            parent=ik_pos_ctl,
            name=name,
            side=side,
            index=index,
            description="ikAim",
            extension="grp",
            m=ORIGINMATRIX,
        )
        ik_aim_grp = ins.create()
        cmds.aimConstraint(
            ik_local_ctl, ik_aim_grp, maintainOffset=False, aimVector=(1, 0, 0)
        )
        cmds.setAttr(f"{ik_aim_grp}.t", 0, 0, 0)

        ins = Transform(
            parent=ik_aim_grp,
            name=name,
            side=side,
            index=index,
            description="ik",
            extension="target",
            m=cmds.xform(ik_aim_grp, query=True, matrix=True, worldSpace=True),
        )
        ik_target = ins.create()

        original_distance_curve = cmds.curve(point=((0, 0, 0), (0, 0, 0)), degree=1)
        original_distance_curve = cmds.rename(
            original_distance_curve,
            Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="origIkDistance",
                extension=Name.curve_extension,
            ),
        )
        original_distance_curve = cmds.parent(
            original_distance_curve, clavicle_bone_npo_inverse
        )[0]
        cmds.hide(original_distance_curve)

        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{ik_pos_npo}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{self.rig_root}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        cmds.connectAttr(
            f"{decom_m}.outputTranslate", f"{original_distance_curve}.cv[0]"
        )
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{ik_npo}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{self.rig_root}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        cmds.connectAttr(
            f"{decom_m}.outputTranslate", f"{original_distance_curve}.cv[1]"
        )

        rigkit.ik_2jnt(
            parent=ik_target,
            name=Name.create(
                convention=Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="",
                extension=Name.ikh_extension,
            ),
            initial_matrix_plugs=[
                f"{self.rig_root}.npo_matrix[2]",
                f"{self.rig_root}.npo_matrix[3]",
                f"{self.rig_root}.npo_matrix[4]",
            ],
            initial_ik_curve=original_distance_curve,
            joints=[ik0_jnt, ik1_jnt, ik2_jnt],
            ik_pos_driver=ik_pos_ctl,
            ik_driver=ik_local_ctl,
            pole_vector=pole_vec_ctl,
            attach_pole_vector_attr=f"{ik_ctl}.attach_to_PV",
            scale_attr=f"{ik_ctl}.ik_scale",
            slide_attr=f"{ik_ctl}.slide",
            soft_ik_attr=f"{ik_ctl}.soft_ik",
            max_stretch_attr=f"{ik_ctl}.max_stretch",
        )
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{self.rig_root}.npo_matrix[2]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(f"{self.rig_root}.npo_matrix[1]", f"{mult_m}.matrixIn[1]")
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{ik0_jnt}.jointOrient")
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{self.rig_root}.npo_matrix[3]", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{ik1_jnt}.jointOrient")
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{self.rig_root}.npo_matrix[4]", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{ik2_jnt}.jointOrient")
        # endregion

        # region RIG - blend joint
        ins = Joint(
            parent=clavicle_bone_npo_inverse,
            name=name,
            side=side,
            index=index,
            description="blend0",
            extension=Name.joint_extension,
            m=cmds.xform(shoulder_ctl, query=True, matrix=True, worldSpace=True),
            use_joint_convention=False,
        )
        blend0_jnt = ins.create()
        plug = cmds.listConnections(
            f"{ik0_jnt}.jointOrient", source=True, destination=False, plugs=True
        )[0]
        cmds.connectAttr(plug, f"{blend0_jnt}.jointOrient")

        ins = Joint(
            parent=blend0_jnt,
            name=name,
            side=side,
            index=index,
            description="blend1",
            extension=Name.joint_extension,
            m=cmds.xform(elbow_ctl, query=True, matrix=True, worldSpace=True),
            use_joint_convention=False,
        )
        blend1_jnt = ins.create()
        plug = cmds.listConnections(
            f"{ik1_jnt}.jointOrient", source=True, destination=False, plugs=True
        )[0]
        cmds.connectAttr(plug, f"{blend1_jnt}.jointOrient")

        ins = Joint(
            parent=blend1_jnt,
            name=name,
            side=side,
            index=index,
            description="blend2",
            extension=Name.joint_extension,
            m=cmds.xform(wrist_ctl, query=True, matrix=True, worldSpace=True),
            use_joint_convention=False,
        )
        blend2_jnt = ins.create()
        plug = cmds.listConnections(
            f"{ik2_jnt}.jointOrient", source=True, destination=False, plugs=True
        )[0]
        cmds.connectAttr(plug, f"{blend2_jnt}.jointOrient")

        ins = Transform(
            parent=blend2_jnt,
            name=name,
            side=side,
            index=index,
            description="alignWristInverse",
            extension=Name.loc_extension,
        )
        align_wrist_Inverse_loc = ins.create()
        cmds.setAttr(f"{align_wrist_Inverse_loc}.t", 0, 0, 0)
        com_m = cmds.createNode("composeMatrix")
        cmds.connectAttr(plug, f"{com_m}.inputRotate")
        inverse_m = cmds.createNode("inverseMatrix")
        cmds.connectAttr(f"{com_m}.outputMatrix", f"{inverse_m}.inputMatrix")
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{inverse_m}.outputMatrix", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{align_wrist_Inverse_loc}.r")

        pair_b = cmds.createNode("pairBlend")
        cmds.setAttr(f"{pair_b}.rotInterpolation", 1)
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{shoulder_ctl}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{clavicle_bone_npo_inverse}.worldInverseMatrix[0]",
            f"{mult_m}.matrixIn[1]",
        )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{pair_b}.inTranslate1")
        cmds.connectAttr(f"{shoulder_ctl}.r", f"{pair_b}.inRotate1")
        cmds.connectAttr(f"{ik0_jnt}.t", f"{pair_b}.inTranslate2")
        cmds.connectAttr(f"{ik0_jnt}.r", f"{pair_b}.inRotate2")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{pair_b}.weight")
        cmds.connectAttr(f"{pair_b}.outTranslate", f"{blend0_jnt}.t")
        cmds.connectAttr(f"{pair_b}.outRotate", f"{blend0_jnt}.r")

        pair_b = cmds.createNode("pairBlend")
        cmds.setAttr(f"{pair_b}.rotInterpolation", 1)
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{elbow_ctl}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{shoulder_ctl}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{pair_b}.inTranslate1")
        cmds.connectAttr(f"{elbow_ctl}.r", f"{pair_b}.inRotate1")
        cmds.connectAttr(f"{ik1_jnt}.t", f"{pair_b}.inTranslate2")
        cmds.connectAttr(f"{ik1_jnt}.r", f"{pair_b}.inRotate2")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{pair_b}.weight")
        cmds.connectAttr(f"{pair_b}.outTranslate", f"{blend1_jnt}.t")
        cmds.connectAttr(f"{pair_b}.outRotate", f"{blend1_jnt}.r")

        pair_b = cmds.createNode("pairBlend")
        cmds.setAttr(f"{pair_b}.rotInterpolation", 1)
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{wrist_ctl}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(f"{elbow_ctl}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]")
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{pair_b}.inTranslate1")
        cmds.connectAttr(f"{wrist_ctl}.r", f"{pair_b}.inRotate1")
        cmds.connectAttr(f"{ik2_jnt}.t", f"{pair_b}.inTranslate2")
        cmds.connectAttr(f"{ik2_jnt}.r", f"{pair_b}.inRotate2")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{pair_b}.weight")
        cmds.connectAttr(f"{pair_b}.outTranslate", f"{blend2_jnt}.t")
        cmds.connectAttr(f"{pair_b}.outRotate", f"{blend2_jnt}.r")
        blend_color = cmds.createNode("blendColors")
        cmds.connectAttr(f"{ik2_jnt}.s", f"{blend_color}.color1")
        cmds.connectAttr(f"{wrist_ctl}.s", f"{blend_color}.color2")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{blend_color}.blender")
        cmds.connectAttr(f"{blend_color}.output", f"{blend2_jnt}.s")
        cmds.hide(blend0_jnt)

        # endregion

        # region RIG - twist SC joint
        ins = Joint(
            parent=clavicle_bone_npo_inverse,
            name=name,
            side=side,
            index=index,
            description="upperNonTwist0",
            extension="SC",
            m=ORIGINMATRIX,
            use_joint_convention=False,
        )
        upper_non_twist0_jnt = ins.create()

        armpit_roll = cmds.createNode(
            "transform",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                extension="armpitRoll",
            ),
            parent=upper_non_twist0_jnt,
        )
        cmds.connectAttr(f"{host_ctl}.armpit_roll", f"{armpit_roll}.rx")

        ins = Joint(
            parent=upper_non_twist0_jnt,
            name=name,
            side=side,
            index=index,
            description="upperNonTwist1",
            extension="SC",
            m=ORIGINMATRIX,
            use_joint_convention=False,
        )
        upper_non_twist1_jnt = ins.create()
        upper_non_twist_ikh, _ = cmds.ikHandle(
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="upperNonTwist",
                extension=Name.ikh_extension,
            ),
            startJoint=upper_non_twist0_jnt,
            endEffector=upper_non_twist1_jnt,
            solver="ikSCsolver",
        )
        plug = cmds.listConnections(
            f"{blend0_jnt}.jointOrient", source=True, destination=False, plugs=True
        )[0]
        cmds.connectAttr(plug, f"{upper_non_twist0_jnt}.jointOrient")
        cmds.connectAttr(plug, f"{upper_non_twist_ikh}.r")
        plug = cmds.listConnections(
            f"{blend0_jnt}.t", source=True, destination=False, plugs=True
        )[0]
        cmds.connectAttr(plug, f"{upper_non_twist0_jnt}.t")
        cmds.setAttr(f"{upper_non_twist1_jnt}.t", 1, 0, 0)
        cmds.connectAttr(f"{negate_condition}.outColorR", f"{upper_non_twist1_jnt}.tx")
        cmds.hide(upper_non_twist_ikh)
        upper_non_twist_ikh = cmds.parent(
            upper_non_twist_ikh, clavicle_bone_npo_inverse
        )[0]

        ins = Joint(
            parent=clavicle_bone_npo_inverse,
            name=name,
            side=side,
            index=index,
            description="upperTwist0",
            extension="SC",
            m=ORIGINMATRIX,
            use_joint_convention=False,
        )
        upper_twist0_jnt = ins.create()

        ins = Joint(
            parent=upper_twist0_jnt,
            name=name,
            side=side,
            index=index,
            description="upperTwist1",
            extension="SC",
            m=ORIGINMATRIX,
            use_joint_convention=False,
        )
        upper_twist1_jnt = ins.create()
        upper_twist_ikh, _ = cmds.ikHandle(
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="upperwist",
                extension=Name.ikh_extension,
            ),
            startJoint=upper_twist0_jnt,
            endEffector=upper_twist1_jnt,
            solver="ikSCsolver",
        )
        plug = cmds.listConnections(
            f"{blend0_jnt}.jointOrient", source=True, destination=False, plugs=True
        )[0]
        cmds.connectAttr(plug, f"{upper_twist0_jnt}.jointOrient")
        plug = cmds.listConnections(
            f"{blend0_jnt}.t", source=True, destination=False, plugs=True
        )[0]
        cmds.connectAttr(plug, f"{upper_twist0_jnt}.t")
        cmds.setAttr(f"{upper_twist1_jnt}.t", 1, 0, 0)
        cmds.connectAttr(f"{negate_condition}.outColorR", f"{upper_twist1_jnt}.tx")
        cmds.hide(upper_twist_ikh)
        upper_twist_ikh = cmds.parent(upper_twist_ikh, clavicle_bone_npo_inverse)[0]

        ins = Joint(
            parent=blend0_jnt,
            name=name,
            side=side,
            index=index,
            description="lowerNonTwist0",
            extension="SC",
            m=ORIGINMATRIX,
            use_joint_convention=False,
        )
        lower_non_twist0_jnt = ins.create()

        ins = Joint(
            parent=lower_non_twist0_jnt,
            name=name,
            side=side,
            index=index,
            description="lowerNonTwist1",
            extension="SC",
            m=ORIGINMATRIX,
            use_joint_convention=False,
        )
        lower_non_twist1_jnt = ins.create()
        lower_non_twist_ikh, _ = cmds.ikHandle(
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="lowerNonTwist",
                extension=Name.ikh_extension,
            ),
            startJoint=lower_non_twist0_jnt,
            endEffector=lower_non_twist1_jnt,
            solver="ikSCsolver",
        )
        plug = cmds.listConnections(
            f"{blend1_jnt}.jointOrient", source=True, destination=False, plugs=True
        )[0]
        cmds.connectAttr(plug, f"{lower_non_twist0_jnt}.jointOrient")
        cmds.setAttr(f"{lower_non_twist1_jnt}.t", 1, 0, 0)
        cmds.connectAttr(f"{negate_condition}.outColorR", f"{lower_non_twist1_jnt}.tx")
        cmds.hide(lower_non_twist_ikh)
        lower_non_twist_ikh = cmds.parent(lower_non_twist_ikh, blend0_jnt)[0]

        ins = Joint(
            parent=blend0_jnt,
            name=name,
            side=side,
            index=index,
            description="lowerTwist0",
            extension="SC",
            m=ORIGINMATRIX,
            use_joint_convention=False,
        )
        lower_twist0_jnt = ins.create()

        ins = Joint(
            parent=lower_twist0_jnt,
            name=name,
            side=side,
            index=index,
            description="lowerTwist1",
            extension="SC",
            m=ORIGINMATRIX,
            use_joint_convention=False,
        )
        lower_twist1_jnt = ins.create()
        lower_twist_ikh, _ = cmds.ikHandle(
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="lowerTwist",
                extension=Name.ikh_extension,
            ),
            startJoint=lower_twist0_jnt,
            endEffector=lower_twist1_jnt,
            solver="ikSCsolver",
        )
        plug = cmds.listConnections(
            f"{blend1_jnt}.jointOrient", source=True, destination=False, plugs=True
        )[0]
        cmds.connectAttr(plug, f"{lower_twist0_jnt}.jointOrient")
        cmds.setAttr(f"{lower_twist1_jnt}.t", 1, 0, 0)
        cmds.connectAttr(f"{negate_condition}.outColorR", f"{lower_twist1_jnt}.tx")
        cmds.hide(lower_twist_ikh)
        lower_twist_ikh = cmds.parent(lower_twist_ikh, blend0_jnt)[0]
        cmds.hide(upper_non_twist0_jnt, upper_twist0_jnt)

        # endregion

        # region RIG - sub controllers
        pin_npo, pin_ctl = self["controller"][10].create(
            parent=clavicle_bone_npo_inverse,
            shape=(
                self["controller"][10]["shape"]
                if "shape" in self["controller"][10]
                else "cube"
            ),
            color=12,
        )
        upper_bend_npo, upper_bend_ctl = self["controller"][11].create(
            parent=clavicle_bone_npo_inverse,
            shape=(
                self["controller"][11]["shape"]
                if "shape" in self["controller"][11]
                else "cube"
            ),
            color=12,
        )
        lower_bend_npo, lower_bend_ctl = self["controller"][12].create(
            parent=clavicle_bone_npo_inverse,
            shape=(
                self["controller"][12]["shape"]
                if "shape" in self["controller"][12]
                else "cube"
            ),
            color=12,
        )
        cmds.addAttr(
            upper_bend_ctl,
            longName="uniform",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=1,
            keyable=True,
        )
        cmds.addAttr(
            upper_bend_ctl,
            longName="volume",
            attributeType="float",
            minValue=-1,
            maxValue=10,
            defaultValue=0,
            keyable=True,
        )
        cmds.addAttr(
            upper_bend_ctl,
            longName="volume_high_bound",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=1,
            keyable=True,
        )
        cmds.addAttr(
            upper_bend_ctl,
            longName="volume_position",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=0.5,
            keyable=True,
        )
        cmds.addAttr(
            upper_bend_ctl,
            longName="volume_low_bound",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=0,
            keyable=True,
        )
        cmds.pointConstraint(blend0_jnt, pin_ctl, upper_bend_npo, maintainOffset=False)
        cons = cmds.orientConstraint(
            armpit_roll, upper_twist0_jnt, upper_bend_npo, maintainOffset=False
        )[0]
        cmds.setAttr(f"{cons}.interpType", 2)
        cmds.pointConstraint(pin_ctl, lower_non_twist0_jnt, maintainOffset=False)
        cmds.pointConstraint(pin_ctl, lower_twist0_jnt, maintainOffset=False)
        cmds.parentConstraint(blend1_jnt, pin_npo, maintainOffset=False)
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{pole_vec_ctl}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{clavicle_bone_npo_inverse}.worldInverseMatrix[0]",
            f"{mult_m}.matrixIn[1]",
        )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{guideline}.cv[0]")
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{pin_ctl}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{clavicle_bone_npo_inverse}.worldInverseMatrix[0]",
            f"{mult_m}.matrixIn[1]",
        )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{guideline}.cv[1]")
        cmds.pointConstraint(pin_ctl, blend2_jnt, lower_bend_npo, maintainOffset=False)
        cons = cmds.orientConstraint(
            lower_non_twist0_jnt, lower_twist0_jnt, lower_bend_npo, maintainOffset=False
        )[0]
        cmds.setAttr(f"{cons}.interpType", 2)
        cmds.addAttr(
            lower_bend_ctl,
            longName="uniform",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=1,
            keyable=True,
        )
        cmds.addAttr(
            lower_bend_ctl,
            longName="volume",
            attributeType="float",
            minValue=-1,
            maxValue=10,
            defaultValue=0,
            keyable=True,
        )
        cmds.addAttr(
            lower_bend_ctl,
            longName="volume_high_bound",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=1,
            keyable=True,
        )
        cmds.addAttr(
            lower_bend_ctl,
            longName="volume_position",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=0.5,
            keyable=True,
        )
        cmds.addAttr(
            lower_bend_ctl,
            longName="volume_low_bound",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=0,
            keyable=True,
        )
        cmds.pointConstraint(pin_ctl, upper_non_twist_ikh, maintainOffset=False)
        cmds.parentConstraint(pin_ctl, upper_twist_ikh, maintainOffset=False)
        cmds.pointConstraint(blend2_jnt, lower_non_twist_ikh, maintainOffset=False)
        cmds.orientConstraint(pin_ctl, lower_non_twist_ikh, maintainOffset=False)
        cmds.pointConstraint(blend2_jnt, lower_twist_ikh, maintainOffset=False)
        cmds.orientConstraint(
            align_wrist_Inverse_loc, lower_twist_ikh, maintainOffset=False
        )
        cmds.connectAttr(f"{host_ctl}.sub_ctls_visibility", f"{upper_bend_npo}.v")
        cmds.connectAttr(f"{host_ctl}.sub_ctls_visibility", f"{pin_npo}.v")
        cmds.connectAttr(f"{host_ctl}.sub_ctls_visibility", f"{lower_bend_npo}.v")

        # endregion

        # region RIG - ribbon driver
        ins = Joint(
            parent=armpit_roll,
            name=name,
            side=side,
            index=index,
            description="upperRibbonDriver0",
            extension=Name.joint_extension,
            m=ORIGINMATRIX,
            use_joint_convention=False,
        )
        upper_ribbon_driver0_jnt = ins.create()
        ins = Joint(
            parent=upper_bend_ctl,
            name=name,
            side=side,
            index=index,
            description="upperRibbonDriver1",
            extension=Name.joint_extension,
            m=ORIGINMATRIX,
            use_joint_convention=False,
        )
        upper_ribbon_driver1_jnt = ins.create()
        ins = Joint(
            parent=upper_twist0_jnt,
            name=name,
            side=side,
            index=index,
            description="upperRibbonDriver2",
            extension=Name.joint_extension,
            m=cmds.xform(upper_non_twist_ikh, query=True, matrix=True, worldSpace=True),
            use_joint_convention=False,
        )
        upper_ribbon_driver2_jnt = ins.create()
        ins = Joint(
            parent=lower_non_twist0_jnt,
            name=name,
            side=side,
            index=index,
            description="lowerRibbonDriver0",
            extension=Name.joint_extension,
            m=ORIGINMATRIX,
            use_joint_convention=False,
        )
        lower_ribbon_driver0_jnt = ins.create()
        ins = Joint(
            parent=lower_bend_ctl,
            name=name,
            side=side,
            index=index,
            description="lowerRibbonDriver1",
            extension=Name.joint_extension,
            m=ORIGINMATRIX,
            use_joint_convention=False,
        )
        lower_ribbon_driver1_jnt = ins.create()
        ins = Joint(
            parent=lower_twist0_jnt,
            name=name,
            side=side,
            index=index,
            description="lowerRibbonDriver2",
            extension=Name.joint_extension,
            m=cmds.xform(lower_twist_ikh, query=True, matrix=True, worldSpace=True),
            use_joint_convention=False,
        )
        lower_ribbon_driver2_jnt = ins.create()
        driver_joints = [
            upper_ribbon_driver0_jnt,
            upper_ribbon_driver1_jnt,
            upper_ribbon_driver2_jnt,
            lower_ribbon_driver0_jnt,
            lower_ribbon_driver1_jnt,
            lower_ribbon_driver2_jnt,
        ]
        cmds.pointConstraint(pin_ctl, upper_ribbon_driver2_jnt, maintainOffset=False)
        cmds.pointConstraint(blend2_jnt, lower_ribbon_driver2_jnt, maintainOffset=False)
        cmds.hide(driver_joints)
        [cmds.setAttr(f"{j}.t", 0, 0, 0) for j in driver_joints]
        [cmds.setAttr(f"{j}.r", 0, 0, 0) for j in driver_joints]
        [cmds.setAttr(f"{j}.jointOrient", 0, 0, 0) for j in driver_joints]
        cmds.matchTransform(
            upper_ribbon_driver2_jnt, upper_non_twist_ikh, position=True
        )
        cmds.matchTransform(
            lower_ribbon_driver2_jnt, lower_non_twist_ikh, position=True
        )

        # endregion

        # region RIG - ribbon
        ribbon_grp = cmds.createNode(
            "transform",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="ribbon",
                extension="grp",
            ),
            parent=clavicle_bone_npo_inverse,
        )
        ins = Surface(data=self["upper_ribbon_surface"]["value"])
        upper_ribbon_surface = ins.create_from_data()
        upper_ribbon_surface = cmds.rename(
            upper_ribbon_surface,
            Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="upperRibbonSurface",
            ),
        )
        cmds.setAttr(f"{upper_ribbon_surface}.t", 0, 0, 0)
        cmds.setAttr(f"{upper_ribbon_surface}.r", 0, 0, 0)
        cmds.setAttr(f"{upper_ribbon_surface}.t", lock=True)
        cmds.setAttr(f"{upper_ribbon_surface}.r", lock=True)
        ins = Surface(data=self["lower_ribbon_surface"]["value"])
        lower_ribbon_surface = ins.create_from_data()
        lower_ribbon_surface = cmds.rename(
            lower_ribbon_surface,
            Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="lowerRibbonSurface",
            ),
        )
        cmds.setAttr(f"{lower_ribbon_surface}.t", 0, 0, 0)
        cmds.setAttr(f"{lower_ribbon_surface}.r", 0, 0, 0)
        cmds.setAttr(f"{lower_ribbon_surface}.t", lock=True)
        cmds.setAttr(f"{lower_ribbon_surface}.r", lock=True)

        upper_auto_volume_multiple = [0]
        c = self["twist_joint_count"]["value"] + 1
        for i in range(1, c):
            upper_auto_volume_multiple.append(i / c)
        upper_auto_volume_multiple.append(1)

        upper_ribbon_surface, upper_ribbon_outputs = rigkit.ribbon_uv(
            ribbon_grp,
            driver_joints=driver_joints[:3],
            driver_inverse_plugs=[
                f"{self.rig_root}.driver_inverse_matrix[0]",
                f"{self.rig_root}.driver_inverse_matrix[1]",
                f"{self.rig_root}.driver_inverse_matrix[2]",
            ],
            surface=upper_ribbon_surface,
            stretch_attr=f"{host_ctl}.stretch",
            squash_attr=f"{host_ctl}.squash",
            uniform_attr=f"{upper_bend_ctl}.uniform",
            auto_volume_attr=f"{host_ctl}.auto_volume",
            auto_volume_multiple=upper_auto_volume_multiple,
            volume_attr=f"{upper_bend_ctl}.volume",
            volume_position_attr=f"{upper_bend_ctl}.volume_position",
            volume_high_bound_attr=f"{upper_bend_ctl}.volume_high_bound",
            volume_low_bound_attr=f"{upper_bend_ctl}.volume_low_bound",
            output_u_value_plugs=[
                f"{self.rig_root}.upper_output_u_values[{i}]"
                for i in range(len(self["upper_output_u_values"]["value"]))
            ],
            negate_plug=f"{negate_condition}.outColorR",
        )
        cmds.connectAttr(
            f"{self.rig_root}.upper_ribbon_surface",
            f"{upper_ribbon_surface}ShapeOrig.create",
        )
        sc = cmds.findDeformers(upper_ribbon_surface)[0]
        cmds.sets(sc, edit=True, addElement="_deformerWeights_sets")
        cmds.skinPercent(
            sc, f"{upper_ribbon_surface}.cv[*][0]", transformValue=[driver_joints[0], 1]
        )
        cmds.skinPercent(
            sc,
            f"{upper_ribbon_surface}.cv[*][1]",
            transformValue=[(driver_joints[0], 0.5), (driver_joints[1], 0.5)],
        )
        cmds.skinPercent(
            sc, f"{upper_ribbon_surface}.cv[*][2]", transformValue=[driver_joints[1], 1]
        )
        cmds.skinPercent(
            sc,
            f"{upper_ribbon_surface}.cv[*][3]",
            transformValue=[(driver_joints[1], 0.5), (driver_joints[2], 0.5)],
        )
        cmds.skinPercent(
            sc, f"{upper_ribbon_surface}.cv[*][4]", transformValue=[driver_joints[2], 1]
        )

        lower_auto_volume_multiple = [1]
        c = self["twist_joint_count"]["value"] + 1
        for i in range(1, c):
            lower_auto_volume_multiple.append(1 - (i / c))
        lower_auto_volume_multiple.append(0)

        lower_ribbon_surface, lower_ribbon_outputs = rigkit.ribbon_uv(
            ribbon_grp,
            driver_joints=driver_joints[3:],
            driver_inverse_plugs=[
                f"{self.rig_root}.driver_inverse_matrix[3]",
                f"{self.rig_root}.driver_inverse_matrix[4]",
                f"{self.rig_root}.driver_inverse_matrix[5]",
            ],
            surface=lower_ribbon_surface,
            stretch_attr=f"{host_ctl}.stretch",
            squash_attr=f"{host_ctl}.squash",
            uniform_attr=f"{lower_bend_ctl}.uniform",
            auto_volume_attr=f"{host_ctl}.auto_volume",
            auto_volume_multiple=lower_auto_volume_multiple,
            volume_attr=f"{lower_bend_ctl}.volume",
            volume_position_attr=f"{lower_bend_ctl}.volume_position",
            volume_high_bound_attr=f"{lower_bend_ctl}.volume_high_bound",
            volume_low_bound_attr=f"{lower_bend_ctl}.volume_low_bound",
            output_u_value_plugs=[
                f"{self.rig_root}.lower_output_u_values[{i}]"
                for i in range(len(self["lower_output_u_values"]["value"]))
            ],
            negate_plug=f"{negate_condition}.outColorR",
        )
        cmds.connectAttr(
            f"{self.rig_root}.lower_ribbon_surface",
            f"{lower_ribbon_surface}ShapeOrig.create",
        )
        sc = cmds.findDeformers(lower_ribbon_surface)[0]
        cmds.sets(sc, edit=True, addElement="_deformerWeights_sets")

        cmds.skinPercent(
            sc, f"{lower_ribbon_surface}.cv[*][0]", transformValue=[driver_joints[3], 1]
        )
        cmds.skinPercent(
            sc,
            f"{lower_ribbon_surface}.cv[*][1]",
            transformValue=[(driver_joints[3], 0.5), (driver_joints[4], 0.5)],
        )
        cmds.skinPercent(
            sc, f"{lower_ribbon_surface}.cv[*][2]", transformValue=[driver_joints[4], 1]
        )
        cmds.skinPercent(
            sc,
            f"{lower_ribbon_surface}.cv[*][3]",
            transformValue=[(driver_joints[4], 0.5), (driver_joints[5], 0.5)],
        )
        cmds.skinPercent(
            sc, f"{lower_ribbon_surface}.cv[*][4]", transformValue=[driver_joints[5], 1]
        )
        cmds.hide(ribbon_grp)
        # endregion

        # wrist
        ins = Transform(
            parent=lower_ribbon_outputs[-1],
            name=name,
            side=side,
            index=index,
            description="wrist",
            extension=Name.loc_extension,
        )
        wrist_loc = ins.create()
        cmds.setAttr(f"{wrist_loc}.t", 0, 0, 0)
        cmds.orientConstraint(blend2_jnt, wrist_loc, maintainOffset=False)

        # scapular
        scapular_npo, scapular_ctl = self["controller"][13].create(
            parent=clavicle_bone_ctl,
            shape=(
                self["controller"][13]["shape"]
                if "shape" in self["controller"][13]
                else "cube"
            ),
            color=12,
            npo_matrix_index=8,
        )
        ins = Transform(
            scapular_ctl,
            name=name,
            side=side,
            index=index,
            description="scapular",
            extension="inverse",
        )
        scapular_negate_inverse = ins.create()
        cmds.setAttr(f"{scapular_negate_inverse}.t", 0, 0, 0)
        cmds.setAttr(f"{scapular_negate_inverse}.r", 0, 0, 0)
        cmds.setAttr(f"{scapular_negate_inverse}.s", 1, 1, 1)
        cmds.connectAttr(
            f"{negate_condition}.outColorR", f"{scapular_negate_inverse}.sz"
        )
        cmds.connectAttr(f"{host_ctl}.scapular_ctl_visibility", f"{scapular_npo}.v")
        cmds.addAttr(
            scapular_ctl,
            longName="rotation",
            attributeType="float",
            minValue=-1,
            maxValue=1,
            defaultValue=0,
            keyable=True,
        )
        cmds.addAttr(
            scapular_ctl,
            longName="upper_winging",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=0,
            keyable=True,
        )
        cmds.addAttr(
            scapular_ctl,
            longName="lower_winging",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=0,
            keyable=True,
        )
        ins = Transform(
            parent=clavicle_bone_npo_inverse,
            name=name,
            side=side,
            index=index,
            description="scapularAim",
            extension=Name.loc_extension,
        )
        scapular_aim_loc = ins.create()
        cmds.connectAttr(
            f"{self.rig_root}.scapular_aim_matrix",
            f"{scapular_aim_loc}.offsetParentMatrix",
        )
        cmds.setAttr(f"{scapular_aim_loc}.t", 0, 0, 0)
        cmds.setAttr(f"{scapular_aim_loc}.r", 0, 0, 0)
        ins = Transform(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description="scapularAutoAim",
            extension=Name.group_extension,
        )
        scapular_auto_aim_grp = ins.create()
        ins = Transform(
            parent=scapular_auto_aim_grp,
            name=name,
            side=side,
            index=index,
            description="scapularAutoAim",
            extension=Name.loc_extension,
        )
        scapular_auto_aim_loc = ins.create()
        cmds.connectAttr(
            f"{self.rig_root}.scapular_aim_matrix",
            f"{scapular_auto_aim_grp}.offsetParentMatrix",
        )
        ins = Transform(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description="scapularBlendAim",
            extension=Name.loc_extension,
        )
        scapular_blend_aim_loc = ins.create()
        ins = Transform(
            parent=scapular_blend_aim_loc,
            name=name,
            side=side,
            index=index,
            description="scapularAutoAim",
            extension="rotationWinging",
        )
        scapular_aim_rotation_winging = ins.create()
        ins = Transform(
            parent=clavicle_bone_npo_inverse,
            name=name,
            side=side,
            index=index,
            description="scapularUp",
            extension=Name.loc_extension,
        )
        scapular_up_loc = ins.create()
        cmds.connectAttr(
            f"{self.rig_root}.scapular_up_matrix",
            f"{scapular_up_loc}.offsetParentMatrix",
        )
        cmds.setAttr(f"{scapular_up_loc}.t", 0, 0, 0)
        cmds.setAttr(f"{scapular_up_loc}.r", 0, 0, 0)
        ins = Transform(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description="scapularAutoUp",
            extension=Name.group_extension,
        )
        scapular_auto_up_grp = ins.create()
        ins = Transform(
            parent=scapular_auto_up_grp,
            name=name,
            side=side,
            index=index,
            description="scapularAutoUp",
            extension=Name.loc_extension,
        )
        scapular_auto_up_loc = ins.create()
        cmds.connectAttr(
            f"{self.rig_root}.scapular_up_matrix",
            f"{scapular_auto_up_grp}.offsetParentMatrix",
        )
        ins = Transform(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description="scapularBlendUp",
            extension=Name.loc_extension,
        )
        scapular_blend_up_loc = ins.create()
        ins = Transform(
            parent=scapular_blend_up_loc,
            name=name,
            side=side,
            index=index,
            description="scapularAutoUp",
            extension="rotationWinging",
        )
        scapular_up_rotation_winging = ins.create()
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{scapular_aim_loc}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{self.rig_root}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        blend_m = cmds.createNode("blendMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{blend_m}.inputMatrix")
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(
            f"{scapular_auto_aim_loc}.worldMatrix[0]",
            f"{mult_m}.matrixIn[0]",
        )
        cmds.connectAttr(
            f"{self.rig_root}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        cmds.connectAttr(
            f"{mult_m}.matrixSum",
            f"{blend_m}.target[0].targetMatrix",
        )
        cmds.connectAttr(f"{host_ctl}.auto_scapular", f"{blend_m}.envelope")
        cmds.connectAttr(
            f"{blend_m}.outputMatrix", f"{scapular_blend_aim_loc}.offsetParentMatrix"
        )
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{scapular_up_loc}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{self.rig_root}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        blend_m = cmds.createNode("blendMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{blend_m}.inputMatrix")
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(
            f"{scapular_auto_up_loc}.worldMatrix[0]",
            f"{mult_m}.matrixIn[0]",
        )
        cmds.connectAttr(
            f"{self.rig_root}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        cmds.connectAttr(
            f"{mult_m}.matrixSum",
            f"{blend_m}.target[0].targetMatrix",
        )
        cmds.connectAttr(f"{host_ctl}.auto_scapular", f"{blend_m}.envelope")
        cmds.connectAttr(
            f"{blend_m}.outputMatrix", f"{scapular_blend_up_loc}.offsetParentMatrix"
        )
        cons = cmds.aimConstraint(
            scapular_aim_rotation_winging,
            scapular_npo,
            aimVector=(-1, 0, 0),
            upVector=(0, -1, 0),
            worldUpType="object",
            worldUpObject=scapular_up_rotation_winging,
            maintainOffset=False,
        )[0]
        cmds.connectAttr(f"{self.rig_root}.scapular_aim_axis_x", f"{cons}.aimVectorX")
        cmds.connectAttr(f"{self.rig_root}.scapular_aim_axis_y", f"{cons}.aimVectorY")
        cmds.connectAttr(f"{self.rig_root}.scapular_aim_axis_z", f"{cons}.aimVectorZ")
        cmds.connectAttr(f"{self.rig_root}.scapular_up_axis_x", f"{cons}.upVectorX")
        cmds.connectAttr(f"{self.rig_root}.scapular_up_axis_y", f"{cons}.upVectorY")
        cmds.connectAttr(f"{self.rig_root}.scapular_up_axis_z", f"{cons}.upVectorZ")

        md = cmds.createNode("multiplyDivide")
        cmds.connectAttr(f"{negate_condition}.outColorR", f"{md}.input2X")
        cmds.connectAttr(f"{negate_condition}.outColorR", f"{md}.input2Y")
        cmds.connectAttr(f"{negate_condition}.outColorR", f"{md}.input2Z")
        cmds.connectAttr(f"{scapular_ctl}.rotation", f"{md}.input1X")

        cmds.connectAttr(f"{scapular_ctl}.upper_winging", f"{md}.input1Y")
        cmds.connectAttr(f"{scapular_ctl}.lower_winging", f"{md}.input1Z")
        cmds.connectAttr(f"{md}.outputX", f"{scapular_aim_rotation_winging}.ty")
        cmds.connectAttr(f"{md}.outputY", f"{scapular_aim_rotation_winging}.tz")
        subtract = cmds.createNode("subtract")
        cmds.connectAttr(f"{md}.outputY", f"{subtract}.input2")
        cmds.connectAttr(f"{md}.outputZ", f"{subtract}.input1")
        cmds.connectAttr(f"{subtract}.output", f"{scapular_up_rotation_winging}.tz")

        # output
        c = 0
        ins = Joint(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description="clavicle",
            extension=Name.output_extension,
            m=ORIGINMATRIX,
        )
        clavicle_output = ins.create()
        cmds.setAttr(f"{clavicle_output}.drawStyle", 2)
        self["output"][c].connect(clavicle_bone_ctl)

        c += 1
        ins = Joint(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description="shoulder",
            extension=Name.output_extension,
            m=ORIGINMATRIX,
        )
        shoulder_output = ins.create()
        cmds.setAttr(f"{shoulder_output}.drawStyle", 2)
        self["output"][c].connect(upper_ribbon_outputs[0])

        upper_twist_outputs = []
        for i in range(self["twist_joint_count"]["value"]):
            c += 1
            ins = Joint(
                parent=self.rig_root,
                name=name,
                side=side,
                index=index,
                description=f"upperTwist{i}",
                extension=Name.output_extension,
                m=ORIGINMATRIX,
            )
            twist_output = ins.create()
            upper_twist_outputs.append(twist_output)
            cmds.setAttr(f"{twist_output}.drawStyle", 2)
            self["output"][c].connect(upper_ribbon_outputs[i + 1])

        c += 1
        ins = Joint(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description="elbow",
            extension=Name.output_extension,
            m=ORIGINMATRIX,
        )
        elbow_output = ins.create()
        cmds.setAttr(f"{elbow_output}.drawStyle", 2)
        self["output"][c].connect(lower_ribbon_outputs[0])

        lower_twist_outputs = []
        for i in range(self["twist_joint_count"]["value"]):
            c += 1
            ins = Joint(
                parent=self.rig_root,
                name=name,
                side=side,
                index=index,
                description=f"lowerTwist{i}",
                extension=Name.output_extension,
                m=ORIGINMATRIX,
            )
            twist_output = ins.create()
            lower_twist_outputs.append(twist_output)
            cmds.setAttr(f"{twist_output}.drawStyle", 2)
            self["output"][c].connect(lower_ribbon_outputs[i + 1])

        c += 1
        ins = Joint(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description="wrist",
            extension=Name.output_extension,
            m=ORIGINMATRIX,
        )
        wrist_output = ins.create()
        cmds.setAttr(f"{wrist_output}.drawStyle", 2)
        self["output"][c].connect(wrist_loc)

        c += 1
        ins = Joint(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description="scapular",
            extension=Name.output_extension,
            m=ORIGINMATRIX,
        )
        scapular_output = ins.create()
        cmds.setAttr(f"{scapular_output}.drawStyle", 2)
        self["output"][c].connect(scapular_negate_inverse)

        # output joint
        if self["create_output_joint"]["value"]:
            for i in range(c + 1):
                self["output_joint"][i].create()

    # endregion

    # region GUIDE
    @build_log(logging.INFO)
    def guide(self):
        super().guide(description=description)

        graph, guide_compound = self.add_guide_graph()

        guide_count = len(self["guide_matrix"]["value"])
        if len(self["guide_mirror_type"]["value"]) != guide_count:
            self["guide_mirror_type"]["value"] = [1 for _ in range(guide_count)]

        name, side, index = self.identifier

        negate_condition = cmds.createNode("condition")
        cmds.connectAttr(f"{self.rig_root}.side", f"{negate_condition}.firstTerm")
        cmds.setAttr(f"{negate_condition}.secondTerm", 2)
        cmds.setAttr(f"{negate_condition}.colorIfTrueR", -1)
        cmds.setAttr(f"{negate_condition}.colorIfFalseR", 1)

        # guide
        clavicle_guide = self.add_guide(
            parent=self.guide_root,
            description="clavicle",
            m=self["guide_matrix"]["value"][0],
            mirror_type=2,
        )
        shoulder_guide = self.add_guide(
            parent=clavicle_guide,
            description="shoulder",
            m=self["guide_matrix"]["value"][1],
            mirror_type=self["guide_mirror_type"]["value"][1],
        )
        elbow_guide = self.add_guide(
            parent=shoulder_guide,
            description="elbow",
            m=self["guide_matrix"]["value"][2],
            mirror_type=self["guide_mirror_type"]["value"][2],
        )
        wrist_guide = self.add_guide(
            parent=elbow_guide,
            description="wrist",
            m=self["guide_matrix"]["value"][3],
            mirror_type=self["guide_mirror_type"]["value"][3],
        )
        wrist_end_guide = self.add_guide(
            parent=wrist_guide,
            description="wristEnd",
            m=self["guide_matrix"]["value"][4],
            mirror_type=self["guide_mirror_type"]["value"][4],
        )
        clavicle_bone_guide = self.add_guide(
            parent=clavicle_guide,
            description="clavicleBone",
            m=self["guide_matrix"]["value"][5],
            mirror_type=self["guide_mirror_type"]["value"][5],
        )
        ins = Transform(
            parent=clavicle_guide,
            name=name,
            side=side,
            index=index,
            description="boneAim",
            extension=Name.loc_extension,
        )
        clavicle_bone_aim_loc = ins.create()
        cmds.setAttr(f"{clavicle_bone_aim_loc}.t", 0, 0, 0)
        cmds.setAttr(f"{clavicle_bone_aim_loc}.r", 0, 0, 0)
        divide = cmds.createNode("divide")
        cmds.connectAttr(
            f"{self.guide_root}.clavicle_bone_distance", f"{divide}.input1"
        )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{clavicle_guide}.worldMatrix[0]", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputScaleX", f"{divide}.input2")
        cmds.connectAttr(f"{divide}.output", f"{clavicle_bone_aim_loc}.tx")
        ins = Joint(
            parent=self.guide_root,
            name=name,
            side=side,
            index=index,
            description="sc0Matrix",
            extension=Name.joint_extension,
            m=ORIGINMATRIX,
        )
        sc0_joint = ins.create()
        cmds.pointConstraint(clavicle_bone_guide, sc0_joint, maintainOffset=False)
        ins = Joint(
            parent=sc0_joint,
            name=name,
            side=side,
            index=index,
            description="sc1Matrix",
            extension=Name.joint_extension,
            m=ORIGINMATRIX,
        )
        sc1_joint = ins.create()
        cmds.setAttr(f"{sc1_joint}.t", 0, 0, 0)
        cmds.setAttr(f"{sc0_joint}.jointOrient", 0, 0, 0)
        cmds.connectAttr(f"{negate_condition}.outColorR", f"{sc1_joint}.tx")
        sc_ikh, _ = cmds.ikHandle(
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="clavicleBoneMatrix",
                extension=Name.ikh_extension,
            ),
            startJoint=sc0_joint,
            endEffector=sc1_joint,
            solver="ikSCsolver",
        )
        sc_ikh = cmds.parent(sc_ikh, self.guide_root)[0]
        cmds.hide(sc_ikh, sc0_joint)
        cmds.pointConstraint(clavicle_bone_guide, sc0_joint, maintainOffset=False)
        cmds.pointConstraint(clavicle_bone_aim_loc, sc_ikh, maintainOffset=False)
        cmds.setAttr(f"{sc_ikh}.r", 0, 0, 0)
        pick_m = cmds.createNode("pickMatrix")
        cmds.setAttr(f"{pick_m}.useRotate", 0)
        cmds.setAttr(f"{pick_m}.useScale", 0)
        cmds.setAttr(f"{pick_m}.useShear", 0)
        cmds.connectAttr(f"{clavicle_guide}.worldMatrix[0]", f"{pick_m}.inputMatrix")
        inverse_m = cmds.createNode("inverseMatrix")
        cmds.connectAttr(f"{pick_m}.outputMatrix", f"{inverse_m}.inputMatrix")
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{sc0_joint}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(f"{inverse_m}.outputMatrix", f"{mult_m}.matrixIn[1]")
        pick_m = cmds.createNode("pickMatrix")
        cmds.setAttr(f"{pick_m}.useScale", 0)
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{pick_m}.inputMatrix")
        cmds.connectAttr(
            f"{pick_m}.outputMatrix", f"{self.guide_root}.clavicle_bone_matrix"
        )
        scapular_guide = self.add_guide(
            parent=clavicle_guide,
            description="scapular",
            m=self["guide_matrix"]["value"][6],
            mirror_type=2,
        )
        scapular_aim_guide = self.add_guide(
            parent=scapular_guide,
            description="scapularAim",
            m=self["guide_matrix"]["value"][7],
            mirror_type=self["guide_mirror_type"]["value"][7],
        )
        cmds.setAttr(f"{scapular_aim_guide}.ty", lock=True)
        cmds.setAttr(f"{scapular_aim_guide}.tz", lock=True)
        cmds.setAttr(f"{scapular_aim_guide}.r", lock=True)
        normalize = cmds.createNode("normalize")
        cmds.connectAttr(f"{scapular_aim_guide}.tx", f"{normalize}.inputX")
        cmds.connectAttr(
            f"{normalize}.outputX", f"{self.guide_root}.scapular_aim_axis_x"
        )
        cmds.connectAttr(f"{scapular_aim_guide}.ty", f"{normalize}.inputY")
        cmds.connectAttr(
            f"{normalize}.outputY", f"{self.guide_root}.scapular_aim_axis_y"
        )
        cmds.connectAttr(f"{scapular_aim_guide}.tz", f"{normalize}.inputZ")
        cmds.connectAttr(
            f"{normalize}.outputZ", f"{self.guide_root}.scapular_aim_axis_z"
        )
        scapular_up_guide = self.add_guide(
            parent=scapular_guide,
            description="scapularUp",
            m=self["guide_matrix"]["value"][8],
            mirror_type=self["guide_mirror_type"]["value"][8],
        )
        cmds.setAttr(f"{scapular_up_guide}.tx", lock=True)
        cmds.setAttr(f"{scapular_up_guide}.tz", lock=True)
        cmds.setAttr(f"{scapular_up_guide}.r", lock=True)
        normalize = cmds.createNode("normalize")
        cmds.connectAttr(f"{scapular_up_guide}.tx", f"{normalize}.inputX")
        cmds.connectAttr(
            f"{normalize}.outputX", f"{self.guide_root}.scapular_up_axis_x"
        )
        cmds.connectAttr(f"{scapular_up_guide}.ty", f"{normalize}.inputY")
        cmds.connectAttr(
            f"{normalize}.outputY", f"{self.guide_root}.scapular_up_axis_y"
        )
        cmds.connectAttr(f"{scapular_up_guide}.tz", f"{normalize}.inputZ")
        cmds.connectAttr(
            f"{normalize}.outputZ", f"{self.guide_root}.scapular_up_axis_z"
        )

        cmds.vnnNode(
            graph,
            "/input",
            createOutputPort=("twist_joint_count", "long"),
        )
        cmds.vnnNode(
            graph,
            "/input",
            createOutputPort=("pole_vector_multiple", "float"),
        )
        cmds.vnnNode(
            graph,
            "/input",
            createOutputPort=("negate", "long"),
        )
        cmds.vnnNode(
            graph,
            "/input",
            createOutputPort=("align_last_transform_to_guide", "long"),
        )
        cmds.vnnNode(
            graph,
            "/output",
            createInputPort=("pole_vector_matrix", "Math::float4x4"),
        )
        cmds.vnnNode(
            graph,
            "/output",
            createInputPort=("driver_inverse_matrix", "array<Math::double4x4>"),
        )
        cmds.vnnNode(
            graph,
            "/output",
            createInputPort=("clavicle_bone_distance", "float"),
        )
        cmds.vnnNode(
            graph,
            "/output",
            createInputPort=("scapular_aim_matrix", "Math::float4x4"),
        )
        cmds.vnnNode(
            graph,
            "/output",
            createInputPort=("scapular_up_matrix", "Math::float4x4"),
        )
        cmds.vnnConnect(
            graph,
            "/input.twist_joint_count",
            f"/{guide_compound}.twist_joint_count",
        )
        cmds.vnnConnect(
            graph,
            "/input.pole_vector_multiple",
            f"/{guide_compound}.pole_vector_multiple",
        )
        cmds.vnnConnect(
            graph,
            "/input.negate",
            f"/{guide_compound}.negate",
        )
        cmds.vnnConnect(
            graph,
            "/input.align_last_transform_to_guide",
            f"/{guide_compound}.align_last_transform_to_guide",
        )
        cmds.vnnConnect(
            graph,
            f"/{guide_compound}.pole_vector_matrix",
            "/output.pole_vector_matrix",
        )
        cmds.vnnConnect(
            graph,
            f"/{guide_compound}.driver_inverse_matrix",
            "/output.driver_inverse_matrix",
        )
        cmds.vnnConnect(
            graph,
            f"/{guide_compound}.clavicle_bone_distance",
            "/output.clavicle_bone_distance",
        )
        cmds.vnnConnect(
            graph,
            f"/{guide_compound}.scapular_aim_matrix",
            "/output.scapular_aim_matrix",
        )
        cmds.vnnConnect(
            graph,
            f"/{guide_compound}.scapular_up_matrix",
            "/output.scapular_up_matrix",
        )
        cmds.connectAttr(f"{self.guide_root}.side", f"{graph}.negate")
        cmds.connectAttr(
            f"{self.guide_root}.align_last_transform_to_guide",
            f"{graph}.align_last_transform_to_guide",
        )
        cmds.connectAttr(
            f"{self.guide_root}.twist_joint_count", f"{graph}.twist_joint_count"
        )
        cmds.connectAttr(
            f"{graph}.clavicle_bone_distance",
            f"{self.guide_root}.clavicle_bone_distance",
        )
        cmds.connectAttr(
            f"{graph}.scapular_aim_matrix",
            f"{self.guide_root}.scapular_aim_matrix",
        )
        cmds.connectAttr(
            f"{graph}.scapular_up_matrix",
            f"{self.guide_root}.scapular_up_matrix",
        )

        mult_m0 = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{shoulder_guide}.worldMatrix[0]", f"{mult_m0}.matrixIn[0]")
        cmds.connectAttr(
            f"{self.guide_root}.worldInverseMatrix[0]", f"{mult_m0}.matrixIn[1]"
        )

        decom_m0 = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m0}.matrixSum", f"{decom_m0}.inputMatrix")

        mult_m1 = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{elbow_guide}.worldMatrix[0]", f"{mult_m1}.matrixIn[0]")
        cmds.connectAttr(
            f"{self.guide_root}.worldInverseMatrix[0]", f"{mult_m1}.matrixIn[1]"
        )

        decom_m1 = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m1}.matrixSum", f"{decom_m1}.inputMatrix")

        mult_m2 = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{wrist_guide}.worldMatrix[0]", f"{mult_m2}.matrixIn[0]")
        cmds.connectAttr(
            f"{self.guide_root}.worldInverseMatrix[0]", f"{mult_m2}.matrixIn[1]"
        )

        decom_m2 = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m2}.matrixSum", f"{decom_m2}.inputMatrix")

        pma0 = cmds.createNode("plusMinusAverage")
        cmds.setAttr(f"{pma0}.operation", 2)
        cmds.connectAttr(f"{decom_m1}.outputTranslate", f"{pma0}.input3D[0]")
        cmds.connectAttr(f"{decom_m0}.outputTranslate", f"{pma0}.input3D[1]")

        pma1 = cmds.createNode("plusMinusAverage")
        cmds.setAttr(f"{pma1}.operation", 2)
        cmds.connectAttr(f"{decom_m2}.outputTranslate", f"{pma1}.input3D[0]")
        cmds.connectAttr(f"{decom_m0}.outputTranslate", f"{pma1}.input3D[1]")

        normalize0 = cmds.createNode("normalize")
        cmds.connectAttr(f"{pma0}.output3D", f"{normalize0}.input")

        normalize1 = cmds.createNode("normalize")
        cmds.connectAttr(f"{pma1}.output3D", f"{normalize1}.input")

        cross_product = cmds.createNode("crossProduct")
        cmds.connectAttr(f"{normalize0}.output", f"{cross_product}.input1")
        cmds.connectAttr(f"{normalize1}.output", f"{cross_product}.input2")

        upperline = cmds.curve(point=((0, 0, 0), (0, 0, 0)), degree=1)
        upperline = cmds.rename(upperline, shoulder_guide.replace("guide", "upperLine"))
        upperline = cmds.parent(upperline, self.guide_root)[0]
        lowerline = cmds.curve(point=((0, 0, 0), (0, 0, 0)), degree=1)
        lowerline = cmds.rename(lowerline, shoulder_guide.replace("guide", "lowerLine"))
        lowerline = cmds.parent(lowerline, self.guide_root)[0]
        cmds.setAttr(f"{upperline}.template", 1)
        cmds.setAttr(f"{lowerline}.template", 1)
        cmds.connectAttr(f"{decom_m0}.outputTranslate", f"{upperline}.controlPoints[0]")
        cmds.connectAttr(f"{decom_m1}.outputTranslate", f"{upperline}.controlPoints[1]")
        cmds.connectAttr(f"{decom_m1}.outputTranslate", f"{lowerline}.controlPoints[0]")
        cmds.connectAttr(f"{decom_m2}.outputTranslate", f"{lowerline}.controlPoints[1]")

        offset_curve0 = cmds.createNode("offsetCurve")
        cmds.setAttr(f"{offset_curve0}.distance", 0.1)
        cmds.connectAttr(f"{upperline}.worldSpace[0]", f"{offset_curve0}.inputCurve")
        cmds.connectAttr(f"{cross_product}.output", f"{offset_curve0}.normal")

        offset_curve1 = cmds.createNode("offsetCurve")
        cmds.setAttr(f"{offset_curve1}.distance", -0.1)
        cmds.connectAttr(f"{upperline}.worldSpace[0]", f"{offset_curve1}.inputCurve")
        cmds.connectAttr(f"{cross_product}.output", f"{offset_curve1}.normal")

        offset_curve2 = cmds.createNode("offsetCurve")
        cmds.setAttr(f"{offset_curve2}.distance", 0.1)
        cmds.connectAttr(f"{lowerline}.worldSpace[0]", f"{offset_curve2}.inputCurve")
        cmds.connectAttr(f"{cross_product}.output", f"{offset_curve2}.normal")

        offset_curve3 = cmds.createNode("offsetCurve")
        cmds.setAttr(f"{offset_curve3}.distance", -0.1)
        cmds.connectAttr(f"{lowerline}.worldSpace[0]", f"{offset_curve3}.inputCurve")
        cmds.connectAttr(f"{cross_product}.output", f"{offset_curve3}.normal")

        linear_rebuild_curve0 = cmds.createNode("rebuildCurve")
        cmds.setAttr(f"{linear_rebuild_curve0}.degree", 1)
        cmds.setAttr(f"{linear_rebuild_curve0}.spans", 4)
        cmds.connectAttr(
            f"{offset_curve0}.outputCurve[0]", f"{linear_rebuild_curve0}.inputCurve"
        )

        linear_rebuild_curve1 = cmds.createNode("rebuildCurve")
        cmds.setAttr(f"{linear_rebuild_curve1}.degree", 1)
        cmds.setAttr(f"{linear_rebuild_curve1}.spans", 4)
        cmds.connectAttr(
            f"{upperline}.worldSpace[0]", f"{linear_rebuild_curve1}.inputCurve"
        )

        linear_rebuild_curve2 = cmds.createNode("rebuildCurve")
        cmds.setAttr(f"{linear_rebuild_curve2}.degree", 1)
        cmds.setAttr(f"{linear_rebuild_curve2}.spans", 4)
        cmds.connectAttr(
            f"{offset_curve1}.outputCurve[0]", f"{linear_rebuild_curve2}.inputCurve"
        )

        linear_rebuild_curve3 = cmds.createNode("rebuildCurve")
        cmds.setAttr(f"{linear_rebuild_curve3}.degree", 1)
        cmds.setAttr(f"{linear_rebuild_curve3}.spans", 4)
        cmds.connectAttr(
            f"{offset_curve2}.outputCurve[0]", f"{linear_rebuild_curve3}.inputCurve"
        )

        linear_rebuild_curve4 = cmds.createNode("rebuildCurve")
        cmds.setAttr(f"{linear_rebuild_curve4}.degree", 1)
        cmds.setAttr(f"{linear_rebuild_curve4}.spans", 4)
        cmds.connectAttr(
            f"{lowerline}.worldSpace[0]", f"{linear_rebuild_curve4}.inputCurve"
        )

        linear_rebuild_curve5 = cmds.createNode("rebuildCurve")
        cmds.setAttr(f"{linear_rebuild_curve5}.degree", 1)
        cmds.setAttr(f"{linear_rebuild_curve5}.spans", 4)
        cmds.connectAttr(
            f"{offset_curve3}.outputCurve[0]", f"{linear_rebuild_curve5}.inputCurve"
        )

        cubic_rebuild_curve0 = cmds.createNode("rebuildCurve")
        cmds.setAttr(f"{cubic_rebuild_curve0}.degree", 3)
        cmds.setAttr(f"{cubic_rebuild_curve0}.keepControlPoints", 1)
        cmds.connectAttr(
            f"{linear_rebuild_curve0}.spans", f"{cubic_rebuild_curve0}.spans"
        )
        cmds.connectAttr(
            f"{linear_rebuild_curve0}.outputCurve", f"{cubic_rebuild_curve0}.inputCurve"
        )

        cubic_rebuild_curve1 = cmds.createNode("rebuildCurve")
        cmds.setAttr(f"{cubic_rebuild_curve1}.degree", 3)
        cmds.setAttr(f"{cubic_rebuild_curve1}.keepControlPoints", 1)
        cmds.connectAttr(
            f"{linear_rebuild_curve1}.spans", f"{cubic_rebuild_curve1}.spans"
        )
        cmds.connectAttr(
            f"{linear_rebuild_curve1}.outputCurve", f"{cubic_rebuild_curve1}.inputCurve"
        )

        cubic_rebuild_curve2 = cmds.createNode("rebuildCurve")
        cmds.setAttr(f"{cubic_rebuild_curve2}.degree", 3)
        cmds.setAttr(f"{cubic_rebuild_curve2}.keepControlPoints", 1)
        cmds.connectAttr(
            f"{linear_rebuild_curve2}.spans", f"{cubic_rebuild_curve2}.spans"
        )
        cmds.connectAttr(
            f"{linear_rebuild_curve2}.outputCurve", f"{cubic_rebuild_curve2}.inputCurve"
        )

        cubic_rebuild_curve3 = cmds.createNode("rebuildCurve")
        cmds.setAttr(f"{cubic_rebuild_curve3}.degree", 3)
        cmds.setAttr(f"{cubic_rebuild_curve3}.keepControlPoints", 1)
        cmds.connectAttr(
            f"{linear_rebuild_curve3}.spans", f"{cubic_rebuild_curve3}.spans"
        )
        cmds.connectAttr(
            f"{linear_rebuild_curve3}.outputCurve", f"{cubic_rebuild_curve3}.inputCurve"
        )

        cubic_rebuild_curve4 = cmds.createNode("rebuildCurve")
        cmds.setAttr(f"{cubic_rebuild_curve4}.degree", 3)
        cmds.setAttr(f"{cubic_rebuild_curve4}.keepControlPoints", 1)
        cmds.connectAttr(
            f"{linear_rebuild_curve4}.spans", f"{cubic_rebuild_curve4}.spans"
        )
        cmds.connectAttr(
            f"{linear_rebuild_curve4}.outputCurve", f"{cubic_rebuild_curve4}.inputCurve"
        )

        cubic_rebuild_curve5 = cmds.createNode("rebuildCurve")
        cmds.setAttr(f"{cubic_rebuild_curve5}.degree", 3)
        cmds.setAttr(f"{cubic_rebuild_curve5}.keepControlPoints", 1)
        cmds.connectAttr(
            f"{linear_rebuild_curve5}.spans", f"{cubic_rebuild_curve5}.spans"
        )
        cmds.connectAttr(
            f"{linear_rebuild_curve5}.outputCurve", f"{cubic_rebuild_curve5}.inputCurve"
        )

        upper_loft = cmds.createNode("loft")
        cmds.setAttr(f"{upper_loft}.degree", 1)
        cmds.connectAttr(
            f"{cubic_rebuild_curve0}.outputCurve", f"{upper_loft}.inputCurve[0]"
        )
        cmds.connectAttr(
            f"{cubic_rebuild_curve1}.outputCurve", f"{upper_loft}.inputCurve[1]"
        )
        cmds.connectAttr(
            f"{cubic_rebuild_curve2}.outputCurve", f"{upper_loft}.inputCurve[2]"
        )
        rebuild_surface = cmds.createNode("rebuildSurface")
        cmds.connectAttr(
            f"{upper_loft}.outputSurface", f"{rebuild_surface}.inputSurface"
        )
        cmds.setAttr(f"{rebuild_surface}.spansU", 2)
        cmds.setAttr(f"{rebuild_surface}.spansV", 2)
        cmds.setAttr(f"{rebuild_surface}.degreeU", 1)
        cmds.setAttr(f"{rebuild_surface}.degreeV", 3)
        cmds.setAttr(f"{rebuild_surface}.direction", 2)
        cmds.setAttr(f"{rebuild_surface}.keepRange", 0)
        cmds.connectAttr(
            f"{rebuild_surface}.outputSurface",
            f"{self.guide_root}.upper_ribbon_surface",
        )

        lower_loft = cmds.createNode("loft")
        cmds.setAttr(f"{lower_loft}.degree", 1)
        cmds.connectAttr(
            f"{cubic_rebuild_curve3}.outputCurve", f"{lower_loft}.inputCurve[0]"
        )
        cmds.connectAttr(
            f"{cubic_rebuild_curve4}.outputCurve", f"{lower_loft}.inputCurve[1]"
        )
        cmds.connectAttr(
            f"{cubic_rebuild_curve5}.outputCurve", f"{lower_loft}.inputCurve[2]"
        )
        rebuild_surface = cmds.createNode("rebuildSurface")
        cmds.connectAttr(
            f"{lower_loft}.outputSurface", f"{rebuild_surface}.inputSurface"
        )
        cmds.setAttr(f"{rebuild_surface}.spansU", 2)
        cmds.setAttr(f"{rebuild_surface}.spansV", 2)
        cmds.setAttr(f"{rebuild_surface}.degreeU", 1)
        cmds.setAttr(f"{rebuild_surface}.degreeV", 3)
        cmds.setAttr(f"{rebuild_surface}.direction", 2)
        cmds.setAttr(f"{rebuild_surface}.keepRange", 0)
        cmds.connectAttr(
            f"{rebuild_surface}.outputSurface",
            f"{self.guide_root}.lower_ribbon_surface",
        )

        for i in range(9):
            cmds.connectAttr(
                f"{self.guide_graph}.npo_matrix[{i}]",
                f"{self.guide_root}.npo_matrix[{i}]",
            )
        for i in range(6):
            cmds.connectAttr(
                f"{self.guide_graph}.driver_inverse_matrix[{i}]",
                f"{self.guide_root}.driver_inverse_matrix[{i}]",
            )
        for i in range(len(self["initialize_output_matrix"]["value"])):
            cmds.connectAttr(
                f"{self.guide_graph}.initialize_output_matrix[{i}]",
                f"{self.guide_root}.initialize_output_matrix[{i}]",
            )
            cmds.connectAttr(
                f"{self.guide_graph}.initialize_output_inverse_matrix[{i}]",
                f"{self.guide_root}.initialize_output_inverse_matrix[{i}]",
            )

        # pole vector guide
        cmds.addAttr(
            elbow_guide,
            longName="pole_vector_multiple",
            attributeType="float",
            keyable=True,
            defaultValue=self["pole_vector_multiple"]["value"],
        )
        multiply = cmds.createNode("multiply")
        cmds.connectAttr(f"{elbow_guide}.pole_vector_multiple", f"{multiply}.input[0]")

        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{self.guide_root}.worldMatrix[0]", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputScaleX", f"{multiply}.input[1]")
        cmds.connectAttr(
            f"{multiply}.output", f"{self.guide_root}.pole_vector_multiple"
        )
        cmds.connectAttr(
            f"{self.guide_root}.pole_vector_multiple",
            f"{self.guide_graph}.pole_vector_multiple",
        )
        cmds.connectAttr(
            f"{self.guide_graph}.pole_vector_matrix",
            f"{self.guide_root}.pole_vector_matrix",
        )

    # endregion
