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
    attribute.Integer(longName="guide_mirror_type", multi=True, value=[1, 1]),
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

description = """## control01
---

COG 컨트롤러 입니다.
pivot 을 움직여 회전 할 수 있는 컨트롤러가 있습니다."""

# endregion


class Rig(component.Rig):

    def __init__(self):
        super().__init__(DATA)

    def populate_controller(self):
        if not self["controller"]:
            self.add_controller(description="", parent_controllers=[])
            self.add_controller(
                description="pivot", parent_controllers=[(self.identifier, "")]
            )

    def populate_output(self):
        if not self["output"]:
            self.add_output(description="", extension="output")

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
        cmds.addAttr(
            cog_ctl,
            longName="pivot_ctl_visibility",
            attributeType="enum",
            enumName="off:on",
            keyable=True,
            defaultValue=0,
        )
        cog_pivot_npo, cog_pivot_ctl = self["controller"][1].create(
            parent=cog_ctl,
            shape=(
                self["controller"][1]["shape"]
                if "shape" in self["controller"][1]
                else "sphere"
            ),
            color=12,
        )
        cmds.setAttr(f"{cog_pivot_ctl}.rx", lock=True, keyable=False)
        cmds.setAttr(f"{cog_pivot_ctl}.ry", lock=True, keyable=False)
        cmds.setAttr(f"{cog_pivot_ctl}.rz", lock=True, keyable=False)
        cmds.connectAttr(
            f"{self.rig_root}.guide_mirror_type[0]", f"{cog_pivot_ctl}.mirror_type"
        )
        cmds.connectAttr(f"{cog_pivot_ctl}.t", f"{cog_ctl}.rotatePivot")
        cmds.connectAttr(f"{cog_ctl}.pivot_ctl_visibility", f"{cog_pivot_npo}.v")

        # output
        ins = Joint(
            self.rig_root,
            name=name,
            side=side,
            index=index,
            description="",
            extension="output",
            m=ORIGINMATRIX,
        )
        output = ins.create()
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{cog_ctl}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
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
        guide_count = len(self["guide_matrix"]["value"])
        if len(self["guide_mirror_type"]["value"]) != guide_count:
            self["guide_mirror_type"]["value"] = [1 for _ in range(guide_count)]

        # guide
        guide = self.add_guide(
            parent=self.guide_root,
            description="",
            m=ORIGINMATRIX,
            mirror_type=self["guide_mirror_type"]["value"][0],
        )

        pick_m = cmds.createNode("pickMatrix")
        cmds.setAttr(f"{pick_m}.useScale", 0)
        cmds.setAttr(f"{pick_m}.useShear", 0)
        cmds.connectAttr(f"{guide}.worldMatrix[0]", f"{pick_m}.inputMatrix")
        cmds.connectAttr(f"{pick_m}.outputMatrix", f"{self.guide_root}.npo_matrix[0]")
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
