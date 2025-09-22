# domino
from domino import component
from domino.core import attribute, Name, Joint
from domino.core.utils import build_log

# maya
from maya.api import OpenMaya as om
from maya import cmds

# built-ins
import logging


# region Initialize Settings
ORIGINMATRIX = om.MMatrix()
matrices = [list(ORIGINMATRIX)]
DATA = [
    attribute.String(longName="component", value="pivot01"),
    attribute.String(longName="name", value="pivot"),
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
    attribute.Integer(longName="guide_mirror_type", multi=True, value=[1]),
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
]

description = """## pivot01
---

하위에 pivot 을 옮길 수 있는 컨트롤러가 있습니다."""

# endregion


class Rig(component.Rig):

    def __init__(self):
        super().__init__(DATA)

    def populate_controller(self):
        if not self["controller"]:
            self.add_controller(description="", parent_controllers=[])
            self.add_controller(
                description="handle", parent_controllers=[(self.identifier, "")]
            )

    def populate_output(self):
        if not self["output"]:
            self.add_output(description="", extension=Name.output_extension)

    def populate_output_joint(self):
        if not self["output_joint"]:
            self.add_output_joint(parent_description=None, description="")

    # region RIG
    @build_log(logging.INFO)
    def rig(self):
        super().rig(description=description)

        name, side, index = self.identifier

        # controller
        npo, ctl = self["controller"][0].create(
            parent=self.rig_root,
            shape=(
                self["controller"][0]["shape"]
                if "shape" in self["controller"][0]
                else "circle"
            ),
            color=12,
            npo_matrix_index=0,
        )
        loc = cmds.createNode(
            "transform",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                extension=Name.loc_extension,
            ),
            parent=ctl,
        )
        condition = cmds.createNode("condition")
        cmds.setAttr(f"{condition}.operation", 0)
        cmds.connectAttr(f"{self.rig_root}.side", f"{condition}.firstTerm")
        cmds.setAttr(f"{condition}.secondTerm", 2)
        cmds.setAttr(f"{condition}.colorIfTrueR", -1)
        cmds.setAttr(f"{condition}.colorIfFalseR", 1)
        cmds.connectAttr(f"{condition}.outColorR", f"{loc}.sz")
        cmds.connectAttr(f"{self.rig_root}.guide_mirror_type[0]", f"{ctl}.mirror_type")
        cmds.addAttr(
            ctl,
            longName="handle_ctl_visibility",
            attributeType="enum",
            enumName="off:on",
            keyable=True,
            defaultValue=0,
        )
        handle_npo, handle_ctl = self["controller"][1].create(
            parent=loc,
            shape=(
                self["controller"][1]["shape"]
                if "shape" in self["controller"][1]
                else "sphere"
            ),
            color=12,
        )
        cmds.setAttr(f"{handle_ctl}.rx", lock=True, keyable=False)
        cmds.setAttr(f"{handle_ctl}.ry", lock=True, keyable=False)
        cmds.setAttr(f"{handle_ctl}.rz", lock=True, keyable=False)
        cmds.connectAttr(f"{handle_ctl}.t", f"{ctl}.rotatePivot")
        cmds.connectAttr(f"{ctl}.handle_ctl_visibility", f"{handle_npo}.v")

        shapes = cmds.listRelatives(ctl, shapes=True)
        for shape in shapes:
            temp_shape_transform = cmds.duplicateCurve(
                shape, constructionHistory=False
            )[0]
            temp_shape = cmds.listRelatives(temp_shape_transform, shapes=True)[0]
            cmds.setAttr(f"{temp_shape}.intermediateObject", 1)
            temp_shape = cmds.parent(temp_shape, ctl, shape=True, relative=True)[0]
            temp_shape = cmds.rename(temp_shape, f"{shape}Orig")

            tg = cmds.createNode("transformGeometry")
            cmds.connectAttr(f"{temp_shape}.local", f"{tg}.inputGeometry")

            mult_m = cmds.createNode("multMatrix")
            cmds.connectAttr(f"{handle_ctl}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
            cmds.connectAttr(f"{ctl}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]")
            cmds.connectAttr(f"{mult_m}.matrixSum", f"{tg}.transform")
            cmds.connectAttr(f"{tg}.outputGeometry", f"{shape}.create", force=True)
            cmds.delete(temp_shape_transform)

        # output
        ins = Joint(
            self.rig_root,
            name=name,
            side=side,
            index=index,
            extension=Name.output_extension,
            m=ORIGINMATRIX,
        )
        output = ins.create()
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{loc}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{self.rig_root}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{output}.offsetParentMatrix")
        self["output"][0].connect()
        cmds.setAttr(f"{output}.drawStyle", 2)

        # output joint
        if self["create_output_joint"]["value"]:
            self["output_joint"][0].create()

    # endregion

    # region GUIDE
    @build_log(logging.INFO)
    def guide(self):
        super().guide(description=description)

        # guide
        guide = self.add_guide(
            parent=self.guide_root,
            description="",
            m=self["guide_matrix"]["value"][0],
            mirror_type=self["guide_mirror_type"]["value"][0],
        )

        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{guide}.worldMatrix[0]", f"{decom_m}.inputMatrix")

        condition = cmds.createNode("condition")
        cmds.setAttr(f"{condition}.operation", 4)
        cmds.connectAttr(f"{decom_m}.outputScaleZ", f"{condition}.firstTerm")
        cmds.setAttr(f"{condition}.secondTerm", 0)
        cmds.setAttr(f"{condition}.colorIfTrue", 1, 1, -1)
        cmds.setAttr(f"{condition}.colorIfFalse", 1, 1, 1)

        compose_m = cmds.createNode("composeMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{compose_m}.inputTranslate")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{compose_m}.inputRotate")
        cmds.connectAttr(f"{condition}.outColor", f"{compose_m}.inputScale")
        cmds.connectAttr(
            f"{compose_m}.outputMatrix", f"{self.guide_root}.npo_matrix[0]"
        )

        pick_m = cmds.createNode("pickMatrix")
        cmds.setAttr(f"{pick_m}.useScale", 0)
        cmds.setAttr(f"{pick_m}.useShear", 0)
        cmds.connectAttr(f"{guide}.worldMatrix[0]", f"{pick_m}.inputMatrix")
        cmds.connectAttr(
            f"{pick_m}.outputMatrix",
            f"{self.guide_root}.initialize_output_matrix[0]",
        )

        inv_m = cmds.createNode("inverseMatrix")
        cmds.connectAttr(f"{pick_m}.outputMatrix", f"{inv_m}.inputMatrix")
        cmds.connectAttr(
            f"{inv_m}.outputMatrix",
            f"{self.guide_root}.initialize_output_inverse_matrix[0]",
        )

    # endregion
