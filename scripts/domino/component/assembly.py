# domino
from domino import component
from domino.core import (
    attribute,
    Name,
    Transform,
    controller_name_convention,
    joint_name_convention,
    controller_extension,
    joint_extension,
    center,
    left,
    right,
)
from domino.core.utils import build_log

# maya
from maya.api import OpenMaya as om  # type: ignore
from maya import cmds

# built-ins
import logging


ORIGINMATRIX = om.MMatrix()
DATA = [
    attribute.String(longName="component", value="assembly"),
    attribute.String(
        longName="controller_name_convention", value=controller_name_convention
    ),
    attribute.String(longName="joint_name_convention", value=joint_name_convention),
    attribute.String(longName="side_c_str", value=center),
    attribute.String(longName="side_l_str", value=left),
    attribute.String(longName="side_r_str", value=right),
    attribute.String(longName="controller_extension", value=controller_extension),
    attribute.String(longName="joint_extension", value=joint_extension),
    attribute.Matrix(longName="guide_matrix", multi=True, value=[list(ORIGINMATRIX)]),
]

description = """assembly component.

최상위 component 입니다. 
COG 컨트롤러를 가지고 있습니다. 무게중심점에 위치시켜주세요.

origin_jnt 는 model 의 원점을 나타내는 역할입니다."""


class Rig(component.Rig):

    @property
    def identifier(self) -> tuple:
        return "origin", "", ""

    def __init__(self):
        super().__init__(DATA)

    def populate_controller(self):
        if not self["controller"]:
            self._controller = []
            self.add_controller(description="")
            self.add_controller(description="sub")
            self.add_controller(description="COG")

    def populate_output(self):
        pass

    def populate_output_joint(self):
        pass

    @build_log(logging.INFO)
    def rig(self):
        super().rig(description=description)
        name, side, index = self.identifier

        Name.side_str_list = (
            self["side_c_str"]["value"],
            self["side_l_str"]["value"],
            self["side_r_str"]["value"],
        )
        Name.controller_name_convention = self["controller_name_convention"]["value"]
        Name.joint_name_convention = self["joint_name_convention"]["value"]
        Name.controller_extension = self["controller_extension"]["value"]
        Name.joint_extension = self["joint_extension"]["value"]

        m = self["guide_matrix"]["value"][0]
        guide = self.add_guide(parent=self.guide_root, description="COG", m=m)

        # rig
        origin_npo, origin_ctl = self["controller"][0].create(
            parent=self.rig_root,
            parent_controllers=[],
            shape=(
                self["controller"][0]["shape"]
                if "shape" in self["controller"][0]
                else "origin"
            ),
            color=17,
        )

        sub_npo, sub_ctl = self["controller"][1].create(
            parent=origin_ctl,
            parent_controllers=[(self.identifier, "")],
            shape=(
                self["controller"][1]["shape"]
                if "shape" in self["controller"][1]
                else "wave"
            ),
            color=21,
        )

        pick_m = cmds.createNode("pickMatrix")
        cmds.setAttr(pick_m + ".useScale", 0)
        cmds.setAttr(pick_m + ".useShear", 0)
        cmds.connectAttr(guide + ".worldMatrix[0]", pick_m + ".inputMatrix")

        COG_npo, COG_ctl = self["controller"][2].create(
            parent=sub_ctl,
            parent_controllers=[(self.identifier, "sub")],
            shape=(
                self["controller"][2]["shape"]
                if "shape" in self["controller"][2]
                else "cylinder"
            ),
            color=17,
            source_plug=pick_m + ".outputMatrix",
        )

        ins = Transform(
            parent=COG_ctl,
            name=name,
            side=side,
            index=index,
            extension="output",
            m=ORIGINMATRIX,
        )
        output = ins.create()

        inverse_m = cmds.createNode("inverseMatrix")
        cmds.connectAttr(pick_m + ".outputMatrix", inverse_m + ".inputMatrix")
        cmds.connectAttr(inverse_m + ".outputMatrix", output + ".offsetParentMatrix")

        self.add_output(output)

        output_joint = self.add_output_joint(
            parent=None,
            description="",
            output=sub_ctl,
            neutralPoseObj=origin_npo,
        )
