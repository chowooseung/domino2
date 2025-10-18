# Qt
from PySide6 import QtWidgets, QtCore, QtGui

# maya
from maya import cmds
from maya import mel
from maya.api import OpenMaya as om
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

# domino
from domino.component import (
    RIG,
    GUIDE,
    RIG_SETS,
    COMPONENTLIST,
    build,
    serialize,
    save,
    load,
    Name,
    SKEL,
    DEFORMER_WEIGHTS_SETS,
    BLENDSHAPE_SETS,
    BREAK_POINT_RIG,
    BREAK_POINT_PRECUSTOMSCRIPTS,
    BREAK_POINT_BLENDSHAPE,
    BREAK_POINT_SPACEMANAGER,
    BREAK_POINT_SDKMANAGER,
    BREAK_POINT_PSDMANAGER,
    BREAK_POINT_DYNAMICMANAGER,
    BREAK_POINT_DEFORMERWEIGHTS,
    BREAK_POINT_DEFORMERORDER,
    BREAK_POINT_POSTCUSTOMSCRIPTS,
)
from domino.core.utils import logger
from domino.dominosettings import Settings

# built-ins
from functools import partial
from pathlib import Path
import importlib
import pprint
import pickle
import os
import re

# icon
icon_dir = Path(__file__).parent.parent.parent / "icons"

# comopnent list
COMPONENTLIST.remove("assembly")


# region maya cb
def cb_setup_output_joint(child, parent, client_data):
    if not cmds.objExists(f"{child.fullPathName()}.is_domino_skel"):
        return

    try:
        cmds.undoInfo(openChunk=True)
        output_joint = child.fullPathName()
        parent = parent.fullPathName()

        index = cmds.getAttr(f"{output_joint}.skel_index")
        if parent.split("|")[-1] == "skel":
            cmds.connectAttr(
                "skel.worldInverseMatrix[0]",
                f"{SKEL}.initialize_parent_inverse_matrix[{index}]",
                force=True,
            )
            logger.info(
                f"Connect {SKEL}.worldInverseMatrix[0] -> {SKEL}.initialize_parent_inverse_matrix[{index}]"
            )
            return
        if cmds.objExists(f"{parent}.is_domino_skel"):
            parent_output_attr = cmds.connectionInfo(
                f"{parent}.output", sourceFromDestination=True
            )
            parent_output = parent_output_attr.split(".")[0]
            parent_root_attr = [
                x
                for x in cmds.connectionInfo(
                    f"{parent_output}.message", destinationFromSource=True
                )
                if cmds.nodeType(x) == "transform" and ".output" in x
            ]
            output_index = int(parent_root_attr[0].split("[")[1].split("]")[0])
            parent_root = parent_root_attr[0].split(".")[0]

            initialize_parent_inverse_matrix = (
                f"{parent_root}.initialize_output_inverse_matrix[{output_index}]"
            )

            cmds.connectAttr(
                initialize_parent_inverse_matrix,
                f"{SKEL}.initialize_parent_inverse_matrix[{index}]",
                force=True,
            )
            logger.info(
                f"Connect {initialize_parent_inverse_matrix} -> {SKEL}.initialize_parent_inverse_matrix[{index}]"
            )
    except Exception as e:
        logger.error(e, exc_info=True)


# endregion


# region Item
class ComponentItem(QtGui.QStandardItem):

    @property
    def component(self):
        return self._component

    @component.setter
    def component(self, c):
        self._component = c

    def __init__(self, *args, **kwargs):
        super(ComponentItem, self).__init__(*args, **kwargs)
        self._component = None


# endregion


