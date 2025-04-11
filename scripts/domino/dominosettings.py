# Qt
from PySide6 import QtWidgets, QtCore, QtGui
from shiboken6 import wrapInstance

# maya
from maya import cmds
from maya.api import OpenMaya as om
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

# built-ins
from functools import partial
from pathlib import Path
import sys
import os
import subprocess
import importlib.util

# domino
from domino.core.utils import logger
from domino.component import SKEL, ORIGINMATRIX

# icon
icon_dir = Path(__file__).parent.parent.parent / "icons"


def get_manager_ui():
    """Manager ui를 refresh 하거나 manager 에서 rig 데이터를 가져오기 위해 사용됨.
    dominomanager 모듈을 직접 import 할수없음"""
    from maya import OpenMayaUI as omui  # type: ignore

    def get_maya_main_window():
        main_window_ptr = omui.MQtUtil.mainWindow()
        return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

    def find_docked_widget(object_name: str):
        main_window = get_maya_main_window()
        return main_window.findChild(QtWidgets.QWidget, object_name)

    return find_docked_widget("domino_manager_ui")


def get_component(rig, name, side, index):
    stack = [rig]
    destination_component = None
    while stack:
        component = stack.pop()
        if component.identifier == (name, side, index):
            destination_component = component
            break
        stack.extend(component["children"])
    return destination_component


