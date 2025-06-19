# domino
from domino import component
from domino.core import attribute, Name, Transform, Joint, rigkit
from domino.core.utils import build_log

# maya
from maya.api import OpenMaya as om
from maya import cmds

# built-ins
import logging


# region Initialize Settings
ORIGINMATRIX = om.MMatrix()
matrices = []
m = om.MMatrix()
tm0 = om.MTransformationMatrix(m)
tm0.setTranslation(om.MVector((0, 0, 0)), om.MSpace.kObject)
radians = [om.MAngle(x, om.MAngle.kDegrees).asRadians() for x in (0, 1, 0)]
euler_rot = om.MEulerRotation(radians, om.MEulerRotation.kXYZ)
tm0.setRotation(euler_rot)
matrices.append(list(tm0.asMatrix()))

tm1 = om.MTransformationMatrix(m)
tm1.setTranslation(om.MVector((5, 0, 0)), om.MSpace.kObject)
radians = [om.MAngle(x, om.MAngle.kDegrees).asRadians() for x in (0, -2, 0)]
euler_rot = om.MEulerRotation(radians, om.MEulerRotation.kXYZ)
tm1.setRotation(euler_rot)
matrices.append(list(tm0.asMatrix() * tm1.asMatrix()))

tm2 = om.MTransformationMatrix(m)
tm2.setTranslation(om.MVector((5, 0, 0)), om.MSpace.kObject)
tm2.setRotation(euler_rot)
matrices.append(list(tm0.asMatrix() * tm1.asMatrix() * tm2.asMatrix()))

tm3 = om.MTransformationMatrix(m)
tm3.setTranslation(om.MVector((2, 0, 0)), om.MSpace.kObject)
matrices.append(list(tm0.asMatrix() * tm1.asMatrix() * tm2.asMatrix() * tm3.asMatrix()))

DATA = [
    attribute.String(longName="component", value="fkik2jnt01"),
    attribute.String(longName="name", value="fkik"),
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
    attribute.Bool(longName="align_last_transform_to_guide", defaultValue=0),
    attribute.Bool(longName="unlock_last_scale", defaultValue=0),
]

description = """## fkik01
---

2jnt fkik blend 를 생성합니다.

#### Settings"""

# endregion


