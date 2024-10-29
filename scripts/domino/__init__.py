# maya
from maya import cmds

# domino
from domino.core import dagmenu


average_vector_command = """from maya import cmds
"""


def install_rig_commands_menu(menuID):
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

    install_rig_commands_menu(menuID=menuID)

    log_menu = cmds.menuItem("DominoLoggingMenu", label="Log Level", subMenu=True)
    cmds.setParent(log_menu, menu=True)
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
