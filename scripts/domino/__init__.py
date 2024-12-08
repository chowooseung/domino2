# maya
from maya import cmds

# domino
from domino.core import dagmenu


average_position_command = """from maya import cmds
import numpy as np
selected = cmds.ls(selection=True, flatten=True)
if selected:
    positions = []
    if cmds.nodeType(selected[0]) == "mesh":
        vertices = cmds.polyListComponentConversion(selected, toVertex=True)
        cmds.select(vertices)
        vertices = cmds.ls(selection=True, flatten=True)
        for vertex in vertices:
            positions.append(cmds.xform(vertex, query=True, translation=True, worldSpace=True))
    else:
        for sel in selected:
            positions.append(cmds.xform(sel, query=True, translation=True, worldSpace=True))
    result = list(np.mean(positions, axis=0))
    loc = cmds.spaceLocator(name="average_loc")[0]
    cmds.setAttr(loc + ".t", *result)"""

print_channel_box_status_command = """from maya import cmds
set_attr_format = "cmds.setAttr('{node}.{attr}', {value})"
result_str = ""
main_objects = cmds.channelBox("mainChannelBox", query=True, mainObjectList=True)
attributes = cmds.channelBox("mainChannelBox", query=True, selectedMainAttributes=True)
if main_objects and attributes:
    for obj in main_objects:
        for attr in attributes:
            value = cmds.getAttr(obj + "." + attr)
            result_str += "\\n" + set_attr_format.format(node=obj, attr=attr, value=value)
shape_objects = cmds.channelBox("mainChannelBox", query=True, shapeObjectList=True)
attributes = cmds.channelBox("mainChannelBox", query=True, selectedShapeAttributes=True)
if shape_objects and attributes:
    for obj in shape_objects:
        for attr in attributes:
            value = cmds.getAttr(obj + "." + attr)
            result_str += "\\n" + set_attr_format.format(node=obj, attr=attr, value=value) 
history_objects = cmds.channelBox("mainChannelBox", query=True, historyObjectList=True)
attributes = cmds.channelBox("mainChannelBox", query=True, selectedHistoryAttributes=True)
if history_objects and attributes:
    for obj in history_objects:
        for attr in attributes:
            value = cmds.getAttr(obj + "." + attr)
            result_str += "\\n" + set_attr_format.format(node=obj, attr=attr, value=value) 
print(result_str)"""

controller_panel_command = """from domino import controllerpanel
controllerpanel.show()"""


def install_rig_commands_menu(menu_id):
    sub_menu = cmds.menuItem(
        parent=menu_id, subMenu=True, label="Rig Commands", tearOff=True
    )
    cmds.menuItem(
        parent=sub_menu,
        label="Place locator at average position",
        command=average_position_command,
    )
    cmds.menuItem(
        parent=sub_menu,
        label="Print channelBox status",
        command=print_channel_box_status_command,
    )
    cmds.menuItem(
        parent=sub_menu,
        label="Controller panel",
        command=controller_panel_command,
    )


manager_command = """from domino import dominomanager
ui = dominomanager.Manager.get_instance()
ui.show(dockable=True)"""


## maya menu
def install():
    menu_id = "Domino"
    if cmds.menu(menu_id, exists=True):
        cmds.deleteUI(menu_id)

    cmds.menu(
        menu_id, parent="MayaWindow", tearOff=True, allowOptionBoxes=True, label=menu_id
    )
    dagmenu.install(menu_id=menu_id)
    cmds.setParent(menu_id, menu=True)

    cmds.menuItem(divider=True)
    cmds.menuItem("domino_manager", label="Manager", command=manager_command)

    install_rig_commands_menu(menu_id=menu_id)
    cmds.setParent(menu_id, menu=True)
    cmds.menuItem(divider=True)

    log_menu = cmds.menuItem("domino_logging_menu", label="Log Level", subMenu=True)
    cmds.setParent(log_menu, menu=True)

    cmds.radioMenuItemCollection()
    cmds.menuItem(
        label="Info",
        radioButton=True,
        command="import logging;from domino.core.utils import logger;logger.setLevel(logging.INFO)",
    )
    cmds.menuItem(
        label="Debug",
        radioButton=False,
        command="import logging;from domino.core.utils import logger;logger.setLevel(logging.DEBUG)",
    )
