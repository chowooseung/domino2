# maya
from maya import cmds, mel

# built-ins
from functools import partial

STATEOPTION = "domino_dag_menu_state"
PARENTMENUS = "domino_command_parent_menus"
CONTROLLER_APPLY_CHILDREN_OPTION = "domino_controller_apply_children"
GUIDE_APPLY_CHILDREN_OPTION = "domino_guide_apply_children"


def install(menu_id: str) -> None:
    if STATEOPTION not in cmds.optionVar(list=True):
        cmds.optionVar(intValue=(STATEOPTION, 0))

    status = cmds.optionVar(query=STATEOPTION)
    if not status:
        parent_menus = []
        for menu in cmds.lsUI(menus=True):
            menu_command = cmds.menu(menu, query=True, postMenuCommand=True) or []
            if isinstance(menu_command, str):
                if "buildObjectMenuItemsNow" in menu_command:
                    m_id = menu_command.split(" ")[-1]
                    parent_menus.append(m_id.replace('"', ""))
        cmds.optionVar(stringValue=(PARENTMENUS, " ".join(parent_menus)))

    def callback_dag_menu_install() -> None:
        status = cmds.optionVar(query=STATEOPTION)
        parent_menus = cmds.optionVar(query=PARENTMENUS).split(" ")
        for menu in parent_menus:
            if status:
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

    cmds.setParent(menu_id, menu=True)
    cmds.menuItem(divider=True)
    cmds.menuItem(
        STATEOPTION + "_menu",
        label="Dag Menu",
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
parent = cmds.listRelatives("space_manager", parent=True)
if not parent or parent[0] != "origin_sub_ctl":
    cmds.parent("space_manager", "origin_sub_ctl")
if not cmds.objExists(selected + ".space_manager"):
    cmds.addAttr(selected, longName="space_manager", attributeType="message")
if cmds.connectionInfo(selected + ".space_manager", sourceFromDestination=True) != "space_manager.message":
    cmds.connectAttr("space_manager.message", selected + ".space_manager", force=True)
cmds.select(selected)"""

posemanager_command = """from maya import cmds
from domino import posemanager
selected = cmds.ls(selection=True)[0]
posemanager.show()
posemanager.initialize()
parent = cmds.listRelatives("pose_manager", parent=True)
if not parent or parent[0] != "origin_sub_ctl":
    cmds.parent("pose_manager", "origin_sub_ctl")
if not cmds.objExists(selected + ".pose_manager"):
    cmds.addAttr(selected, longName="pose_manager", attributeType="message")
if cmds.connectionInfo(selected + ".pose_manager", sourceFromDestination=True) != "pose_manager.message":
    cmds.connectAttr("pose_manager.message", selected + ".pose_manager", force=True)
cmds.select(selected)"""

sdkmanager_command = """from maya import cmds
from domino import sdkmanager
selected = cmds.ls(selection=True)[0]
sdkmanager.show()
sdkmanager.initialize()
parent = cmds.listRelatives("sdk_manager", parent=True)
if not parent or parent[0] != "origin_sub_ctl":
    cmds.parent("sdk_manager", "origin_sub_ctl")
if not cmds.objExists(selected + ".sdk_manager"):
    cmds.addAttr(selected, longName="sdk_manager", attributeType="message")
if cmds.connectionInfo(selected + ".sdk_manager", sourceFromDestination=True) != "sdk_manager.message":
    cmds.connectAttr("sdk_manager.message", selected + ".sdk_manager", force=True)
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
        label="Attach Guide",
        radialPosition="NE",
        command=attach_guide_command,
        image="plug-connected.svg",
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Detach Guide",
        radialPosition="E",
        command=detach_guide_command,
        image="plug-connected-x.svg",
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


apply_children_option_commnad = f"""from maya import cmds
apply_children_state = cmds.optionVar(query="{CONTROLLER_APPLY_CHILDREN_OPTION}")
state = False if apply_children_state else True
cmds.optionVar(intValue=("{CONTROLLER_APPLY_CHILDREN_OPTION}", state))"""

controller_panel_command = """from domino import controllerpanel
controllerpanel.show()"""

attach_guide_command = """from maya import cmds
selected = [x for x in cmds.ls(selection=True) if cmds.objExists(x + ".is_domino_controller")]
roots = []
for sel in selected:
    roots.append(cmds.listConnections(sel + ".message", type="transform", connections=True)[1])
for root in set(roots):
    if cmds.objExists(root.replace("rigRoot", "guideRoot")):
        continue   
    component = cmds.getAttr(root + ".component")
    module = importlib.import_module("domino.component." + component)
    rig = module.Rig()
    attribute_data = module.DATA
    for attr in attribute_data.copy():
        if attr[attr.long_name]["multi"]:
            value = []
            for a in cmds.listAttr(root + "." + attr.long_name, multi=True) or []:
                value.append(cmds.getAttr(root + "." + a))
        else:
            value = cmds.getAttr(root + "." + attr.long_name)
        rig[attr.long_name]["value"] = value
    rig.attach_guide()
cmds.select(selected)"""

detach_guide_command = """from maya import cmds
selected = [x for x in cmds.ls(selection=True) if cmds.objExists(x + ".is_domino_controller")]
roots = []
for sel in selected:
    roots.append(cmds.listConnections(sel + ".message", type="transform", connections=True)[1])
for root in set(roots):
    if not cmds.objExists(root.replace("rigRoot", "guideRoot")):
        continue   
    component = cmds.getAttr(root + ".component")
    module = importlib.import_module("domino.component." + component)
    rig = module.Rig()
    attribute_data = module.DATA
    for attr in attribute_data.copy():
        if attr[attr.long_name]["multi"]:
            value = []
            for a in cmds.listAttr(root + "." + attr.long_name, multi=True) or []:
                value.append(cmds.getAttr(root + "." + a))
        else:
            value = cmds.getAttr(root + "." + attr.long_name)
        rig[attr.long_name]["value"] = value
    rig.detach_guide()
cmds.select(selected)"""

reset_command = """from domino.core import Controller
from maya import cmds
for sel in cmds.ls(selection=True):
    if not cmds.objExists(sel + ".is_domino_controller"):
        continue
    Controller.reset(node=sel)"""

reset_child_command = """from domino.core import Controller
from maya import cmds
selected = cmds.ls(selection=True)
controllers = []
for sel in selected:
    if cmds.objExists(sel + ".is_domino_controller"):
        controllers.append(sel)
        controllers.extend(Controller.get_child_controller(sel))
for con in set(controllers):
    Controller.reset(node=con)"""

rt_symmetry_controller_command = """from maya import cmds
from domino.core import Controller
selected = [x for x in cmds.ls(selection=True) if cmds.objExists(x + ".is_domino_controller")]
for sel in selected:
    mirror_ctl = cmds.getAttr(sel + ".mirror_controller_name")
    if not cmds.objExists(mirror_ctl) or mirror_ctl == sel: 
        continue
    t, r = Controller.get_mirror_RT(node=sel)
    cmds.setAttr(mirror_ctl + ".t", *t)
    cmds.setAttr(mirror_ctl + ".r", *r)"""

rt_flip_controller_command = """from maya import cmds
from domino.core import Controller
selected = [x for x in cmds.ls(selection=True) if cmds.objExists(x + ".is_domino_controller")]
for sel in selected:
    mirror_ctl = cmds.getAttr(sel + ".mirror_controller_name")
    if not cmds.objExists(mirror_ctl) or mirror_ctl == sel: 
        continue
    t, r = Controller.get_mirror_RT(node=sel)
    mirror_t = cmds.getAttr(mirror_ctl + ".t")[0]
    mirror_r = cmds.getAttr(mirror_ctl + ".r")[0]
    cmds.setAttr(mirror_ctl + ".t", *t)
    cmds.setAttr(mirror_ctl + ".r", *r)
    cmds.setAttr(sel + ".t", *mirror_t)
    cmds.setAttr(sel + ".r", *mirror_r)"""

matrix_symmetry_controller_command = """"""
matrix_flip_controller_command = """"""

preroll_command = """from domino.core import Controller
from maya import cmds 
cogCtl = "origin_COG_ctl"
"""

fkik_switch_command = """"""


def controller_menu(
    parent_menu: str, is_assembly: bool = False, has_fkik_switch: bool = False
) -> None:
    cmds.menu(parent_menu, edit=True, deleteAllItems=True)
    if CONTROLLER_APPLY_CHILDREN_OPTION not in cmds.optionVar(list=True):
        cmds.optionVar(intValue=(CONTROLLER_APPLY_CHILDREN_OPTION, 0))
    apply_children_state = cmds.optionVar(query=CONTROLLER_APPLY_CHILDREN_OPTION)

    cmds.menuItem(
        parent=parent_menu,
        label="Apply children",
        radialPosition="N",
        command=apply_children_option_commnad,
        checkBox=apply_children_state,
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Controller Panel",
        radialPosition="NE",
        command=controller_panel_command,
        image="origin_shape.png",
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Attach Guide",
        radialPosition="E",
        command=attach_guide_command,
        image="plug-connected.svg",
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Detach Guide",
        radialPosition="SE",
        command=detach_guide_command,
        image="plug-connected-x.svg",
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Reset",
        radialPosition="NW",
        command=reset_child_command if apply_children_state else reset_command,
        image="refresh.png",
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Mirror / Flip (PLANE)",
        radialPosition="W",
        image="symmetryConstraint.svg",
        command=rt_symmetry_controller_command,
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parent_menu,
        optionBox=True,
        command='print("Mirror Set Key")',
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Mirror / Flip (SRT)",
        radialPosition="SW",
        image="arrows-exchange.svg",
        command=rt_flip_controller_command,
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parent_menu,
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
