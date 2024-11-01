# maya
from maya import cmds, mel

# built-ins
from functools import partial

STATEOPTION = "dominoDagMenuState"
PARENTMENUS = "dominoCommandParentMenus"


def install(menuID: str) -> None:
    if STATEOPTION not in cmds.optionVar(list=True):
        cmds.optionVar(intValue=(STATEOPTION, 0))

    parent_menus = []
    for menu in cmds.lsUI(menus=True):
        menu_command = cmds.menu(menu, query=True, postMenuCommand=True) or []
        if isinstance(menu_command, str):
            if "buildObjectMenuItemsNow" in menu_command:
                parent_menus.append(menu_command.split(" ")[-1][1:-1])
    cmds.optionVar(stringValue=(PARENTMENUS, " ".join(parent_menus)))

    def callback_dag_menu_install() -> None:
        state = cmds.optionVar(query=STATEOPTION)
        parent_menus = cmds.optionVar(query=PARENTMENUS).split(" ")
        for menu in parent_menus:
            if state:
                cmds.menu(menu, edit=True, postMenuCommand=partial(popup_menu, menu))
            else:
                mel.eval(
                    f"""menu -edit -postMenuCommand "buildObjectMenuItemsNow {menu}" {menu}"""
                )

    def toggle_domino_dag_menu_status(*args, **kwargs) -> None:
        if cmds.optionVar(query=STATEOPTION):
            cmds.optionVar(intValue=(STATEOPTION, 0))
        else:
            cmds.optionVar(intValue=(STATEOPTION, 1))

        callback_dag_menu_install()

    original_status = cmds.optionVar(query=STATEOPTION)

    cmds.setParent(menuID, menu=True)
    cmds.menuItem(divider=True)
    cmds.menuItem(
        STATEOPTION + "Menu",
        label="DagMenu",
        command=partial(toggle_domino_dag_menu_status),
        checkBox=original_status,
    )
    callback_dag_menu_install()


def popup_menu(parent_menu: str, *args, **kwargs) -> None:
    selection = cmds.ls(selection=True)
    maya_dag_menu = False

    if selection:
        if cmds.objExists(selection[0] + ".is_domino_guide") or cmds.objExists(
            selection[0] + ".is_domino_guide_root"
        ):
            guide_menu(parent_menu)
            maya_dag_menu = True
        elif cmds.objExists(selection[0] + ".is_domino_rig"):
            rig_menu(parent_menu)
            maya_dag_menu = True
        elif cmds.objExists(selection[0] + ".is_domino_controller"):
            controller_menu(
                parent_menu,
                (
                    True
                    if cmds.getAttr(selection[0] + ".component") == "assembly"
                    else False
                ),
                True if cmds.objExists(selection[0] + ".fkik_command_attr") else False,
            )
            maya_dag_menu = True
        elif cmds.objExists(selection[0] + ".is_domino_skel"):
            skel_menu(parent_menu)
            maya_dag_menu = True
    if not maya_dag_menu:
        mel.eval("buildObjectMenuItemsNow " + parent_menu)


manager_command = """"""

settings_command = """from maya import cmds, mel
selected = cmds.ls(selection=True)
if cmds.objExists(selected[0] + ".is_domino_guide_root"):
    cmds.AttributeEditor()
    mel.eval('setLocalView "Rigging" "" 1;')
if cmds.objExists(selected[0] + ".is_domino_guide"):
    cmds.select(cmds.listConnections(selected[0] + ".worldMatrix[0]", source=False, destination=True, type="transform"))
    cmds.AttributeEditor()
    mel.eval('setLocalView "Rigging" "" 1;')"""

symmetry_guide_command = """"""

matchTR_command = """from maya import cmds
selected = cmds.ls(selection=True)
if len(selected) > 1:
    cmds.matchTransform(selected[:-1], selected[-1], position=True, rotation=True)"""

aim_command = """from maya import cmds
selected = cmds.ls(selection=True)
if len(selected) == 2:
    cmds.delete(cmds.aimConstraint(selected[1], selected[0], aimVector=(1, 0, 0), upVector=(0, 1, 0), worldUpType="scene"))
    cmds.select(selected)
if len(selected) == 3:
    cmds.delete(cmds.aimConstraint(selected[1], selected[0], aimVector=(1, 0, 0), upVector=(0, 1, 0), worldUpType="object", worldUpObject=selected[2]))
    cmds.select(selected)"""


