# Qt
from PySide6 import QtWidgets

# maya
from maya import cmds
from maya.api import OpenMaya as om
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

# domino
from domino.core.utils import logger
from domino.component.assemblyui import Assembly
from domino.component.pivot01ui import Pivot01
from domino.component.cog01ui import COG01
from domino.component.control01ui import Control01
from domino.component.uicontainer01ui import UIContainer01
from domino.component.fk01ui import Fk01
from domino.component.fkik2jnt01ui import Fkik2Jnt01
from domino.component.humanspine01ui import HumanSpine01
from domino.component.humanneck01ui import HumanNeck01
from domino.component.humanarm01ui import HumanArm01
from domino.component.humanleg01ui import HumanLeg01
from domino.component.psd01ui import Psd01
from domino.component.chain01ui import Chain01
from domino.component.foot01ui import Foot01


UITABLE = {
    "assembly": Assembly,
    "pivot01": Pivot01,
    "cog01": COG01,
    "control01": Control01,
    "uicontainer01": UIContainer01,
    "fk01": Fk01,
    "fkik2jnt01": Fkik2Jnt01,
    "humanspine01": HumanSpine01,
    "humanneck01": HumanNeck01,
    "humanarm01": HumanArm01,
    "humanleg01": HumanLeg01,
    "foot01": Foot01,
    "psd01": Psd01,
    "chain01": Chain01,
}


def cb_auto_settings(*args):
    selected = cmds.ls(selection=True)
    if not selected:
        return None

    if cmds.objExists(f"{selected[0]}.is_domino_guide_root") or cmds.objExists(
        f"{selected[0]}.is_domino_guide"
    ):
        ui = Settings.get_instance()
        ui.refresh()


class Settings(MayaQWidgetDockableMixin, QtWidgets.QDialog):

    # 싱글톤 패턴
    _instance = None

    # maya ui script
    ui_name = "domino_settings_ui"
    ui_script = """from maya import cmds
command = "from domino.dominosettings import Settings;ui=Settings.get_instance();ui.show(dockable=True)"
cmds.evalDeferred(command)"""
    control_name = f"{ui_name}WorkspaceControl"

    callback_id = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, parent=None):
        if cmds.workspaceControl(self.control_name, query=True, exists=True):
            cmds.workspaceControl(self.control_name, edit=True, restore=True)
            cmds.workspaceControl(self.control_name, edit=True, close=True)
            cmds.deleteUI(self.control_name, control=True)

        super(Settings, self).__init__(parent=parent)
        self.setObjectName(self.ui_name)
        self.setWindowTitle("Domino Settings")

        self.layout_ = QtWidgets.QVBoxLayout(self)

    def refresh(self):
        # region -    Settings / clear layout
        self.empty_label = QtWidgets.QLabel("Guide 를 선택해주세요.")

        stack = [self.layout_]
        while stack:
            layout = stack.pop(0)
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                sub_layout = item.layout()
                if sub_layout is not None:
                    stack.append(sub_layout)
        # endregion

        selected = cmds.ls(selection=True, objectsOnly=True)
        if not selected:
            self.layout_.addWidget(self.empty_label)
            return None

        try:
            if cmds.objExists(f"{selected[0]}.is_domino_guide"):
                plug = cmds.listConnections(
                    f"{selected[0]}.message",
                    source=False,
                    destination=True,
                    type="transform",
                )[0]
                guide_root = plug.split(".")[0]
            elif cmds.objExists(f"{selected[0]}.is_domino_guide_root"):
                guide_root = selected[0]
            else:
                return
            component = cmds.getAttr(f"{guide_root}.component")
            ui_ins = UITABLE[component](root=guide_root)
        except Exception as e:
            logger.error(e, exc_info=True)
            self.layout_.addWidget(self.empty_label)
            return None

        # add settings widget
        self.layout_.addWidget(ui_ins)

    def showEvent(self, e):
        cmds.workspaceControl(self.control_name, edit=True, uiScript=self.ui_script)
        self.refresh()
        if self.callback_id is None:
            self.callback_id = om.MEventMessage.addEventCallback(
                "SelectionChanged", cb_auto_settings
            )
            logger.info(f"Add Auto Settings callback id: {self.callback_id}")
        super(Settings, self).showEvent(e)

    def hideEvent(self, e):
        if self.callback_id:
            logger.info(f"Remove Auto Settings callback id: {self.callback_id}")
            om.MMessage.removeCallback(self.callback_id)
            self.callback_id = None
        super(Settings, self).hideEvent(e)
