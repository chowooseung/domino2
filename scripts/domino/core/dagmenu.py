# maya
from maya import cmds, mel

# built-ins
from functools import partial

STATEOPTION = "dominoDagMenuState"
PARENTMENUS = "dominoCommandParentMenus"


def install(menuID: str) -> None:
    if STATEOPTION not in cmds.optionVar(list=True):
        cmds.optionVar(intValue=(STATEOPTION, 0))

    parentMenus = []
    for menu in cmds.lsUI(menus=True):
        menuCommand = cmds.menu(menu, query=True, postMenuCommand=True) or []
        if isinstance(menuCommand, str):
            if "buildObjectMenuItemsNow" in menuCommand:
                parentMenus.append(menuCommand.split(" ")[-1][1:-1])
    cmds.optionVar(stringValue=(PARENTMENUS, " ".join(parentMenus)))

    def callbackDagMenuInstall() -> None:
        state = cmds.optionVar(query=STATEOPTION)
        parentMenus = cmds.optionVar(query=PARENTMENUS).split(" ")
        for menu in parentMenus:
            if state:
                cmds.menu(menu, edit=True, postMenuCommand=partial(popupMenu, menu))
            else:
                mel.eval(
                    f"""menu -edit -postMenuCommand "buildObjectMenuItemsNow {menu}" {menu}"""
                )

    def toggleDominoDagMenuStatus(*args, **kwargs) -> None:
        if cmds.optionVar(query=STATEOPTION):
            cmds.optionVar(intValue=(STATEOPTION, 0))
        else:
            cmds.optionVar(intValue=(STATEOPTION, 1))

        callbackDagMenuInstall()

    originalStatus = cmds.optionVar(query=STATEOPTION)

    cmds.setParent(menuID, menu=True)
    cmds.menuItem(divider=True)
    cmds.menuItem(
        STATEOPTION + "Menu",
        label="DagMenu",
        command=partial(toggleDominoDagMenuStatus),
        checkBox=originalStatus,
    )
    callbackDagMenuInstall()


def popupMenu(parentMenu: str, *args, **kwargs) -> None:
    selection = cmds.ls(selection=True)
    mayaDagMenu = False

    if selection:
        if cmds.objExists(selection[0] + ".isDominoGuide") or cmds.objExists(
            selection[0] + ".isDominoGuideRoot"
        ):
            guideMenu(parentMenu)
            mayaDagMenu = True
        elif cmds.objExists(selection[0] + ".isDominoRig"):
            rigMenu(parentMenu)
            mayaDagMenu = True
        elif cmds.objExists(selection[0] + ".isDominoController"):
            controllerMenu(
                parentMenu,
                (
                    True
                    if cmds.getAttr(selection[0] + ".component") == "assembly"
                    else False
                ),
                True if cmds.objExists(selection[0] + ".fkikCommandAttr") else False,
            )
            mayaDagMenu = True
        elif cmds.objExists(selection[0] + ".isDominoSkel"):
            skelMenu(parentMenu)
            mayaDagMenu = True
    if not mayaDagMenu:
        mel.eval("buildObjectMenuItemsNow " + parentMenu)


managerCommand = """"""

settingsCommand = """from maya import cmds, mel
selected = cmds.ls(selection=True)
if cmds.objExists(selected[0] + ".isDominoGuideRoot"):
    cmds.AttributeEditor()
    mel.eval('setLocalView "Rigging" "" 1;')
if cmds.objExists(selected[0] + ".isDominoGuide"):
    cmds.select(cmds.listConnections(selected[0] + ".worldMatrix[0]", source=False, destination=True, type="transform"))
    cmds.AttributeEditor()
    mel.eval('setLocalView "Rigging" "" 1;')"""

symmetryGuideCommand = """"""

matchTRCommand = """from maya import cmds
selected = cmds.ls(selection=True)
if len(selected) > 1:
    cmds.matchTransform(selected[:-1], selected[-1], position=True, rotation=True)"""

aimCommand = """from maya import cmds
selected = cmds.ls(selection=True)
if len(selected) == 2:
    cmds.delete(cmds.aimConstraint(selected[1], selected[0], aimVector=(1, 0, 0), upVector=(0, 1, 0), worldUpType="scene"))
    cmds.select(selected)
if len(selected) == 3:
    cmds.delete(cmds.aimConstraint(selected[1], selected[0], aimVector=(1, 0, 0), upVector=(0, 1, 0), worldUpType="object", worldUpObject=selected[2]))
    cmds.select(selected)"""


def guideMenu(parentMenu: str) -> None:
    cmds.menu(parentMenu, edit=True, deleteAllItems=True)

    cmds.menuItem(
        parent=parentMenu,
        label="Manager",
        radialPosition="N",
        image="swipe.svg",
        command=managerCommand,
    )
    cmds.menuItem(
        parent=parentMenu,
        label="Settings",
        radialPosition="NE",
        command=settingsCommand,
        image="advancedSettings.png",
    )

    cmds.menuItem(
        parent=parentMenu,
        label="Symmetry",
        radialPosition="W",
        image="symmetryConstraint.svg",
        enableCommandRepeat=True,
        command=symmetryGuideCommand,
    )

    cmds.menuItem(
        parent=parentMenu,
        label="Match TR",
        radialPosition="SE",
        command=matchTRCommand,
        image="status-change.svg",
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parentMenu,
        label="Aim",
        radialPosition="S",
        command=aimCommand,
        image="aimConstraint.png",
        enableCommandRepeat=True,
    )


