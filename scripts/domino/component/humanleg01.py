# domino
from domino import component
from domino.core import attribute, Name, Transform, Joint, rigkit, NurbsSurface
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
    om.MVector((0.8842910385180538, 9.667090526505518, 0.1690758409372688)),
    om.MSpace.kObject,
)
radians = [
    om.MAngle(x, om.MAngle.kDegrees).asRadians()
    for x in (90, 3.527297366784589, -85.9752590901959)
]
euler_rot = om.MEulerRotation(radians, om.MEulerRotation.kXYZ)
tm0.setRotation(euler_rot)
matrices.append(list(tm0.asMatrix()))

tm1 = om.MTransformationMatrix(m)
tm1.setTranslation(om.MVector((4.6, 0, 0)), om.MSpace.kObject)
radians = [om.MAngle(x, om.MAngle.kDegrees).asRadians() for x in (0, 0, -1.0)]
euler_rot = om.MEulerRotation(radians, om.MEulerRotation.kXYZ)
tm1.setRotation(euler_rot)
matrices.append(list(tm1.asMatrix() * tm0.asMatrix()))

tm2 = om.MTransformationMatrix(m)
tm2.setTranslation(
    om.MVector((3.9780000000000006, -2.220446049250313e-16, -4.440892098500626e-16)),
    om.MSpace.kObject,
)
radians = [
    om.MAngle(x, om.MAngle.kDegrees).asRadians()
    for x in (265.975, 8.250965870290722, 94.5272973667846)
]
euler_rot = om.MEulerRotation(radians, om.MEulerRotation.kXYZ)
tm2.setRotation(euler_rot)
matrices.append(list(tm2.asMatrix() * tm1.asMatrix() * tm0.asMatrix()))

tm3 = om.MTransformationMatrix(m)
tm3.setTranslation(om.MVector((1, 0, 0)), om.MSpace.kObject)
matrices.append(list(tm3.asMatrix() * tm2.asMatrix() * tm1.asMatrix() * tm0.asMatrix()))

DATA = [
    attribute.String(longName="component", value="humanleg01"),
    attribute.String(longName="name", value="humanLeg"),
    attribute.Enum(longName="side", enumName=Name.side_list, value=0),
    attribute.Integer(longName="index", minValue=0),
    attribute.Matrix(longName="guide_matrix", multi=True, value=matrices),
    attribute.Matrix(longName="npo_matrix", multi=True, value=matrices),
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
    attribute.Integer(longName="guide_mirror_type", multi=True, value=[1, 1, 1, 1]),
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
    attribute.Float(longName="pole_vector_multiple", minValue=1, value=5),
    attribute.Matrix(longName="pole_vector_matrix", value=list(ORIGINMATRIX)),
    attribute.Enum(
        longName="controller_primary_axis", enumName=["x", "y", "z"], value=0
    ),
    attribute.Enum(
        longName="controller_secondary_axis", enumName=["x", "y", "z"], value=1
    ),
    attribute.Bool(longName="align_last_transform_to_guide", defaultValue=1, value=1),
    attribute.Bool(longName="unlock_last_scale", defaultValue=0),
    attribute.Matrix(
        longName="driver_inverse_matrix",
        multi=True,
        value=[list(ORIGINMATRIX) for _ in range(6)],
    ),
    attribute.NurbsSurface(
        longName="upper_ribbon_surface",
        value={
            "parent_name": "",
            "surface_name": "upperRibbonSurface",
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
            "visibility": True,
            "surface": {
                "form_u": 0,
                "form_v": 0,
                "knot_u": [0.0, 0.0, 0.0, 0.5, 1.0, 1.0, 1.0],
                "knot_v": [0.0, 1.0],
                "degree_u": 3,
                "degree_v": 1,
                "cvs": [
                    (0.883859001537635, 9.673227745707386, 0.06926528095228635, 1.0),
                    (0.8847230754984726, 9.660953307303652, 0.2688864009222512, 1.0),
                    (0.9644214039926372, 8.52823702214492, -0.0014874028595507627, 1.0),
                    (0.9652854779534749, 8.515962583741182, 0.1981337171104141, 1.0),
                    (1.044983806447639, 7.383246298582454, -0.07224008667138754, 1.0),
                    (1.0458478804084765, 7.37097186017872, 0.12738103329857747, 1.0),
                    (1.1255462089026416, 6.238255575019987, -0.1429927704832247, 1.0),
                    (1.126410282863479, 6.225981136616249, 0.05662834948674021, 1.0),
                    (1.2061086113576434, 5.09326485145752, -0.21374545429506153, 1.0),
                    (1.2069726853184808, 5.080990413053785, -0.014124334325096632, 1.0),
                ],
            },
        },
    ),
    attribute.NurbsSurface(
        longName="lower_ribbon_surface",
        value={
            "parent_name": "",
            "surface_name": "lowerRibbonSurface",
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
            "visibility": True,
            "surface": {
                "form_u": 0,
                "form_v": 0,
                "knot_u": [0.0, 0.0, 0.0, 0.5, 1.0, 1.0, 1.0],
                "knot_v": [0.0, 1.0],
                "degree_u": 3,
                "degree_v": 1,
                "cvs": [
                    (1.205986410170961, 5.0950014849106315, -0.2136228715616859, 1.0),
                    (1.2070948673984767, 5.079253648636767, -0.014246911874914637, 1.0),
                    (1.275569812138244, 4.106049437868076, -0.2921227802787598, 1.0),
                    (1.27667826936576, 4.09030160159421, -0.09274682059198859, 1.0),
                    (1.3451532141055262, 3.1170973908255166, -0.3706226889958337, 1.0),
                    (1.3462616998590429, 3.1013495521250096, -0.17124673274091823, 1.0),
                    (1.4147366425280232, 2.1281453412106135, -0.4491226011447592, 1.0),
                    (1.4158451018263263, 2.112397505082451, -0.24974664145799225, 1.0),
                    (1.4843200444953064, 1.1391932941680574, -0.5276225098618335, 1.0),
                    (1.4854285037936092, 1.1234454580398952, -0.32824655017506643, 1.0),
                ],
            },
        },
    ),
]

