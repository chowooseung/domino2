# maya
from maya import cmds

# built-ins
import json
from functools import partial


ERROR = -11111


root_node_name = "sdkManager"


def initialize():
    selected = cmds.ls(selection=True)
    if not cmds.objExists(root_node_name):
        cmds.createNode("transform", name=root_node_name)
    if not cmds.objExists(root_node_name + "._data"):
        cmds.addAttr(root_node_name, longName="_data", dataType="string")
        cmds.setAttr(root_node_name + "._data", json.dumps({}), type="string")
    if selected:
        cmds.select(selected)


def get_data():
    if not cmds.objExists(root_node_name):
        return None

    return json.loads(cmds.getAttr(root_node_name + "._data"))


def set_data(data):
    if cmds.objExists(root_node_name):
        cmds.setAttr(root_node_name + "._data", json.dumps(data), type="string")


def add_attr():
    pass


def delete_attr():
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
