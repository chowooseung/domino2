# gui
from shiboken6 import wrapInstance
from PySide6 import QtCore, QtWidgets

# domino
from domino.component import SKEL
from domino.core.utils import logger
from domino.core import center, left, right

# maya
from maya import cmds
from maya import OpenMayaUI as omui  # type: ignore

# built-ins
from functools import partial


def get_maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


def find_docked_widget(object_name: str):
    main_window = get_maya_main_window()
    return main_window.findChild(QtWidgets.QWidget, object_name)


def get_manager_ui():
    """Manager ui를 refresh 하거나 manager 에서 rig 데이터를 가져오기 위해 사용됨.
    dominomanager 모듈을 직접 import 할수없음"""

    return find_docked_widget("domino_manager_ui")


def get_settings_ui():
    """Settings ui를 refresh 하기위해 사용됨.
    dominosettings 모듈을 직접 import 할수없음"""

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


class UIGenerator:

    # region -    UIGenerator / common settings
    @classmethod
    def add_common_component_settings(cls, parent, root):

        manager_ui = get_manager_ui()
        settings_ui = get_settings_ui()

        def edit_name():
            if not cmds.objExists(root):
                return

            new_name = name_line_edit.text()

            for s in new_name:
                if not s.isalpha() and not s.isalnum():
                    logger.warning(f"{new_name} `{s}`는 유효하지 않습니다.")
                    settings_ui.refresh()
                    return
            if old_name == new_name:
                logger.warning(f"이전과 같습니다.")
                settings_ui.refresh()
                return
            if not new_name:
                logger.warning(f"빈 문자열을 이름으로 사용 할 수 없습니다.")
                settings_ui.refresh()
                return
            if not new_name[0].isalpha():
                logger.warning(f"문자열의 시작은 알파벳 이어야합니다.")
                settings_ui.refresh()
                return

            rig = manager_ui.rig_tree_model.rig

            current_component = get_component(rig, old_name, old_side_str, old_index)
            destination_component = get_component(
                rig, new_name, old_side_str, old_index
            )

            if destination_component:
                logger.warning(
                    f"{new_name}_{old_side_str}{old_index} Component 는 이미 존재합니다."
                )
                settings_ui.refresh()
                return

            try:
                cmds.undoInfo(openChunk=True)
                current_component.rename_component(new_name, old_side, old_index, True)
                cmds.select(current_component.guide_root)
            finally:
                cmds.undoInfo(closeChunk=True)
            logger.info(
                f"Rename Component {old_name}_{old_side_str}{old_index} -> {new_name}_{old_side_str}{old_index}"
            )
            # manager ui refresh
            manager_ui.refresh()
            # settings ui refresh
            settings_ui.refresh()

        def edit_side(new_side):
            if not cmds.objExists(root):
                return

            new_side_str = [center, left, right][new_side]
            if old_side == new_side:
                logger.warning(f"이전과 같습니다.")
                settings_ui.refresh()
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
                settings_ui.refresh()
                return

            try:
                cmds.undoInfo(openChunk=True)
                current_component.rename_component(old_name, new_side, old_index, True)
                cmds.select(current_component.guide_root)
            finally:
                cmds.undoInfo(closeChunk=True)
            logger.info(
                f"Rename Component {old_name}_{old_side_str}{old_index} -> {old_name}_{new_side_str}{old_index}"
            )
            # manager ui refresh
            manager_ui.refresh()
            # settings ui refresh
            settings_ui.refresh()

        def edit_index():
            if not cmds.objExists(root):
                return

            index = index_spin_box.value()
            manager_ui = get_manager_ui()
            rig = manager_ui.rig_tree_model.rig

            current_component = get_component(rig, old_name, old_side_str, old_index)
            destination_component = get_component(rig, old_name, old_side_str, index)

            if destination_component:
                logger.warning(
                    f"{old_name}_{old_side_str}{index} Component 는 이미 존재합니다."
                )
                settings_ui.refresh()
                return

            try:
                cmds.undoInfo(openChunk=True)
                current_component.rename_component(old_name, old_side, index, True)
                cmds.select(current_component.guide_root)
            finally:
                cmds.undoInfo(closeChunk=True)
            logger.info(
                f"Rename Component {old_name}_{old_side_str}{old_index} -> {old_name}_{old_side_str}{index}"
            )
            # manager ui refresh
            manager_ui.refresh()
            # settings ui refresh
            settings_ui.refresh()

        def set_parent_output_index():
            if not cmds.objExists(root):
                return

            manager_ui = get_manager_ui()
            rig = manager_ui.rig_tree_model.rig

            current_component = get_component(rig, old_name, old_side_str, old_index)

            parent_component = current_component.get_parent()
            parent_rig_root = parent_component.rig_root

            outputs = cmds.listConnections(
                f"{parent_rig_root}.output", source=True, destination=False
            )
            if not outputs:
                settings_ui.refresh()
                return

            output_index = parent_output_index_spin_box.value()
            if output_index >= len(outputs):
                output_index = -1
            old_parent = cmds.listRelatives(current_component.rig_root, parent=True)[0]
            if old_parent == outputs[output_index]:
                settings_ui.refresh()
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
            # manager ui refresh
            manager_ui.refresh()
            # settings ui refresh
            settings_ui.refresh()

        def toggle_create_output_joint(state):
            if not cmds.objExists(root):
                return

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
                    current_component.populate_output_joint()
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
            # manager ui refresh
            manager_ui.refresh()
            # settings ui refresh
            settings_ui.refresh()

        def change_offset_output_rotate(spin_box, attr):
            if not cmds.objExists(root):
                return

            manager_ui = get_manager_ui()
            cmds.setAttr(f"{root}.{attr}", spin_box.value())
            # manager ui refresh
            manager_ui.refresh()
            # settings ui refresh

        old_name = cmds.getAttr(f"{root}.name")
        old_side = cmds.getAttr(f"{root}.side")
        old_side_str = [center, left, right][old_side]
        old_index = cmds.getAttr(f"{root}.index")
        name_line_edit = QtWidgets.QLineEdit(old_name)
        name_line_edit.editingFinished.connect(partial(edit_name))
        side_combo_box = QtWidgets.QComboBox()
        side_combo_box.addItems([center, left, right])
        side_combo_box.setCurrentIndex(old_side)
        side_combo_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        side_combo_box.currentIndexChanged.connect(partial(edit_side))
        index_spin_box = QtWidgets.QSpinBox()
        index_spin_box.setRange(0, 9999)
        index_spin_box.setValue(old_index)
        index_spin_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        index_spin_box.editingFinished.connect(partial(edit_index))
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
        create_output_joint_check_box.toggled.connect(
            partial(toggle_create_output_joint)
        )

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
    def add_ribbon_settings(cls, parent, attribute):

        def change_output_index():
            if not cmds.objExists(attribute):
                return

            index = combo_box.currentIndex()
            slider.setValue(int(u_values[index] * 100))

        def edit_u_value():
            if not cmds.objExists(attribute):
                return

            index = combo_box.currentIndex()
            value = slider.value()
            cmds.setAttr(f"{attribute}[{index}]", value / 100)

        frame = QtWidgets.QFrame()
        frame.setFrameShape(QtWidgets.QFrame.Shape.Box)

        layout = QtWidgets.QFormLayout(frame)

        combo_box = QtWidgets.QComboBox()
        combo_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        layout.addRow("Ribbon Output Index", combo_box)
        u_values = cmds.getAttr(attribute)[0]
        for i in range(len(u_values)):
            combo_box.addItem(str(i))

        horizontal_layout = QtWidgets.QHBoxLayout()
        slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        slider.setRange(0, 100)
        horizontal_layout.addWidget(slider)
        spin_box = QtWidgets.QSpinBox()
        spin_box.setRange(0, 100)
        horizontal_layout.addWidget(spin_box)
        layout.addRow(horizontal_layout)

        slider.valueChanged.connect(spin_box.setValue)
        spin_box.valueChanged.connect(slider.setValue)

        slider.valueChanged.connect(edit_u_value)
        combo_box.currentIndexChanged.connect(change_output_index)

        parent_layout = parent.layout()
        parent_layout.addRow(frame)

    @classmethod
    def add_line_edit(cls, parent, label, attribute):

        def change_attribute() -> None:
            if not cmds.objExists(attribute):
                return

            text = line_edit.text()
            cmds.setAttr(attribute, text, type="string")

        old_text = cmds.getAttr(attribute)
        line_edit = QtWidgets.QLineEdit(old_text)
        line_edit.editingFinished.connect(change_attribute)

        parent_layout = parent.layout()
        parent_layout.addRow(label, line_edit)

        return line_edit

    @classmethod
    def add_check_box(cls, parent, label, attribute):

        def toggle_attribute():
            if not cmds.objExists(attribute):
                return

            checked = check_box.isChecked()
            cmds.setAttr(attribute, checked)

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
    def add_spin_box(cls, parent, label, attribute, slider, min_value, max_value):

        def change_attribute():
            if not cmds.objExists(attribute):
                return

            value = spin_box.value()
            cmds.setAttr(attribute, value)

        old_value = cmds.getAttr(attribute)
        spin_box = QtWidgets.QSpinBox()
        spin_box.setRange(min_value, max_value)
        spin_box.setValue(old_value)
        spin_box.setFixedWidth(50)
        spin_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Fixed,
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
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Fixed,
            )
        spin_box.valueChanged.connect(change_attribute)

        parent_layout = parent.layout()
        parent_layout.addRow(label, child)

        return spin_box

    @classmethod
    def add_combo_box(cls, parent, label, attribute):

        def change_index():
            if not cmds.objExists(attribute):
                return

            value = combo_box.currentIndex()
            cmds.setAttr(attribute, value)

        combo_box = QtWidgets.QComboBox()

        old_value = cmds.getAttr(attribute)
        enum_list = cmds.addAttr(attribute, query=True, enumName=True).split(":")
        combo_box.addItems(enum_list)
        combo_box.setCurrentIndex(old_value)
        combo_box.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        combo_box.currentIndexChanged.connect(change_index)

        parent_layout = parent.layout()
        parent_layout.addRow(label, combo_box)
        return combo_box

    @classmethod
    def add_notes(cls, parent, attribute):
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


class DynamicWidget(QtWidgets.QWidget):

    def __init__(self, parent=None, root=None) -> None:
        # root is guide root
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
