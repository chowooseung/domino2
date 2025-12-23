# maya
from maya import cmds, mel

# built-ins
from functools import partial

STATEOPTION = "domino_dag_menu_state"
PARENTMENUS = "domino_command_parent_menus"
CONTROLLER_APPLY_CHILDREN_OPTION = "domino_controller_apply_children"
GUIDE_APPLY_CHILDREN_OPTION = "domino_guide_apply_children"


# region INSTALL Menu
def install(menu_id):
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

    def callback_dag_menu_install():
        status = cmds.optionVar(query=STATEOPTION)
        parent_menus = cmds.optionVar(query=PARENTMENUS).split(" ")
        for menu in parent_menus:
            if status:
                cmds.menu(menu, edit=True, postMenuCommand=partial(popup_menu, menu))
            else:
                mel.eval(
                    f"""menu -edit -postMenuCommand "buildObjectMenuItemsNow {menu}" {menu}"""
                )

    def toggle_domino_dag_menu_status(*args, **kwargs):
        if cmds.optionVar(query=STATEOPTION):
            cmds.optionVar(intValue=(STATEOPTION, 0))
        else:
            cmds.optionVar(intValue=(STATEOPTION, 1))

        callback_dag_menu_install()

    original_status = cmds.optionVar(query=STATEOPTION)

    cmds.setParent(menu_id, menu=True)
    cmds.menuItem(divider=True)
    cmds.menuItem(
        f"{STATEOPTION}_menu",
        label="Dag Menu",
        command=partial(toggle_domino_dag_menu_status),
        checkBox=original_status,
    )
    callback_dag_menu_install()


def popup_menu(parent_menu, *args, **kwargs):
    selection = cmds.ls(selection=True)
    maya_dag_menu = False

    # 마야가 pSphere1.vtx[0].is_domino_guide 같은것도 true 로 반환한다. fuck
    if selection and "." not in selection[0]:
        if cmds.objExists(f"{selection[0]}.is_domino_guide") or cmds.objExists(
            f"{selection[0]}.is_domino_guide_root"
        ):
            guide_menu(parent_menu)
            maya_dag_menu = True
        elif cmds.objExists(f"{selection[0]}.is_domino_rig"):
            rig_menu(parent_menu)
            maya_dag_menu = True
        elif cmds.objExists(f"{selection[0]}.is_domino_controller"):
            stack = (
                cmds.listConnections(
                    f"{selection[0]}.message",
                    source=False,
                    destination=True,
                    type="transform",
                )
                or []
            )
            root = None
            while stack:
                n = stack.pop(0)
                if cmds.objExists(f"{n}.is_domino_rig_root"):
                    root = n
                    break
            host = (
                cmds.listConnections(
                    f"{root}.host", source=True, destination=False, type="transform"
                )
                or []
            )
            controller_menu(
                parent_menu,
                True if host else False,
                (
                    True
                    if cmds.getAttr(f"{selection[0]}.component") == "assembly"
                    else False
                ),
                True if cmds.objExists(f"{selection[0]}.fkik_command_attr") else False,
            )
            maya_dag_menu = True
        elif cmds.objExists(f"{selection[0]}.is_domino_skel"):
            skel_menu(parent_menu)
            maya_dag_menu = True
    if not maya_dag_menu:
        mel.eval(f"buildObjectMenuItemsNow {parent_menu}")


# endregion

# region GUIDE Commands
matchTR_command = """from maya import cmds

selected = cmds.ls(selection=True)
if len(selected) > 1:
    cmds.matchTransform(selected[:-1], selected[-1], position=True, rotation=True)"""

aim_command = """from maya import cmds

selected = cmds.ls(selection=True)
if len(selected) == 2:
    cmds.delete(
        cmds.aimConstraint(
            selected[1],
            selected[0],
            aimVector=(1, 0, 0),
            upVector=(0, 1, 0),
            worldUpType="scene",
        )
    )
    cmds.select(selected)
elif len(selected) == 3:
    cmds.delete(
        cmds.aimConstraint(
            selected[1],
            selected[0],
            aimVector=(1, 0, 0),
            upVector=(0, 1, 0),
            worldUpType="object",
            worldUpObject=selected[2],
        )
    )
    cmds.select(selected)"""

detach_guide_command = """from maya import cmds
from domino.component import serialize

roots = []
for sel in cmds.ls(selection=True):
    if cmds.objExists(sel + ".is_domino_guide"):
        roots.append(
            cmds.listConnections(
                sel + ".worldMatrix[0]", type="transform", connections=True
            )[1]
        )
    elif cmds.objExists(sel + ".is_domino_guide_root"):
        roots.append(sel)
rig = serialize()
stack = [rig]
while stack:
    component = stack.pop(0)
    if component.guide_root in roots and cmds.objExists(component.guide_root):
        component.detach_guide()
    stack.extend(component["children"])"""
