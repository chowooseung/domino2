# maya
from maya import cmds

# domino
from domino.core import dagmenu


averageVectorCommand = """from maya import cmds
"""


def installRigCommandsMenu(menuID):
    pass


## maya menu
def install():
    menuID = "Domino"

    cmds.menu(
        menuID, parent="MayaWindow", tearOff=True, allowOptionBoxes=True, label=menuID
    )
    dagmenu.install(menuID=menuID)

    cmds.setParent(menuID, menu=True)
    cmds.menuItem(divider=True)

    installRigCommandsMenu(menuID=menuID)

    logMenu = cmds.menuItem("DominoLoggingMenu", label="Log Level", subMenu=True)
    cmds.setParent(logMenu, menu=True)
    cmds.radioMenuItemCollection()
    cmds.menuItem(
        label="Info",
        radioButton=True,
        command="import logging;from domino.core.utils import LOGGER;LOGGER.setLevel(logging.INFO)",
    )
    cmds.menuItem(
        label="Debug",
        radioButton=False,
        command="import logging;from domino.core.utils import LOGGER;LOGGER.setLevel(logging.DEBUG)",
    )
