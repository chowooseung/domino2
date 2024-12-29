# Qt
from PySide6 import QtWidgets, QtCore, QtGui

# maya
from maya import cmds, mel
from maya.api import OpenMaya as om  # type: ignore
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin  # type: ignore

# domino
from domino.component import (
    __all__ as component_list,
    build,
    serialize,
    T,
    save,
    load,
    Name,
)
from domino.core.utils import logger

# built-ins
from functools import partial
from pathlib import Path
import importlib
import pickle
import shutil
import os
import re

icon_dir = Path(__file__).parent.parent.parent / "icons"
component_list.remove("assembly")


def cb_setup_output_joint(child, parent, client_data) -> None:
    if not cmds.objExists(child.fullPathName() + ".is_domino_skel"):
        return

    try:
        output_joint = child.fullPathName()
        parent = parent.fullPathName()

        output_attr = cmds.connectionInfo(
            output_joint + ".output", sourceFromDestination=True
        )
        output = output_attr.split(".")[0]

        skel_graph_attr = [
            x
            for x in cmds.connectionInfo(
                output + ".worldMatrix[0]", destinationFromSource=True
            )
            if cmds.nodeType(x) == "bifrostGraphShape"
        ]
        if not skel_graph_attr:
            return
        index = int(skel_graph_attr[0].split("[")[1].split("]")[0])
        if parent.split("|")[-1] == "skel":
            cmds.connectAttr(
                "skel.worldMatrix[0]",
                f"skel_bifGraph.initialize_parent_output_matrix[{index}]",
                force=True,
            )
            cmds.connectAttr(
                "skel.worldMatrix[0]",
                f"skel_bifGraph.parent_output_matrix[{index}]",
                force=True,
            )
            logger.info(
                f"Connect skel.worldMatrix[0] -> skel_bifGraph.initialize_parent_output_matrix[{index}]"
            )
            logger.info(
                f"Connect skel.worldMatrix[0] -> skel_bifGraph.parent_output_matrix[{index}]"
            )
            return
        if cmds.objExists(parent + ".is_domino_skel"):
            parent_output_attr = cmds.connectionInfo(
                parent + ".output", sourceFromDestination=True
            )
            parent_output = parent_output_attr.split(".")[0]
            parent_root_attr = [
                x
                for x in cmds.connectionInfo(
                    parent_output + ".message", destinationFromSource=True
                )
                if cmds.nodeType(x) == "transform" and ".output" in x
            ]
            if not parent_root_attr:
                return
            output_index = int(parent_root_attr[0].split("[")[1].split("]")[0])
            parent_root = parent_root_attr[0].split(".")[0]

            parent_output_matrix = parent_output + ".worldMatrix[0]"
            initialize_parent_output_matrix = (
                parent_root + f".initialize_output_matrix[{output_index}]"
            )

            cmds.connectAttr(
                parent_output_matrix,
                f"skel_bifGraph.parent_output_matrix[{index}]",
                force=True,
            )
            cmds.connectAttr(
                initialize_parent_output_matrix,
                f"skel_bifGraph.initialize_parent_output_matrix[{index}]",
                force=True,
            )
            logger.info(
                f"Connect {initialize_parent_output_matrix} -> skel_bifGraph.initialize_parent_output_matrix[{index}]"
            )
            logger.info(
                f"Connect {parent_output_matrix} -> skel_bifGraph.parent_output_matrix[{index}]"
            )
    except Exception as e:
        logger.error(e, exc_info=True)


class ComponentItem(QtGui.QStandardItem):

    @property
    def component(self) -> T | None:
        return self._component

    @component.setter
    def component(self, c: T) -> None:
        self._component = c

    def __init__(self, *args, **kwargs):
        super(ComponentItem, self).__init__(*args, **kwargs)
        self._component = None


