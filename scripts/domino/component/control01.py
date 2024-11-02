# domino
from domino import component
from domino.core import attribute, Name
from domino.core.utils import build_log

# maya
from maya.api import OpenMaya as om  # type: ignore

# built-ins
import logging


ORIGINMATRIX = om.MMatrix()
DATA = [
    attribute.String(longName="component", value="control01"),
    attribute.String(longName="name", value="control"),
    attribute.Enum(longName="side", enumName=Name.side_list, value=0),
    attribute.Integer(longName="index", minValue=0),
    attribute.Matrix(longName="guide_matrix", multi=True, value=[list(ORIGINMATRIX)]),
    attribute.Integer(longName="output_parent_index", minValue=-1),
    attribute.String(longName="output_joint_hierarchy"),
    attribute.Bool(longName="create_output_joint", value=1),
    attribute.Enum(
        longName="mirror_axis",
        enumName=["orientation", "behavior", "inverse_scale"],
        defaultValue=1,
        value=1,
    ),
]

description = """control01 component.

개별 컨트롤러를 생성합니다."""


class Rig(component.Rig):

    def __init__(self):
        super().__init__(DATA)

    def populate_controller(self):
        if not self["controller"]:
            self._controller = []
            for i in range(len(self["guide_matrix"]["value"])):
                self.add_controller(description=i)

    def populate_output(self):
        if not self["output"]:
            pass

    def populate_output_joint(self):
        if not self["output_joint"]:
            pass

    @build_log(logging.INFO)
    def rig(self):
        super().rig(description=description)

        self.add_guide_graph()

        for i, m in enumerate(self["guide_matrix"]["value"]):
            # guide
            self.add_guide(parent=self.guide_root, description=i, m=m)

            # rig
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
                source_plug=self.guide_graph + f".initialize_transform[{i}]",
            )

            self.add_output(ctl)

            # output
            if self["create_output_joint"]["value"]:
                # outputJoint
                output_joint = self.add_output_joint(
                    parent=None,
                    description=i,
                    output=ctl,
                    neutralPoseObj=npo,
                )