# region UIGenerator
class UIGenerator:

    # region -    UIGenerator / common settings
    @classmethod
    def add_common_component_settings(
        cls, parent: QtWidgets.QWidget, root: str
    ) -> None:

        def rename_name():
            new_name = name_line_edit.text()
            if old_name == new_name:
                logger.warning(f"이전과 같습니다.")
                Settings.get_instance().refresh()
                return
            if not new_name:
                logger.warning(f"빈 문자열을 이름으로 사용 할 수 없습니다.")
                Settings.get_instance().refresh()
                return
            if not new_name[0].isalpha():
                logger.warning(f"문자열의 시작은 알파벳 이어야합니다.")
                Settings.get_instance().refresh()
                return
            if not (new_name[-1].isalnum() or new_name[-1].isalpha()):
                logger.warning(f"문자열의 끝은 숫자 혹은 알파벳 이어야합니다.")
                Settings.get_instance().refresh()
                return

            manager_ui = get_manager_ui()
            rig = manager_ui.rig_tree_model.rig

            current_component = get_component(rig, old_name, old_side_str, old_index)
            destination_component = get_component(
                rig, new_name, old_side_str, old_index
            )

            if destination_component:
                logger.warning(
                    f"{new_name}_{old_side_str}{old_index} Component 는 이미 존재합니다."
                )
                Settings.get_instance().refresh()
                return

            try:
                cmds.undoInfo(openChunk=True)
                current_component.rename_component(new_name, old_side, old_index, True)
            finally:
                cmds.undoInfo(closeChunk=True)
            logger.info(
                f"Rename Component {old_name}_{old_side_str}{old_index} -> {new_name}_{old_side_str}{old_index}"
            )
            # manager ui refresh
            manager_ui.rig_tree_model.populate_model()
            # settings ui refresh
            Settings.get_instance().refresh()

        def rename_side(new_side):
            new_side_str = ["C", "L", "R"][new_side]
            if old_side == new_side:
                logger.warning(f"이전과 같습니다.")
                Settings.get_instance().refresh()
                return
            manager_ui = get_manager_ui()
            rig = manager_ui.rig_tree_model.rig

            current_component = get_component(rig, old_name, old_side_str, old_index)
            destination_component = get_component(
                rig, old_name, new_side_str, old_index
            )

            if destination_component:
                logger.warning(
                    f"{old_name}_{new_side_str}{old_index} Component 는 이미 존재합니다."
                )
                Settings.get_instance().refresh()
                return

            try:
                cmds.undoInfo(openChunk=True)
                current_component.rename_component(old_name, new_side, old_index, True)
            finally:
                cmds.undoInfo(closeChunk=True)
            logger.info(
                f"Rename Component {old_name}_{old_side_str}{old_index} -> {old_name}_{new_side_str}{old_index}"
            )
            # manager ui refresh
            manager_ui.rig_tree_model.populate_model()
            # settings ui refresh
            Settings.get_instance().refresh()

        def rename_index():
            index = index_spin_box.value()
            manager_ui = get_manager_ui()
            rig = manager_ui.rig_tree_model.rig

            current_component = get_component(rig, old_name, old_side_str, old_index)
            destination_component = get_component(rig, old_name, old_side_str, index)

            if destination_component:
                logger.warning(
                    f"{old_name}_{old_side_str}{index} Component 는 이미 존재합니다."
                )
                Settings.get_instance().refresh()
                return

            try:
                cmds.undoInfo(openChunk=True)
                current_component.rename_component(old_name, old_side, index, True)
            finally:
                cmds.undoInfo(closeChunk=True)
            logger.info(
                f"Rename Component {old_name}_{old_side_str}{old_index} -> {old_name}_{old_side_str}{index}"
            )
            # manager ui refresh
            manager_ui.rig_tree_model.populate_model()
            # settings ui refresh
            Settings.get_instance().refresh()

        def set_parent_output_index():
            manager_ui = get_manager_ui()
            rig = manager_ui.rig_tree_model.rig

            current_component = get_component(rig, old_name, old_side_str, old_index)

            parent_component = current_component.get_parent()
            parent_rig_root = parent_component.rig_root

            outputs = cmds.listConnections(
                f"{parent_rig_root}.output", source=True, destination=False
            )
            if not outputs:
                Settings.get_instance().refresh()
                return

            output_index = parent_output_index_spin_box.value()
            if output_index >= len(outputs):
                output_index = -1
            old_parent = cmds.listRelatives(current_component.rig_root, parent=True)[0]
            if old_parent == outputs[output_index]:
                Settings.get_instance().refresh()
                return

            try:
                cmds.undoInfo(openChunk=True)
                cmds.parent(current_component.rig_root, outputs[output_index])
                cmds.setAttr(
                    f"{current_component.guide_root}.parent_output_index", output_index
                )
                cmds.select(current_component.guide_root)
            finally:
                cmds.undoInfo(closeChunk=True)
            logger.info(f"Reparent rig root {old_parent} -> {outputs[output_index]}")
            Settings.get_instance().refresh()

        def create_output_joint(state):
            manager_ui = get_manager_ui()
            rig = manager_ui.rig_tree_model.rig

            current_component = get_component(rig, old_name, old_side_str, old_index)
            output_joints = (
                cmds.listConnections(
                    f"{current_component.rig_root}.output_joint", source=True
                )
                or []
            )
            children = []
            for j in output_joints:
                c = cmds.listRelatives(j, children=True) or []
                children.extend(list(set(c) - set(output_joints)))

            try:
                cmds.undoInfo(openChunk=True)
                if output_joints and not state:
                    if children:
                        cmds.parent(children, SKEL)
                    cmds.delete(output_joints)
                    logger.info(f"Remove {output_joints}")

                joints = []
                if not output_joints and state:
                    for output_joint in current_component["output_joint"]:
                        joints.append(output_joint.create())
                    current_component.setup_skel(joints)
                    logger.info(f"Create {joints}")
                cmds.setAttr(
                    f"{current_component.guide_root}.create_output_joint", state
                )
                cmds.select(current_component.guide_root)
            finally:
                cmds.undoInfo(closeChunk=True)
            Settings.get_instance().refresh()

        def change_offset_output_rotate(spin_box, attr):
            cmds.setAttr(f"{root}.{attr}", spin_box.value())

        old_name = cmds.getAttr(f"{root}.name")
        old_side = cmds.getAttr(f"{root}.side")
        old_side_str = ["C", "L", "R"][old_side]
        old_index = cmds.getAttr(f"{root}.index")
        name_line_edit = QtWidgets.QLineEdit(old_name)
        name_line_edit.editingFinished.connect(partial(rename_name))
        side_combo_box = QtWidgets.QComboBox()
        side_combo_box.addItems(["C", "L", "R"])
        side_combo_box.setCurrentIndex(old_side)
        side_combo_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        side_combo_box.currentIndexChanged.connect(partial(rename_side))
        index_spin_box = QtWidgets.QSpinBox()
        index_spin_box.setRange(0, 9999)
        index_spin_box.setValue(old_index)
        index_spin_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        index_spin_box.editingFinished.connect(partial(rename_index))
        old_parent_output_index = cmds.getAttr(f"{root}.parent_output_index")
        parent_output_index_spin_box = QtWidgets.QSpinBox()
        parent_output_index_spin_box.setRange(-1, 9999)
        parent_output_index_spin_box.setValue(old_parent_output_index)
        parent_output_index_spin_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        parent_output_index_spin_box.editingFinished.connect(
            partial(set_parent_output_index)
        )
        old_create_output_joint = cmds.getAttr(f"{root}.create_output_joint")
        create_output_joint_check_box = QtWidgets.QCheckBox()
        create_output_joint_check_box.setChecked(old_create_output_joint)
        create_output_joint_check_box.toggled.connect(partial(create_output_joint))

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)

        offset_layout = QtWidgets.QHBoxLayout()
        offset_x_spin_box = QtWidgets.QSpinBox()
        offset_x_spin_box.setRange(0, 360)
        offset_x_spin_box.setValue(cmds.getAttr(f"{root}.offset_output_rotate_x"))
        offset_x_spin_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        offset_x_spin_box.editingFinished.connect(
            partial(
                change_offset_output_rotate, offset_x_spin_box, "offset_output_rotate_x"
            )
        )
        offset_y_spin_box = QtWidgets.QSpinBox()
        offset_y_spin_box.setRange(0, 360)
        offset_y_spin_box.setValue(cmds.getAttr(f"{root}.offset_output_rotate_y"))
        offset_y_spin_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        offset_y_spin_box.editingFinished.connect(
            partial(
                change_offset_output_rotate, offset_y_spin_box, "offset_output_rotate_y"
            )
        )
        offset_z_spin_box = QtWidgets.QSpinBox()
        offset_z_spin_box.setValue(cmds.getAttr(f"{root}.offset_output_rotate_z"))
        offset_z_spin_box.setRange(0, 360)
        offset_z_spin_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        offset_z_spin_box.editingFinished.connect(
            partial(
                change_offset_output_rotate, offset_z_spin_box, "offset_output_rotate_z"
            )
        )
        offset_layout.addWidget(offset_x_spin_box)
        offset_layout.addWidget(offset_y_spin_box)
        offset_layout.addWidget(offset_z_spin_box)

        parent_layout = parent.layout()
        parent_layout.addRow("Name", name_line_edit)
        parent_layout.addRow("Side", side_combo_box)
        parent_layout.addRow("Index", index_spin_box)
        parent_layout.addRow("Parent Output Index", parent_output_index_spin_box)
        parent_layout.addRow("Create Output Joint", create_output_joint_check_box)
        parent_layout.addRow("Offset Output Rotate", offset_layout)
        parent_layout.addRow(line)

    # endregion

    # region -    UIGenerator / ui
    @classmethod
    def add_line_edit(
        cls, parent: QtWidgets.QWidget, label: str, attribute: str
    ) -> QtWidgets.QLineEdit:

        def change_attribute() -> None:
            text = line_edit.text()
            cmds.setAttr(attribute, text, type="string")

        old_text = cmds.getAttr(attribute)
        line_edit = QtWidgets.QLineEdit(old_text)
        line_edit.editingFinished.connect(change_attribute)

        parent_layout = parent.layout()
        parent_layout.addRow(label, line_edit)

        return line_edit

    @classmethod
    def add_check_box(
        cls, parent: QtWidgets.QWidget, label: str, attribute: str
    ) -> QtWidgets.QCheckBox:

        def toggle_attribute():
            pass

        check = True if cmds.getAttr(attribute) else False
        check_box = QtWidgets.QCheckBox()
        check_box.setChecked(check)
        check_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        check_box.toggled.connect(toggle_attribute)
        parent_layout = parent.layout()
        parent_layout.addRow(label, check_box)

        return check_box

    @classmethod
    def add_spin_box(
        cls,
        parent: QtWidgets.QWidget,
        label: str,
        attribute: str,
        slider: bool,
        min_value: int,
        max_value: int,
    ) -> QtWidgets.QSpinBox:

        def change_attribute():
            value = spin_box.value()
            cmds.setAttr(attribute, value)

        old_value = cmds.getAttr(attribute)
        spin_box = QtWidgets.QSpinBox()
        spin_box.setRange(min_value, max_value)
        spin_box.setValue(old_value)
        spin_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )

        child = spin_box
        if slider:
            _slider = QtWidgets.QSlider()
            _slider.setOrientation(QtCore.Qt.Orientation.Horizontal)
            _slider.setRange(min_value, max_value)
            _slider.setValue(old_value)
            spin_box.valueChanged.connect(_slider.setValue)
            _slider.valueChanged.connect(spin_box.setValue)
            h_layout = QtWidgets.QHBoxLayout()
            h_layout.addWidget(spin_box)
            h_layout.addWidget(_slider)
            child = h_layout
            spin_box.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Fixed,
                QtWidgets.QSizePolicy.Policy.Fixed,
            )
        spin_box.valueChanged.connect(change_attribute)

        parent_layout = parent.layout()
        parent_layout.addRow(label, child)

        return spin_box

    @classmethod
    def add_notes(cls, parent: QtWidgets.QWidget, attribute: str) -> None:
        notes = cmds.getAttr(attribute)
        text_edit = QtWidgets.QTextEdit()
        text_edit.setMarkdown(notes)
        text_edit.setReadOnly(True)

        parent_layout = parent.layout()
        parent_layout.addItem(
            QtWidgets.QSpacerItem(
                0,
                0,
                QtWidgets.QSizePolicy.Policy.Minimum,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        )
        parent_layout.addRow(text_edit)

    # endregion


# endregion


# region Dynamicwidget
class DynamicWidget(QtWidgets.QWidget):

    def __init__(self, parent=None, root: str = None) -> None:
        super(DynamicWidget, self).__init__(parent=parent)

        layout = QtWidgets.QVBoxLayout(self)
        scroll_widget = QtWidgets.QScrollArea(self)
        scroll_widget.setWidgetResizable(True)
        scroll_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Expanding,
        )
        scroll_widget.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        self.parent_widget = QtWidgets.QWidget()
        scroll_widget.setWidget(self.parent_widget)

        form_layout = QtWidgets.QFormLayout(self.parent_widget)
        form_layout.setContentsMargins(0, 0, 0, 0)

        # form layout 의 label 부분의 넓이를 고정합니다.
        label = QtWidgets.QLabel()
        label.setFixedSize(QtCore.QSize(0, 0))
        form_layout.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, label)
        form_layout.itemAt(
            0, QtWidgets.QFormLayout.ItemRole.LabelRole
        ).widget().setFixedWidth(110)

        self.component_label = QtWidgets.QLabel(f"  {root}")
        font = self.component_label.font()
        font.setPointSize(12)
        self.component_label.setFont(font)
        layout.addWidget(self.component_label)
        layout.addWidget(scroll_widget)