# endregion


# region GUIDE Menu
def guide_menu(parent_menu):
    cmds.menu(parent_menu, edit=True, deleteAllItems=True)

    cmds.menuItem(
        parent=parent_menu,
        label="Match TR",
        radialPosition="NE",
        command=matchTR_command,
        image="status-change.svg",
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Aim",
        radialPosition="E",
        command=aim_command,
        image="aimConstraint.png",
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Detach Guide",
        radialPosition="SW",
        command=detach_guide_command,
        image="plug-connected-x.svg",
    )


# endregion

# region RIG Commands
validation_command = """from domino import validation
validation.show_ui()
ins = validation.ValidateUI.get_instance()
ins.stacked_widget.slide_to_index(0)
ins.validate()
"""

spacemanager_command = """from domino import spacemanager

ins = spacemanager.SpaceManager.get_instance()
ins.show()
ins.refresh()"""

psdmanager_command = """from domino import psdmanager

ins = psdmanager.PSDManager.get_instance()
ins.show()
ins.refresh()"""


sdkmanager_command = """from domino import sdkmanager

ins = sdkmanager.SDKManager.get_instance()
ins.show()
ins.refresh()"""

dynamicmanager_command = """from domino import dynamicmanager

ins = dynamicmanager.DynamicManager.get_instance()
ins.show()
ins.refresh()"""

add_data_command = """from maya import cmds
from maya import OpenMayaUI as omui
from shiboken6 import wrapInstance
from PySide6 import QtWidgets

selected = cmds.ls(selection=True)
if cmds.objExists("rig"):
    for sel in selected[1:]:
        shapes = cmds.listRelatives(sel, shapes=True)
        if not shapes:
            continue
        if cmds.nodeType(shapes[0]) == "nurbsCurve":
            cmds.parent(sel, "rig")
            next_index = len(
                cmds.listConnections(
                    "rig.custom_nurbscurve_data",
                    source=True,
                    destination=False,
                )
                or []
            )
            cmds.connectAttr(sel + ".message", f"rig.custom_nurbscurve_data[{next_index}]")
        elif cmds.nodeType(shapes[0]) == "nurbsSurface":
            cmds.parent(sel, "rig")
            next_index = len(
                cmds.listConnections(
                    "rig.custom_nurbssurface_data",
                    source=True,
                    destination=False,
                )
                or []
            )
            cmds.connectAttr(sel + ".message", f"rig.custom_nurbssurface_data[{next_index}]")
        elif cmds.nodeType(shapes[0]) == "mesh":
            cmds.parent(sel, "rig")
            next_index = len(
                cmds.listConnections(
                    "rig.custom_mesh_data",
                    source=True,
                    destination=False,
                )
                or []
            )
            cmds.connectAttr(sel + ".message", f"rig.custom_mesh_data[{next_index}]")
    cmds.select(selected)
    main_window_ptr = omui.MQtUtil.mainWindow()
    main_window_widget = wrapInstance(int(main_window_ptr), QtWidgets.QWidget)
    domino_manager_ui = main_window_widget.findChild(QtWidgets.QWidget, "domino_manager_ui")
    if domino_manager_ui:
        domino_manager_ui.refresh()"""
# endregion


# region RIG Menu
def rig_menu(parent_menu):
    cmds.menu(parent_menu, edit=True, deleteAllItems=True)

    cmds.menuItem(
        parent=parent_menu,
        label="Validate",
        radialPosition="N",
        command=validation_command,
        image="list.svg",
    )

    cmds.menuItem(
        parent=parent_menu,
        label="Show Space Manager",
        command=spacemanager_command,
        image="bounce-right.svg",
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Show PSD Manager",
        command=psdmanager_command,
        image="yoga.svg",
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Show SDK Manager",
        command=sdkmanager_command,
        image="sdk.svg",
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Show Dynamic Manager",
        command=dynamicmanager_command,
        image="flag.svg",
    )
    cmds.menuItem(parent=parent_menu, divider=True)
    cmds.menuItem(
        parent=parent_menu,
        label="Add Data (Mesh / Curve)",
        command=add_data_command,
        enableCommandRepeat=True,
        image="lasso-polygon.svg",
    )


# endregion

# region Controller Commands
go_to_host_command = """from maya import cmds
selected = cmds.ls(selection=True)
hosts = []
for sel in selected:
    stack = cmds.listConnections(sel + ".message", source=False, destination=True, type="transform") or []
    root = None
    while stack:
        n = stack.pop(0)
        if cmds.objExists(n + ".is_domino_rig_root"):
            root = n
            break
    host = cmds.listConnections(root + ".host", source=True, destination=False, type="transform") or []
    if host:
        hosts.append(host[0])
if hosts:
    cmds.select(hosts)
"""