# region Model
class RigModel(QtGui.QStandardItemModel):

    def __init__(self):
        super(RigModel, self).__init__()
        self.rig = None

    def serialize(self):
        self.rig = serialize()
        return self.rig

    def flags(self, index):
        default_flags = super(RigModel, self).flags(index)
        if index.isValid():
            return (
                default_flags
                | QtCore.Qt.ItemFlag.ItemIsDragEnabled
                | QtCore.Qt.ItemFlag.ItemIsDropEnabled
            )
        return default_flags | QtCore.Qt.ItemFlag.ItemIsDropEnabled

    def mimeData(self, indexes):
        mime_data = QtCore.QMimeData()

        data = []
        for index in indexes:
            identifier = self.itemFromIndex(index).component.identifier
            data.append(identifier)

        binary_data = pickle.dumps(data)
        mime_data.setData("application/x-custom-data", binary_data)
        return mime_data

    def canDropMimeData(self, data, action, row, column, parent):
        if not data.hasFormat("application/x-custom-data"):
            return False
        return True

    def dropMimeData(self, data, action, row, column, parent):
        if not data.hasFormat("application/x-custom-data"):
            return False
        binary_data = data.data("application/x-custom-data").data()
        identifiers = pickle.loads(binary_data)

        parent_item = self.itemFromIndex(parent)
        if parent_item:
            parent_component = parent_item.component

            try:
                cmds.undoInfo(openChunk=True)
                selected = cmds.ls(selection=True)
                for identifier in identifiers:
                    stack = [self.rig]
                    while stack:
                        component = stack.pop(0)
                        if component.identifier == identifier:
                            component.set_parent(parent_component)
                        stack.extend(component["children"])
                if selected:
                    cmds.select(selected)
            finally:
                cmds.undoInfo(closeChunk=True)

        self.populate_model()
        return True

    def supportedDropActions(self):
        return super(RigModel, self).supportedDropActions()

    def populate_model(self):
        self.layoutAboutToBeChanged.emit()
        self.clear()

        if self.rig is None:
            return

        # model setup
        stack = [(self.rig, self.invisibleRootItem())]
        while stack:
            component, parent_item = stack.pop(0)
            item = ComponentItem("{0} {1}{2}".format(*component.identifier))
            item.component = component
            if parent_item:
                parent_item.appendRow(item)
            stack.extend([(c, item) for c in component["children"]])

        self.layoutChanged.emit()


# endregion


