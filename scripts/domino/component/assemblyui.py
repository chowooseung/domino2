# domino
from domino.core.utils import logger
from domino.dominoui import DynamicWidget, UIGenerator

# Qt
from PySide6 import QtCore, QtGui, QtWidgets

# maya
from maya import cmds

# built-ins
import importlib.util
import os
import subprocess
import sys
from functools import partial
from pathlib import Path


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

    def add_check_box_line_edit_btn(self, parent, label, attributes, icon):

        def change_check_box_attribute():
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

    def __init__(self, parent=None, root=""):
        # region -    Assembly / callback
        def get_script_path(_attrs):
            _script_paths = []
            for _attr in _attrs:
                _data = cmds.getAttr(f"{root}.{_attr}")
                if _data:
                    _script_paths.append(_data)
            return _script_paths

        def set_script_path(_rig_root, _attribute, _script_paths, _list_widget):
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

        def add_script(_list_widget, _attribute):
            start_directroy = (
                Path(start_directroy).with_suffix(".metadata") / "scripts"
                if os.getenv("DOMINO_RIG_WORK_PATH", None)
                else cmds.workspace(query=True, rootDirectory=True)
            )
            file_path = cmds.fileDialog2(
                caption="Add Python Script",
                startingDirectory=start_directroy,
                fileFilter="Python (*.py)",
                fileMode=1,
            )
            if not file_path:
                return
            file_path = Path(file_path[0])

            _attrs = cmds.listAttr(f"{root}.{_attribute}", multi=True) or []
            rig_root = cmds.connectionInfo(
                f"{root}.guide_matrix[0]", destinationFromSource=True
            )[0].split(".")[0]

            _script_paths = get_script_path(_attrs)
            _script_paths.append(file_path.as_posix())

            # clear mult attribute
            for _attr in _attrs:
                cmds.removeMultiInstance(f"{root}.{_attr}", b=True)
            _list_widget.clear()

            # add
            set_script_path(rig_root, _attribute, _script_paths, _list_widget)

        def create_script(_list_widget, _attribute):
            start_directroy = (
                Path(start_directroy).with_suffix(".metadata") / "scripts"
                if os.getenv("DOMINO_RIG_WORK_PATH", None)
                else cmds.workspace(query=True, rootDirectory=True)
            )
            file_path = cmds.fileDialog2(
                caption="Create Python Script",
                startingDirectory=start_directroy,
                fileFilter="Python (*.py)",
                fileMode=0,
            )
            if not file_path:
                return
            file_path = Path(file_path[0])

            content = """# maya\nfrom maya import cmds\n\n\ndef run(context, *args, **kwargs):\n\t..."""
            with open(file_path, "w") as f:
                f.write(content)

            _attrs = cmds.listAttr(f"{root}.{_attribute}", multi=True) or []
            rig_root = cmds.connectionInfo(
                f"{root}.guide_matrix[0]", destinationFromSource=True
            )[0].split(".")[0]

            _script_paths = get_script_path(_attrs)
            _script_paths.append(file_path.as_posix())

            # clear mult attribute
            for _attr in _attrs:
                cmds.removeMultiInstance(f"{root}.{_attr}", b=True)
            _list_widget.clear()

            # add
            set_script_path(rig_root, _attribute, _script_paths, _list_widget)

        def edit_script(_list_widget):
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

        def delete_script(_list_widget, _attribute):
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
                f"{root}.guide_matrix[0]", destinationFromSource=True
            )[0].split(".")[0]

            # clear mult attribute
            for _attr in _attrs:
                cmds.removeMultiInstance(f"{root}.{_attr}", b=True)
                cmds.removeMultiInstance(f"{rig_root}.{_attr}", b=True)
            _list_widget.clear()

            # add
            set_script_path(rig_root, _attribute, _script_paths, _list_widget)

        def run_script(_list_widget):
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

        def order_changed(_list_widget, _attribute):
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
                f"{root}.guide_matrix[0]", destinationFromSource=True
            )[0].split(".")[0]

            # clear mult attribute
            for _attr in _attrs:
                cmds.removeMultiInstance(f"{root}.{_attr}", b=True)
            _list_widget.clear()

            # add
            set_script_path(rig_root, _attribute, _script_paths, _list_widget)

        def enable_script(_list_widget, _attribute):
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
                f"{root}.guide_matrix[0]", destinationFromSource=True
            )[0].split(".")[0]

            # clear mult attribute
            for _attr in _attrs:
                cmds.removeMultiInstance(f"{root}.{_attr}", b=True)
            _list_widget.clear()

            # add
            set_script_path(rig_root, _attribute, _script_paths, _list_widget)

        def disable_script(_list_widget, _attribute):
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
                f"{root}.guide_matrix[0]", destinationFromSource=True
            )[0].split(".")[0]

            # clear mult attribute
            for _attr in _attrs:
                cmds.removeMultiInstance(f"{root}.{_attr}", b=True)
            _list_widget.clear()

            # add
            set_script_path(rig_root, _attribute, _script_paths, _list_widget)

        def toggled_run_script(_attr, _checked):
            cmds.setAttr(_attr, _checked)

        # endregion
        super(Assembly, self).__init__(parent=parent, root=root)

        # region -    Assembly / context menu
        def show_context_menu(_list_widget, _attribute, pos):
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
                partial(show_context_menu, list_widget, attribute)
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