apply_children_option_commnad = f"""from maya import cmds
apply_children_state = cmds.optionVar(query="{CONTROLLER_APPLY_CHILDREN_OPTION}")
state = False if apply_children_state else True
cmds.optionVar(intValue=("{CONTROLLER_APPLY_CHILDREN_OPTION}", state))"""

controller_panel_command = """from domino import controllerpanel
controllerpanel.show()"""

reset_command = """from domino.core import Controller
from maya import cmds
selected = [
    x for x in cmds.ls(selection=True) if cmds.objExists(x + ".is_domino_controller")
]
controllers = []
for sel in selected:
    controllers.append(sel)
    if {0}:
        controllers.extend(Controller.get_child_controller(sel))
for ctl in set(controllers):
    Controller.reset(node=ctl, srt={1})"""

mirror_controller_command = """from maya import cmds
from domino.core import Controller

selected = [
    x for x in cmds.ls(selection=True) if cmds.objExists(x + ".is_domino_controller")
]
controllers = []
for sel in selected:
    controllers.append(sel)
    if {0}:
        controllers.extend(Controller.get_child_controller(sel))
controllers = list(set(controllers))
attrs = ["tx", "ty", "tz", "rx", "ry", "rz"]
for ctl in controllers:
    mirror_ctl = cmds.getAttr(ctl + ".mirror_controller_name")
    if not cmds.objExists(mirror_ctl) or mirror_ctl == ctl:
        continue
    orig_t = cmds.getAttr(ctl + ".t")[0]
    orig_r = cmds.getAttr(ctl + ".r")[0]
    mirror_type = cmds.getAttr(ctl + ".mirror_type")
    t, r = Controller.get_mirror_RT(t=orig_t, r=orig_r, mirror_type=mirror_type)
    for attr, value in zip(attrs, t + r):
        if cmds.getAttr(mirror_ctl + "." + attr, lock=True):
            continue   
        cmds.setAttr(mirror_ctl + "." + attr, value)"""

flip_controller_command = """from maya import cmds
from domino.core import Controller

selected = [
    x for x in cmds.ls(selection=True) if cmds.objExists(x + ".is_domino_controller")
]
controllers = []
for sel in selected:
    controllers.append(sel)
    if {0}:
        controllers.extend(Controller.get_child_controller(sel))
controllers = list(set(controllers))
attrs = ["tx", "ty", "tz", "rx", "ry", "rz"]
for ctl in controllers:
    mirror_ctl = cmds.getAttr(ctl + ".mirror_controller_name")
    if not cmds.objExists(mirror_ctl) or mirror_ctl == ctl:
        continue
    target_t = cmds.getAttr(mirror_ctl + ".t")[0]
    target_r = cmds.getAttr(mirror_ctl + ".r")[0]
    source_t = cmds.getAttr(ctl + ".t")[0]
    source_r = cmds.getAttr(ctl + ".r")[0]
    mirror_type = cmds.getAttr(ctl + ".mirror_type")
    target_t, target_r = Controller.get_mirror_RT(t=target_t, r=target_r, mirror_type=mirror_type)
    source_t, source_r = Controller.get_mirror_RT(t=source_t, r=source_r, mirror_type=mirror_type)
    for attr, target_value, source_value in zip(attrs, target_t + target_r, source_t + source_r):
        if not cmds.getAttr(mirror_ctl + "." + attr, lock=True):
            cmds.setAttr(mirror_ctl + "." + attr, source_value)
        if not cmds.getAttr(ctl + "." + attr, lock=True):
            cmds.setAttr(ctl + "." + attr, target_value)"""

preroll_command = """from domino.core import Controller
from maya import cmds 

origin_ctl = cmds.ls(selection=True)[0]
controllers = Controller.get_child_controller(origin_ctl)
for ctl in set(controllers):
    Controller.reset(node=ctl, srt=False)
cmds.setKeyframe(controllers)"""

select_origin_controller_command = """from maya import cmds
selection = cmds.ls(selection=True)
if selection:
    _, namespace = cmds.ls(selection[0], showNamespace=True)
    if cmds.objExists(f"{namespace}:origin_ctl"):
        cmds.select(f"{namespace}:origin_ctl")"""

select_child_controller_command = """from domino.core import Controller
from maya import cmds
controllers = []
for sel in cmds.ls(selection=True):
    if not cmds.objExists(sel + ".is_domino_controller"):
        continue
    controllers.append(sel)
    controllers.extend(Controller.get_child_controller(node=sel))
cmds.select(controllers)"""

fkik_switch_command = """
a_time_slider = mel.eval('$tmpVar=$gPlayBackSlider')
time_range = cmds.timeControl(a_time_slider, query=True, rangeArray=True)"""

dynamic_tools_command = """from domino import dynamicmanager
dynamicmanager.show_dynamic_tools_ui()"""
# endregion


