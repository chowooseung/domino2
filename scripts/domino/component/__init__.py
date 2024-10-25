# domino
from domino.core import (
    Name,
    Transform,
    Joint,
    Controller,
    attribute,
)
from domino.core.utils import buildLog, logger

# maya
from maya import cmds
from maya.api import OpenMaya as om  # type: ignore

# built-ins
from typing import TypeVar
import copy
import json
import importlib
import logging

__all__ = [
    "assembly",
    "control01",
    "humanspine01",
    "humanneck01",
    "humanarm01",
    "humanleg01",
    "humanfinger01",
]

GUIDE = "guide"
RIG = "rig"
SKEL = "skel"
ORIGINMATRIX = om.MMatrix()


T = TypeVar("T", bound="Rig")


class Rig(dict):
    """
    Guide Matrix -> Bifrost -> initial Matrix(controller, outputJoint) -> outputJoint

    Args:
        dict (_type_): _description_

    Returns:
        _type_: _description_
    """

    @property
    def data(self) -> dict:
        return self

    @data.setter
    def data(self, data: dict) -> None:
        self.clear()
        self.update(data)

    @property
    def parent(self) -> T:
        return self._parent if hasattr(self, "_parent") else None

    @parent.setter
    def parent(self, parent: T) -> None:
        self._parent = parent
        parent.children = self

    @property
    def children(self) -> list:
        return self["children"]

    @children.setter
    def children(self, child: T) -> None:
        self["children"].append(child)

    @property
    def assembly(self) -> T:
        component = self
        while component.parent is not None:
            component = self.parent
        return component

    @property
    def identifier(self) -> tuple:
        return (
            self["name"]["value"],
            Name.sideStrList[self["side"]["value"]],
            self["index"]["value"],
        )

    @property
    def guideRoot(self) -> str:
        name, side, index = self.identifier
        return Name.create(
            convention=Name.controllerNameConvention,
            name=name,
            side=side,
            index=index,
            extension="guideRoot",
        )

    @property
    def rigRoot(self) -> str:
        name, side, index = self.identifier
        return Name.create(
            convention=Name.controllerNameConvention,
            name=name,
            side=side,
            index=index,
            extension="rigRoot",
        )

    @property
    def guideGraph(self) -> str:
        name, side, index = self.identifier
        return Name.create(
            convention=Name.controllerNameConvention,
            name=name,
            side=side,
            index=index,
            extension="bifGuideGraph",
        )

    @property
    def rigGraph(self) -> str:
        name, side, index = self.identifier
        return Name.create(
            convention=Name.controllerNameConvention,
            name=name,
            side=side,
            index=index,
            extension="bifRigGraph",
        )

    @buildLog(logging.DEBUG)
    def addRoot(self) -> None:
        if not cmds.pluginInfo("dominoNodes.py", loaded=True, query=True):
            cmds.loadPlugin("dominoNodes.py")

        component = self["component"]["value"].capitalize()
        cmds.createNode(f"d{component}", name=self.guideRoot, parent=GUIDE)
        cmds.addAttr(self.guideRoot, longName="isDominoGuideRoot", attributeType="bool")

        name, side, index = self.identifier
        parent = RIG
        if self.parent:
            parentOutput = cmds.listConnections(
                self.parent.rigRoot + ".output", source=True, destination=False
            )
            parent = parentOutput[-1]

        ins = Transform(
            parent=parent, name=name, side=side, index=index, extension="rigRoot"
        )
        rigRoot = ins.create()
        cmds.addAttr(rigRoot, longName="isDominoRigRoot", attributeType="bool")
        cmds.addAttr(rigRoot, longName="parent", attributeType="message")
        cmds.addAttr(rigRoot, longName="children", attributeType="message")
        cmds.addAttr(
            rigRoot, longName="controller", attributeType="message", multi=True
        )
        cmds.addAttr(rigRoot, longName="output", attributeType="message", multi=True)
        cmds.addAttr(
            rigRoot, longName="outputJoint", attributeType="message", multi=True
        )
        cmds.setAttr(rigRoot + ".useOutlinerColor", 1)
        cmds.setAttr(rigRoot + ".outlinerColor", 0.375, 0.75, 0.75)

        # data
        for longName, data in self.items():
            if "dataType" not in data and "attributeType" not in data:
                continue
            attrType = data["dataType"] if "dataType" in data else data["attributeType"]
            ins = attribute.TYPETABLE[attrType](longName=longName, **data)
            ins.node = self.guideRoot
            ins.create()

            ins.node = self.rigRoot
            ins.create()

            cmds.connectAttr(
                self.guideRoot + "." + longName, self.rigRoot + "." + longName
            )

        # parent, child
        if self.parent:
            cmds.connectAttr(
                self.parent.rigRoot + ".children", self.rigRoot + ".parent"
            )

    @buildLog(logging.DEBUG)
    def addGuide(
        self, parent: str, description: str, m: list | om.MMatrix, mirrorAxis: int = 1
    ) -> str:
        """Guide -> rig root attribute
        ~~_guideRoot
         ~~_guide -> ~~_rigRoot.guide[0] -> bifrost.~~Data.guideMatrix[0]
          ~~_guide -> ~~_rigRoot.guide[1] -> bifrost.~~Data.guideMatrix[1]

        Args:
            parent (str): _description_
            description (str): _description_
            m (list | om.MMatrix): _description_

        Returns:
            str: _description_
        """
        name, side, index = self.identifier
        ins = Transform(
            parent=parent,
            name=name,
            side=side,
            index=index,
            description=description,
            extension="guide",
            m=m,
        )
        guide = ins.create()
        cmds.setAttr(guide + ".displayHandle", 1)
        cmds.addAttr(guide, longName="isDominoGuide", attributeType="bool")
        nextIndex = len(
            cmds.listConnections(
                self.guideRoot + ".guideMatrix", source=True, destination=False
            )
            or []
        )
        cmds.connectAttr(
            guide + ".worldMatrix[0]", self.guideRoot + f".guideMatrix[{nextIndex}]"
        )
        at = attribute.Enum(
            longName="mirrorAxis",
            enumName=["orientation", "behavior", "inverseScale"],
            defaultValue=1,
            value=mirrorAxis,
        )
        at.node = guide
        at.create()
        return guide

    @buildLog(logging.DEBUG)
    def addController(
        self,
        parent: str,
        parentControllers: list,
        description: str,
        shape: str,
        color: int | om.MColor,
        sourcePlug: str = "",
        fkikCommandAttr: str = "",
    ) -> tuple:
        """
        ~~_ctl -> ~~_rigRoot.controller[0]
        ~~_ctl -> ~~_rigRoot.controller[1]

        Args:
            parent (str): _description_
            parentControllers (list): _description_
            description (str): _description_
            source (str): _description_
            shape (str): _description_
            color (int | om.MColor): _description_

        Returns:
            tuple: _description_
        """
        name, side, index = self.identifier
        ins = Controller(
            parent=parent,
            parentControllers=parentControllers,
            name=name,
            side=side,
            index=index,
            description=description,
            extension=Name.controllerExtension,
            m=ORIGINMATRIX,
            shape=shape,
            color=color,
        )
        npo, ctl = ins.create()
        if sourcePlug:
            cmds.connectAttr(sourcePlug, npo + ".offsetParentMatrix")
        nextIndex = len(
            cmds.listConnections(
                self.rigRoot + ".controller", source=True, destination=False
            )
            or []
        )
        cmds.addAttr(ctl, longName="component", dataType="string")
        cmds.setAttr(ctl + ".component", self["component"]["value"], type="string")
        cmds.setAttr(ctl + ".component", lock=True)
        cmds.connectAttr(ctl + ".message", self.rigRoot + f".controller[{nextIndex}]")
        if fkikCommandAttr:
            cmds.addAttr(ctl, longName="fkikCommandAttr", dataType="message")
            cmds.connectAttr(fkikCommandAttr, ctl + ".fkikCommandAttr")
        return npo, ctl

    @buildLog(logging.DEBUG)
    def addDriverTransform(self, description: str, sourcePlug: str) -> tuple:
        name, side, index = self.identifier

        multMatrix = cmds.createNode("multMatrix")
        cmds.connectAttr(sourcePlug, multMatrix + ".matrixIn[0]")
        cmds.connectAttr(
            self.rigRoot + ".worldInverseMatrix[0]", multMatrix + ".matrixIn[1]"
        )

        ins = Transform(
            parent=self.rigRoot,
            name=name,
            side=side,
            index=index,
            description=description,
            extension="driver",
            m=ORIGINMATRIX,
        )
        driver = ins.create()
        cmds.connectAttr(multMatrix + ".matrixSum", driver + ".offsetParentMatrix")
        if cmds.objExists(self.rigGraph):
            nextIndex = len(
                cmds.listConnections(
                    self.rigGraph + ".driverMatrix", source=True, destination=False
                )
                or []
            )
            cmds.connectAttr(
                driver + ".dagLocalMatrix",
                self.rigGraph + f".driverMatrix[{nextIndex}]",
            )
        return driver

    @buildLog(logging.DEBUG)
    def addJoint(
        self,
        parent: str,
        description: str,
        m: list | om.MMatrix,
    ) -> str:
        name, side, index = self.identifier
        ins = Joint(
            parent=parent,
            name=name,
            side=side,
            index=index,
            description=description,
            extension=Name.jointExtension,
            m=m,
            useJointConvention=False,
        )
        return ins.create()

    @buildLog(logging.DEBUG)
    def addOutput(self, node: str) -> None:
        nextIndex = len(
            cmds.listConnections(
                self.rigRoot + ".output", source=True, destination=False
            )
            or []
        )
        cmds.connectAttr(node + ".message", self.rigRoot + f".output[{nextIndex}]")

    @buildLog(logging.DEBUG)
    def addOutputJoint(
        self, parent: str, description: str, output: str, neutralPoseObj: str
    ) -> str:
        name, side, index = self.identifier
        ins = Joint(
            parent=parent if parent else SKEL,
            name=name,
            side=side,
            index=index,
            description=description,
            extension=Name.jointExtension,
            m=cmds.xform(output, query=True, matrix=True, worldSpace=True),
            useJointConvention=True,
        )
        nextIndex = len(
            cmds.listConnections(
                self.rigRoot + ".outputJoint", source=True, destination=False
            )
            or []
        )
        jnt = ins.create()
        cmds.addAttr(jnt, longName="isDominoSkel", attributeType="bool", keyable=False)
        cmds.addAttr(jnt, longName="neutralPoseObj", attributeType="message")
        cmds.connectAttr(neutralPoseObj + ".message", jnt + ".neutralPoseObj")
        cmds.connectAttr(jnt + ".message", self.rigRoot + f".outputJoint[{nextIndex}]")

        # translate, scale, shear
        multM = cmds.createNode("multMatrix")
        cmds.connectAttr(output + ".worldMatrix[0]", multM + ".matrixIn[0]")
        cmds.connectAttr(jnt + ".parentInverseMatrix", multM + ".matrixIn[1]")

        decomM = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(multM + ".matrixSum", decomM + ".inputMatrix")

        cmds.connectAttr(decomM + ".outputTranslate", jnt + ".t")
        cmds.connectAttr(decomM + ".outputScale", jnt + ".s")
        cmds.connectAttr(decomM + ".outputShear", jnt + ".shear")

        # rotate
        multM = cmds.createNode("multMatrix")
        cmds.connectAttr(output + ".worldMatrix[0]", multM + ".matrixIn[1]")
        cmds.connectAttr(jnt + ".parentInverseMatrix", multM + ".matrixIn[2]")

        decomM = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(multM + ".matrixSum", decomM + ".inputMatrix")
        cmds.connectAttr(decomM + ".outputRotate", jnt + ".r")
        return jnt

    @buildLog(logging.DEBUG)
    def addGuideGraph(self) -> str:
        component = self["component"]["value"]

        parent = cmds.createNode(
            "transform",
            name=self.guideGraph.replace("Graph", ""),
            parent=self.guideRoot,
        )
        graph = cmds.createNode(
            "bifrostGraphShape", name=self.guideGraph, parent=parent
        )

        cmds.vnnNode(
            graph,
            "/input",
            createOutputPort=("guideMatrix", "array<Math::float4x4>"),
        )

        guideCompound = cmds.vnnCompound(
            graph,
            "/",
            addNode="BifrostGraph,Domino::components," + component + "Guide",
        )[0]
        cmds.vnnConnect(graph, "/input.guideMatrix", f"/{guideCompound}.guideMatrix")
        cmds.connectAttr(self.rigRoot + ".guideMatrix", graph + ".guideMatrix")
        cmds.vnnNode(
            graph,
            "/output",
            createInputPort=("initializeTransform", "array<Math::float4x4>"),
        )
        cmds.vnnConnect(
            graph,
            f"/{guideCompound}.initializeTransform",
            "/output.initializeTransform",
        )
        return graph

    @buildLog(logging.DEBUG)
    def addRigGraph(self) -> str:
        component = self["component"]["value"]

        parent = cmds.createNode(
            "transform", name=self.rigGraph.replace("Graph", ""), parent=self.rigRoot
        )
        graph = cmds.createNode("bifrostGraphShape", name=self.rigGraph, parent=parent)
        cmds.vnnNode(
            graph,
            "/input",
            createOutputPort=("driverMatrix", "array<Math::float4x4>"),
        )
        rigCompound = cmds.vnnCompound(
            graph,
            "/",
            addNode="BifrostGraph,Domino::components," + component + "Rig",
        )[0]
        cmds.vnnConnect(graph, "/input.driverMatrix", f"/{rigCompound}.driverMatrix")
        cmds.vnnNode(
            graph, "/output", createInputPort=("output", "array<Math::float4x4>")
        )
        cmds.vnnConnect(graph, f"/{rigCompound}.output", "/output.output")
        return graph

    def __init__(self, data: list = []) -> None:
        """initialize 시 component 의 데이터를 instance 에 업데이트 합니다."""
        self["children"] = []

        for d in data:
            if hasattr(d, "longName") and d.longName not in self:
                copydata = copy.deepcopy(d)
                self.update(copydata)
            else:
                self.update(d)

    def rig(self, description: str = "") -> None:
        attrs = [".tx", ".ty", ".tz", ".rx", ".ry", ".rz", ".sx", ".sy", ".sz"]
        if not cmds.objExists(GUIDE):
            ins = Transform(parent=None, name="", side="", index="", extension=GUIDE)
            ins.create()
            for attr in attrs:
                cmds.setAttr(GUIDE + attr, lock=True, keyable=False)
        if not cmds.objExists(RIG):
            ins = Transform(parent=None, name="", side="", index="", extension=RIG)
            rig = ins.create()
            cmds.addAttr(rig, longName="isDominoRig", attributeType="bool")
            for attr in attrs:
                cmds.setAttr(RIG + attr, lock=True, keyable=False)
        if not cmds.objExists(SKEL):
            ins = Transform(parent=None, name="", side="", index="", extension=SKEL)
            ins.create()
            for attr in attrs:
                cmds.setAttr(SKEL + attr, lock=True, keyable=False)

        self.addRoot()

        cmds.addAttr(self.guideRoot, longName="notes", dataType="string")
        cmds.setAttr(self.guideRoot + ".notes", description, type="string")
        cmds.setAttr(self.guideRoot + ".notes", lock=True)
        cmds.addAttr(self.rigRoot, longName="notes", dataType="string")
        cmds.connectAttr(self.guideRoot + ".notes", self.rigRoot + ".notes")
        cmds.setAttr(self.rigRoot + ".notes", lock=True)