def guide_menu(parent_menu: str) -> None:
    cmds.menu(parent_menu, edit=True, deleteAllItems=True)

    cmds.menuItem(
        parent=parent_menu,
        label="Manager",
        radialPosition="N",
        image="swipe.svg",
        command=manager_command,
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Settings",
        radialPosition="NE",
        command=settings_command,
        image="advancedSettings.png",
    )

    cmds.menuItem(
        parent=parent_menu,
        label="Symmetry",
        radialPosition="W",
        image="symmetryConstraint.svg",
        enableCommandRepeat=True,
        command=symmetry_guide_command,
    )

    cmds.menuItem(
        parent=parent_menu,
        label="Match TR",
        radialPosition="SE",
        command=matchTR_command,
        image="status-change.svg",
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Aim",
        radialPosition="S",
        command=aim_command,
        image="aimConstraint.png",
        enableCommandRepeat=True,
    )


validation_command = "from domino import validation;validation.show()"

pack_up_rig_command = """from maya import cmds
from domino.core import utils
if cmds.objExists("guide"):
    cmds.delete("guide")
info = "mayaVersion : " + utils.maya_version() + "\\n"
info += "usedPlugins : "
plugins = utils.used_plugins()
for i in range(int(len(plugins) / 2)):
    info += "\\n\\t" + plugins[i * 2] + "\\t" + plugins[i * 2 + 1]
cmds.addAttr("rig", longName="notes", dataType="string")
cmds.setAttr("rig.notes", info, type="string")
cmds.setAttr("rig.notes", lock=True)"""

spacemanager_command = """from maya import cmds
from domino import spacemanager
selected = cmds.ls(selection=True)[0]
spacemanager.show()
spacemanager.initialize()
parent = cmds.listRelatives("spaceManager", parent=True)
if not parent or parent[0] != selected:
    cmds.parent("spaceManager", selected)
if not cmds.objExists(selected + ".spacemanager"):
    cmds.addAttr(selected, longName="spacemanager", attributeType="message")
if cmds.connectionInfo(selected + ".spacemanager", sourceFromDestination=True) != "spaceManager.message":
    cmds.connectAttr("spaceManager.message", selected + ".spacemanager", force=True)
cmds.select(selected)"""

posemanager_command = """from maya import cmds
from domino import posemanager
selected = cmds.ls(selection=True)[0]
posemanager.show()
posemanager.initialize()
parent = cmds.listRelatives("poseManager", parent=True)
if not parent or parent[0] != selected:
    cmds.parent("poseManager", selected)
if not cmds.objExists(selected + ".posemanager"):
    cmds.addAttr(selected, longName="posemanager", attributeType="message")
if cmds.connectionInfo(selected + ".posemanager", sourceFromDestination=True) != "poseManager.message":
    cmds.connectAttr("poseManager.message", selected + ".posemanager", force=True)
cmds.select(selected)"""

sdkmanager_command = """from maya import cmds
from domino import sdkmanager
selected = cmds.ls(selection=True)[0]
sdkmanager.show()
sdkmanager.initialize()
parent = cmds.listRelatives("sdkManager", parent=True)
if not parent or parent[0] != selected:
    cmds.parent("sdkManager", selected)
if not cmds.objExists(selected + ".sdkmanager"):
    cmds.addAttr(selected, longName="sdkmanager", attributeType="message")
if cmds.connectionInfo(selected + ".sdkmanager", sourceFromDestination=True) != "sdkManager.message":
    cmds.connectAttr("sdkManager.message", selected + ".sdkmanager", force=True)
cmds.select(selected)"""

add_data_command = """from maya import cmds
from domino.core import Curve, Polygon
assembly_node = ""
for n in cmds.ls(type="transform"):
    if (
        cmds.objExists(n + ".is_domino_rig_root")
        and cmds.getAttr(n + ".component") == "assembly"
    ):
        assembly_node = n
if not cmds.objExists(assembly_node + ".custom_curve_data"):        
    cmds.addAttr(assembly_node, longName="custom_curve_data", attributeType="message", multi=True)
if not cmds.objExists(assembly_node + ".custom_polygon_data"):        
    cmds.addAttr(assembly_node, longName="custom_polygon_data", attributeType="message", multi=True)
if cmds.objExists("guide"):
    selected = cmds.ls(selection=True)
    for sel in selected[1:]:
        shapes = cmds.listRelatives(sel, shapes=True)
        if not shapes:
            continue
        if cmds.nodeType(shapes[0]) == "nurbsCurve":
            cmds.parent(sel, selected[0])
            next_index = len(
                cmds.listConnections(
                    assembly_node + ".custom_curve_data",
                    source=True,
                    destination=False,
                )
                or []
            )
            cmds.connectAttr(sel + ".message", f"{assembly_node}.custom_curve_data[{next_index}]")
        elif cmds.nodeType(shapes[0]) == "mesh":
            cmds.parent(sel, selected[0])
            next_index = len(
                cmds.listConnections(
                    assembly_node + ".custom_polygon_data",
                    source=True,
                    destination=False,
                )
                or []
            )
            cmds.connectAttr(sel + ".message", f"{assembly_node}.custom_polygon_data[{next_index}]")"""

