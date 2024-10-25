# maya
from maya import cmds

# built-ins
from functools import partial
from typing import Iterable

ID = "dominoValidationUI"


def show(*args) -> None:
    if cmds.window(ID, query=True, exists=True):
        cmds.deleteUI(ID)
    cmds.workspaceControl(
        ID,
        retain=False,
        floating=True,
        label="Validate Rig Scene",
        uiScript="from domino import validation;validation.ui()",
    )


def ui(*args, **kwargs) -> None:
    layout = cmds.scrollLayout(parent=ID, childResizable=True)

    # total node count
    nodes = list(set(cmds.ls()) - set(cmds.ls(defaultNodes=True)))
    meshNodes = len(cmds.ls(type="mesh"))
    cmds.text(f"total node count : {len(nodes)}")
    cmds.text(f"total mesh count : {meshNodes}")

    # clashes
    clashesIns = ValidateClashes()
    clashesIns.createUI(layout)
    clashesIns.isValid()

    # same name
    sameNameIns = ValidateSameName()
    sameNameIns.createUI(layout)
    sameNameIns.isValid()

    # namespace
    namespaceIns = ValidateNamespace()
    namespaceIns.createUI(layout)
    namespaceIns.isValid()

    # display layer
    displayLayerIns = ValidateDiaplayLayer()
    displayLayerIns.createUI(layout)
    displayLayerIns.isValid()

    # anim layer
    animLayerIns = ValidateAnimLayer()
    animLayerIns.createUI(layout)
    animLayerIns.isValid()

    # unknown plug-ins
    unknownPluginIns = ValidateUnknownPlugins()
    unknownPluginIns.createUI(layout)
    unknownPluginIns.isValid()

    # unknown nodes
    unknownNodeIns = ValidateUnknownNode()
    unknownNodeIns.createUI(layout)
    unknownNodeIns.isValid()

    # expression
    expressionIns = ValidateExpression()
    expressionIns.createUI(layout)
    expressionIns.isValid()

    # script
    scriptIns = ValidateScript()
    scriptIns.createUI(layout)
    scriptIns.isValid()

    # orig shape
    origShapeIns = ValidateOrigShape()
    origShapeIns.createUI(layout)
    origShapeIns.isValid()

    # default controller
    defaultValueControllerIns = ValidateController()
    defaultValueControllerIns.createUI(layout)
    defaultValueControllerIns.isValid()

    # keyframe
    keyframeIns = ValidateKeyframe()
    keyframeIns.createUI(layout)
    keyframeIns.isValid()

    # groupID, groupParts
    groupIDPartsIns = ValidateGroupIDParts()
    groupIDPartsIns.createUI(layout)
    groupIDPartsIns.isValid()

    # validate All
    def validate(insList: list, *args) -> None:
        for ins in insList:
            ins.isValid()

    insList = []
    for key, value in locals().items():
        if key.endswith("Ins"):
            insList.append(value)
    cmds.separator(parent=layout, height=10)
    cmds.button(
        "Validate",
        parent=layout,
        command=partial(validate, insList),
    )


class Validate:

    def setColorFrameLayout(self, isValid: bool, level: int) -> None:
        def setColorFromLevel(level: int) -> None:
            if level == 0:
                cmds.frameLayout(
                    self.layout,
                    edit=True,
                    backgroundColor=(0, 1, 0),
                    collapse=True,
                )
            elif level == 1:
                cmds.frameLayout(
                    self.layout,
                    edit=True,
                    backgroundColor=(1, 1, 0),
                    collapse=False,
                )
            elif level == 2:
                cmds.frameLayout(
                    self.layout,
                    edit=True,
                    backgroundColor=(1, 0, 0),
                    collapse=False,
                )

        if isValid:
            setColorFromLevel(level=0)
        else:
            setColorFromLevel(level=level)

    def callbackSelectItems(self, *args) -> None:
        nodes = cmds.textScrollList(self.textScrollList, query=True, selectItem=True)
        cmds.select(nodes)

    def _isValid(self, data: Iterable) -> bool:
        return False if data else True