description = """## humanleg01
---

human leg component 입니다.
fkik2jnt01 을 베이스로 수정되었습니다.

ik 를 생성하기 때문에 humanleg 구성요소를 일직선 상에 놓지 마세요.  
rotate 를 사용해서 평면을 만들어주세요.

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
            fk_descriptions = ["thigh", "knee", "ankle"]
            parent_controllers = [(self.identifier, "host")]
            for description in fk_descriptions:
                self.add_controller(
                    description=description,
                    parent_controllers=parent_controllers,
                )
                parent_controllers = [(self.identifier, description)]

            parent_controllers = [(self.identifier, "host")]
            ik_descriptions = ["ikPos", "poleVec", "ik", "ikLocal"]
            for description in ik_descriptions:
                self.add_controller(
                    description=description,
                    parent_controllers=parent_controllers,
                )
                parent_controllers = [(self.identifier, description)]

            self.add_controller(
                description="pin",
                parent_controllers=[(self.identifier, "knee")],
            )
            self.add_controller(
                description="upperBend",
                parent_controllers=[(self.identifier, "pin")],
            )
            self.add_controller(
                description="lowerBend",
                parent_controllers=[(self.identifier, "pin")],
            )

    def populate_output(self):
        if not self["output"]:
            self.add_output(description="thigh", extension=Name.output_extension)
            for i in range(self["twist_joint_count"]["value"]):
                self.add_output(
                    description=f"upperTwist{i}", extension=Name.output_extension
                )
            self.add_output(description="knee", extension=Name.output_extension)
            for i in range(self["twist_joint_count"]["value"]):
                self.add_output(
                    description=f"lowerTwist{i}", extension=Name.output_extension
                )
            self.add_output(description="ankle", extension=Name.output_extension)

    def populate_output_joint(self):
        if not self["output_joint"]:
            self.add_output_joint(parent_description=None, description="thigh")
            parent_description = "thigh"
            for i in range(self["twist_joint_count"]["value"]):
                description = f"upperTwist{i}"
                self.add_output_joint(
                    parent_description=parent_description, description=description
                )
                parent_description = description
            self.add_output_joint(
                parent_description=parent_description, description="knee"
            )
            parent_description = "knee"
            for i in range(self["twist_joint_count"]["value"]):
                description = f"lowerTwist{i}"
                self.add_output_joint(
                    parent_description=parent_description, description=description
                )
                parent_description = description
            self.add_output_joint(
                parent_description=parent_description, description="ankle"
            )

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

        # controller
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
            longName="fkik",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=0,
            keyable=True,
        )
        cmds.addAttr(
            host_ctl,
            longName="start_roll",
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
        thigh_npo, thigh_ctl = self["controller"][1].create(
            parent=self.rig_root,
            shape=(
                self["controller"][1]["shape"]
                if "shape" in self["controller"][1]
                else "cube"
            ),
            color=12,
            npo_matrix_index=0,
        )
        cmds.setAttr(f"{thigh_ctl}.mirror_type", 1)
        ins = Transform(
            parent=thigh_ctl,
            name=name,
            side=side,
            index=index,
            description="thighLength",
            m=ORIGINMATRIX,
        )
        thigh_length_grp = ins.create()
        cmds.setAttr(f"{thigh_length_grp}.t", 0, 0, 0)
        cmds.setAttr(f"{thigh_length_grp}.r", 0, 0, 0)
        cmds.addAttr(
            thigh_ctl,
            longName="length",
            attributeType="float",
            keyable=True,
            defaultValue=0,
        )
        multiply0 = cmds.createNode("multiply")
        cmds.connectAttr(f"{thigh_ctl}.length", f"{multiply0}.input[0]")
        cmds.connectAttr(f"{negate_condition}.outColorR", f"{multiply0}.input[1]")
        cmds.connectAttr(f"{multiply0}.output", f"{thigh_length_grp}.tx")

        knee_npo, knee_ctl = self["controller"][2].create(
            parent=thigh_length_grp,
            shape=(
                self["controller"][2]["shape"]
                if "shape" in self["controller"][2]
                else "cube"
            ),
            color=12,
            npo_matrix_index=1,
        )
        cmds.setAttr(f"{knee_ctl}.rx", lock=True, keyable=False)
        cmds.setAttr(f"{knee_ctl}.rz", lock=True, keyable=False)
        cmds.setAttr(f"{knee_ctl}.mirror_type", 1)
        ins = Transform(
            parent=knee_ctl,
            name=name,
            side=side,
            index=index,
            description="kneeLength",
            m=ORIGINMATRIX,
        )
        knee_length_grp = ins.create()
        cmds.setAttr(f"{knee_length_grp}.t", 0, 0, 0)
        cmds.setAttr(f"{knee_length_grp}.r", 0, 0, 0)
        cmds.addAttr(
            knee_ctl,
            longName="length",
            attributeType="float",
            keyable=True,
            defaultValue=0,
        )
        multiply0 = cmds.createNode("multiply")
        cmds.connectAttr(f"{knee_ctl}.length", f"{multiply0}.input[0]")
        cmds.connectAttr(f"{negate_condition}.outColorR", f"{multiply0}.input[1]")
        cmds.connectAttr(f"{multiply0}.output", f"{knee_length_grp}.tx")

        ankle_npo, ankle_ctl = self["controller"][3].create(
            parent=knee_length_grp,
            shape=(
                self["controller"][3]["shape"]
                if "shape" in self["controller"][3]
                else "cube"
            ),
            color=12,
            npo_matrix_index=2,
        )
        cmds.setAttr(f"{ankle_ctl}.mirror_type", 1)
        if self["unlock_last_scale"]["value"]:
            cmds.setAttr(f"{ankle_ctl}.sx", lock=False, keyable=True)
            cmds.setAttr(f"{ankle_ctl}.sy", lock=False, keyable=True)
            cmds.setAttr(f"{ankle_ctl}.sz", lock=False, keyable=True)
        else:
            cmds.setAttr(f"{ankle_ctl}.sx", lock=True, keyable=False)
            cmds.setAttr(f"{ankle_ctl}.sy", lock=True, keyable=False)
            cmds.setAttr(f"{ankle_ctl}.sz", lock=True, keyable=False)

        ik_pos_npo, ik_pos_ctl = self["controller"][4].create(
            parent=self.rig_root,
            shape=(
                self["controller"][4]["shape"]
                if "shape" in self["controller"][4]
                else "cube"
            ),
            color=12,
            npo_matrix_index=3,
        )
        cmds.setAttr(f"{ik_pos_ctl}.rx", lock=True, keyable=False)
        cmds.setAttr(f"{ik_pos_ctl}.ry", lock=True, keyable=False)
        cmds.setAttr(f"{ik_pos_ctl}.rz", lock=True, keyable=False)
        cmds.setAttr(f"{ik_pos_ctl}.mirror_type", 0)

        pole_vec_npo, pole_vec_ctl = self["controller"][5].create(
            parent=self.rig_root,
            shape=(
                self["controller"][5]["shape"]
                if "shape" in self["controller"][5]
                else "cube"
            ),
            color=12,
        )
        cmds.setAttr(f"{pole_vec_ctl}.rx", lock=True, keyable=False)
        cmds.setAttr(f"{pole_vec_ctl}.ry", lock=True, keyable=False)
        cmds.setAttr(f"{pole_vec_ctl}.rz", lock=True, keyable=False)
        cmds.setAttr(f"{pole_vec_ctl}.mirror_type", 0)
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
        guideline = cmds.parent(guideline, self.rig_root)[0]
        cmds.setAttr(f"{guideline}.overrideEnabled", 1)
        cmds.setAttr(f"{guideline}.overrideDisplayType", 1)
        cmds.setAttr(f"{guideline}.t", 0, 0, 0)
        cmds.setAttr(f"{guideline}.r", 0, 0, 0)

        ins = Joint(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description="fk0",
            extension=Name.joint_extension,
            m=cmds.xform(thigh_ctl, query=True, matrix=True, worldSpace=True),
            use_joint_convention=False,
        )
        fk0_jnt = ins.create()
        cmds.parentConstraint(thigh_ctl, fk0_jnt, maintainOffset=False)
        cmds.scaleConstraint(thigh_ctl, fk0_jnt, maintainOffset=False)
        cmds.hide(fk0_jnt)

        ins = Joint(
            parent=fk0_jnt,
            name=name,
            side=side,
            index=index,
            description="fk1",
            extension=Name.joint_extension,
            m=cmds.xform(knee_ctl, query=True, matrix=True, worldSpace=True),
            use_joint_convention=False,
        )
        fk1_jnt = ins.create()
        cmds.parentConstraint(knee_ctl, fk1_jnt, maintainOffset=False)
        cmds.scaleConstraint(knee_ctl, fk1_jnt, maintainOffset=False)

        ins = Joint(
            parent=fk1_jnt,
            name=name,
            side=side,
            index=index,
            description="fk2",
            extension=Name.joint_extension,
            m=cmds.xform(ankle_ctl, query=True, matrix=True, worldSpace=True),
            use_joint_convention=False,
        )
        fk2_jnt = ins.create()
        cmds.parentConstraint(ankle_ctl, fk2_jnt, maintainOffset=False)
        cmds.scaleConstraint(ankle_ctl, fk2_jnt, maintainOffset=False)

        ins = Joint(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description="ik0",
            extension=Name.joint_extension,
            m=cmds.xform(thigh_ctl, query=True, matrix=True, worldSpace=True),
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
            m=cmds.xform(knee_ctl, query=True, matrix=True, worldSpace=True),
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
            m=cmds.xform(ankle_ctl, query=True, matrix=True, worldSpace=True),
            use_joint_convention=False,
        )
        ik2_jnt = ins.create()
        cmds.pointConstraint(ik_pos_ctl, ik0_jnt, maintainOffset=False)
        cmds.hide(ik0_jnt)

        ik_npo, ik_ctl = self["controller"][6].create(
            parent=self.rig_root,
            shape=(
                self["controller"][6]["shape"]
                if "shape" in self["controller"][6]
                else "cube"
            ),
            color=12,
            npo_matrix_index=4,
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

        ik_local_npo, ik_local_ctl = self["controller"][7].create(
            parent=ik_ctl,
            shape=(
                self["controller"][7]["shape"]
                if "shape" in self["controller"][7]
                else "cube"
            ),
            color=12,
            npo_matrix_index=5,
        )
        cmds.setAttr(f"{ik_local_ctl}.mirror_type", 1)
        if self["unlock_last_scale"]["value"]:
            cmds.setAttr(f"{ik_local_ctl}.sx", lock=False, keyable=True)
            cmds.setAttr(f"{ik_local_ctl}.sy", lock=False, keyable=True)
            cmds.setAttr(f"{ik_local_ctl}.sz", lock=False, keyable=True)
        else:
            cmds.setAttr(f"{ik_local_ctl}.sx", lock=True, keyable=False)
            cmds.setAttr(f"{ik_local_ctl}.sy", lock=True, keyable=False)
            cmds.setAttr(f"{ik_local_ctl}.sz", lock=True, keyable=False)
        ik_local_loc = cmds.createNode(
            "transform",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="ikLocal",
                extension=Name.loc_extension,
            ),
            parent=ik_local_ctl,
        )

        cmds.orientConstraint(ik_local_loc, ik2_jnt)
        cmds.scaleConstraint(ik_local_loc, ik2_jnt)

        cmds.connectAttr(f"{host_ctl}.fkik", f"{ik_pos_npo}.v")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{pole_vec_npo}.v")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{ik_npo}.v")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{guideline}.v")

        rev = cmds.createNode("reverse")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{rev}.inputX")
        cmds.connectAttr(f"{rev}.outputX", f"{thigh_npo}.v")

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
            ik_local_loc, ik_aim_grp, maintainOffset=False, aimVector=(1, 0, 0)
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
        original_distance_curve = cmds.parent(original_distance_curve, self.rig_root)[0]
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
                f"{self.rig_root}.npo_matrix[0]",
                f"{self.rig_root}.npo_matrix[1]",
                f"{self.rig_root}.npo_matrix[2]",
            ],
            initial_ik_curve=original_distance_curve,
            joints=[ik0_jnt, ik1_jnt, ik2_jnt],
            ik_pos_driver=ik_pos_ctl,
            ik_driver=ik_local_loc,
            pole_vector=pole_vec_ctl,
            attach_pole_vector_attr=f"{ik_ctl}.attach_to_PV",
            scale_attr=f"{ik_ctl}.ik_scale",
            slide_attr=f"{ik_ctl}.slide",
            soft_ik_attr=f"{ik_ctl}.soft_ik",
            max_stretch_attr=f"{ik_ctl}.max_stretch",
        )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{self.rig_root}.npo_matrix[0]", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{fk0_jnt}.jointOrient")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{ik0_jnt}.jointOrient")
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{self.rig_root}.npo_matrix[1]", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{fk1_jnt}.jointOrient")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{ik1_jnt}.jointOrient")
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{self.rig_root}.npo_matrix[2]", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{fk2_jnt}.jointOrient")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{ik2_jnt}.jointOrient")

        ins = Joint(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description="blend0",
            extension=Name.joint_extension,
            m=cmds.xform(thigh_ctl, query=True, matrix=True, worldSpace=True),
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
            m=cmds.xform(knee_ctl, query=True, matrix=True, worldSpace=True),
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
            m=cmds.xform(ankle_ctl, query=True, matrix=True, worldSpace=True),
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
        cmds.connectAttr(f"{fk0_jnt}.t", f"{pair_b}.inTranslate1")
        cmds.connectAttr(f"{fk0_jnt}.r", f"{pair_b}.inRotate1")
        cmds.connectAttr(f"{ik0_jnt}.t", f"{pair_b}.inTranslate2")
        cmds.connectAttr(f"{ik0_jnt}.r", f"{pair_b}.inRotate2")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{pair_b}.weight")
        cmds.connectAttr(f"{pair_b}.outTranslate", f"{blend0_jnt}.t")
        cmds.connectAttr(f"{pair_b}.outRotate", f"{blend0_jnt}.r")

        pair_b = cmds.createNode("pairBlend")
        cmds.setAttr(f"{pair_b}.rotInterpolation", 1)
        cmds.connectAttr(f"{fk1_jnt}.t", f"{pair_b}.inTranslate1")
        cmds.connectAttr(f"{fk1_jnt}.r", f"{pair_b}.inRotate1")
        cmds.connectAttr(f"{ik1_jnt}.t", f"{pair_b}.inTranslate2")
        cmds.connectAttr(f"{ik1_jnt}.r", f"{pair_b}.inRotate2")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{pair_b}.weight")
        cmds.connectAttr(f"{pair_b}.outTranslate", f"{blend1_jnt}.t")
        cmds.connectAttr(f"{pair_b}.outRotate", f"{blend1_jnt}.r")

        pair_b = cmds.createNode("pairBlend")
        cmds.setAttr(f"{pair_b}.rotInterpolation", 1)
        cmds.connectAttr(f"{fk2_jnt}.t", f"{pair_b}.inTranslate1")
        cmds.connectAttr(f"{fk2_jnt}.r", f"{pair_b}.inRotate1")
        cmds.connectAttr(f"{ik2_jnt}.t", f"{pair_b}.inTranslate2")
        cmds.connectAttr(f"{ik2_jnt}.r", f"{pair_b}.inRotate2")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{pair_b}.weight")
        cmds.connectAttr(f"{pair_b}.outTranslate", f"{blend2_jnt}.t")
        cmds.connectAttr(f"{pair_b}.outRotate", f"{blend2_jnt}.r")
        blend_color = cmds.createNode("blendColors")
        cmds.connectAttr(f"{ik2_jnt}.s", f"{blend_color}.color1")
        cmds.connectAttr(f"{ankle_ctl}.s", f"{blend_color}.color2")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{blend_color}.blender")
        cmds.connectAttr(f"{blend_color}.output", f"{blend2_jnt}.s")
        cmds.hide(blend0_jnt)

        # region RIG - twist SC joint
        ins = Joint(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description="upperNonTwist0",
            extension="SC",
            m=ORIGINMATRIX,
            use_joint_convention=False,
        )
        upper_non_twist0_jnt = ins.create()

        start_roll = cmds.createNode(
            "transform",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                extension="start_roll",
            ),
            parent=upper_non_twist0_jnt,
        )
        cmds.connectAttr(f"{host_ctl}.start_roll", f"{start_roll}.rx")

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
        upper_non_twist_ikh = cmds.parent(upper_non_twist_ikh, self.rig_root)[0]

        ins = Joint(
            parent=self.rig_root,
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
        upper_twist_ikh = cmds.parent(upper_twist_ikh, self.rig_root)[0]

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
        pin_npo, pin_ctl = self["controller"][8].create(
            parent=self.rig_root,
            shape=(
                self["controller"][8]["shape"]
                if "shape" in self["controller"][8]
                else "cube"
            ),
            color=12,
        )
        upper_bend_npo, upper_bend_ctl = self["controller"][9].create(
            parent=self.rig_root,
            shape=(
                self["controller"][9]["shape"]
                if "shape" in self["controller"][9]
                else "cube"
            ),
            color=12,
        )
        lower_bend_npo, lower_bend_ctl = self["controller"][10].create(
            parent=self.rig_root,
            shape=(
                self["controller"][10]["shape"]
                if "shape" in self["controller"][10]
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
            start_roll, upper_twist0_jnt, upper_bend_npo, maintainOffset=False
        )[0]
        cmds.setAttr(f"{cons}.interpType", 2)
        cmds.pointConstraint(pin_ctl, lower_non_twist0_jnt, maintainOffset=False)
        cmds.pointConstraint(pin_ctl, lower_twist0_jnt, maintainOffset=False)
        cmds.parentConstraint(blend1_jnt, pin_npo, maintainOffset=False)
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{pole_vec_ctl}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{self.rig_root}.worldInverseMatrix[0]",
            f"{mult_m}.matrixIn[1]",
        )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{guideline}.cv[0]")
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{pin_ctl}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{self.rig_root}.worldInverseMatrix[0]",
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
            parent=start_roll,
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
            parent=self.rig_root,
        )
        ins = NurbsSurface(data=self["upper_ribbon_surface"]["value"])
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
        ins = NurbsSurface(data=self["lower_ribbon_surface"]["value"])
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
            secondary_axis=(0, 0, -1),
        )
        cmds.connectAttr(
            f"{self.rig_root}.upper_ribbon_surface",
            f"{upper_ribbon_surface}ShapeOrig.create",
        )
        sc = cmds.findDeformers(upper_ribbon_surface)[0]
        cmds.sets(sc, edit=True, addElement=component.DEFORMER_WEIGHTS_SETS)

        cmds.skinPercent(
            sc, f"{upper_ribbon_surface}.cv[0][1]", transformValue=[driver_joints[0], 1]
        )
        cmds.skinPercent(
            sc,
            f"{upper_ribbon_surface}.cv[1][*]",
            transformValue=[(driver_joints[0], 0.5), (driver_joints[1], 0.5)],
        )
        cmds.skinPercent(
            sc, f"{upper_ribbon_surface}.cv[2][*]", transformValue=[driver_joints[1], 1]
        )
        cmds.skinPercent(
            sc,
            f"{upper_ribbon_surface}.cv[3][*]",
            transformValue=[(driver_joints[1], 0.5), (driver_joints[2], 0.5)],
        )
        cmds.skinPercent(
            sc, f"{upper_ribbon_surface}.cv[4][*]", transformValue=[driver_joints[2], 1]
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
            secondary_axis=(0, 0, -1),
        )
        cmds.connectAttr(
            f"{self.rig_root}.lower_ribbon_surface",
            f"{lower_ribbon_surface}ShapeOrig.create",
        )
        sc = cmds.findDeformers(lower_ribbon_surface)[0]
        cmds.sets(sc, edit=True, addElement=component.DEFORMER_WEIGHTS_SETS)

        cmds.skinPercent(
            sc, f"{lower_ribbon_surface}.cv[0][*]", transformValue=[driver_joints[3], 1]
        )
        cmds.skinPercent(
            sc,
            f"{lower_ribbon_surface}.cv[1][*]",
            transformValue=[(driver_joints[3], 0.5), (driver_joints[4], 0.5)],
        )
        cmds.skinPercent(
            sc, f"{lower_ribbon_surface}.cv[2][*]", transformValue=[driver_joints[4], 1]
        )
        cmds.skinPercent(
            sc,
            f"{lower_ribbon_surface}.cv[3][*]",
            transformValue=[(driver_joints[4], 0.5), (driver_joints[5], 0.5)],
        )
        cmds.skinPercent(
            sc, f"{lower_ribbon_surface}.cv[4][*]", transformValue=[driver_joints[5], 1]
        )
        cmds.hide(ribbon_grp)
        # endregion

        # wrist
        ins = Transform(
            parent=lower_ribbon_outputs[-1],
            name=name,
            side=side,
            index=index,
            description="ankle",
            extension=Name.loc_extension,
        )
        ankle_loc = ins.create()
        cmds.setAttr(f"{ankle_loc}.t", 0, 0, 0)
        cmds.orientConstraint(blend2_jnt, ankle_loc, maintainOffset=False)

        # output
        c = 0
        ins = Joint(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description="thigh",
            extension=Name.output_extension,
            m=ORIGINMATRIX,
        )
        thigh_loc = ins.create()
        cmds.setAttr(f"{thigh_loc}.drawStyle", 2)
        self["output"][c].connect(start_roll)

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
            description="knee",
            extension=Name.output_extension,
            m=ORIGINMATRIX,
        )
        knee_loc = ins.create()
        cmds.setAttr(f"{knee_loc}.drawStyle", 2)
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
            description="ankle",
            extension=Name.output_extension,
            m=ORIGINMATRIX,
        )
        ankle_output = ins.create()
        cmds.setAttr(f"{ankle_output}.drawStyle", 2)
        self["output"][c].connect(ankle_loc)

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

        negate_condition = cmds.createNode("condition")
        cmds.connectAttr(f"{self.rig_root}.side", f"{negate_condition}.firstTerm")
        cmds.setAttr(f"{negate_condition}.secondTerm", 2)
        cmds.setAttr(f"{negate_condition}.colorIfTrueR", -1)
        cmds.setAttr(f"{negate_condition}.colorIfFalseR", 1)

        # guide
        guide0 = self.add_guide(
            parent=self.guide_root,
            description="thigh",
            m=self["guide_matrix"]["value"][0],
            mirror_type=self["guide_mirror_type"]["value"][0],
        )

        guide1 = self.add_guide(
            parent=guide0,
            description="knee",
            m=self["guide_matrix"]["value"][1],
            mirror_type=self["guide_mirror_type"]["value"][1],
        )

        guide2 = self.add_guide(
            parent=guide1,
            description="ankle",
            m=self["guide_matrix"]["value"][2],
            mirror_type=self["guide_mirror_type"]["value"][2],
        )

        guide3 = self.add_guide(
            parent=guide2,
            description="ankleAim",
            m=self["guide_matrix"]["value"][3],
            mirror_type=self["guide_mirror_type"]["value"][3],
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
        cmds.connectAttr(f"{self.guide_root}.side", f"{graph}.negate")
        cmds.connectAttr(
            f"{self.guide_root}.align_last_transform_to_guide",
            f"{graph}.align_last_transform_to_guide",
        )
        cmds.connectAttr(
            f"{self.guide_root}.twist_joint_count", f"{graph}.twist_joint_count"
        )

        mult_m0 = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{guide0}.worldMatrix[0]", f"{mult_m0}.matrixIn[0]")
        cmds.connectAttr(
            f"{self.guide_root}.worldInverseMatrix[0]", f"{mult_m0}.matrixIn[1]"
        )

        decom_m0 = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m0}.matrixSum", f"{decom_m0}.inputMatrix")

        mult_m1 = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{guide1}.worldMatrix[0]", f"{mult_m1}.matrixIn[0]")
        cmds.connectAttr(
            f"{self.guide_root}.worldInverseMatrix[0]", f"{mult_m1}.matrixIn[1]"
        )

        decom_m1 = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m1}.matrixSum", f"{decom_m1}.inputMatrix")

        mult_m2 = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{guide2}.worldMatrix[0]", f"{mult_m2}.matrixIn[0]")
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
        upperline = cmds.rename(upperline, guide0.replace("guide", "upperLine"))
        upperline = cmds.parent(upperline, self.guide_root)[0]
        cmds.setAttr(f"{upperline}.t", lock=True)
        cmds.setAttr(f"{upperline}.r", lock=True)
        cmds.setAttr(f"{upperline}.s", lock=True)
        cmds.setAttr(f"{upperline}.template", 1)
        lowerline = cmds.curve(point=((0, 0, 0), (0, 0, 0)), degree=1)
        lowerline = cmds.rename(lowerline, guide0.replace("guide", "lowerLine"))
        lowerline = cmds.parent(lowerline, self.guide_root)[0]
        cmds.setAttr(f"{lowerline}.t", lock=True)
        cmds.setAttr(f"{lowerline}.r", lock=True)
        cmds.setAttr(f"{lowerline}.s", lock=True)
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
            f"{offset_curve1}.outputCurve[0]", f"{linear_rebuild_curve1}.inputCurve"
        )

        linear_rebuild_curve2 = cmds.createNode("rebuildCurve")
        cmds.setAttr(f"{linear_rebuild_curve2}.degree", 1)
        cmds.setAttr(f"{linear_rebuild_curve2}.spans", 4)
        cmds.connectAttr(
            f"{offset_curve2}.outputCurve[0]", f"{linear_rebuild_curve2}.inputCurve"
        )

        linear_rebuild_curve3 = cmds.createNode("rebuildCurve")
        cmds.setAttr(f"{linear_rebuild_curve3}.degree", 1)
        cmds.setAttr(f"{linear_rebuild_curve3}.spans", 4)
        cmds.connectAttr(
            f"{offset_curve3}.outputCurve[0]", f"{linear_rebuild_curve3}.inputCurve"
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

        upper_loft = cmds.createNode("loft")
        cmds.setAttr(f"{upper_loft}.degree", 1)
        cmds.setAttr(f"{upper_loft}.reverseSurfaceNormals", 1)
        cmds.connectAttr(
            f"{cubic_rebuild_curve0}.outputCurve", f"{upper_loft}.inputCurve[0]"
        )
        cmds.connectAttr(
            f"{cubic_rebuild_curve1}.outputCurve", f"{upper_loft}.inputCurve[1]"
        )
        rebuild_surface = cmds.createNode("rebuildSurface")
        cmds.connectAttr(
            f"{upper_loft}.outputSurface", f"{rebuild_surface}.inputSurface"
        )
        cmds.setAttr(f"{rebuild_surface}.spansU", 2)
        cmds.setAttr(f"{rebuild_surface}.spansV", 1)
        cmds.setAttr(f"{rebuild_surface}.degreeU", 3)
        cmds.setAttr(f"{rebuild_surface}.degreeV", 1)
        cmds.setAttr(f"{rebuild_surface}.direction", 2)
        cmds.setAttr(f"{rebuild_surface}.keepRange", 0)
        cmds.connectAttr(
            f"{rebuild_surface}.outputSurface",
            f"{self.guide_root}.upper_ribbon_surface",
        )

        lower_loft = cmds.createNode("loft")
        cmds.setAttr(f"{lower_loft}.degree", 1)
        cmds.setAttr(f"{lower_loft}.reverseSurfaceNormals", 1)
        cmds.connectAttr(
            f"{cubic_rebuild_curve2}.outputCurve", f"{lower_loft}.inputCurve[0]"
        )
        cmds.connectAttr(
            f"{cubic_rebuild_curve3}.outputCurve", f"{lower_loft}.inputCurve[1]"
        )
        rebuild_surface = cmds.createNode("rebuildSurface")
        cmds.connectAttr(
            f"{lower_loft}.outputSurface", f"{rebuild_surface}.inputSurface"
        )
        cmds.setAttr(f"{rebuild_surface}.spansU", 2)
        cmds.setAttr(f"{rebuild_surface}.spansV", 1)
        cmds.setAttr(f"{rebuild_surface}.degreeU", 3)
        cmds.setAttr(f"{rebuild_surface}.degreeV", 1)
        cmds.setAttr(f"{rebuild_surface}.direction", 2)
        cmds.setAttr(f"{rebuild_surface}.keepRange", 0)
        cmds.connectAttr(
            f"{rebuild_surface}.outputSurface",
            f"{self.guide_root}.lower_ribbon_surface",
        )

        for i in range(6):
            decom_m = cmds.createNode("decomposeMatrix")
            cmds.connectAttr(
                f"{self.guide_graph}.npo_matrix[{i}]", f"{decom_m}.inputMatrix"
            )
            compose_m = cmds.createNode("composeMatrix")
            cmds.connectAttr(
                f"{decom_m}.outputTranslate", f"{compose_m}.inputTranslate"
            )
            cmds.connectAttr(f"{decom_m}.outputRotate", f"{compose_m}.inputRotate")
            cmds.connectAttr(f"{decom_m}.outputShear", f"{compose_m}.inputShear")
            for z in range(3):
                output_s = [".outputScaleX", ".outputScaleY", ".outputScaleZ"]
                input_s = [".inputScaleX", ".inputScaleY", ".inputScaleZ"]
                round = cmds.createNode("round")
                cmds.connectAttr(f"{decom_m}{output_s[z]}", f"{round}.input")
                cmds.connectAttr(f"{round}.output", f"{compose_m}{input_s[z]}")
            cmds.connectAttr(
                f"{compose_m}.outputMatrix", f"{self.guide_root}.npo_matrix[{i}]"
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
            guide1,
            longName="pole_vector_multiple",
            attributeType="float",
            minValue=0,
            keyable=True,
            defaultValue=self["pole_vector_multiple"]["value"],
        )
        multiply = cmds.createNode("multiply")
        cmds.connectAttr(f"{guide1}.pole_vector_multiple", f"{multiply}.input[0]")

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