# region Controller Menu
def controller_menu(
    parent_menu, has_host=False, is_assembly=False, has_fkik_switch=False
):
    cmds.menu(parent_menu, edit=True, deleteAllItems=True)
    if CONTROLLER_APPLY_CHILDREN_OPTION not in cmds.optionVar(list=True):
        cmds.optionVar(intValue=(CONTROLLER_APPLY_CHILDREN_OPTION, 0))
    apply_children_state = cmds.optionVar(query=CONTROLLER_APPLY_CHILDREN_OPTION)

    if has_host:
        cmds.menuItem(
            parent=parent_menu,
            label="Go to host",
            radialPosition="N",
            command=go_to_host_command,
            image="host.png",
        )
    cmds.menuItem(
        parent=parent_menu,
        label="Reset",
        radialPosition="NE",
        command=(
            reset_command.format(True, True)
            if apply_children_state
            else reset_command.format(False, True)
        ),
        image="refresh.png",
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parent_menu,
        optionBox=True,
        command=(
            reset_command.format(True, False)
            if apply_children_state
            else reset_command.format(False, False)
        ),
        enableCommandRepeat=True,
    )
    if has_fkik_switch:
        cmds.menuItem(
            parent=parent_menu,
            label="FK / IK Switch",
            radialPosition="E",
            command=fkik_switch_command,
            enableCommandRepeat=True,
        )
        cmds.menuItem(
            parent=parent_menu,
            optionBox=True,
            command='print("fk/ik Set Key")',
        )
    cmds.menuItem(
        parent=parent_menu,
        label="Apply children",
        checkBox=apply_children_state,
        command=apply_children_option_commnad,
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Mirror",
        image="symmetryConstraint.svg",
        command=(
            mirror_controller_command.format(True)
            if apply_children_state
            else mirror_controller_command.format(False)
        ),
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parent_menu,
        label="Flip",
        image="arrows-exchange.svg",
        command=(
            flip_controller_command.format(True)
            if apply_children_state
            else flip_controller_command.format(False)
        ),
        enableCommandRepeat=True,
    )
    cmds.menuItem(parent=parent_menu, divider=True)
    if not is_assembly:
        cmds.menuItem(
            parent=parent_menu,
            label="Select origin controller",
            image="origin_shape.png",
            command=select_origin_controller_command,
            enableCommandRepeat=True,
        )
    cmds.menuItem(
        parent=parent_menu,
        label="Select child controllers",
        image="pointer-down.svg",
        command=select_child_controller_command,
        enableCommandRepeat=True,
    )
    if is_assembly:
        cmds.menuItem(parent=parent_menu, divider=True)
        cmds.menuItem(
            parent=parent_menu,
            label="Set pre-roll frame",
            image="character.svg",
            command=preroll_command,
            enableCommandRepeat=True,
        )
        cmds.menuItem(
            parent=parent_menu,
            label="Dynamic Tools",
            image="flag.svg",
            command=dynamic_tools_command,
            enableCommandRepeat=True,
        )


# endregion

# region Skeleton Commands
select_skel_command = """from maya import cmds

selected = cmds.ls(selection=True)[0]
namespace = selected.split(":")[0] if ":" in selected else ""
cmds.select(
    [
        x
        for x in cmds.ls(namespace + ":*" if namespace else "*", type="joint")
        if cmds.objExists(x + ".is_domino_skel")
    ]
)"""

bind_command = """from maya import cmds
from domino.core import rigkit

selected = cmds.ls(selection=True)
geometries = cmds.ls(selection=True, dagObjects=True, noIntermediate=True, type="mesh")
joints = cmds.ls(selection=True, type="joint")

for geometry in geometries:
    scs = [
        x
        for x in cmds.findDeformers(geometry) or []
        if cmds.nodeType(x) == "skinCluster"
    ]
    parent = cmds.listRelatives(geometry, parent=True)[0]
    name = parent + str(len(scs)) + "_sc"
    sc = rigkit.bind_skincluster(parent, joints, name)
cmds.select(selected)"""

bake_command = """from maya import cmds

selected = cmds.ls(selection=True)[0]
namespace = selected.split(":")[0] if ":" in selected else ""
joints = [
    x
    for x in cmds.ls(namespace + ":*" if namespace else "*", type="joint")
    if cmds.objExists(x + ".is_domino_skel")
]
start_time = cmds.playbackOptions(query=True, minTime=True)
end_time = cmds.playbackOptions(query=True, maxTime=True)
cmds.bakeResults(
    joints,
    simulation=True,
    t=(start_time, end_time),
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
    shape=True,
)"""
# endregion


# region Skeleton Menu
def skel_menu(parent_menu):
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
        label="Bake(Time slider)",
        radialPosition="SE",
        command=bake_command,
        image="bakeAnimation.png",
    )


# endregion