def serialize() -> T:
    """마야 노드에서 json 으로 저장 할 수 있는 데이터로 직렬화합니다."""
    assemblyNode = ""
    for n in cmds.ls(type="transform"):
        if (
            cmds.objExists(n + ".isDominoRigRoot")
            and cmds.getAttr(n + ".component") == "assembly"
        ):
            assemblyNode = n

    if not assemblyNode:
        return

    def nodeToComponent(node, parent):
        moduleName = cmds.getAttr(node + ".component")
        module = importlib.import_module("domino.component." + moduleName)
        component = module.Rig()

        attributeData = module.DATA
        for attr in attributeData.copy():
            if attr[attr.longName]["multi"]:
                value = []
                for a in cmds.listAttr(node + "." + attr.longName, multi=True) or []:
                    value.append(cmds.getAttr(node + "." + a))
            else:
                value = cmds.getAttr(node + "." + attr.longName)
            component[attr.longName]["value"] = value

        if parent:
            component.parent = parent

        children = (
            cmds.listConnections(node + ".children", destination=True, source=False)
            or []
        )
        for child in children:
            nodeToComponent(child, component)
        return component

    return nodeToComponent(assemblyNode, None)


def deserialize(data: dict, create=True) -> T:
    """직렬화 한 데이터를 마야 노드로 변환합니다."""

    def dataToNode(componentData, parent):
        moduleName = componentData["component"]["value"]
        module = importlib.import_module("domino.component." + moduleName)
        component = module.Rig()

        for attr in module.DATA:
            component[attr.longName]["value"] = componentData[attr.longName]["value"]

        if parent:
            component.parent = parent

        if create:
            component.rig()

        for child in componentData["children"]:
            dataToNode(child, component)

        return component

    return dataToNode(data, None)


@buildLog(logging.INFO)
def save(filePath: str) -> None:
    """리그를 json 으로 저장합니다."""
    if not filePath:
        return

    data = serialize()

    if not data:
        return

    with open(filePath, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Save filePath: {filePath}")


@buildLog(logging.INFO)
def load(filePath: str, create=True) -> T:
    """json 을 리그로 불러옵니다."""
    if not filePath:
        return

    with open(filePath, "r") as f:
        data = json.load(f)

    logger.info(f"Load filePath: {filePath}")

    return deserialize(data, create)