validationCommand = "from domino import validation;validation.show()"

packUpRigCommand = """from maya import cmds
from domino.core import utils
if cmds.objExists("guide"):
    cmds.delete("guide")
info = "mayaVersion : " + utils.mayaVersion() + "\\n"
info += "usedPlugins : "
plugins = utils.usedPlugins()
for i in range(int(len(plugins) / 2)):
    info += "\\n\\t" + plugins[i * 2] + "\\t" + plugins[i * 2 + 1]
cmds.addAttr("rig", longName="notes", dataType="string")
cmds.setAttr("rig.notes", info, type="string")
cmds.setAttr("rig.notes", lock=True)
utils.localizeBifrostGraph()"""

spacemanagerCommand = """from maya import cmds
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

posemanagerCommand = """from maya import cmds
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

sdkmanagerCommand = """from maya import cmds
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

addDataCommand = """from maya import cmds
from domino.core import Curve, Polygon
assemblyNode = ""
for n in cmds.ls(type="transform"):
    if (
        cmds.objExists(n + ".isDominoRigRoot")
        and cmds.getAttr(n + ".component") == "assembly"
    ):
        assemblyNode = n
if not cmds.objExists(assemblyNode + ".customCurveData"):        
    cmds.addAttr(assemblyNode, longName="customCurveData", attributeType="message", multi=True)
if not cmds.objExists(assemblyNode + ".customPolygonData"):        
    cmds.addAttr(assemblyNode, longName="customPolygonData", attributeType="message", multi=True)
if cmds.objExists("guide"):
    selected = cmds.ls(selection=True)
    for sel in selected[1:]:
        shapes = cmds.listRelatives(sel, shapes=True)
        if not shapes:
            continue
        if cmds.nodeType(shapes[0]) == "nurbsCurve":
            cmds.parent(sel, selected[0])
            nextIndex = len(
                cmds.listConnections(
                    assemblyNode + ".customCurveData",
                    source=True,
                    destination=False,
                )
                or []
            )
            cmds.connectAttr(sel + ".message", f"{assemblyNode}.customCurveData[{nextIndex}]")
        elif cmds.nodeType(shapes[0]) == "mesh":
            cmds.parent(sel, selected[0])
            nextIndex = len(
                cmds.listConnections(
                    assemblyNode + ".customPolygonData",
                    source=True,
                    destination=False,
                )
                or []
            )
            cmds.connectAttr(sel + ".message", f"{assemblyNode}.customPolygonData[{nextIndex}]")"""

saveCommand = """from domino.component import save
filePath = cmds.fileDialog2(caption="Save Domino Rig",
                            startingDirectory=cmds.workspace(query=True, rootDirectory=True),
                            fileFilter="Domino Rig (*.domino)",
                            fileMode=0)
if filePath:
    save(filePath[0])"""


def rigMenu(parentMenu: str) -> None:
    cmds.menu(parentMenu, edit=True, deleteAllItems=True)

    cmds.menuItem(
        parent=parentMenu,
        label="Validate",
        radialPosition="N",
        command=validationCommand,
        image="list.svg",
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parentMenu,
        label="Pack up Rig",
        radialPosition="W",
        command=packUpRigCommand,
        image="empty-state.png",
        enableCommandRepeat=True,
    )

    cmds.menuItem(
        parent=parentMenu,
        label="Show Space Manager",
        command=spacemanagerCommand,
        image="bounce-right.svg",
    )
    cmds.menuItem(
        parent=parentMenu,
        label="Show Pose Manager",
        command=posemanagerCommand,
        image="yoga.svg",
    )
    cmds.menuItem(
        parent=parentMenu,
        label="Show SDK Manager",
        command=sdkmanagerCommand,
        image="sdk.svg",
    )
    cmds.menuItem(parent=parentMenu, divider=True)
    cmds.menuItem(
        parent=parentMenu,
        label="Add Data (Mesh / Curve)",
        command=addDataCommand,
        enableCommandRepeat=True,
        image="lasso-polygon.svg",
    )

    cmds.menuItem(parent=parentMenu, divider=True)
    cmds.menuItem(
        parent=parentMenu,
        label="Save rig to File",
        image="save.png",
        command=saveCommand,
    )


resetCommand = """from domino.core import Controller
from maya import cmds
trAttrs = [".tx", ".ty", ".tz", ".rx", ".ry", ".rz"]
sAttrs = [".sx", ".sy", ".sz"]
for sel in cmds.ls(selection=True):
    if not cmds.objExists(sel + ".isDominoController"):
        continue
    for attr in trAttrs:
        if cmds.getAttr(sel + attr, lock=True):
            continue
        cmds.setAttr(sel + attr, 0)
    for attr in sAttrs:
        if cmds.getAttr(sel + attr, lock=True):
            continue
        cmds.setAttr(sel + attr, 1)
    keyableAttrs = cmds.listAttr(sel, userDefined=True, keyable=True) or []
    for attr in keyableAttrs:
        defaultValue = cmds.addAttr(sel + "." + attr, query=True, defaultValue=True)
        cmds.setAttr(sel + "." + attr, defaultValue)"""

resetChildCommand = """from domino.core import Controller
from maya import cmds
selected = cmds.ls(selection=True)
trAttrs = [".tx", ".ty", ".tz", ".rx", ".ry", ".rz"]
sAttrs = [".sx", ".sy", ".sz"]
controllers = []
for sel in selected:
    if cmds.objExists(sel + ".isDominoController"):
        controllers.append(sel)
        controllers.extend(Controller.getChildController(sel))