save_command = """from domino.component import save
filePath = cmds.fileDialog2(caption="Save Domino Rig",
                            startingDirectory=cmds.workspace(query=True, rootDirectory=True),
                            fileFilter="Domino Rig (*.domino)",
                            fileMode=0)
if filePath:
    save(filePath[0])"""


def rig_menu(parent_menu: str) -> None:
    cmds.menu(parent_menu, edit=True, deleteAllItems=True)

    cmds.menuItem(
        parent=parent_menu,
        label="Validate",
        radialPosition="N",
        command=validation_command,
        image="list.svg",
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Pack up Rig",
        radialPosition="W",
        command=pack_up_rig_command,
        image="empty-state.png",
        enableCommandRepeat=True,
    )

    cmds.menuItem(
        parent=parent_menu,
        label="Show Space Manager",
        command=spacemanager_command,
        image="bounce-right.svg",
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Show Pose Manager",
        command=posemanager_command,
        image="yoga.svg",
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Show SDK Manager",
        command=sdkmanager_command,
        image="sdk.svg",
    )
    cmds.menuItem(parent=parent_menu, divider=True)
    cmds.menuItem(
        parent=parent_menu,
        label="Add Data (Mesh / Curve)",
        command=add_data_command,
        enableCommandRepeat=True,
        image="lasso-polygon.svg",
    )

    cmds.menuItem(parent=parent_menu, divider=True)
    cmds.menuItem(
        parent=parent_menu,
        label="Save rig to File",
        image="save.png",
        command=save_command,
    )


reset_command = """from domino.core import Controller
from maya import cmds
tr_attrs = [".tx", ".ty", ".tz", ".rx", ".ry", ".rz"]
s_attrs = [".sx", ".sy", ".sz"]
for sel in cmds.ls(selection=True):
    if not cmds.objExists(sel + ".is_domino_controller"):
        continue
    for attr in tr_attrs:
        if cmds.getAttr(sel + attr, lock=True):
            continue
        cmds.setAttr(sel + attr, 0)
    for attr in s_attrs:
        if cmds.getAttr(sel + attr, lock=True):
            continue
        cmds.setAttr(sel + attr, 1)
    keyable_attrs = cmds.listAttr(sel, userDefined=True, keyable=True) or []
    for attr in keyable_attrs:
        default_value = cmds.addAttr(sel + "." + attr, query=True, defaultValue=True)
        cmds.setAttr(sel + "." + attr, default_value)"""

reset_child_command = """from domino.core import Controller
from maya import cmds
selected = cmds.ls(selection=True)
tr_attrs = [".tx", ".ty", ".tz", ".rx", ".ry", ".rz"]
s_attrs = [".sx", ".sy", ".sz"]
controllers = []
for sel in selected:
    if cmds.objExists(sel + ".is_domino_controller"):
        controllers.append(sel)
        controllers.extend(Controller.get_child_controller(sel))
for con in controllers:
    for attr in tr_attrs:
        if cmds.getAttr(con + attr, lock=True):
            continue
        cmds.setAttr(con + attr, 0)
    for attr in s_attrs:
        if cmds.getAttr(con + attr, lock=True):
            continue
        cmds.setAttr(con + attr, 1)
    keyable_attrs = cmds.listAttr(con, userDefined=True, keyable=True) or []
    for attr in keyable_attrs:
        default_value = cmds.addAttr(con + "." + attr, query=True, defaultValue=True)
        cmds.setAttr(con + "." + attr, default_value)"""

symmetry_controller_command = """"""

flip_controller_command = """"""

preroll_command = """from domino.core import Controller
from maya import cmds 
cogCtl = "origin_COG_ctl"
"""

