# domino
from domino import component
from domino.core import (
    attribute,
    Name,
    Transform,
    controllerNameConvention,
    jointNameConvention,
    controllerExtension,
    jointExtension,
    center,
    left,
    right,
)
from domino.core.utils import buildLog

# maya
from maya.api import OpenMaya as om  # type: ignore
from maya import cmds

# built-ins
import logging


ORIGINMATRIX = om.MMatrix()
DATA = [
    attribute.String(longName="component", value="assembly"),
    attribute.String(
        longName="controllerNameConvention", value=controllerNameConvention
    ),
    attribute.String(longName="jointNameConvention", value=jointNameConvention),
    attribute.String(longName="sideCStr", value=center),
    attribute.String(longName="sideLStr", value=left),
    attribute.String(longName="sideRStr", value=right),
    attribute.String(longName="controllerExtension", value=controllerExtension),
    attribute.String(longName="jointExtension", value=jointExtension),
    attribute.Matrix(longName="guideMatrix", multi=True, value=[list(ORIGINMATRIX)]),
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

    @buildLog(logging.INFO)
    def rig(self):
        super().rig(description=description)
        name, side, index = self.identifier

        Name.sideStrList = (
            self["sideCStr"]["value"],
            self["sideLStr"]["value"],
            self["sideRStr"]["value"],
        )
        Name.controllerNameConvention = self["controllerNameConvention"]["value"]
        Name.jointNameConvention = self["jointNameConvention"]["value"]
        Name.controllerExtension = self["controllerExtension"]["value"]
        Name.jointExtension = self["jointExtension"]["value"]

        m = self["guideMatrix"]["value"][0]
        guide = self.addGuide(parent=self.guideRoot, description="COG", m=m)

        # rig
        originNpo, originCtl = self.addController(
            parent=self.rigRoot,
            parentControllers=[],
            description="",
            shape="origin",
            color=12,
        )
        originCtlIns = component.Controller(node=originCtl)
        originCtlIns.scaleShape((24, 24, 24))

        subNpo, subCtl = self.addController(
            parent=originCtl,
            parentControllers=[originCtl],
            description="sub",
            shape="circle",
            color=12,
        )
        subCtlIns = component.Controller(node=subCtl)
        subCtlIns.scaleShape((18, 18, 18))

        pickM = cmds.createNode("pickMatrix")
        cmds.setAttr(pickM + ".useScale", 0)
        cmds.setAttr(pickM + ".useShear", 0)
        cmds.connectAttr(guide + ".worldMatrix[0]", pickM + ".inputMatrix")

        COGNpo, COGCtl = self.addController(
            parent=subCtl,
            parentControllers=[subCtl],
            description="COG",
            shape="circle",
            color=12,
            sourcePlug=pickM + ".outputMatrix",
        )
        COGCtlIns = component.Controller(node=COGCtl)
        COGCtlIns.scaleShape((12, 12, 12))

        ins = Transform(
            parent=COGCtl,
            name=name,
            side=side,
            index=index,
            extension="output",
            m=ORIGINMATRIX,
        )
        output = ins.create()

        inverseM = cmds.createNode("inverseMatrix")
        cmds.connectAttr(pickM + ".outputMatrix", inverseM + ".inputMatrix")
        cmds.connectAttr(inverseM + ".outputMatrix", output + ".offsetParentMatrix")

        self.addOutput(output)

        outputJoint = self.addOutputJoint(
            parent=None,
            description="",
            output=subCtl,
            neutralPoseObj=originNpo,
        )
