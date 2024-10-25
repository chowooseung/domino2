# domino
from domino import component
from domino.core import attribute, Name
from domino.core.utils import buildLog

# maya
from maya.api import OpenMaya as om  # type: ignore

# built-ins
import logging


ORIGINMATRIX = om.MMatrix()
DATA = [
    attribute.String(longName="component", value="control01"),
    attribute.String(longName="name", value="control"),
    attribute.Enum(longName="side", enumName=Name.sideList, value=0),
    attribute.Integer(longName="index", minValue=0),
    attribute.Matrix(longName="guideMatrix", multi=True, value=[list(ORIGINMATRIX)]),
    attribute.Integer(longName="outputParentIndex", minValue=-1),
    attribute.String(longName="outputJointHierarchy"),
    attribute.Bool(longName="createOutputJoint", value=1),
    attribute.Enum(
        longName="mirrorAxis",
        enumName=["orientation", "behavior", "inverseScale"],
        defaultValue=1,
        value=1,
    ),
]

description = """control01 component.

개별 컨트롤러를 생성합니다."""


class Rig(component.Rig):

    def __init__(self):
        super().__init__(DATA)

    @buildLog(logging.INFO)
    def rig(self):
        super().rig(description=description)

        self.addGuideGraph()

        for i, m in enumerate(self["guideMatrix"]["value"]):
            # guide
            self.addGuide(parent=self.guideRoot, description=i, m=m)

            # rig
            npo, ctl = self.addController(
                parent=self.rigRoot,
                parentControllers=[],
                description=i,
                shape="cube",
                color=12,
                sourcePlug=self.guideGraph + f".initializeTransform[{i}]",
            )

            self.addOutput(ctl)

            # output
            if self["createOutputJoint"]["value"]:
                # outputJoint
                outputJoint = self.addOutputJoint(
                    parent=None,
                    description=i,
                    output=ctl,
                    neutralPoseObj=npo,
                )