fkik_switch_command = """"""


def controller_menu(
    parent_menu: str, is_assembly: bool = False, has_fkik_switch: bool = False
) -> None:
    cmds.menu(parent_menu, edit=True, deleteAllItems=True)

    cmds.menuItem(
        parent=parent_menu,
        label="Reset",
        radialPosition="NE",
        command=reset_command,
        image="refresh.png",
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Reset Child",
        radialPosition="E",
        command=reset_child_command,
        image="refresh.png",
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Symmetry",
        radialPosition="W",
        image="symmetryConstraint.svg",
        command=symmetry_controller_command,
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Symmetry(Set Key)",
        optionBox=True,
        command='print("Mirror Set Key")',
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Flip",
        radialPosition="SW",
        image="arrows-exchange.svg",
        command=flip_controller_command,
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Flip(Set Key)",
        optionBox=True,
        command='print("Flip Set Key")',
    )

    if is_assembly:
        cmds.menuItem(
            parent=parent_menu,
            label="Set pre-roll frame",
            image="character.svg",
            command=preroll_command,
            enableCommandRepeat=True,
        )

    if has_fkik_switch:
        cmds.menuItem(
            parent=parent_menu,
            label="FK / IK Switch",
            command=fkik_switch_command,
            enableCommandRepeat=True,
        )
        cmds.menuItem(
            parent=parent_menu,
            label="FK / IK Switch(Set Key)",
            optionBox=True,
            command='print("fk/ik Set Key")',
        )


select_skel_command = """from maya import cmds
selected = cmds.ls(selection=True)[0]
namespace = selected.split(":")[0] if ":" in selected else ""
cmds.select([x for x in cmds.ls(namespace + ":*" if namespace else "*", type="joint") if cmds.objExists(x + ".is_domino_skel")])"""

bind_command = """from maya import cmds
selected = cmds.ls(selection=True)
meshes = cmds.ls(selection=True, dagObjects=True, noIntermediate=True, type="mesh")
joints = cmds.ls(selection=True, type="joint")
for mesh in meshes:
    scs = [x for x in cmds.listHistory(mesh, pruneDagObjects=True) if cmds.nodeType(x) == "skinCluster"]
    name = cmds.listRelatives(mesh, parent=True)[0] + str(len(scs)) + "_sc"
    cmds.skinCluster(
        joints + [mesh], 
        name=name, 
        maximumInfluences=1, 
        normalizeWeights=True, 
        obeyMaxInfluences=False, 
        weightDistribution=1,
        multi=True
    )
cmds.select(selected)"""

break_command = """from maya import cmds
joints = [x for x in cmds.ls("*", type="joint") if cmds.objExists(x + ".is_domino_skel")]
for jnt in joints:
    plugs = cmds.listConnections(
        jnt, 
        source=True, 
        destination=False, 
        plugs=True, 
        connections=True
    ) or []
    for i in range(int(len(plugs) / 2 )):
        cmds.disconnectAttr(plugs[i * 2 + 1], plugs[i * 2])"""

bake_command = """from maya import cmds
selected = cmds.ls(selection=True)[0]
namespace = selected.split(":")[0] if ":" in selected else ""
joints = [x for x in cmds.ls(namespace + ":*" if namespace else "*", type="joint") if cmds.objExists(x + ".is_domino_skel")]
cmds.bakeResults(
    joints,
    simulation=True, 
    t="1:120", 
    sampleBy=1, 
    oversamplingRate=1, 
    disableImplicitControl=True, 
    preserveOutsideKeys=True, 
    sparseAnimCurveBake=False, 
    removeBakedAttributeFromLayer=False, 
    removeBakedAnimFromLayer=False, 
    bakeOnOverrideLayer=False, 
    minimizeRotation=True, 
    controlPoints=False, 
    shape=True)"""


def skel_menu(parent_menu: str) -> None:
    cmds.menu(parent_menu, edit=True, deleteAllItems=True)
    cmds.menuItem(
        parent=parent_menu,
        label="Select All Skel",
        radialPosition="NW",
        command=select_skel_command,
        image="kinJoint.png",
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Bind Skin",
        radialPosition="N",
        command=bind_command,
        image="smoothSkin.png",
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Break(All Bind Skel)",
        radialPosition="E",
        command=break_command,
        image="resetSettings.svg",
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Bake(Time slider)",
        radialPosition="SE",
        command=bake_command,
        image="resetSettings.svg",
    )
