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
    attribute.String(longName="component", value="cog01"),
    attribute.String(longName="name", value="COG"),
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

description = """## COG01
---

COG 컨트롤러 입니다."""

# endregion


class Rig(component.Rig):

    def __init__(self):
        super().__init__(DATA)

    def populate_controller(self):
        if not self["controller"]:
            self.add_controller(description="", parent_controllers=[])

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
        cog_npo, cog_ctl = self["controller"][0].create(
            parent=self.rig_root,
            shape=(
                self["controller"][0]["shape"]
                if "shape" in self["controller"][0]
                else "circle"
            ),
            color=12,
            npo_matrix_index=0,
        )
        cmds.connectAttr(
            f"{self.rig_root}.guide_mirror_type[0]", f"{cog_ctl}.mirror_type"
        )
        loc = cmds.createNode(
            "transform",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description=Name.loc_extension,
            ),
            parent=cog_ctl,
        )
        condition = cmds.createNode("condition")
        cmds.setAttr(f"{condition}.operation", 0)
        cmds.connectAttr(f"{self.rig_root}.side", f"{condition}.firstTerm")
        cmds.setAttr(f"{condition}.secondTerm", 2)
        cmds.setAttr(f"{condition}.colorIfTrueR", -1)
        cmds.setAttr(f"{condition}.colorIfFalseR", 1)
        cmds.connectAttr(f"{condition}.outColorR", f"{loc}.sz")

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
        self["output"][0].connect(loc)
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
