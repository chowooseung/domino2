# maya
from maya import cmds
from maya.api import OpenMaya as om

# domino
from domino.core import dagmenu
from domino.core.utils import logger

# built-ins
import os


place_a_locator_average_position_command = """from maya import cmds
import numpy as np

selected = cmds.ls(orderedSelection=True, flatten=True)
if selected:
    positions = []
    if cmds.nodeType(selected[0]) == "mesh":
        vertices = cmds.polyListComponentConversion(selected, toVertex=True)
        cmds.select(vertices)
        vertices = cmds.ls(orderedSelection=True, flatten=True)
        for vertex in vertices:
            positions.append(
                cmds.xform(vertex, query=True, translation=True, worldSpace=True)
            )
    else:
        for sel in selected:
            positions.append(
                cmds.xform(sel, query=True, translation=True, worldSpace=True)
            )
    result = list(np.mean(positions, axis=0))
    loc = cmds.spaceLocator(name="average_loc")[0]
    cmds.setAttr(loc + ".t", *result)"""

place_locators_each_position_command = """from maya import cmds
selected = cmds.ls(orderedSelection=True, flatten=True)
if selected:
    for sel in selected:
        t = cmds.xform(sel, query=True, translation=True, worldSpace=True)
        loc = cmds.spaceLocator(name="locators")[0]
        cmds.setAttr(loc + ".t", *t)"""

print_channel_box_status_command = """from maya import cmds

set_attr_format = "cmds.setAttr('{node}.{attr}', {value})"
result_str = ""
main_objects = cmds.channelBox("mainChannelBox", query=True, mainObjectList=True)
attributes = cmds.channelBox("mainChannelBox", query=True, selectedMainAttributes=True)
if main_objects and attributes:
    for obj in main_objects:
        for attr in attributes:
            value = cmds.getAttr(obj + "." + attr)
            result_str += "\\n" + set_attr_format.format(
                node=obj, attr=attr, value=value
            )
shape_objects = cmds.channelBox("mainChannelBox", query=True, shapeObjectList=True)
attributes = cmds.channelBox("mainChannelBox", query=True, selectedShapeAttributes=True)
if shape_objects and attributes:
    for obj in shape_objects:
        for attr in attributes:
            value = cmds.getAttr(obj + "." + attr)
            result_str += "\\n" + set_attr_format.format(
                node=obj, attr=attr, value=value
            )
history_objects = cmds.channelBox("mainChannelBox", query=True, historyObjectList=True)
attributes = cmds.channelBox(
    "mainChannelBox", query=True, selectedHistoryAttributes=True
)
if history_objects and attributes:
    for obj in history_objects:
        for attr in attributes:
            value = cmds.getAttr(obj + "." + attr)
            result_str += "\\n" + set_attr_format.format(
                node=obj, attr=attr, value=value
            )
print(result_str)"""

controller_panel_command = """from domino import controllerpanel
controllerpanel.show()"""

create_multi_plane_at_positions_command = """from maya import cmds
from maya.api import OpenMaya as om

positions = [
    cmds.xform(x, query=True, translation=True, worldSpace=True)
    for x in cmds.ls(orderedSelection=True)
]
meshes = []
v1 = om.MVector((0.1, 0, -0.1))
v2 = om.MVector((0.1, 0, 0.1))
v3 = om.MVector((-0.1, 0, -0.1))
v4 = om.MVector((-0.1, 0, 0.1))
for position in positions:
    p = om.MVector(position)
    plane = cmds.polyPlane(
        constructionHistory=False, subdivisionsHeight=1, subdivisionsWidth=1
    )[0]
    for i, v in enumerate([v1, v2, v3, v4]):
        vtx_position = list(p + v)
        cmds.move(*vtx_position, plane + f".vtx[{i}]")
    meshes.append(plane)
if len(meshes) == 1:
    cmds.rename(meshes[0], "face_at_position")
if len(meshes) > 1:
    cmds.polyUnite(meshes, name="face_at_position", constructionHistory=False)
    cmds.polyAutoProjection(constructionHistory=False, percentageSpace=5, layout=2)"""

extract_select_polygon_face_command = """from maya import cmds
faces = [x for x in cmds.ls(orderedSelection=True) if ".f" in x]
if faces:
    mesh = faces[0].split(".")[0]
    mesh = cmds.duplicate(mesh)[0]
    faces = [mesh + "." + f.split(".")[1] for f in faces]
    cmds.polyChipOff(faces, constructionHistory=False, duplicate=False)
    _, extract_mesh = cmds.polySeparate(
        mesh, removeShells=True, constructionHistory=False, inp=True
    )
    extract_mesh = cmds.rename(extract_mesh, "extract_mesh")
    cmds.delete(mesh)"""

copy_paste_vertex_weight_command = """from maya import cmds
from maya import mel

selected = cmds.ls(orderedSelection=True, flatten=True)
vertices = [x for x in selected if "vtx" in x]
cmds.select(vertices[0])
mel.eval('doCopyVertexWeightsArgList 1 { "1" };')
cmds.select(vertices[1:])
mel.eval('doPasteVertexWeightsArgList 1 { "1" };')
cmds.select(selected)"""


def install_rig_commands_menu(menu_id):
    sub_menu = cmds.menuItem(
        parent=menu_id, subMenu=True, label="Rig Commands", tearOff=True
    )
    cmds.menuItem(
        parent=sub_menu,
        label="Controller panel",
        command=controller_panel_command,
    )
    cmds.menuItem(
        parent=sub_menu,
        label="Place a locator at the average position",
        command=place_a_locator_average_position_command,
    )
    cmds.menuItem(
        parent=sub_menu,
        label="Place locators at each position",
        command=place_locators_each_position_command,
    )
    cmds.menuItem(
        parent=sub_menu,
        label="Create multi plane at positions",
        command=create_multi_plane_at_positions_command,
    )
    cmds.menuItem(
        parent=sub_menu,
        label="Extract select polygon face",
        command=extract_select_polygon_face_command,
    )
    cmds.menuItem(
        parent=sub_menu,
        label="Print channelBox status",
        command=print_channel_box_status_command,
    )
    cmds.menuItem(
        parent=sub_menu,
        label="Copy / Paste vertex weight",
        command=copy_paste_vertex_weight_command,
    )


manager_command = """from domino import dominomanager
ui = dominomanager.Manager.get_instance()
ui.show(dockable=True)"""


def cb_joint_inverse_scale_disconnect(child, parent, client_data):
    """parent 시 joint inverseScale 연결 해제.
    생성 시는 domino.core Joint 에서 해제"""
    if not cmds.objExists(f"{child.fullPathName()}.is_domino_skel"):
        return

    plug = cmds.listConnections(
        f"{child.fullPathName()}.inverseScale",
        source=True,
        destination=False,
        plugs=True,
    )
    if plug:
        cmds.disconnectAttr(plug[0], f"{child.fullPathName()}.inverseScale")


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

    _id = os.getenv("DOMINO_JOINT_INVERSE_SCALE_DISCONNECT", None)
    if _id is not None:
        logger.info(f"Remove joint inverseScale disconnect callback id: {_id}")
        om.MMessage.removeCallback(int(_id))
    _id = om.MDagMessage.addParentAddedCallback(cb_joint_inverse_scale_disconnect)
    logger.info(f"Add joint inverseScale disconnect callback id: {_id}")
    os.environ["DOMINO_JOINT_INVERSE_SCALE_DISCONNECT"] = str(_id)
