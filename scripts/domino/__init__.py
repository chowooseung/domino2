# maya
from maya import cmds

# domino
from domino.core import dagmenu


average_vector_command = """from maya import cmds
"""


def install_rig_commands_menu(menu_id):
    sub_menu = cmds.menuItem(
        parent=menu_id, subMenu=True, label="Rig Commands", tearOff=True
    )


## maya menu
def install():
    menu_id = "domino"
    if cmds.menu(menu_id, exists=True):
        cmds.deleteUI(menu_id)

    cmds.menu(
        menu_id, parent="MayaWindow", tearOff=True, allowOptionBoxes=True, label=menu_id
    )
    dagmenu.install(menu_id=menu_id)

    cmds.setParent(menu_id, menu=True)
    cmds.menuItem(divider=True)

    install_rig_commands_menu(menu_id=menu_id)
    cmds.setParent(menu_id, menu=True)

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