# region Manager
class Manager(MayaQWidgetDockableMixin, QtWidgets.QDialog):

    # 싱글톤 패턴
    _instance = None

    # maya ui script
    ui_name = "domino_manager_ui"
    ui_script = """from maya import cmds
command = "from domino.dominomanager import Manager;ui=Manager.get_instance();ui.show(dockable=True)"
cmds.evalDeferred(command)"""
    control_name = f"{ui_name}WorkspaceControl"

    # callback
    callback_id = None

    def __init__(self, parent=None):
        if cmds.workspaceControl(self.control_name, query=True, exists=True):
            cmds.workspaceControl(self.control_name, edit=True, restore=True)
            cmds.workspaceControl(self.control_name, edit=True, close=True)
            cmds.deleteUI(self.control_name, control=True)

        super(Manager, self).__init__(parent=parent)
        self.setObjectName(self.ui_name)
        self.expand_state = []
        self.setWindowTitle("Domino Manager")

        layout = QtWidgets.QVBoxLayout(self)

        # region -    Manager / menubar
        self.menu_bar = QtWidgets.QMenuBar()
        layout.setMenuBar(self.menu_bar)

        self.command_menu = self.menu_bar.addMenu("Commands")
        self.refresh_ui_action = QtGui.QAction("Refresh")
        self.refresh_ui_action.triggered.connect(self.refresh)
        self.build_new_scene_action = QtGui.QAction("Build in new scene")
        self.build_new_scene_action.triggered.connect(partial(self.build, True))
        self.print_component_action = QtGui.QAction("Print component")
        self.print_component_action.triggered.connect(self.print_component)
        self.add_deformer_weights_sets_action = QtGui.QAction(
            f"Add {DEFORMER_WEIGHTS_SETS}"
        )
        self.add_blendshape_sets_action = QtGui.QAction(f"Add {BLENDSHAPE_SETS}")
        self.command_menu.addAction(self.refresh_ui_action)
        self.command_menu.addAction(self.build_new_scene_action)
        self.command_menu.addAction(self.print_component_action)
        self.command_menu.addAction(self.add_deformer_weights_sets_action)
        self.command_menu.addAction(self.add_blendshape_sets_action)

        self.template_menu = self.menu_bar.addMenu("Templates")
        # endregion

        # region -    Manager / domino path
        domino_layout = QtWidgets.QHBoxLayout()
        self.domino_path_line_edit = QtWidgets.QLineEdit()
        self.domino_path_line_edit.setReadOnly(True)
        self.domino_path_line_edit.setPlaceholderText("Domino Path")
        self.domino_path_load_btn = QtWidgets.QPushButton()
        self.domino_path_load_btn.setIcon(
            QtGui.QIcon((icon_dir / "arrow-big-down-lines.svg").as_posix())
        )
        self.domino_path_load_btn.setFixedWidth(24)
        self.domino_path_load_btn.setFixedHeight(18)
        self.domino_path_load_btn.clicked.connect(self.load)
        self.domino_path_load_btn.setToolTip("Load file")
        self.domino_path_version_up_btn = QtWidgets.QPushButton()
        self.domino_path_version_up_btn.setIcon(
            QtGui.QIcon((icon_dir / "arrow-big-up-lines.svg").as_posix())
        )
        self.domino_path_version_up_btn.setFixedWidth(24)
        self.domino_path_version_up_btn.setFixedHeight(18)
        self.domino_path_version_up_btn.clicked.connect(self.save)
        self.domino_path_version_up_btn.setToolTip("Version up file")
        domino_layout.addWidget(self.domino_path_line_edit)
        domino_layout.addWidget(self.domino_path_load_btn)
        domino_layout.addWidget(self.domino_path_version_up_btn)
        domino_layout.setSpacing(4)
        layout.addLayout(domino_layout)
        # endregion

        # region -    Manager / tree
        self.rig_tree_view = QtWidgets.QTreeView()
        self.rig_tree_view.header().hide()
        self.rig_tree_view.setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.rig_tree_view.setDragEnabled(True)
        self.rig_tree_view.setAcceptDrops(True)
        self.rig_tree_view.setDropIndicatorShown(True)
        self.rig_tree_view.setDragDropMode(
            QtWidgets.QTreeView.DragDropMode.InternalMove
        )
        self.rig_tree_view.setSelectionMode(
            QtWidgets.QTreeView.SelectionMode.ExtendedSelection
        )
        self.rig_tree_view.setEditTriggers(
            QtWidgets.QTreeView.EditTrigger.NoEditTriggers
        )
        self.rig_tree_model = RigModel()
        self.rig_tree_view.setStyleSheet(
            f"""
QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children {{
    image: url("{icon_dir.as_posix()}/chevron-down.svg");
}}
QTreeView::branch:open:has-children:!has-siblings, 
QTreeView::branch:open:has-children  {{
    image: url("{icon_dir.as_posix()}/chevron-right.svg");
}}
        """
        )
        self.rig_tree_model.populate_model()
        layout.addWidget(self.rig_tree_view)
        self.rig_tree_view.setModel(self.rig_tree_model)
        self.rig_tree_view.clicked.connect(self.set_settings)
        self.rig_tree_model.layoutAboutToBeChanged.connect(self.store_expand_state)
        self.rig_tree_model.layoutChanged.connect(self.restore_expand_state)
        # endregion

        # region -    Manager / tree context menu
        self.context_menu = QtWidgets.QMenu(self)

        self.expand_child_item_action = QtGui.QAction("Expand child Items")
        self.expand_child_item_action.triggered.connect(self.expand_items)
        self.clear_action = QtGui.QAction("Clear")
        self.clear_action.triggered.connect(self.clear_rig_view)
        self.settings_action = QtGui.QAction("Settings")
        self.settings_action.triggered.connect(self.open_settings)
        self.set_side_c_action = QtGui.QAction("Set Side C")
        self.set_side_c_action.triggered.connect(partial(self.set_side, 0))
        self.set_side_l_action = QtGui.QAction("Set Side L")
        self.set_side_l_action.triggered.connect(partial(self.set_side, 1))
        self.set_side_r_action = QtGui.QAction("Set Side R")
        self.set_side_r_action.triggered.connect(partial(self.set_side, 2))
        self.duplicate_action = QtGui.QAction("Duplicate")
        self.duplicate_action.triggered.connect(self.duplicate_component)
        self.reuse_mirror_action = QtGui.QAction("Mirror(reuse exists)")
        self.reuse_mirror_action.triggered.connect(partial(self.mirror_component, True))
        self.new_mirror_action = QtGui.QAction("Mirror(new)")
        self.new_mirror_action.triggered.connect(partial(self.mirror_component, False))
        self.remove_action = QtGui.QAction("Remove")
        self.remove_action.triggered.connect(self.remove_component)

        self.context_menu.addAction(self.expand_child_item_action)
        self.context_menu.addAction(self.clear_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.settings_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.set_side_c_action)
        self.context_menu.addAction(self.set_side_l_action)
        self.context_menu.addAction(self.set_side_r_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.duplicate_action)
        self.context_menu.addAction(self.reuse_mirror_action)
        self.context_menu.addAction(self.new_mirror_action)
        self.context_menu.addSeparator()
        self.context_menu.addAction(self.remove_action)
        self.rig_tree_view.customContextMenuRequested[QtCore.QPoint].connect(
            lambda Point: self.context_menu.exec(
                self.rig_tree_view.viewport().mapToGlobal(Point)
            )
        )
        # endregion

        # component list
        self.component_list_widget = QtWidgets.QListWidget()
        self.component_list_widget.setMaximumHeight(250)
        layout.addWidget(self.component_list_widget)
        self.component_list_widget.doubleClicked.connect(self.add_component)

    def refresh(self):
        self.rig_tree_model.serialize()
        self.rig_tree_model.populate_model()
        self.component_list_widget.clear()
        self.component_list_widget.addItems(COMPONENTLIST)

        if self.rig_tree_model.rig and cmds.objExists(
            self.rig_tree_model.rig.guide_root
        ):
            domino_path = cmds.getAttr(
                f"{self.rig_tree_model.rig.guide_root}.domino_path"
            )
            if domino_path:
                self.domino_path_line_edit.setText(domino_path)

        template_dir = os.getenv("DOMINO_RIG_TEMPLATE_DIR", None)
        # 메모리에서 제거되는거 방지.
        self.actions = []
        menu = [
            x
            for x in self.menu_bar.children()
            if isinstance(x, QtWidgets.QMenu) and x.title() == "Templates"
        ][0]
        if template_dir:
            for template in Path(template_dir).iterdir():
                action = QtGui.QAction(template.name.split(".")[0])
                action.triggered.connect(
                    partial(self.load_template, template.as_posix(), True)
                )
                menu.addAction(action)
                self.actions.append(action)

    def set_modeling_path(self):
        file_path = cmds.fileDialog2(
            caption="Set Modeling Path",
            startingDirectory=cmds.workspace(query=True, rootDirectory=True),
            fileFilter="Maya Scene (*.mb *.ma)",
            fileMode=1,
        )
        if file_path:
            cmds.setAttr(f"{RIG}.modeling_path", file_path[0], type="string")
            self.modeling_path_line_edit.setText(file_path[0])
        else:
            cmds.setAttr(f"{RIG}.modeling_path", "", type="string")
            self.modeling_path_line_edit.setText("")

    def expand_items(self):
        indexes = self.rig_tree_view.selectedIndexes()
        if not indexes:
            return
        for index in indexes:
            item = self.rig_tree_model.itemFromIndex(index)
            stack = [item]
            while stack:
                it = stack.pop(0)
                i = self.rig_tree_model.indexFromItem(it)
                self.rig_tree_view.expand(i)
                stack.extend([it.child(x) for x in range(it.rowCount())])

    def open_settings(self):
        item_index = self.rig_tree_view.selectedIndexes()
        if not item_index:
            return
        rig = self.rig_tree_model.rig
        rig.sync_from_scene()
        item = self.rig_tree_model.itemFromIndex(item_index[0])
        component = item.component

        try:
            cmds.undoInfo(openChunk=True)
            stack = [component]
            while stack:
                c = stack.pop(0)
                if not cmds.objExists(c.guide_root):
                    c.attach_guide()
                stack.extend(c["children"])

            cmds.select(component.guide_root)
            ui = Settings.get_instance()
            ui.refresh()
            ui.show(dockable=True)
        finally:
            cmds.undoInfo(closeChunk=True)

    def set_settings(self, index):
        if index:
            item = self.rig_tree_model.itemFromIndex(index)
            guide_root = item.component.guide_root
            if cmds.objExists(guide_root):
                cmds.select(guide_root)

    def clear_rig_view(self):
        self.rig_tree_model.rig = None
        self.rig_tree_model.clear()

    def store_expand_state(self):
        self.expand_state.clear()

        # item expand 상태 저장
        root = self.rig_tree_model.invisibleRootItem()
        if root.rowCount():
            stack = [(root.child(0), "")]
            while stack:
                item, path = stack.pop(0)
                index = self.rig_tree_model.indexFromItem(item)
                new_path = f"{path}/{item.text()}"
                if self.rig_tree_view.isExpanded(index):
                    self.expand_state.append(new_path)

                stack.extend(
                    [(item.child(i), new_path) for i in range(item.rowCount())]
                )

    def restore_expand_state(self):
        # item expand 상태 복원.
        root = self.rig_tree_model.invisibleRootItem()
        if root.rowCount():
            stack = [(root.child(0), "")]
            while stack:
                item, path = stack.pop(0)
                index = self.rig_tree_model.indexFromItem(item)
                new_path = f"{path}/{item.text()}"
                if new_path in self.expand_state:
                    self.rig_tree_view.expand(index)

                stack.extend(
                    [(item.child(i), new_path) for i in range(item.rowCount())]
                )

    def add_component(self):
        try:
            cmds.undoInfo(openChunk=True)

            selected = cmds.ls(selection=True)

            # region import component
            items = self.component_list_widget.selectedItems()
            if not items:
                return
            module_name = items[0].text()
            try:
                module = importlib.import_module(f"domino.component.{module_name}")
            except ModuleNotFoundError:
                return
            component = module.Rig()
            if hasattr(component, "input_data"):
                result = component.input_data()
                if not result:
                    return
            # endregion

            # region 이미 존재하는 리그가 없다면 assembly 생성.
            rig = self.rig_tree_model.rig
            if rig is None:
                assembly_module = importlib.import_module("domino.component.assembly")
                rig = assembly_module.Rig()
                rig.populate()
                rig.rig()
                rig.attach_guide()
                self.rig_tree_model.rig = rig
                output_joints = []
                for data in rig["output_joint"]:
                    name, side, index = rig.identifier
                    output_joints.append(
                        Name.create(
                            convention=Name.joint_name_convention,
                            name=name,
                            side=side,
                            index=index,
                            description=data["description"],
                            extension=Name.joint_extension,
                        )
                    )
                # setup output joint
                rig.setup_skel(output_joints)
            rig.sync_from_scene()
            # endregion

            # region setup component
            parent = rig
            parent_item_index = self.rig_tree_view.selectedIndexes()
            if parent_item_index:
                item = self.rig_tree_model.itemFromIndex(parent_item_index[0])
                parent = item.component

            if component["component"]["value"] != "uicontainer01":
                index = rig.get_valid_component_index(
                    component["name"]["value"], component["side"]["value"]
                )
                component["index"]["value"] = index
            component.set_parent(parent)
            component.populate()
            # endregion

            # create rig
            component.rig()
            # attach guide
            component.attach_guide()

            # region setup skel
            output_joints = []
            name, side, index = component.identifier
            for data in component["output_joint"]:
                output_joints.append(
                    Name.create(
                        convention=Name.joint_name_convention,
                        name=name,
                        side=side,
                        index=index,
                        description=data["description"],
                        extension=Name.joint_extension,
                    )
                )
            component.setup_skel(output_joints)
            # endregion

            # refresh model
            self.refresh()

            cmds.select(selected) if selected else cmds.select(clear=True)
        finally:
            cmds.undoInfo(closeChunk=True)

    def duplicate_component(self):
        indexes = self.rig_tree_view.selectedIndexes()
        if not indexes:
            return
        try:
            cmds.undoInfo(openChunk=True)
            rig = self.rig_tree_model.rig
            rig.sync_from_scene()
            for index in indexes:
                item = self.rig_tree_model.itemFromIndex(index)
                item.component.duplicate_component(True)
            self.refresh()
        finally:
            cmds.undoInfo(closeChunk=True)

    def mirror_component(self, reuse_exists=False):
        indexes = self.rig_tree_view.selectedIndexes()
        if not indexes:
            return
        try:
            cmds.undoInfo(openChunk=True)
            rig = self.rig_tree_model.rig
            rig.sync_from_scene()
            for index in indexes:
                item = self.rig_tree_model.itemFromIndex(index)
                item.component.mirror_component(reuse_exists, True)
            self.refresh()
        finally:
            cmds.undoInfo(closeChunk=True)

    def remove_component(self):
        indexes = self.rig_tree_view.selectedIndexes()
        if not indexes:
            return
        try:
            cmds.undoInfo(openChunk=True)
            rig = self.rig_tree_model.rig
            rig.sync_from_scene()
            for index in indexes:
                item = self.rig_tree_model.itemFromIndex(index)
                item.component.remove_component()
            self.refresh()
        finally:
            cmds.undoInfo(closeChunk=True)

    def set_side(self, side):
        indexes = self.rig_tree_view.selectedIndexes()
        if not indexes:
            return
        try:
            cmds.undoInfo(openChunk=True)
            rig = self.rig_tree_model.rig
            rig.sync_from_scene()
            for index in indexes:
                item = self.rig_tree_model.itemFromIndex(index)
                component = item.component
                if component["component"]["value"] in ["assembly", "uicontainer01"]:
                    continue
                index = rig.get_valid_component_index(component["name"]["value"], side)
                component.rename_component(
                    component["name"]["value"], side, index, True
                )
            self.refresh()
        finally:
            cmds.undoInfo(closeChunk=True)

    # region -    Manager / Import, Export
    def save(self):
        self.rig_tree_model.serialize()
        data = self.rig_tree_model.rig
        if not data:
            return

        # region get file path
        def ensure_version_in_file_path(file_path):
            path = Path(file_path)
            directory = path.parent
            name, ext = path.name.split(".")
            return (directory / ".".join([name + "_v001", ext])).as_posix()

        def increase_version_in_file_path(file_path, version):
            fill_count = len(version) - 1
            new_version = int(version[1:]) + 1
            return file_path.replace(version, f"v{str(new_version).zfill(fill_count)}")

        file_path = self.domino_path_line_edit.text()
        modifiers = QtWidgets.QApplication.keyboardModifiers()

        pattern = r"v\d+"
        if file_path and modifiers == QtCore.Qt.KeyboardModifier.ControlModifier:
            match = re.search(pattern, file_path)
            if not match:
                file_path = ensure_version_in_file_path(file_path)
            elif match:
                version = match.group()
                file_path = increase_version_in_file_path(file_path, version)
        else:
            file_path = cmds.fileDialog2(
                caption="Save Domino Rig",
                startingDirectory=cmds.workspace(query=True, rootDirectory=True),
                fileFilter="Domino Rig (*.domino)",
                fileMode=0,
            )
            if not file_path:
                return
            file_path = file_path[0]
            match = re.search(pattern, file_path)
            if not match:
                file_path = ensure_version_in_file_path(file_path)
        # endregion

        save(file_path, data)
        if cmds.objExists(data.guide_root):
            cmds.setAttr(f"{data.guide_root}.domino_path", file_path, type="string")
        self.domino_path_line_edit.setText(file_path)
        ui = Settings.get_instance()
        ui.refresh()

    def load(self):
        mel.eval(
            """
global proc DominoLoadOptionsUISetup(string $parent)
{
    setParent $parent;
    $parent = `scrollLayout -childResizable true`;

    columnLayout -adj true;

    string $gDominoRadioCollection = `radioCollection`;

    radioButton -l "Rig" breakpoint_rig;
    radioButton -l "Pre Scripts" breakpoint_pre_scripts;
    radioButton -l "BlendShape" breakpoint_blendshape;
    radioButton -l "SpaceManager" breakpoint_spacemanager;
    radioButton -l "PSDManager" breakpoint_psdmanager;
    radioButton -l "SDKManager" breakpoint_sdkmanager;
    radioButton -l "DynamicManager" breakpoint_dynamicmanager;
    radioButton -l "DeformerWeights" breakpoint_deformerweights;
    radioButton -l "DeformerOrder" breakpoint_deformerorder;
    radioButton -l "Post Scripts" -select breakpoint_post_scripts;

    // 컬렉션 이름을 optionVar에 저장
    optionVar -sv "dominoBreakPointCollection" $gDominoRadioCollection;
}

global proc DominoLoadOptionsUICommit(string $parent)
{
    // 저장해둔 radioCollection 이름 불러오기
    string $col = `optionVar -q "dominoBreakPointCollection"`;
    string $sel = `radioCollection -q -select $col`;

    // 선택된 버튼 이름도 optionVar 로 저장
    optionVar -sv "dominoBreakPoint" $sel;
}
"""
        )

        file_path = cmds.fileDialog2(
            caption="Load Domino Rig",
            startingDirectory=cmds.workspace(query=True, rootDirectory=True),
            fileFilter="Domino Rig (*.domino)",
            fileMode=1,
            optionsUICreate="DominoLoadOptionsUISetup",
            optionsUICommit="DominoLoadOptionsUICommit",
            optionsUITitle="Debug Point Option",
        )

        if file_path:
            break_point = cmds.optionVar(q="dominoBreakPoint")
            if break_point == "breakpoint_rig":
                break_point = BREAK_POINT_RIG
            elif break_point == "breakpoint_pre_scripts":
                break_point = BREAK_POINT_PRECUSTOMSCRIPTS
            elif break_point == "breakpoint_spacemanager":
                break_point = BREAK_POINT_SPACEMANAGER
            elif break_point == "breakpoint_blendshape":
                break_point = BREAK_POINT_BLENDSHAPE
            elif break_point == "breakpoint_psdmanager":
                break_point = BREAK_POINT_PSDMANAGER
            elif break_point == "breakpoint_sdkmanager":
                break_point = BREAK_POINT_SDKMANAGER
            elif break_point == "breakpoint_dynamicmanager":
                break_point = BREAK_POINT_DYNAMICMANAGER
            elif break_point == "breakpoint_deformerweights":
                break_point = BREAK_POINT_DEFORMERWEIGHTS
            elif break_point == "breakpoint_deformerorder":
                break_point = BREAK_POINT_DEFORMERORDER
            elif break_point == "breakpoint_post_scripts":
                break_point = BREAK_POINT_POSTCUSTOMSCRIPTS
            if cmds.objExists(RIG):
                cmds.delete(RIG)
            if cmds.objExists(GUIDE):
                cmds.delete(GUIDE)
            if cmds.objExists(RIG_SETS):
                cmds.delete((cmds.sets(RIG_SETS, query=True) or []) + [RIG_SETS])
            tags = cmds.ls(type="controller")
            if tags:
                cmds.delete(tags)

            load(file_path[0], create=True, break_point=break_point)
            self.refresh()
            self.domino_path_line_edit.setText(file_path[0])

    def load_template(self, file_path, create):
        """file_line_edit 에 path 를 기록하지 않고 load 합니다."""
        if cmds.objExists(RIG):
            cmds.delete(GUIDE)
        if cmds.objExists(GUIDE):
            cmds.delete(GUIDE)
        if cmds.objExists(RIG_SETS):
            cmds.delete((cmds.sets(RIG_SETS, query=True) or []) + [RIG_SETS])
        tags = cmds.ls(type="controller")
        if tags:
            cmds.delete(tags)
        load(file_path, create)
        self.refresh()

    # endregion
    def build(self, new_scene=False):
        rig = self.rig_tree_model.rig
        if rig:
            if new_scene:
                cmds.file(newFile=True, force=True)
                build({}, rig)
        orig_path = self.domino_path_line_edit.text()
        self.refresh()
        self.domino_path_line_edit.setText(orig_path)

    def showEvent(self, e):
        cmds.workspaceControl(self.control_name, edit=True, uiScript=self.ui_script)
        self.refresh()
        if self.callback_id is None:
            self.callback_id = om.MDagMessage.addParentAddedCallback(
                cb_setup_output_joint
            )
            logger.info(f"Add output joint Dag callback id: {self.callback_id}")
        super(Manager, self).showEvent(e)

    def hideEvent(self, e):
        if self.callback_id:
            logger.info(f"Remove output joint Dag callback id: {self.callback_id}")
            om.MMessage.removeCallback(self.callback_id)
            self.callback_id = None
        super(Manager, self).hideEvent(e)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def print_component(self):
        indexes = self.rig_tree_view.selectedIndexes()
        if not indexes:
            return
        item = self.rig_tree_model.itemFromIndex(indexes[0])
        for k, v in item.component.items():
            if k == "children":
                continue
            logger.info(k)
            logger.info(pprint.pformat(v))


# endregion