class RigModel(QtGui.QStandardItemModel):

    def __init__(self):
        super(RigModel, self).__init__()
        self.rig = None

    def serialize(self) -> T | None:
        self.rig = serialize()
        return self.rig

    def flags(self, index: QtCore.QModelIndex):
        default_flags = super(RigModel, self).flags(index)
        if index.isValid():
            return (
                default_flags
                | QtCore.Qt.ItemFlag.ItemIsDragEnabled
                | QtCore.Qt.ItemFlag.ItemIsDropEnabled
            )
        return default_flags | QtCore.Qt.ItemFlag.ItemIsDropEnabled

    def mimeData(self, indexes: list) -> QtCore.QMimeData:
        mime_data = QtCore.QMimeData()

        data = []
        for index in indexes:
            identifier = self.itemFromIndex(index).component.identifier
            data.append(identifier)

        binary_data = pickle.dumps(data)
        mime_data.setData("application/x-custom-data", binary_data)
        return mime_data

    def canDropMimeData(self, data, action, row, column, parent) -> bool:
        if not data.hasFormat("application/x-custom-data"):
            return False
        return True

    def dropMimeData(self, data, action, row, column, parent) -> bool:
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

    def supportedDropActions(self) -> QtCore.Qt.DropAction:
        return super(RigModel, self).supportedDropActions()

    def populate_model(self) -> None:
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

            tooltip_str = []

            # empty parent controller data
            for data in component["controller"]:
                if (
                    component.get_parent() is not None
                    and not data["parent_controllers"]
                ):
                    tooltip_str.append(
                        f"`description {data['description']}` 의 parent controller 가 설정되지 않았습니다."
                    )

            if tooltip_str:
                item.setForeground(QtGui.QBrush(QtGui.QColor("yellow")))
                item.setToolTip("\n".join(tooltip_str))
            stack.extend([(c, item) for c in component["children"]])

        self.layoutChanged.emit()


