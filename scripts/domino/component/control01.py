# domino
from domino import component
from domino.core import attribute, Name
from domino.core.utils import build_log

# maya
from maya.api import OpenMaya as om  # type: ignore
from maya import cmds

# built-ins
import logging


ORIGINMATRIX = om.MMatrix()
DATA = [
    attribute.String(longName="component", value="control01"),
    attribute.String(longName="name", value="control"),
    attribute.Enum(longName="side", enumName=Name.side_list, value=0),
    attribute.Integer(longName="index", minValue=0),
    attribute.Matrix(longName="guide_matrix", multi=True, value=[list(ORIGINMATRIX)]),
    attribute.Integer(longName="guide_mirror_type", multi=True),
    # 부모로 사용할 상위 component 의 output index
    attribute.Integer(
        longName="parent_output_index", minValue=-1, defaultValue=-1, value=-1
    ),
    # output joint 생성 option
    attribute.Bool(longName="create_output_joint", value=1),
    # mirror option
    attribute.Enum(
        longName="mirror_axis",
        enumName=["orientation", "behavior", "inverse_scale"],
        defaultValue=1,
        value=1,
    ),
    # controlelr 갯수.
    attribute.Integer(longName="controller_count", minValue=1, value=1),
]

description = """control01 component.

개별 컨트롤러를 생성합니다."""


class Rig(component.Rig):

    def __init__(self):
        super().__init__(DATA)

    def populate_controller(self):
        if not self["controller"]:
            for i in range(len(self["guide_matrix"]["value"])):
                self.add_controller(description=i)

    def populate_output(self):
        if not self["output"]:
            for i in range(len(self["guide_matrix"]["value"])):
                self.add_output(description=i, extension=Name.controller_extension)

    def populate_output_joint(self):
        if not self["output_joint"]:
            for i in range(len(self["guide_matrix"]["value"])):
                self.add_output_joint(description=i)

    @build_log(logging.INFO)
    def rig(self):
        super().rig(description=description)

        for i, m in enumerate(self["guide_matrix"]["value"]):
            # controller
            npo, ctl = self["controller"][i].create(
                parent=self.rig_root,
                parent_controllers=(
                    self["controller"][i]["parent_controllers"]
                    if "parent_controllers" in self["controller"][i]
                    else []
                ),
                shape=(
                    self["controller"][i]["shape"]
                    if "shape" in self["controller"][i]
                    else "cube"
                ),
                color=12,
                npo_matrix_index=i,
            )

            # output
            self["output"][i].connect()

            # output joint
            if self["create_output_joint"]["value"]:
                self["output_joint"][i].create(parent=None, output=ctl)

    @build_log(logging.INFO)
    def guide(self):
        super().guide(description=description)
        self.add_guide_graph()
        guide_count = len(self["guide_matrix"]["value"])
        if len(self["guide_mirror_type"]["value"]) != guide_count:
            self["guide_mirror_type"]["value"] = [1 for _ in range(guide_count)]

        for i, m in enumerate(self["guide_matrix"]["value"]):
            # guide
            guide = self.add_guide(
                parent=self.guide_root,
                description=i,
                m=m,
                mirror_type=self["guide_mirror_type"]["value"][i],
            )
            pick_m = cmds.createNode("pickMatrix")
            cmds.setAttr(pick_m + ".useScale", 0)
            cmds.setAttr(pick_m + ".useShear", 0)
            cmds.connectAttr(guide + ".worldMatrix[0]", pick_m + ".inputMatrix")
            cmds.connectAttr(
                pick_m + ".outputMatrix", self.guide_root + f".npo_matrix[{i}]"
            )