for con in controllers:
    for attr in trAttrs:
        if cmds.getAttr(con + attr, lock=True):
            continue
        cmds.setAttr(con + attr, 0)
    for attr in sAttrs:
        if cmds.getAttr(con + attr, lock=True):
            continue
        cmds.setAttr(con + attr, 1)
    keyableAttrs = cmds.listAttr(con, userDefined=True, keyable=True) or []
    for attr in keyableAttrs:
        defaultValue = cmds.addAttr(con + "." + attr, query=True, defaultValue=True)
        cmds.setAttr(con + "." + attr, defaultValue)"""

symmetryControllerCommand = """"""

flipControllerCommand = """"""

prerollCommand = """from domino.core import Controller
from maya import cmds 
cogCtl = "origin_COG_ctl"
"""

fkikSwitchCommand = """"""


def controllerMenu(
    parentMenu: str, isAssembly: bool = False, hasFkikSwitch: bool = False
) -> None:
    cmds.menu(parentMenu, edit=True, deleteAllItems=True)

    cmds.menuItem(
        parent=parentMenu,
        label="Reset",
        radialPosition="NE",
        command=resetCommand,
        image="refresh.png",
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parentMenu,
        label="Reset Child",
        radialPosition="E",
        command=resetChildCommand,
        image="refresh.png",
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parentMenu,
        label="Symmetry",
        radialPosition="W",
        image="symmetryConstraint.svg",
        command=symmetryControllerCommand,
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parentMenu,
        label="Symmetry(Set Key)",
        optionBox=True,
        command='print("Mirror Set Key")',
    )
    cmds.menuItem(
        parent=parentMenu,
        label="Flip",
        radialPosition="SW",
        image="arrows-exchange.svg",
        command=flipControllerCommand,
        enableCommandRepeat=True,
    )
    cmds.menuItem(
        parent=parentMenu,
        label="Flip(Set Key)",
        optionBox=True,
        command='print("Flip Set Key")',
    )

    if isAssembly:
        cmds.menuItem(
            parent=parentMenu,
            label="Set pre-roll frame",
            image="character.svg",
            command=prerollCommand,
            enableCommandRepeat=True,
        )

    if hasFkikSwitch:
        cmds.menuItem(
            parent=parentMenu,
            label="FK / IK Switch",
            command=fkikSwitchCommand,
            enableCommandRepeat=True,
        )
        cmds.menuItem(
            parent=parentMenu,
            label="FK / IK Switch(Set Key)",
            optionBox=True,
            command='print("fk/ik Set Key")',
        )


selectSkelCommand = """from maya import cmds
selected = cmds.ls(selection=True)[0]
namespace = selected.split(":")[0] if ":" in selected else ""
cmds.select([x for x in cmds.ls(namespace + ":*" if namespace else "*", type="joint") if cmds.objExists(x + ".isDominoSkel")])"""

bindCommand = """from maya import cmds
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

breakCommand = """from maya import cmds
joints = [x for x in cmds.ls("*", type="joint") if cmds.objExists(x + ".isDominoSkel")]
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

bakeCommand = """from maya import cmds
selected = cmds.ls(selection=True)[0]
namespace = selected.split(":")[0] if ":" in selected else ""
joints = [x for x in cmds.ls(namespace + ":*" if namespace else "*", type="joint") if cmds.objExists(x + ".isDominoSkel")]
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


def skelMenu(parentMenu: str) -> None:
    cmds.menu(parentMenu, edit=True, deleteAllItems=True)
    cmds.menuItem(
        parent=parentMenu,
        label="Select All Skel",
        radialPosition="NW",
        command=selectSkelCommand,
        image="kinJoint.png",
    )
    cmds.menuItem(
        parent=parentMenu,
        label="Bind Skin",
        radialPosition="N",
        command=bindCommand,
        image="smoothSkin.png",
    )
    cmds.menuItem(
        parent=parentMenu,
        label="Break(All Bind Skel)",
        radialPosition="E",
        command=breakCommand,
        image="resetSettings.svg",
    )
    cmds.menuItem(
        parent=parentMenu,
        label="Bake(Time slider)",
        radialPosition="SE",
        command=bakeCommand,
        image="resetSettings.svg",
    )