class Manager(MayaQWidgetDockableMixin, QtWidgets.QDialog):

    # 싱글톤 패턴
    _instance = None

    # maya ui script
    ui_name = "domino_manager_ui"
    ui_script = """from maya import cmds
command = "from domino.dominomanager import Manager;ui=Manager.get_instance();ui.show(dockable=True)"
cmds.evalDeferred(command)"""
    control_name = ui_name + "WorkspaceControl"

    # callback
    callback_id = None

    def __init__(self, parent=None) -> None:
        if cmds.workspaceControl(self.control_name, query=True, exists=True):
            cmds.workspaceControl(self.control_name, edit=True, restore=True)
            cmds.workspaceControl(self.control_name, edit=True, close=True)
            cmds.deleteUI(self.control_name, control=True)

        super(Manager, self).__init__(parent=parent)
        self.expand_state = []
        self.setObjectName(self.ui_name)
        self.setWindowTitle("Domino Manager")

        layout = QtWidgets.QVBoxLayout(self)

        # menubar
        self.menu_bar = QtWidgets.QMenuBar()
        layout.setMenuBar(self.menu_bar)

        self.command_menu = self.menu_bar.addMenu("Commands")
        self.refresh_ui_action = QtGui.QAction("Refresh")
        self.refresh_ui_action.triggered.connect(self.refresh)
        self.build_new_scene_action = QtGui.QAction("Build in new scene")
        self.build_new_scene_action.triggered.connect(partial(self.build, True))
        self.print_component_action = QtGui.QAction("Print component")
        self.print_component_action.triggered.connect(self.print_component)
        self.command_menu.addAction(self.refresh_ui_action)
        self.command_menu.addAction(self.build_new_scene_action)
        self.command_menu.addAction(self.print_component_action)

        self.template_menu = self.menu_bar.addMenu("Templates")

        # modeling path
        modeling_path_layout = QtWidgets.QHBoxLayout()
        self.modeling_path_line_edit = QtWidgets.QLineEdit()
        self.modeling_path_line_edit.setReadOnly(True)
        self.modeling_path_line_edit.setPlaceholderText("Modeling Path")
        self.modeling_path_load_btn = QtWidgets.QPushButton()
        self.modeling_path_load_btn.setFixedWidth(24)
        self.modeling_path_load_btn.setFixedHeight(18)
        self.modeling_path_load_btn.clicked.connect(self.set_modeling_path)
        modeling_path_layout.addWidget(self.modeling_path_line_edit)
        modeling_path_layout.addWidget(self.modeling_path_load_btn)
        modeling_path_layout.setSpacing(4)
        layout.addLayout(modeling_path_layout)

        # file line
        file_layout = QtWidgets.QHBoxLayout()
        self.file_path_line_edit = QtWidgets.QLineEdit()
        self.file_path_line_edit.setReadOnly(True)
        self.file_path_line_edit.setPlaceholderText("Domino Path")
        self.file_path_load_btn = QtWidgets.QPushButton()
        self.file_path_load_btn.setIcon(
            QtGui.QIcon((icon_dir / "arrow-big-down-lines.svg").as_posix())
        )
        self.file_path_load_btn.setFixedWidth(24)
        self.file_path_load_btn.setFixedHeight(18)
        self.file_path_load_btn.clicked.connect(self.load)
        self.file_path_load_btn.setToolTip("Load file")
        self.file_path_version_up_btn = QtWidgets.QPushButton()
        self.file_path_version_up_btn.setIcon(
            QtGui.QIcon((icon_dir / "arrow-big-up-lines.svg").as_posix())
        )
        self.file_path_version_up_btn.setFixedWidth(24)
        self.file_path_version_up_btn.setFixedHeight(18)
        self.file_path_version_up_btn.clicked.connect(self.save)
        self.file_path_version_up_btn.setToolTip("Version up file")
        file_layout.addWidget(self.file_path_line_edit)
        file_layout.addWidget(self.file_path_load_btn)
        file_layout.addWidget(self.file_path_version_up_btn)
        file_layout.setSpacing(4)
        layout.addLayout(file_layout)

        # tree
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

        # tree context menu
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

        # component list
        self.component_list_widget = QtWidgets.QListWidget()
        self.component_list_widget.setMaximumHeight(250)
        layout.addWidget(self.component_list_widget)

        self.rig_tree_model.layoutAboutToBeChanged.connect(self.store_expand_state)
        self.rig_tree_model.layoutChanged.connect(self.restore_expand_state)
        self.component_list_widget.doubleClicked.connect(self.add_component)

    def refresh(self) -> None:
        self.modeling_path_line_edit.clear()
        self.file_path_line_edit.clear()
        self.rig_tree_model.serialize()
        self.rig_tree_model.populate_model()
        self.component_list_widget.clear()
        self.component_list_widget.addItems(component_list)

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
            self.modeling_path_line_edit.setText(file_path[0])

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

    def open_settings(self) -> None:
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
            cmds.AttributeEditor()
            mel.eval('setLocalView "Rigging" "" 1;')
        finally:
            cmds.undoInfo(closeChunk=True)

    def set_settings(self, index):
        if index:
            item = self.rig_tree_model.itemFromIndex(index)
            guide_root = item.component.guide_root
            if cmds.objExists(guide_root):
                cmds.select(guide_root)
                cmds.AttributeEditor()
                mel.eval('setLocalView "Rigging" "" 1;')

    def clear_rig_view(self) -> None:
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

            # import component
            items = self.component_list_widget.selectedItems()
            if not items:
                return
            module_name = items[0].text()
            try:
                module = importlib.import_module("domino.component." + module_name)
            except ModuleNotFoundError:
                return
            component = module.Rig()

            # 이미 존재하는 리그가 없다면 assembly 생성.
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
                # # setup output joint
                rig.setup_skel_graph(output_joints)
            rig.sync_from_scene()

            # get parent component
            parent = rig
            parent_item_index = self.rig_tree_view.selectedIndexes()
            if parent_item_index:
                item = self.rig_tree_model.itemFromIndex(parent_item_index[0])
                parent = item.component

            # set component index
            index = rig.get_valid_component_index(
                component["name"]["value"], component["side"]["value"]
            )
            component["index"]["value"] = index
            component.set_parent(parent)
            component.populate()
            # create rig
            component.rig()
            # attach guide
            component.attach_guide()
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
            # # setup output joint
            component.setup_skel_graph(output_joints)

            # refresh model
            self.rig_tree_model.populate_model()

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
            self.rig_tree_model.populate_model()
        finally:
            cmds.undoInfo(closeChunk=True)

    def mirror_component(self, reuse_exists: bool = False) -> None:
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
            self.rig_tree_model.populate_model()
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
            self.rig_tree_model.populate_model()
        finally:
            cmds.undoInfo(closeChunk=True)

    def set_side(self, side: str) -> None:
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
                index = rig.get_valid_component_index(component["name"]["value"], side)
                component.rename_component(
                    component["name"]["value"], side, index, True
                )
            self.rig_tree_model.populate_model()
        finally:
            cmds.undoInfo(closeChunk=True)

    def save(self) -> None:
        def ensure_version_in_file_path(file_path: str) -> str:
            path = Path(file_path)
            directory = path.parent
            name, ext = path.name.split(".")
            return (directory / ".".join([name + "_v001", ext])).as_posix()

        def increase_version_in_file_path(file_path: str, version: str) -> str:
            fill_count = len(version) - 1
            new_version = int(version[1:]) + 1
            return file_path.replace(version, "v" + str(new_version).zfill(fill_count))

        def copy_file(source_path, destination_path):
            try:
                shutil.copy2(source_path, destination_path)
                logger.info(f"File copied from {source_path} to {destination_path}")
            except FileNotFoundError:
                logger.info(f"Source file not found: {source_path}")
            except PermissionError:
                logger.info(f"Permission denied to copy file to: {destination_path}")
            except Exception as e:
                logger.info(f"An error occurred: {e}")

        data = self.rig_tree_model.rig
        if not data:
            return
        data.sync_from_scene()
        file_path = self.file_path_line_edit.text()
        pattern = r"v\d+"
        if file_path:
            match = re.search(pattern, file_path)
            if not match:
                file_path = ensure_version_in_file_path(file_path)
            elif match:
                version = match.group()
                file_path = increase_version_in_file_path(file_path, version)
        elif not file_path:
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

        # scripts version up
        path = Path(file_path)
        scripts_dir = path.parent / (path.name.split(".")[0] + ".metadata")
        if not scripts_dir.exists():
            scripts_dir.mkdir()
        replace_scripts = []
        for script_path in data["pre_custom_scripts"]["value"]:
            if not script_path:
                continue
            disable = False
            if script_path.startswith("*"):
                script_path = script_path[1:]
                disable = True
            source_file = Path(script_path)
            name = source_file.name
            destination_file = scripts_dir / name
            copy_file(source_file.as_posix(), destination_file.as_posix())
            replace_script = "*" if disable else ""
            replace_script += destination_file.as_posix()
            replace_scripts.append(replace_script)
        data["pre_custom_scripts"]["value"] = replace_scripts
        replace_scripts = []
        for script_path in data["post_custom_scripts"]["value"]:
            if not script_path:
                continue
            disable = False
            if script_path.startswith("*"):
                script_path = script_path[1:]
                disable = True
            source_file = Path(script_path)
            name = source_file.name
            destination_file = scripts_dir / name
            copy_file(source_file.as_posix(), destination_file.as_posix())
            replace_script = "*" if disable else ""
            replace_script += destination_file.as_posix()
            replace_scripts.append(replace_script)
        data["post_custom_scripts"]["value"] = replace_scripts

        root = data.rig_root
        if cmds.objExists(data.guide_root):
            root = data.guide_root

        for i, path in enumerate(data["pre_custom_scripts"]["value"]):
            cmds.setAttr(root + f".pre_custom_scripts[{i}]", path, type="string")
        for i, path in enumerate(data["post_custom_scripts"]["value"]):
            cmds.setAttr(root + f".post_custom_scripts[{i}]", path, type="string")

        selected = cmds.ls(selection=True)
        if selected and cmds.objExists(selected[0] + ".is_domino_guide_root"):
            mel.eval('setLocalView "Rigging" "" 1;')

        save(file_path, data)
        self.file_path_line_edit.setText(file_path)

    def load(self):
        file_path = cmds.fileDialog2(
            caption="Load Domino Rig",
            startingDirectory=cmds.workspace(query=True, rootDirectory=True),
            fileFilter="Domino Rig (*.domino)",
            fileMode=1,
        )
        if file_path:
            if cmds.objExists("rig"):
                cmds.delete("rig")
            if cmds.objExists("guide"):
                cmds.delete("guide")

            rig = load(file_path[0], create=False)
            self.rig_tree_model.rig = rig
            self.rig_tree_model.populate_model()
            self.file_path_line_edit.setText(file_path[0])
            if "modeling" in rig:
                self.modeling_path_line_edit.setText(rig["modeling"])
            else:
                self.modeling_path_line_edit.clear()
            build({}, rig)

    def load_template(self, file_path: str, create: bool) -> None:
        """file_line_edit 에 path 를 기록하지 않고 load 합니다."""
        self.modeling_path_line_edit.clear()
        rig = load(file_path, create)
        self.rig_tree_model.rig = rig
        self.rig_tree_model.populate_model()

    def build(self, new_scene: bool = False) -> None:
        if new_scene:
            cmds.file(newFile=True, force=True)
        rig = self.rig_tree_model.rig
        modeling_file = self.modeling_path_line_edit.text()
        if modeling_file:
            rig["modeling"] = modeling_file
        build({}, rig)

    def showEvent(self, e) -> None:
        cmds.workspaceControl(self.control_name, edit=True, uiScript=self.ui_script)
        self.refresh()
        if self.callback_id is None:
            self.callback_id = om.MDagMessage.addParentAddedCallback(
                cb_setup_output_joint
            )
            logger.info(f"Add output joint Dag callback id: {self.callback_id}")
        super(Manager, self).showEvent(e)

    def hideEvent(self, e) -> None:
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
            logger.info("\t", v)