# endregion


# region Assembly
class ScriptListWidget(QtWidgets.QListWidget):

    orderChanged = QtCore.Signal()

    def __init__(self, parent=None) -> None:
        super(ScriptListWidget, self).__init__(parent=parent)
        self.setSelectionMode(QtWidgets.QListWidget.SelectionMode.ExtendedSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QtWidgets.QListView.DragDropMode.InternalMove)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        font = self.font()
        font.setPointSize(10)
        self.setFont(font)

    def dropEvent(self, event):
        super().dropEvent(event)
        self.orderChanged.emit()


class Assembly(DynamicWidget):

    def add_check_box_line_edit_btn(
        self, parent: QtWidgets.QWidget, label: str, attributes: list, icon: str
    ) -> None:
        def change_check_box_attribute() -> None:
            v = check_box.isChecked()
            cmds.setAttr(check_box_attribute, v)

        check_box_attribute, line_edit_attribute = attributes
        check_box_value = cmds.getAttr(check_box_attribute)
        line_edit_value = cmds.getAttr(line_edit_attribute)

        check_box = QtWidgets.QCheckBox()
        check_box.setChecked(check_box_value)
        check_box.toggled.connect(change_check_box_attribute)
        line_edit = QtWidgets.QLineEdit()
        line_edit.setText(line_edit_value)
        line_edit.setReadOnly(True)
        btn = QtWidgets.QPushButton()
        btn.setFixedSize(QtCore.QSize(36, 18))
        btn.setIcon(QtGui.QIcon(icon))

        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(line_edit)
        layout.addWidget(check_box)
        layout.addWidget(btn)

        parent_layout = parent.layout()
        parent_layout.addRow(label, layout)

    def __init__(self, parent=None, root: str = "") -> None:
        # region -    Assembly / callback
        def get_script_path(_attrs: list) -> list:
            _script_paths = []
            for _attr in _attrs:
                _data = cmds.getAttr(f"{root}.{_attr}")
                if _data:
                    _script_paths.append(_data)
            return _script_paths

        def set_script_path(
            _rig_root: str,
            _attribute: str,
            _script_paths: list,
            _list_widget: QtWidgets.QListWidget,
        ) -> None:
            for _i, _script_path in enumerate(_script_paths):
                cmds.setAttr(f"{root}.{_attribute}[{_i}]", _script_path, type="string")
                cmds.connectAttr(
                    f"{root}.{_attribute}[{_i}]",
                    f"{_rig_root}.{_attribute}[{_i}]",
                )
                _text = ""
                if _script_path.startswith("*"):
                    _script_path = _script_path[1:]
                    _text += "*"
                _script_path = Path(_script_path)
                _text += f"{_script_path.name} {_script_path.parent.as_posix()}"
                _list_widget.addItem(_text)

        def add_script(_list_widget: QtWidgets.QListWidget, _attribute: str) -> None:
            file_path = cmds.fileDialog2(
                caption="Add Python Script",
                startingDirectory=cmds.workspace(query=True, rootDirectory=True),
                fileFilter="Python (*.py)",
                fileMode=1,
            )
            if not file_path:
                return
            file_path = Path(file_path[0])

            _attrs = cmds.listAttr(f"{root}.{_attribute}", multi=True)
            rig_root = cmds.connectionInfo(
                f"{root}.{_attribute}[0]", destinationFromSource=True
            )[0].split(".")[0]

            _script_paths = get_script_path(_attrs)
            _script_paths.append(file_path.as_posix())

            # clear mult attribute
            for _attr in _attrs:
                cmds.removeMultiInstance(f"{root}.{_attr}", b=True)
            _list_widget.clear()

            # add
            set_script_path(rig_root, _attribute, _script_paths, _list_widget)

        def create_script(_list_widget: QtWidgets.QListWidget, _attribute: str) -> None:
            file_path = cmds.fileDialog2(
                caption="Create Python Script",
                startingDirectory=cmds.workspace(query=True, rootDirectory=True),
                fileFilter="Python (*.py)",
                fileMode=0,
            )
            if not file_path:
                return
            file_path = Path(file_path[0])

            content = """def run(context, *args, **kwargs):\n\t..."""
            with open(file_path, "w") as f:
                f.write(content)

            _attrs = cmds.listAttr(f"{root}.{_attribute}", multi=True)
            rig_root = cmds.connectionInfo(
                f"{root}.{_attribute}[0]", destinationFromSource=True
            )[0].split(".")[0]

            _script_paths = get_script_path(_attrs)
            _script_paths.append(file_path.as_posix())

            # clear mult attribute
            for _attr in _attrs:
                cmds.removeMultiInstance(f"{root}.{_attr}", b=True)
            _list_widget.clear()

            # add
            set_script_path(rig_root, _attribute, _script_paths, _list_widget)

        def edit_script(_list_widget: QtWidgets.QListWidget) -> None:
            _select_items = _list_widget.selectedItems()

            if not _select_items:
                return

            _text = _select_items[0].text()
            _name, _parent = _text.split(" ")
            if _text.startswith("*"):
                _name = _name[:1]
            _path = Path(_parent) / _name

            if sys.platform.startswith("darwin"):
                subprocess.call(("open", _path.as_posix()))
            elif os.name == "nt":
                os.startfile(_path.as_posix())
            elif os.name == "posix":
                subprocess.call(("xdg-open", _path.as_posix()))

        def delete_script(_list_widget: QtWidgets.QListWidget, _attribute: str) -> None:
            _select_items = _list_widget.selectedItems()

            if not _select_items:
                return

            for _item in _select_items:
                _list_widget.takeItem(_list_widget.row(_item))

            _all_items = [
                _list_widget.item(i).text() for i in range(_list_widget.count())
            ]
            _script_paths = []
            for _item in _all_items:
                _name, _parent = _item.split(" ")
                if _name.startswith("*"):
                    _path = f"*{(Path(_parent) / _name[1:]).as_posix()}"
                else:
                    _path = (Path(_parent) / _name).as_posix()
                _script_paths.append(_path)

            _attrs = cmds.listAttr(f"{root}.{_attribute}", multi=True)
            rig_root = cmds.connectionInfo(
                f"{root}.{_attribute}[0]", destinationFromSource=True
            )[0].split(".")[0]

            # clear mult attribute
            for _attr in _attrs:
                cmds.removeMultiInstance(f"{root}.{_attr}", b=True)
            _list_widget.clear()

            # add
            set_script_path(rig_root, _attribute, _script_paths, _list_widget)

        def run_script(_list_widget: QtWidgets.QListWidget) -> None:
            _select_items = [i.text() for i in _list_widget.selectedItems()]

            if not _select_items:
                return

            try:
                for _item in _select_items:
                    if _item.startswith("*"):
                        _item = _item[1:]
                    _name, _parent = _item.split(" ")
                    _path = (Path(_parent) / _name).as_posix()
                    _spec = importlib.util.spec_from_file_location(_name[:-3], _path)
                    _module = importlib.util.module_from_spec(_spec)
                    _spec.loader.exec_module(_module)
                    sys.modules[_name[:-3]] = _module

                    _module.run({})
            except Exception as e:
                logger.error(e, exc_info=True)

        def order_changed(_list_widget: QtWidgets.QListWidget, _attribute: str) -> None:
            _all_items = [
                _list_widget.item(i).text() for i in range(_list_widget.count())
            ]
            _script_paths = []
            for _item in _all_items:
                _name, _parent = _item.split(" ")
                if _name.startswith("*"):
                    _path = f"*{(Path(_parent) / _name[1:]).as_posix()}"
                else:
                    _path = (Path(_parent) / _name).as_posix()
                _script_paths.append(_path)

            _attrs = cmds.listAttr(f"{root}.{_attribute}", multi=True)
            rig_root = cmds.connectionInfo(
                f"{root}.{_attribute}[0]", destinationFromSource=True
            )[0].split(".")[0]

            # clear mult attribute
            for _attr in _attrs:
                cmds.removeMultiInstance(f"{root}.{_attr}", b=True)
            _list_widget.clear()

            # add
            set_script_path(rig_root, _attribute, _script_paths, _list_widget)

        def enable_script(_list_widget: QtWidgets.QListWidget, _attribute: str) -> None:
            _select_items = [i for i in _list_widget.selectedItems()]

            if not _select_items:
                return

            for _item in _select_items:
                _text = _item.text()
                if _text.startswith("*"):
                    _item.setText(_text[1:])

            _all_items = [
                _list_widget.item(i).text() for i in range(_list_widget.count())
            ]
            _script_paths = []
            for _item in _all_items:
                _name, _parent = _item.split(" ")
                if _name.startswith("*"):
                    _path = f"*{(Path(_parent) / _name[1:]).as_posix()}"
                else:
                    _path = (Path(_parent) / _name).as_posix()
                _script_paths.append(_path)

            _attrs = cmds.listAttr(f"{root}.{_attribute}", multi=True)
            rig_root = cmds.connectionInfo(
                f"{root}.{_attribute}[0]", destinationFromSource=True
            )[0].split(".")[0]

            # clear mult attribute
            for _attr in _attrs:
                cmds.removeMultiInstance(f"{root}.{_attr}", b=True)
            _list_widget.clear()

            # add
            set_script_path(rig_root, _attribute, _script_paths, _list_widget)

        def disable_script(
            _list_widget: QtWidgets.QListWidget, _attribute: str
        ) -> None:
            _select_items = [i for i in _list_widget.selectedItems()]

            if not _select_items:
                return

            for _item in _select_items:
                _text = _item.text()
                if not _text.startswith("*"):
                    _item.setText(f"*{_text}")

            _all_items = [
                _list_widget.item(i).text() for i in range(_list_widget.count())
            ]
            _script_paths = []
            for _item in _all_items:
                _name, _parent = _item.split(" ")
                if _name.startswith("*"):
                    _path = f"*{(Path(_parent) / _name[1:]).as_posix()}"
                else:
                    _path = (Path(_parent) / _name).as_posix()
                _script_paths.append(_path)

            _attrs = cmds.listAttr(f"{root}.{_attribute}", multi=True)
            rig_root = cmds.connectionInfo(
                f"{root}.{_attribute}[0]", destinationFromSource=True
            )[0].split(".")[0]

            # clear mult attribute
            for _attr in _attrs:
                cmds.removeMultiInstance(f"{root}.{_attr}", b=True)
            _list_widget.clear()

            # add
            set_script_path(rig_root, _attribute, _script_paths, _list_widget)

        def toggled_run_script(_attr, _checked):
            cmds.setAttr(_attr, _checked)

        def set_modeling_path():
            pass

        def set_dummy_path():
            pass

        def set_blendshape_manager_path():
            pass

        def set_space_manager_path():
            pass

        def set_pose_manager_path():
            pass

        def set_sdk_manager_path():
            pass

        def set_deformer_manager_path():
            pass

        # endregion
        super(Assembly, self).__init__(parent=parent, root=root)

        up_icon = (icon_dir / "arrow-big-up-lines.svg").as_posix()
        down_icon = (icon_dir / "arrow-big-down-lines.svg").as_posix()

        self.add_check_box_line_edit_btn(
            self.parent_widget,
            "Modeling",
            [f"{root}.run_import_modeling", f"{root}.modeling_path"],
            down_icon,
        )
        self.add_check_box_line_edit_btn(
            self.parent_widget,
            "Dummy",
            [f"{root}.run_import_dummy", f"{root}.dummy_path"],
            down_icon,
        )
        self.add_check_box_line_edit_btn(
            self.parent_widget,
            "BlendShape Manager",
            [
                f"{root}.run_import_blendshape_manager",
                f"{root}.blendshape_manager_path",
            ],
            up_icon,
        )
        self.add_check_box_line_edit_btn(
            self.parent_widget,
            "Pose Manager",
            [f"{root}.run_import_pose_manager", f"{root}.pose_manager_path"],
            up_icon,
        )
        self.add_check_box_line_edit_btn(
            self.parent_widget,
            "SDK Manager",
            [f"{root}.run_import_sdk_manager", f"{root}.sdk_manager_path"],
            up_icon,
        )
        self.add_check_box_line_edit_btn(
            self.parent_widget,
            "Space Manager",
            [f"{root}.run_import_space_manager", f"{root}.space_manager_path"],
            up_icon,
        )
        self.add_check_box_line_edit_btn(
            self.parent_widget,
            "DeformerWeights Manager",
            [
                f"{root}.run_import_deformer_weights_manager",
                f"{root}.deformer_weights_manager_path",
            ],
            up_icon,
        )

        # region -    Assembly / context menu
        def show_context_menu(
            pos, _list_widget: QtWidgets.QListWidget, _attribute: str
        ) -> None:
            menu = QtWidgets.QMenu(self)

            enable_action = menu.addAction("Enable")
            disable_action = menu.addAction("Disable")
            reveal_in_explorer_action = menu.addAction("Reveal in Explorer")

            _item = _list_widget.itemAt(pos)
            if not _item:
                return

            enable_action.triggered.connect(
                partial(enable_script, _list_widget, _attribute)
            )
            disable_action.triggered.connect(
                partial(disable_script, _list_widget, _attribute)
            )
            reveal_in_explorer_action.triggered.connect(
                partial(reveal_in_explorer, _item.text())
            )
            menu.exec(_list_widget.mapToGlobal(pos))

        def reveal_in_explorer(_text):
            _, _parent = _text.split(" ")

            _path = Path(_parent)
            if _path.exists():
                if sys.platform.startswith("darwin"):
                    os.system(f'open "{_path}"')
                elif os.name == "nt":
                    os.startfile(_path)  # Windows 탐색기에서 열기
                elif os.name == "posix":
                    os.system(f'xdg-open "{_path}"')

        # endregion

        # region -    Assembly / ui
        for attribute in ["pre_custom_scripts", "post_custom_scripts"]:
            label = f"Run {attribute.replace('_', ' ').capitalize()}"
            check_box = UIGenerator.add_check_box(
                parent=self.parent_widget,
                label=label,
                attribute=f"{root}.run_{attribute}",
            )
            checked = cmds.getAttr(f"{root}.run_{attribute}")
            check_box.setChecked(checked)
            check_box.toggled.connect(
                partial(toggled_run_script, f"{root}.run_{attribute}")
            )
            list_widget = ScriptListWidget()
            list_widget.clear()

            # populate
            attrs = cmds.listAttr(f"{root}.{attribute}", multi=True) or []
            script_paths = get_script_path(attrs)
            for path in script_paths:
                text = ""
                if path.startswith("*"):
                    path = path[1:]
                    text += "*"
                path = Path(path)
                text += f"{path.name} {path.parent.as_posix()}"
                list_widget.addItem(text)

            list_widget.orderChanged.connect(
                partial(order_changed, list_widget, attribute)
            )
            list_widget.customContextMenuRequested.connect(
                partial(
                    show_context_menu, _list_widget=list_widget, _attribute=attribute
                )
            )

            layout = QtWidgets.QHBoxLayout()
            layout.addWidget(list_widget)

            btn_layout = QtWidgets.QVBoxLayout()
            layout.addLayout(btn_layout)

            add_btn = QtWidgets.QPushButton("Add")
            add_btn.setFixedWidth(56)
            add_btn.setFixedHeight(24)
            add_btn.clicked.connect(partial(add_script, list_widget, attribute))
            create_btn = QtWidgets.QPushButton("Create")
            create_btn.setFixedWidth(56)
            create_btn.setFixedHeight(24)
            create_btn.clicked.connect(partial(create_script, list_widget, attribute))
            edit_btn = QtWidgets.QPushButton("Edit")
            edit_btn.setFixedWidth(56)
            edit_btn.setFixedHeight(24)
            edit_btn.clicked.connect(partial(edit_script, list_widget))
            delete_btn = QtWidgets.QPushButton("Delete")
            delete_btn.setFixedWidth(56)
            delete_btn.setFixedHeight(24)
            delete_btn.clicked.connect(partial(delete_script, list_widget, attribute))
            run_btn = QtWidgets.QPushButton("Run Item")
            run_btn.setFixedWidth(56)
            run_btn.setFixedHeight(24)
            run_btn.clicked.connect(partial(run_script, list_widget))

            btn_layout.addWidget(add_btn)
            btn_layout.addWidget(create_btn)
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(delete_btn)
            btn_layout.addWidget(run_btn)
            btn_layout.addItem(
                QtWidgets.QSpacerItem(
                    0,
                    0,
                    QtWidgets.QSizePolicy.Policy.Minimum,
                    QtWidgets.QSizePolicy.Policy.Expanding,
                )
            )

            label = " ".join([x.capitalize() for x in attribute.split("_")])
            self.parent_widget.layout().addRow(label, layout)
        # endregion

        UIGenerator.add_notes(self.parent_widget, f"{root}.notes")

        self.parent_widget.layout().addItem(
            QtWidgets.QSpacerItem(
                0,
                0,
                QtWidgets.QSizePolicy.Policy.Minimum,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        )


# endregion


# region Control01
class Control01(DynamicWidget):

    def __init__(self, parent=None, root=None):
        super(Control01, self).__init__(parent=parent, root=root)
        UIGenerator.add_common_component_settings(self.parent_widget, root)

        def change_controller_count():
            manager_ui = get_manager_ui()
            rig = manager_ui.rig_tree_model.rig

            current_component = get_component(rig, name, side_str, index)
            if current_component["children"]:
                logger.warning("하위 컴포넌트가 존재합니다. 확인해주세요.")
                Settings.get_instance().refresh()
                return

            old_count = len(cmds.listAttr(f"{root}.guide_matrix", multi=True))
            count = controller_count_spin_box.value()

            if old_count == count:
                Settings.get_instance().refresh()
                return

            try:
                cmds.undoInfo(openChunk=True)
                current_component.detach_guide()
                output_joints = cmds.listConnections(
                    f"{current_component.rig_root}.output_joint",
                    source=True,
                    destination=False,
                )
                joint_children = []
                for j in output_joints:
                    children = cmds.listRelatives(j, children=True)
                    if children:
                        joint_children.extend(list(set(children) - set(output_joints)))
                if joint_children:
                    cmds.parent(joint_children, SKEL)
                cmds.delete([current_component.rig_root] + output_joints)
                if old_count > count:
                    current_component["guide_matrix"]["value"] = current_component[
                        "guide_matrix"
                    ]["value"][:count]
                    current_component["initialize_output_matrix"]["value"] = (
                        current_component["initialize_output_matrix"]["value"][:count]
                    )
                    current_component["initialize_output_inverse_matrix"]["value"] = (
                        current_component["initialize_output_inverse_matrix"]["value"][
                            :count
                        ]
                    )
                elif old_count < count:
                    for _ in range(old_count, count):
                        current_component["guide_matrix"]["value"].append(
                            list(ORIGINMATRIX)
                        )
                        current_component["initialize_output_matrix"]["value"].append(
                            list(ORIGINMATRIX)
                        )
                        current_component["initialize_output_inverse_matrix"][
                            "value"
                        ].append(list(ORIGINMATRIX))
                current_component["controller_count"]["value"] = count
                current_component["controller"] = []
                current_component["output"] = []
                current_component["output_joint"] = []
                current_component.populate()
                current_component.rig()
                current_component.attach_guide()
                output_joints = cmds.listConnections(
                    f"{current_component.rig_root}.output_joint",
                    source=True,
                    destination=False,
                )
                current_component.setup_skel(output_joints)

                cmds.select(current_component.guide_root)
                manager_ui.rig_tree_model.populate_model()
                Settings.get_instance().refresh()
            finally:
                cmds.undoInfo(closeChunk=True)

        controller_count_spin_box = UIGenerator.add_spin_box(
            self.parent_widget,
            label="Controller Count",
            attribute=f"{root}.controller_count",
            slider=False,
            min_value=1,
            max_value=999,
        )
        name = cmds.getAttr(f"{root}.name")
        side = cmds.getAttr(f"{root}.side")
        side_str = ["C", "L", "R"][side]
        index = cmds.getAttr(f"{root}.index")
        controller_count_spin_box.editingFinished.connect(change_controller_count)
        UIGenerator.add_notes(self.parent_widget, f"{root}.notes")


# endregion


# region Fk01
class Fk01(DynamicWidget):

    def __init__(self, parent=None, root=None):
        super(Fk01, self).__init__(parent=parent, root=root)
        UIGenerator.add_common_component_settings(self.parent_widget, root)

        def change_count():
            manager_ui = get_manager_ui()
            rig = manager_ui.rig_tree_model.rig

            current_component = get_component(rig, name, side_str, index)
            if current_component["children"]:
                logger.warning("하위 컴포넌트가 존재합니다. 확인해주세요.")
                Settings.get_instance().refresh()
                return

            root_count = root_count_spin_box.value()
            chain_counts = [s_box.value() for s_box in chain_count_spin_boxes]

            if (old_root_count == root_count) and (old_chain_counts == chain_counts):
                Settings.get_instance().refresh()
                return

            matrices = [list(ORIGINMATRIX) for _ in range(2)]
            try:
                cmds.undoInfo(openChunk=True)
                current_component.detach_guide()
                output_joints = cmds.listConnections(
                    f"{current_component.rig_root}.output_joint",
                    source=True,
                    destination=False,
                )
                joint_children = []
                for j in output_joints:
                    children = cmds.listRelatives(j, children=True)
                    if children:
                        joint_children.extend(list(set(children) - set(output_joints)))
                if joint_children:
                    cmds.parent(joint_children, SKEL)
                cmds.delete([current_component.rig_root] + output_joints)
                if old_root_count > root_count:
                    delete_count = sum(old_chain_counts[old_root_count - root_count :])
                    current_component["guide_matrix"]["value"] = current_component[
                        "guide_matrix"
                    ]["value"][:delete_count]
                    current_component["initialize_output_matrix"]["value"] = (
                        current_component["initialize_output_matrix"]["value"][
                            :delete_count
                        ]
                    )
                    current_component["initialize_output_inverse_matrix"]["value"] = (
                        current_component["initialize_output_inverse_matrix"]["value"][
                            :delete_count
                        ]
                    )
                    chain_counts = chain_counts[:delete_count]
                elif old_root_count < root_count:
                    for _ in range(old_root_count, root_count):
                        current_component["guide_matrix"]["value"].extend(matrices)
                        current_component["initialize_output_matrix"]["value"].extend(
                            matrices
                        )
                        current_component["initialize_output_inverse_matrix"][
                            "value"
                        ].extend(matrices)
                        chain_counts.append(2)
                elif old_chain_counts != chain_counts:
                    chain_guide_matrices = []
                    chain_output_matrices = []
                    chain_output_inverse_matrices = []
                    i = 0
                    for count in old_chain_counts:
                        chain_guide_matrices.append(
                            current_component["guide_matrix"]["value"][i : i + count]
                        )
                        chain_output_matrices.append(
                            current_component["initialize_output_matrix"]["value"][
                                i : i + count
                            ]
                        )
                        chain_output_inverse_matrices.append(
                            current_component["initialize_output_inverse_matrix"][
                                "value"
                            ][i : i + count]
                        )
                        i += count
                    c = 0
                    for new_count, old_count in zip(chain_counts, old_chain_counts):
                        if old_count > new_count:
                            chain_guide_matrices[c] = chain_guide_matrices[c][
                                :new_count
                            ]
                            chain_output_matrices[c] = chain_output_matrices[c][
                                :new_count
                            ]
                            chain_output_inverse_matrices[c] = (
                                chain_output_inverse_matrices[c][:new_count]
                            )
                        elif old_count < new_count:
                            chain_guide_matrices[c].append(list(ORIGINMATRIX))
                            chain_output_matrices[c].append(list(ORIGINMATRIX))
                            chain_output_inverse_matrices[c].append(list(ORIGINMATRIX))
                        c += 1
                    current_component["guide_matrix"]["value"].extend(
                        [y for x in chain_guide_matrices for y in x]
                    )
                    current_component["initialize_output_matrix"]["value"].extend(
                        [y for x in chain_output_inverse_matrices for y in x]
                    )
                    current_component["initialize_output_inverse_matrix"][
                        "value"
                    ].extend([y for x in chain_output_inverse_matrices for y in x])
                current_component["root_count"]["value"] = root_count
                current_component["chain_count"]["value"] = chain_counts
                current_component["controller"] = []
                current_component["output"] = []
                current_component["output_joint"] = []
                current_component.populate()
                current_component.rig()
                current_component.attach_guide()
                output_joints = cmds.listConnections(
                    f"{current_component.rig_root}.output_joint",
                    source=True,
                    destination=False,
                )
                current_component.setup_skel(output_joints)

                cmds.select(current_component.guide_root)
                manager_ui.rig_tree_model.populate_model()
                Settings.get_instance().refresh()
            finally:
                cmds.undoInfo(closeChunk=True)

        name = cmds.getAttr(f"{root}.name")
        side = cmds.getAttr(f"{root}.side")
        side_str = ["C", "L", "R"][side]
        index = cmds.getAttr(f"{root}.index")

        old_root_count = cmds.getAttr(f"{root}.root_count")
        old_chain_counts = []
        for i in range(old_root_count):
            old_chain_counts.append(cmds.getAttr(f"{root}.chain_count[{i}]"))

        root_count = cmds.getAttr(f"{root}.root_count")
        root_count_spin_box = UIGenerator.add_spin_box(
            self.parent_widget,
            label="Root Count",
            attribute=f"{root}.root_count",
            slider=False,
            min_value=1,
            max_value=999,
        )
        root_count_spin_box.editingFinished.connect(change_count)
        chain_count_spin_boxes = []
        for i in range(root_count):
            chain_count_spin_box = UIGenerator.add_spin_box(
                self.parent_widget,
                label=f"Root {i + 1} Chain Count",
                attribute=f"{root}.chain_count[{i}]",
                slider=False,
                min_value=1,
                max_value=999,
            )
            chain_count_spin_box.editingFinished.connect(change_count)
            chain_count_spin_boxes.append(chain_count_spin_box)
        UIGenerator.add_notes(self.parent_widget, f"{root}.notes")


# endregion


# region Settings
UITABLE = {"assembly": Assembly, "control01": Control01, "fk01": Fk01}


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
                plug = cmds.connectionInfo(
                    f"{selected[0]}.message", destinationFromSource=True
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


# endregion