class Rig(component.Rig):

    def __init__(self):
        super().__init__(DATA)

    def populate_controller(self):
        if not self["controller"]:
            self.add_controller(
                description="host",
                parent_controllers=[],
            )
            fk_descriptions = ["fk0", "fk1", "fk2"]
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

    def populate_output(self):
        if not self["output"]:
            for i in range(3):
                self.add_output(description=i, extension="output")

    def populate_output_joint(self):
        if not self["output_joint"]:
            parent_description = None
            for i in range(3):
                self.add_output_joint(
                    parent_description=parent_description, description=i
                )
                parent_description = i

    # region RIG
    @build_log(logging.INFO)
    def rig(self):
        super().rig(description=description)

        name, side, index = self.identifier

        # controller
        host_npo, host_ctl = self["controller"][0].create(
            parent=self.rig_root,
            shape=(
                self["controller"][0]["shape"]
                if "shape" in self["controller"][0]
                else "cube"
            ),
            color=12,
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
        fk0_npo, fk0_ctl = self["controller"][1].create(
            parent=self.rig_root,
            shape=(
                self["controller"][1]["shape"]
                if "shape" in self["controller"][1]
                else "cube"
            ),
            color=12,
            npo_matrix_index=0,
        )
        cmds.setAttr(f"{fk0_ctl}.mirror_type", 1)
        ins = Transform(
            parent=fk0_ctl,
            name=name,
            side=side,
            index=index,
            description="fk0Length",
            m=ORIGINMATRIX,
        )
        fk0_length_grp = ins.create()
        cmds.setAttr(f"{fk0_length_grp}.t", 0, 0, 0)
        cmds.setAttr(f"{fk0_length_grp}.r", 0, 0, 0)
        cmds.addAttr(
            fk0_ctl,
            longName="length",
            attributeType="float",
            keyable=True,
            defaultValue=0,
        )
        multiply0 = cmds.createNode("multiply")
        cmds.connectAttr(f"{fk0_ctl}.length", f"{multiply0}.input[0]")
        condition0 = cmds.createNode("condition")
        cmds.connectAttr(f"{self.rig_root}.side", f"{condition0}.firstTerm")
        cmds.setAttr(f"{condition0}.secondTerm", 2)
        cmds.setAttr(f"{condition0}.colorIfTrueR", -1)
        cmds.setAttr(f"{condition0}.colorIfFalseR", 1)
        cmds.connectAttr(f"{condition0}.outColorR", f"{multiply0}.input[1]")
        cmds.connectAttr(f"{multiply0}.output", f"{fk0_length_grp}.tx")

        fk1_npo, fk1_ctl = self["controller"][2].create(
            parent=fk0_length_grp,
            shape=(
                self["controller"][2]["shape"]
                if "shape" in self["controller"][2]
                else "cube"
            ),
            color=12,
            npo_matrix_index=1,
        )
        cmds.setAttr(f"{fk1_ctl}.mirror_type", 1)
        ins = Transform(
            parent=fk1_ctl,
            name=name,
            side=side,
            index=index,
            description="fk1Length",
            m=ORIGINMATRIX,
        )
        fk1_length_grp = ins.create()
        cmds.setAttr(f"{fk1_length_grp}.t", 0, 0, 0)
        cmds.setAttr(f"{fk1_length_grp}.r", 0, 0, 0)
        cmds.addAttr(
            fk1_ctl,
            longName="length",
            attributeType="float",
            keyable=True,
            defaultValue=0,
        )
        multiply0 = cmds.createNode("multiply")
        cmds.connectAttr(f"{fk1_ctl}.length", f"{multiply0}.input[0]")
        condition0 = cmds.createNode("condition")
        cmds.connectAttr(f"{self.rig_root}.side", f"{condition0}.firstTerm")
        cmds.setAttr(f"{condition0}.secondTerm", 2)
        cmds.setAttr(f"{condition0}.colorIfTrueR", -1)
        cmds.setAttr(f"{condition0}.colorIfFalseR", 1)
        cmds.connectAttr(f"{condition0}.outColorR", f"{multiply0}.input[1]")
        cmds.connectAttr(f"{multiply0}.output", f"{fk1_length_grp}.tx")

        fk2_npo, fk2_ctl = self["controller"][3].create(
            parent=fk1_length_grp,
            shape=(
                self["controller"][3]["shape"]
                if "shape" in self["controller"][3]
                else "cube"
            ),
            color=12,
            npo_matrix_index=2,
        )
        cmds.setAttr(f"{fk2_ctl}.mirror_type", 1)
        if self["unlock_last_scale"]["value"]:
            cmds.setAttr(f"{fk2_ctl}.sx", lock=False, keyable=True)
            cmds.setAttr(f"{fk2_ctl}.sy", lock=False, keyable=True)
            cmds.setAttr(f"{fk2_ctl}.sz", lock=False, keyable=True)
        else:
            cmds.setAttr(f"{fk2_ctl}.sx", lock=True, keyable=False)
            cmds.setAttr(f"{fk2_ctl}.sy", lock=True, keyable=False)
            cmds.setAttr(f"{fk2_ctl}.sz", lock=True, keyable=False)

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
        cmds.setAttr(f"{ik_pos_ctl}.mirror_type", 2)

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
        guideline = cmds.parent(guideline, self.rig_root)[0]
        cmds.setAttr(f"{guideline}.overrideEnabled", 1)
        cmds.setAttr(f"{guideline}.overrideDisplayType", 1)

        ins = Joint(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description="ik0",
            extension=Name.joint_extension,
            m=cmds.xform(fk0_ctl, query=True, matrix=True, worldSpace=True),
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
            m=cmds.xform(fk1_ctl, query=True, matrix=True, worldSpace=True),
            use_joint_convention=False,
        )
        ik1_jnt = ins.create()
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{pole_vec_ctl}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{self.rig_root}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{guideline}.cv[0]")
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{ik1_jnt}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{self.rig_root}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{guideline}.cv[1]")

        ins = Joint(
            parent=ik1_jnt,
            name=name,
            side=side,
            index=index,
            description="ik2",
            extension=Name.joint_extension,
            m=cmds.xform(fk2_ctl, query=True, matrix=True, worldSpace=True),
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

        cmds.orientConstraint(ik_local_ctl, ik2_jnt)
        cmds.scaleConstraint(ik_local_ctl, ik2_jnt)

        cmds.connectAttr(f"{host_ctl}.fkik", f"{ik_pos_npo}.v")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{pole_vec_npo}.v")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{ik_npo}.v")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{guideline}.v")

        rev = cmds.createNode("reverse")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{rev}.inputX")
        cmds.connectAttr(f"{rev}.outputX", f"{fk0_npo}.v")

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
            ik_driver=ik_local_ctl,
            pole_vector=pole_vec_ctl,
            attach_pole_vector_attr=f"{ik_ctl}.attach_to_PV",
            scale_attr=f"{ik_ctl}.ik_scale",
            slide_attr=f"{ik_ctl}.slide",
            soft_ik_attr=f"{ik_ctl}.soft_ik",
            max_stretch_attr=f"{ik_ctl}.max_stretch",
        )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{self.rig_root}.npo_matrix[0]", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{ik0_jnt}.jointOrient")
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{self.rig_root}.npo_matrix[1]", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{ik1_jnt}.jointOrient")
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{self.rig_root}.npo_matrix[2]", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{ik2_jnt}.jointOrient")

        ins = Joint(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description="blend0",
            extension=Name.joint_extension,
            m=cmds.xform(fk0_ctl, query=True, matrix=True, worldSpace=True),
            use_joint_convention=False,
        )
        blend0_jnt = ins.create()
        plug = cmds.listConnections(
            f"{ik0_jnt}.jointOrient", source=True, destination=False, plugs=True
        )[0]
        cmds.connectAttr(plug, f"{blend0_jnt}.jointOrient")

        start_roll = cmds.createNode(
            "transform",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                extension="startRoll",
            ),
            parent=blend0_jnt,
        )
        cmds.connectAttr(f"{host_ctl}.start_roll", f"{start_roll}.rx")

        ins = Joint(
            parent=blend0_jnt,
            name=name,
            side=side,
            index=index,
            description="blend1",
            extension=Name.joint_extension,
            m=cmds.xform(fk1_ctl, query=True, matrix=True, worldSpace=True),
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
            m=cmds.xform(fk2_ctl, query=True, matrix=True, worldSpace=True),
            use_joint_convention=False,
        )
        blend2_jnt = ins.create()
        plug = cmds.listConnections(
            f"{ik2_jnt}.jointOrient", source=True, destination=False, plugs=True
        )[0]
        cmds.connectAttr(plug, f"{blend2_jnt}.jointOrient")

        pair_b = cmds.createNode("pairBlend")
        cmds.setAttr(f"{pair_b}.rotInterpolation", 1)
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{fk0_ctl}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{self.rig_root}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{pair_b}.inTranslate1")
        cmds.connectAttr(f"{fk0_ctl}.r", f"{pair_b}.inRotate1")
        cmds.connectAttr(f"{ik0_jnt}.t", f"{pair_b}.inTranslate2")
        cmds.connectAttr(f"{ik0_jnt}.r", f"{pair_b}.inRotate2")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{pair_b}.weight")
        cmds.connectAttr(f"{pair_b}.outTranslate", f"{blend0_jnt}.t")
        cmds.connectAttr(f"{pair_b}.outRotate", f"{blend0_jnt}.r")
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{start_roll}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{self.rig_root}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        blend0_jnt_input_matrix = f"{mult_m}.matrixSum"

        pair_b = cmds.createNode("pairBlend")
        cmds.setAttr(f"{pair_b}.rotInterpolation", 1)
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{fk1_ctl}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(f"{fk0_ctl}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]")
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{pair_b}.inTranslate1")
        cmds.connectAttr(f"{fk1_ctl}.r", f"{pair_b}.inRotate1")
        cmds.connectAttr(f"{ik1_jnt}.t", f"{pair_b}.inTranslate2")
        cmds.connectAttr(f"{ik1_jnt}.r", f"{pair_b}.inRotate2")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{pair_b}.weight")
        cmds.connectAttr(f"{pair_b}.outTranslate", f"{blend1_jnt}.t")
        cmds.connectAttr(f"{pair_b}.outRotate", f"{blend1_jnt}.r")
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{blend1_jnt}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{self.rig_root}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        blend1_jnt_input_matrix = f"{mult_m}.matrixSum"

        pair_b = cmds.createNode("pairBlend")
        cmds.setAttr(f"{pair_b}.rotInterpolation", 1)
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{fk2_ctl}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(f"{fk1_ctl}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]")
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{pair_b}.inTranslate1")
        cmds.connectAttr(f"{fk2_ctl}.r", f"{pair_b}.inRotate1")
        cmds.connectAttr(f"{ik2_jnt}.t", f"{pair_b}.inTranslate2")
        cmds.connectAttr(f"{ik2_jnt}.r", f"{pair_b}.inRotate2")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{pair_b}.weight")
        cmds.connectAttr(f"{pair_b}.outTranslate", f"{blend2_jnt}.t")
        cmds.connectAttr(f"{pair_b}.outRotate", f"{blend2_jnt}.r")
        blend_color = cmds.createNode("blendColors")
        cmds.connectAttr(f"{ik2_jnt}.s", f"{blend_color}.color1")
        cmds.connectAttr(f"{fk2_ctl}.s", f"{blend_color}.color2")
        cmds.connectAttr(f"{host_ctl}.fkik", f"{blend_color}.blender")
        cmds.connectAttr(f"{blend_color}.output", f"{blend2_jnt}.s")
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{blend2_jnt}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{self.rig_root}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        blend2_jnt_input_matrix = f"{mult_m}.matrixSum"

        # output
        ins = Joint(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description=0,
            extension="output",
            m=ORIGINMATRIX,
        )
        fkik0_loc = ins.create()
        cmds.setAttr(f"{fkik0_loc}.drawStyle", 2)
        self["output"][0].connect()
        cmds.connectAttr(blend0_jnt_input_matrix, f"{fkik0_loc}.offsetParentMatrix")

        ins = Joint(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description=1,
            extension="output",
            m=ORIGINMATRIX,
        )
        fkik1_loc = ins.create()
        cmds.setAttr(f"{fkik1_loc}.drawStyle", 2)
        self["output"][1].connect()
        cmds.connectAttr(blend1_jnt_input_matrix, f"{fkik1_loc}.offsetParentMatrix")

        ins = Joint(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description=2,
            extension="output",
            m=ORIGINMATRIX,
        )
        fkik2_loc = ins.create()
        cmds.setAttr(f"{fkik2_loc}.drawStyle", 2)
        self["output"][2].connect()
        cmds.connectAttr(blend2_jnt_input_matrix, f"{fkik2_loc}.offsetParentMatrix")

        # output joint
        if self["create_output_joint"]["value"]:
            self["output_joint"][0].create()
            self["output_joint"][1].create()
            self["output_joint"][2].create()

    # endregion

    # region GUIDE
    @build_log(logging.INFO)
    def guide(self):
        super().guide(description=description)
        graph, guide_compound = self.add_guide_graph()

        guide_count = len(self["guide_matrix"]["value"])
        if len(self["guide_mirror_type"]["value"]) != guide_count:
            self["guide_mirror_type"]["value"] = [1 for _ in range(guide_count)]

        cmds.vnnNode(
            graph,
            "/input",
            createOutputPort=("pole_vector_multiple", "float"),
        )
        cmds.vnnNode(
            graph,
            "/input",
            createOutputPort=("controller_primary_axis", "long"),
        )
        cmds.vnnNode(
            graph,
            "/input",
            createOutputPort=("controller_secondary_axis", "long"),
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
        cmds.vnnConnect(
            graph,
            "/input.pole_vector_multiple",
            f"/{guide_compound}.pole_vector_multiple",
        )
        cmds.vnnConnect(
            graph,
            "/input.controller_primary_axis",
            f"/{guide_compound}.controller_primary_axis",
        )
        cmds.vnnConnect(
            graph,
            "/input.controller_secondary_axis",
            f"/{guide_compound}.controller_secondary_axis",
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
        cmds.connectAttr(
            f"{self.guide_root}.controller_primary_axis",
            f"{graph}.controller_primary_axis",
        )
        cmds.connectAttr(
            f"{self.guide_root}.controller_secondary_axis",
            f"{graph}.controller_secondary_axis",
        )
        cmds.connectAttr(f"{self.guide_root}.side", f"{graph}.negate")
        cmds.connectAttr(
            f"{self.guide_root}.align_last_transform_to_guide",
            f"{graph}.align_last_transform_to_guide",
        )

        # guide
        guide0 = self.add_guide(
            parent=self.guide_root,
            description="fkik0",
            m=self["guide_matrix"]["value"][0],
            mirror_type=self["guide_mirror_type"]["value"][0],
        )

        guide1 = self.add_guide(
            parent=guide0,
            description="fkik1",
            m=self["guide_matrix"]["value"][1],
            mirror_type=self["guide_mirror_type"]["value"][1],
        )

        guide2 = self.add_guide(
            parent=guide1,
            description="fkik2",
            m=self["guide_matrix"]["value"][2],
            mirror_type=self["guide_mirror_type"]["value"][2],
        )

        guide3 = self.add_guide(
            parent=guide2,
            description="fkik3",
            m=self["guide_matrix"]["value"][3],
            mirror_type=self["guide_mirror_type"]["value"][3],
        )

        for i in range(6):
            cmds.connectAttr(
                f"{self.guide_graph}.npo_matrix[{i}]",
                f"{self.guide_root}.npo_matrix[{i}]",
            )

        for i in range(3):
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