class ValidateClashes(Validate):
    uiName = "Validate Clash node"

    def __init__(self):
        self.layout = None
        self.textScrollList = None
        self.button = None

    def createUI(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.uiName,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 Clash 노드를 검사합니다.")
        self.textScrollList = cmds.textScrollList(
            selectCommand=self.callbackSelectItems, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.cleanUp)

    def isValid(self) -> tuple:
        cmds.textScrollList(self.textScrollList, edit=True, removeAll=True)
        nodes = cmds.ls("clash*") + cmds.ls("*:clash*")
        isValid = self._isValid(nodes)

        if not self.layout:
            return isValid, nodes

        self.setColorFrameLayout(isValid, 2)

        for node in nodes:
            cmds.textScrollList(self.textScrollList, edit=True, append=node)
        return isValid, nodes

    def cleanUp(self, *args) -> None:
        allItems = cmds.textScrollList(self.textScrollList, query=True, allItems=True)
        if allItems:
            cmds.delete(allItems)
        self.isValid()


class ValidateSameName(Validate):
    uiName = "Validate Same name"

    def __init__(self):
        self.layout = None
        self.textScrollList = None
        self.button = None

    def createUI(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.uiName,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 같은 이름의 노드를 검사합니다.")
        self.textScrollList = cmds.textScrollList(
            selectCommand=self.callbackSelectItems, allowMultiSelection=True
        )
        self.button = cmds.button("is valid?", command=self.isValid)

    def isValid(self, *args) -> tuple:
        cmds.textScrollList(self.textScrollList, edit=True, removeAll=True)
        nodes = []
        for node in cmds.ls():
            if "|" in node:
                nodes.append(node)
        isValid = self._isValid(nodes)

        if not self.layout:
            return isValid, nodes

        self.setColorFrameLayout(isValid, 2)

        for node in nodes:
            cmds.textScrollList(self.textScrollList, edit=True, append=node)
        return isValid, nodes


class ValidateNamespace(Validate):
    uiName = "Validate Namespace"

    def __init__(self):
        self.layout = None
        self.treeView = None
        self.button = None

    def createUI(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.uiName,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 namespace 를 검사합니다.")
        self.treeView = cmds.treeView(parent=self.layout, height=80)
        self.button = cmds.button("Cleaning", command=partial(self.cleanUp))

    def getNamespaceHierarchy(self, parent: str = ":") -> dict:
        data = {parent: {}}
        for ns in cmds.namespaceInfo(parent, listOnlyNamespaces=True) or []:
            data[parent][ns] = self.getNamespaceHierarchy(ns)[ns]
        return data

    def populateNamespace(self, data, parent=":"):
        for key, value in data.items():
            label = key.split(":")[-1]
            cmds.treeView(self.treeView, edit=True, addItem=(key, parent))
            cmds.treeView(self.treeView, edit=True, displayLabel=(key, label))
            self.populateNamespace(value, key)

    def isValid(self, *args) -> tuple:
        cmds.treeView(self.treeView, edit=True, removeAll=True)

        hierarchy = self.getNamespaceHierarchy()
        hierarchy[":"].pop("UI", None)
        hierarchy[":"].pop("shared", None)
        isValid = self._isValid(hierarchy[":"])

        if not self.layout:
            return isValid, hierarchy

        self.setColorFrameLayout(isValid, 2)

        self.populateNamespace(hierarchy)
        return isValid, hierarchy

    def cleanUp(self, *args) -> None:
        hierarchy = self.getNamespaceHierarchy()
        hierarchy[":"].pop("UI", None)
        hierarchy[":"].pop("shared", None)

        cmds.namespace(setNamespace=":")

        def removeNamespace(data):
            for key, value in data.items():
                removeNamespace(value)
                if key != ":":
                    cmds.namespace(removeNamespace=key, mergeNamespaceWithRoot=True)

        removeNamespace(hierarchy)
        self.isValid()


class ValidateDiaplayLayer(Validate):
    uiName = "Validate Display layer"

    def __init__(self):
        self.layout = None
        self.textScrollList = None
        self.button = None

    def createUI(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.uiName,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 display layer 를 검사합니다.")
        self.textScrollList = cmds.textScrollList(
            selectCommand=self.callbackSelectItems, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.cleanUp)

    def isValid(self, *args) -> tuple:
        cmds.textScrollList(self.textScrollList, edit=True, removeAll=True)
        nodes = cmds.ls(type="displayLayer")[1:]
        isValid = self._isValid(nodes)

        if not self.layout:
            return isValid, nodes

        self.setColorFrameLayout(isValid, 1)

        for node in nodes:
            cmds.textScrollList(self.textScrollList, edit=True, append=node)
        return isValid, nodes

    def cleanUp(self, *args) -> None:
        allItems = cmds.textScrollList(self.textScrollList, query=True, allItems=True)
        if allItems:
            cmds.delete(allItems)
        self.isValid()


class ValidateAnimLayer(Validate):
    uiName = "Validate Anim layer"

    def __init__(self):
        self.layout = None
        self.textScrollList = None
        self.button = None

    def createUI(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.uiName,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 anim layer 를 검사합니다.")
        self.textScrollList = cmds.textScrollList(
            selectCommand=self.callbackSelectItems, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.cleanUp)

    def isValid(self, *args) -> tuple:
        cmds.textScrollList(self.textScrollList, edit=True, removeAll=True)
        nodes = cmds.ls(type="animLayer")
        isValid = self._isValid(nodes)

        if not self.layout:
            return isValid, nodes

        self.setColorFrameLayout(isValid, 2)

        for node in nodes:
            cmds.textScrollList(self.textScrollList, edit=True, append=node)
        return isValid, nodes

    def cleanUp(self, *args) -> None:
        allItems = cmds.textScrollList(self.textScrollList, query=True, allItems=True)
        if allItems:
            cmds.delete(allItems)
        self.isValid()


class ValidateUnknownPlugins(Validate):
    uiName = "Validate Unknown plug-ins"

    def __init__(self):
        self.layout = None
        self.textScrollList = None
        self.button = None

    def createUI(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.uiName,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 unknown plug-ins 를 검사합니다.")
        self.textScrollList = cmds.textScrollList()
        self.button = cmds.button("Cleaning", command=self.cleanUp)

    def isValid(self, *args) -> tuple:
        cmds.textScrollList(self.textScrollList, edit=True, removeAll=True)
        plugins = cmds.unknownPlugin(query=True, list=True) or []
        isValid = self._isValid(plugins)

        if not self.layout:
            return isValid, plugins

        self.setColorFrameLayout(isValid, 2)

        for plugin in plugins:
            cmds.textScrollList(self.textScrollList, edit=True, append=plugin)
        return isValid, plugins

    def cleanUp(self, *args) -> None:
        allItems = cmds.textScrollList(self.textScrollList, query=True, allItems=True)
        if allItems:
            cmds.delete(allItems)
        self.isValid()


class ValidateUnknownNode(Validate):
    uiName = "Validate Unknown node"

    def __init__(self):
        self.layout = None
        self.textScrollList = None
        self.button = None

    def createUI(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.uiName,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 unknown node 를 검사합니다.")
        self.textScrollList = cmds.textScrollList(
            selectCommand=self.callbackSelectItems, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.cleanUp)

    def isValid(self, *args) -> tuple:
        cmds.textScrollList(self.textScrollList, edit=True, removeAll=True)
        nodes = (
            cmds.ls(type="unknown")
            + cmds.ls(type="unknownDag")
            + cmds.ls(type="unknownTransform")
        )
        isValid = self._isValid(nodes)

        if not self.layout:
            return isValid, nodes

        self.setColorFrameLayout(isValid, 2)

        for node in nodes:
            cmds.textScrollList(self.textScrollList, edit=True, append=node)
        return isValid, nodes

    def cleanUp(self, *args) -> None:
        allItems = cmds.textScrollList(self.textScrollList, query=True, allItems=True)
        if allItems:
            cmds.delete(allItems)
        self.isValid()


class ValidateExpression(Validate):
    uiName = "Validate Expression"

    def __init__(self):
        self.layout = None
        self.textScrollList = None
        self.button = None

    def createUI(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.uiName,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 expression 를 검사합니다.")
        self.textScrollList = cmds.textScrollList(
            selectCommand=self.callbackSelectItems, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.cleanUp)

    def isValid(self, *args) -> tuple:
        cmds.textScrollList(self.textScrollList, edit=True, removeAll=True)
        expression = cmds.ls(type="expression")
        isValid = self._isValid(expression)

        if not self.layout:
            return isValid, expression

        self.setColorFrameLayout(isValid, 1)

        for exp in expression:
            cmds.textScrollList(self.textScrollList, edit=True, append=exp)
        return isValid, expression

    def cleanUp(self, *args) -> None:
        allItems = cmds.textScrollList(self.textScrollList, query=True, allItems=True)
        if allItems:
            cmds.delete(allItems)
        self.isValid()


class ValidateScript(Validate):
    uiName = "Validate Script node"

    def __init__(self):
        self.layout = None
        self.textScrollList = None
        self.button = None

    def createUI(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.uiName,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 script node 를 검사합니다.")
        self.textScrollList = cmds.textScrollList(
            selectCommand=self.callbackSelectItems, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.cleanUp)

    def isValid(self, *args) -> tuple:
        cmds.textScrollList(self.textScrollList, edit=True, removeAll=True)
        nodes = cmds.ls(type="script")
        isValid = self._isValid(nodes)

        if not self.layout:
            return isValid, nodes

        self.setColorFrameLayout(isValid, 1)

        for node in nodes:
            cmds.textScrollList(self.textScrollList, edit=True, append=node)
        return isValid, nodes

    def cleanUp(self, *args) -> None:
        allItems = cmds.textScrollList(self.textScrollList, query=True, allItems=True)
        if allItems:
            cmds.delete(allItems)
        self.isValid()


class ValidateOrigShape(Validate):
    uiName = "Validate Orig shape"

    def __init__(self):
        self.layout = None
        self.textScrollList = None
        self.button = None

    def createUI(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.uiName,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 Orig shape 를 검사합니다.")
        self.textScrollList = cmds.textScrollList(
            selectCommand=self.callbackSelectItems, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.cleanUp)

    def isValid(self, *args) -> tuple:
        cmds.textScrollList(self.textScrollList, edit=True, removeAll=True)
        nodes = [
            x
            for x in cmds.ls("*Orig*", type="mesh", intermediateObjects=True)
            + cmds.ls("*Orig*", type="nurbsCurve", intermediateObjects=True)
            + cmds.ls("*Orig*", type="nurbsSurface", intermediateObjects=True)
            if not x.endswith("Orig")
        ]
        isValid = self._isValid(nodes)

        if not self.layout:
            return isValid, nodes

        self.setColorFrameLayout(isValid, 2)

        for node in nodes:
            cmds.textScrollList(self.textScrollList, edit=True, append=node)
        return isValid, nodes

    def cleanUp(self, *args) -> None:
        allItems = cmds.textScrollList(self.textScrollList, query=True, allItems=True)
        if allItems:
            cmds.delete(allItems)
        self.isValid()


class ValidateController(Validate):
    uiName = "Validate Controller"

    tr = (
        ".tx",
        ".ty",
        ".tz",
        ".rx",
        ".ry",
        ".rz",
        ".shearXY",
        ".shearXZ",
        ".shearYZ",
    )
    s = [".sx", ".sy", ".sz"]

    def __init__(self):
        self.layout = None
        self.textScrollList = None
        self.button = None

    def createUI(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.uiName,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 controller default value 를 검사합니다.")
        self.textScrollList = cmds.textScrollList(
            selectCommand=self.callbackSelectItems, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.cleanUp)

    def isValid(self, *args) -> tuple:
        cmds.textScrollList(self.textScrollList, edit=True, removeAll=True)
        controllers = cmds.controller(query=True, allControllers=True)

        result = []
        for ctl in controllers:
            keyable = cmds.listAttr(ctl, userDefined=True, keyable=True) or []
            channelbox = cmds.listAttr(ctl, userDefined=True, channelBox=True) or []
            for attr in self.tr:
                if cmds.getAttr(ctl + attr) != 0.0:
                    result.append(ctl + attr)
            for attr in self.s:
                if cmds.getAttr(ctl + attr) != 1.0:
                    result.append(ctl + attr)
            attrs = keyable + channelbox
            for attr in ["." + x for x in attrs]:
                defaultValue = cmds.addAttr(ctl + attr, query=True, defaultValue=True)
                if defaultValue != cmds.getAttr(ctl + attr):
                    result.append(ctl + attr)
        isValid = self._isValid(result)

        if not self.layout:
            return isValid, result

        self.setColorFrameLayout(isValid, 2)

        for attr in result:
            cmds.textScrollList(self.textScrollList, edit=True, append=attr)
        return isValid, result

    def cleanUp(self, *args) -> None:
        items = cmds.textScrollList(self.textScrollList, query=True, selectItem=True)
        for attr in items:
            if "." + attr.split(".")[-1] in self.tr:
                cmds.setAttr(attr, 0.0)
            elif "." + attr.split(".")[-1] in self.s:
                cmds.setAttr(attr, 1.0)
            else:
                defaultValue = cmds.addAttr(attr, query=True, defaultValue=True)
                cmds.setAttr(attr, defaultValue)
        self.isValid()


class ValidateKeyframe(Validate):
    uiName = "Validate Keyframe"

    def __init__(self):
        self.layout = None
        self.textScrollList = None
        self.button = None

    def createUI(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.uiName,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 keyframe 를 검사합니다.")
        self.textScrollList = cmds.textScrollList(
            selectCommand=self.callbackSelectItems, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.cleanUp)

    def isValid(self, *args) -> tuple:
        cmds.textScrollList(self.textScrollList, edit=True, removeAll=True)
        translate = cmds.ls(type="animCurveTL")
        rotate = cmds.ls(type="animCurveTA")
        scale = cmds.ls(type="animCurveTU")
        nodes = translate + rotate + scale
        isValid = self._isValid(nodes)

        if not self.layout:
            return isValid, nodes

        self.setColorFrameLayout(isValid, 2)

        for node in nodes:
            cmds.textScrollList(self.textScrollList, edit=True, append=node)
        return isValid, nodes

    def cleanUp(self, *args) -> None:
        allItems = cmds.textScrollList(self.textScrollList, query=True, allItems=True)
        if allItems:
            cmds.delete(allItems)
        self.isValid()


class ValidateGroupIDParts(Validate):
    uiName = "Validate GroupID, GroupParts"

    def __init__(self):
        self.layout = None
        self.textScrollList = None
        self.button = None

    def createUI(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.uiName,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 groupId, groupParts 를 검사합니다.")
        self.textScrollList = cmds.textScrollList(
            selectCommand=self.callbackSelectItems, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.cleanUp)

    def isValid(self, *args) -> tuple:
        cmds.textScrollList(self.textScrollList, edit=True, removeAll=True)
        nodes = []
        for node in cmds.ls(type="groupId") + cmds.ls(type="groupParts"):
            connections = (
                cmds.listConnections(node, source=True, destination=True) or []
            )
            if not connections:
                nodes.append(node)
        isValid = self._isValid(nodes)

        if not self.layout:
            return isValid, nodes

        self.setColorFrameLayout(isValid, 2)

        for node in nodes:
            cmds.textScrollList(self.textScrollList, edit=True, append=node)
        return isValid, nodes

    def cleanUp(self, *args) -> None:
        allItems = cmds.textScrollList(self.textScrollList, query=True, allItems=True)
        if allItems:
            cmds.delete(allItems)
        self.isValid()
