# maya
from maya import cmds

# built-ins
import json
from functools import partial


ERROR = -11111


rootNodeName = "sdkManager"


def initialize():
    selected = cmds.ls(selection=True)
    if not cmds.objExists(rootNodeName):
        cmds.createNode("transform", name=rootNodeName)
    if not cmds.objExists(rootNodeName + "._data"):
        cmds.addAttr(rootNodeName, longName="_data", dataType="string")
        cmds.setAttr(rootNodeName + "._data", json.dumps({}), type="string")
    if selected:
        cmds.select(selected)


def getData():
    if not cmds.objExists(rootNodeName):
        return None

    return json.loads(cmds.getAttr(rootNodeName + "._data"))


def setData(data):
    if cmds.objExists(rootNodeName):
        cmds.setAttr(rootNodeName + "._data", json.dumps(data), type="string")


def addAttr():
    pass


def deleteAttr():
    pass


ID = "sdkManagerUI"


def show(*args) -> None:
    if cmds.window(ID, query=True, exists=True):
        cmds.deleteUI(ID)
    cmds.workspaceControl(
        ID,
        retain=False,
        floating=True,
        label="SDK Manager UI",
        uiScript="from domino import sdkmanager;sdkmanager.ui()",
    )


def ui(*args, **kwargs) -> None:
    pass
