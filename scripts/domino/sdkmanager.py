# maya
from maya import cmds

# built-ins
import json
from pathlib import Path

# Qt
from PySide6 import QtWidgets, QtCore, QtGui

# domino
from domino.core import anim, left, right, nurbscurve, Name
from domino.core.utils import logger

SDK_SETS = "sdk_sets"
SDK_MANAGER = "sdk_manager"


def create_sdk_node():
    sdk_node = cmds.createNode("transform", name=SDK_MANAGER)
    cmds.addAttr(sdk_node, longName="_data", dataType="string")

    data = {"controls": [], "sdk": {}}
    cmds.setAttr(f"{sdk_node}._data", json.dumps(data), type="string")
    return sdk_node


def get_sdk_node():
    return SDK_MANAGER if cmds.objExists(SDK_MANAGER) else None


def add_sdk_control(controls):
    sdk_node = get_sdk_node()
    if sdk_node is None:
        return

    data = json.loads(cmds.getAttr(f"{sdk_node}._data"))

    sdk_controls = []
    for control in controls:
        parent = cmds.listRelatives(control, parent=True)
        parent = parent[0] if parent else None
        m = cmds.xform(control, query=True, matrix=True, worldSpace=True)
        if cmds.objExists(f"{control}_{Name.sdk_extension}"):
            logger.warning(f"이미 `{control}_{Name.sdk_extension}` 가 존재합니다.")
            continue
        sdk_control = nurbscurve.create("axis", None)
        sdk_control = cmds.rename(sdk_control, f"{control}_{Name.sdk_extension}")
        for shape in cmds.listRelatives(sdk_control, shapes=True):
            cmds.setAttr(f"{shape}.overrideEnabled", 1)
            cmds.setAttr(f"{shape}.overrideColor", 14)
        cmds.addAttr(
            sdk_control,
            longName="is_domino_sdk_controller",
            attributeType="bool",
            keyable=False,
        )
        cmds.addAttr(
            sdk_control,
            longName="mirror_type",
            attributeType="enum",
            enumName="orientation:behavior:inverseScale",
            keyable=False,
            defaultValue=0,
        )
        if cmds.objExists(f"{control}.is_domino_controller"):
            cmds.connectAttr(f"{control}.mirror_type", f"{sdk_control}.mirror_type")
        for attr in [
            "tx",
            "ty",
            "tz",
            "rx",
            "ry",
            "rz",
            "sx",
            "sy",
            "sz",
            "mirror_type",
        ]:
            cmds.setAttr(f"{sdk_control}.{attr}", channelBox=True)
        cmds.setAttr(f"{sdk_control}.v", keyable=False, lock=True)
        if parent:
            cmds.parent(sdk_control, parent)
        cmds.xform(sdk_control, matrix=m, worldSpace=True)
        cmds.parent(control, sdk_control)
        sdk_controls.append(sdk_control)

    cmds.sets(sdk_controls, edit=True, addElement=SDK_SETS)

    data["controls"].extend(sdk_controls)
    cmds.setAttr(f"{sdk_node}._data", json.dumps(data), type="string")
    cmds.select(sdk_controls)
    return sdk_controls


def remove_sdk_control(controls):
    sdk_node = get_sdk_node()
    if sdk_node is None:
        return

    data = json.loads(cmds.getAttr(f"{sdk_node}._data"))

    selected = cmds.ls(selection=True)
    sdk_controls = []
    for control in controls:
        sdk_control = cmds.listRelatives(control, parent=True)[0]
        if not cmds.objExists(f"{sdk_control}.is_domino_sdk_controller"):
            continue
        parent = cmds.listRelatives(sdk_control, parent=True)
        cmds.parent(control, parent[0]) if parent else cmds.parent(control, world=True)
        sdk_controls.append(sdk_control)
    cmds.delete(sdk_controls)

    sdk_sets = set(sdk_controls)
    data["controls"] = [ctl for ctl in data["controls"] if ctl not in sdk_sets]
    cmds.setAttr(f"{sdk_node}._data", json.dumps(data), type="string")
    if selected:
        cmds.select([s for s in selected if cmds.objExists(s)])


def add_sdk_driver(drivers=None):
    sdk_node = get_sdk_node()
    if sdk_node is None:
        return

    data = json.loads(cmds.getAttr(f"{sdk_node}._data"))

    if drivers is None:
        drivers = []
        main_objects = cmds.channelBox(
            "mainChannelBox", query=True, mainObjectList=True
        )
        main_object = main_objects[0] if main_objects else None
        attributes = (
            cmds.channelBox("mainChannelBox", query=True, selectedMainAttributes=True)
            or []
        )
        drivers.extend([f"{main_object}.{attr}" for attr in attributes])
        shape_objects = cmds.channelBox(
            "mainChannelBox", query=True, shapeObjectList=True
        )
        shape_object = shape_objects[0] if shape_objects else None
        attributes = (
            cmds.channelBox("mainChannelBox", query=True, selectedShapeAttributes=True)
            or []
        )
        drivers.extend([f"{shape_object}.{attr}" for attr in attributes])
        history_objects = cmds.channelBox(
            "mainChannelBox", query=True, historyObjectList=True
        )
        history_object = history_objects[0] if history_objects else None
        attributes = (
            cmds.channelBox(
                "mainChannelBox", query=True, selectedHistoryAttributes=True
            )
            or []
        )
        drivers.extend([f"{history_object}.{attr}" for attr in attributes])
        drivers = [d for d in drivers if cmds.objExists(d)]

    if not drivers:
        return logger.warning(
            "추가할 driver 가 존재하지 않습니다. channelBox 에서 선택해주세요."
        )

    for driver in drivers.copy():
        if driver in data["sdk"].keys():
            logger.warning(f"{driver} 이 이미 존재합니다.")
            drivers.remove(driver)

    data["sdk"].update({driver: {"driven": [], "fcurve": []} for driver in drivers})

    cmds.setAttr(f"{sdk_node}._data", json.dumps(data), type="string")


def remove_sdk_driver(drivers):
    sdk_node = get_sdk_node()
    if sdk_node is None:
        return

    data = json.loads(cmds.getAttr(f"{sdk_node}._data"))

    for driver in drivers:
        if driver not in data["sdk"]:
            return logger.warning(f"{driver} 가 존재하지 않습니다.")

    remove_list = []
    for driver in drivers:
        anim_curves = anim.get_fcurve(driver)
        if not anim_curves:
            logger.warning(f"{driver} 에 연결된 fcurve 노드가 없습니다.")
            continue
        for anim_curve in anim_curves:
            driven = anim.get_driven(anim_curve)
            if not driven:
                logger.warning(f"{anim_curve} 연결이 끊긴 fcurve 노드가 있습니다.")
                continue
            node, attr = driven.split(".")
            short_name = cmds.attributeQuery(attr, node=node, shortName=True)
            if f"{node}.{short_name}" in data["sdk"][driver]["driven"]:
                remove_list.append(anim_curve)
    if remove_list:
        cmds.delete(remove_list)
    for driver in drivers:
        if driver in data["sdk"]:
            del data["sdk"][driver]

    cmds.setAttr(f"{sdk_node}._data", json.dumps(data), type="string")


def mirror_sdk_driver(drivers):
    sdk_node = get_sdk_node()
    if sdk_node is None:
        return

    data = json.loads(cmds.getAttr(f"{sdk_node}._data"))

    for driver in drivers:
        if len(driver.split("_")) < 2:
            continue

        _, side, *_ = driver.split("_")
        if not side.startswith(left) and not side.startswith(right):
            logger.warning(f"{driver} 는 Mirror 할 수 없습니다.")
            continue

        mirror_side = f"_{right}" if side.startswith(left) else f"_{left}"
        side = f"_{side[0]}"

        # mirror data["sdk"][driver]
        mirror_driver = driver.replace(side, mirror_side)
        mirror_data = {
            "driven": [
                d.replace(side, mirror_side)
                for d in data["sdk"][driver]["driven"]
                if cmds.objExists(d.replace(side, mirror_side))
            ],
            "fcurve": [],
        }
        data["sdk"][mirror_driver] = mirror_data
        cmds.setAttr(f"{sdk_node}._data", json.dumps(data), type="string")

        trs_attrs = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]
        orientation_multiple = [-1, 1, 1, 1, -1, -1, 1, 1, 1]
        behavior_multiple = [-1, -1, -1, 1, 1, 1, 1, 1, 1]
        inverse_scale_multiple = [1, 1, 1, 1, 1, 1, 1, 1, 1]

        # anim curve mirror
        anim_curves = anim.get_fcurve(driver)
        if not anim_curves:
            continue

        for anim_curve in anim_curves:
            # static fcurve 는 제외
            if anim.is_static(anim_curve):
                continue

            anim_data = anim.serialize_fcurve(anim_curve)
            driven = anim_data["driven"]

            # driven 이 없는 fcurve 는 제외
            if not driven:
                continue

            # driven 이 sdk 에 등록되어 있지 않으면 제외
            mirror_driven = driven.replace(side, mirror_side)
            node, attr = mirror_driven.split(".")
            short_name = cmds.attributeQuery(attr, node=node, shortName=True)
            if f"{node}.{short_name}" not in data["sdk"][mirror_driver]["driven"]:
                continue

            # driven mirror
            driven_mirror_type = None
            if cmds.objExists(f"{node}.mirror_type"):
                driven_mirror_type = cmds.getAttr(f"{node}.mirror_type")

            value_multiple = 1
            if short_name in trs_attrs and driven_mirror_type is not None:
                index = trs_attrs.index(short_name)
                if driven_mirror_type == 0:  # orientation
                    multiple_list = orientation_multiple
                elif driven_mirror_type == 1:  # behavior
                    multiple_list = behavior_multiple
                elif driven_mirror_type == 2:  # inverseScale
                    multiple_list = inverse_scale_multiple
                value_multiple = multiple_list[index]

            # driver mirror
            driver_mirror_type = None
            driver_node, driver_attr = driver.split(".")
            short_name = cmds.attributeQuery(
                driver_attr, node=driver_node, shortName=True
            )
            if cmds.objExists(f"{driver_node}.mirror_type"):
                driver_mirror_type = cmds.getAttr(f"{driver_node}.mirror_type")

            float_multiple = 1
            if short_name in trs_attrs and driver_mirror_type is not None:
                index = trs_attrs.index(short_name)
                if driver_mirror_type == 0:  # orientation
                    multiple_list = orientation_multiple
                elif driver_mirror_type == 1:  # behavior
                    multiple_list = behavior_multiple
                elif driver_mirror_type == 2:  # inverseScale
                    multiple_list = inverse_scale_multiple
                float_multiple = multiple_list[index]

            mirror_anim_curve = anim.deserialize_fcurve(
                anim_data, custom_driver=mirror_driver, custom_driven=mirror_driven
            )
            if float_multiple != 1:
                cmds.scaleKey(mirror_anim_curve, floatScale=-1, floatPivot=0)
            if value_multiple != 1:
                cmds.scaleKey(mirror_anim_curve, valueScale=-1, valuePivot=0)


def add_sdk_driven(driver, drivens=None):
    sdk_node = get_sdk_node()
    if sdk_node is None:
        return

    data = json.loads(cmds.getAttr(f"{sdk_node}._data"))

    if drivens is None:
        drivens = []
        main_objects = (
            cmds.channelBox("mainChannelBox", query=True, mainObjectList=True) or []
        )
        attributes = (
            cmds.channelBox("mainChannelBox", query=True, selectedMainAttributes=True)
            or []
        )
        for main_object in main_objects:
            drivens.extend([f"{main_object}.{attr}" for attr in attributes])
        shape_objects = (
            cmds.channelBox("mainChannelBox", query=True, shapeObjectList=True) or []
        )
        attributes = (
            cmds.channelBox("mainChannelBox", query=True, selectedShapeAttributes=True)
            or []
        )
        for shape_object in shape_objects:
            drivens.extend([f"{shape_object}.{attr}" for attr in attributes])
        history_objects = (
            cmds.channelBox("mainChannelBox", query=True, historyObjectList=True) or []
        )
        attributes = (
            cmds.channelBox(
                "mainChannelBox", query=True, selectedHistoryAttributes=True
            )
            or []
        )
        for history_object in history_objects:
            drivens.extend([f"{history_object}.{attr}" for attr in attributes])
        drivens = [d for d in drivens if cmds.objExists(d)]

    if not drivens:
        return logger.warning(
            "추가할 driven 가 존재하지 않습니다. channelBox 에서 선택해주세요."
        )

    for driven in drivens.copy():
        if driven in data["sdk"][driver]["driven"]:
            logger.warning(f"{driven} 이 이미 존재합니다.")
            drivens.remove(driven)

    data["sdk"][driver]["driven"].extend(drivens)

    cmds.setAttr(f"{sdk_node}._data", json.dumps(data), type="string")


def remove_sdk_driven(driver, drivens):
    sdk_node = get_sdk_node()
    if sdk_node is None:
        return

    data = json.loads(cmds.getAttr(f"{sdk_node}._data"))

    for driven in data["sdk"][driver]["driven"]:
        if driven not in drivens:
            continue

    anim_curves = anim.get_fcurve(driver)
    if not anim_curves:
        return logger.warning(f"{driver} 에 연결된 fcurve 노드가 없습니다.")

    remove_list = []
    for anim_curve in anim_curves:
        driven = anim.get_driven(anim_curve)
        if not driven:
            logger.warning(f"{anim_curve} 연결이 끊긴 fcurve 노드가 있습니다.")
            continue
        node, attr = driven.split(".")
        short_name = cmds.attributeQuery(attr, node=node, shortName=True)
        if f"{node}.{short_name}" in drivens:
            remove_list.append(anim_curve)
    if remove_list:
        cmds.delete(remove_list)

    driven_set = set(data["sdk"][driver]["driven"])
    data["sdk"][driver]["driven"] = list(driven_set - set(drivens))

    cmds.setAttr(f"{sdk_node}._data", json.dumps(data), type="string")


def set_key(driver, drivens):
    for driven in drivens:
        cmds.setDrivenKeyframe(driven, currentDriver=driver)


def optimize(drivers):
    sdk_node = get_sdk_node()
    if sdk_node is None:
        return

    data = json.loads(cmds.getAttr(f"{sdk_node}._data"))

    for driver in drivers:
        if driver not in data["sdk"]:
            return logger.warning(f"{driver} 가 존재하지 않습니다.")

    remove_list = []
    for driver in drivers:
        anim_curves = anim.get_fcurve(driver)
        if not anim_curves:
            logger.warning(f"{driver} 에 연결된 fcurve 노드가 없습니다.")
            continue
        for anim_curve in anim_curves:
            if anim.is_static(anim_curve):
                remove_list.append(anim_curve)
    if remove_list:
        cmds.delete(remove_list)


def import_sdk(file_path):
    sdk_node = get_sdk_node()
    if sdk_node:
        return

    file_path = Path(file_path)
    if not file_path.exists():
        return logger.warning(f"경로가 존재하지 않습니다: {file_path}")

    with open(file_path, "r") as f:
        data = json.load(f)

    create_sdk_node()
    add_sdk_control(
        [ctl.removesuffix(f"_{Name.sdk_extension}") for ctl in data["controls"]]
    )
    add_sdk_driver(list(data["sdk"].keys()))
    for driver in data["sdk"].keys():
        add_sdk_driven(driver, data["sdk"][driver]["driven"])

    for driver in data["sdk"].keys():
        for fcurve_data in data["sdk"][driver]["fcurve"]:
            anim.deserialize_fcurve(fcurve_data)


def export_sdk(file_path):
    sdk_node = get_sdk_node()
    if sdk_node is None:
        return

    file_path = Path(file_path)
    if not file_path.parent.exists():
        return logger.warning(f"경로가 존재하지 않습니다: {file_path.parent}")

    data = json.loads(cmds.getAttr(f"{sdk_node}._data"))

    for driver in data["sdk"].keys():
        anim_curves = anim.get_fcurve(driver)
        if not anim_curves:
            continue

        for anim_curve in anim_curves:
            # static fcurve 는 제외
            if anim.is_static(anim_curve):
                continue

            # driven 이 없는 fcurve 는 제외
            driven = anim.get_driven(anim_curve)
            if not driven:
                continue

            # driven 이 sdk 에 등록되어 있지 않으면 제외
            node, attr = driven.split(".")
            short_name = cmds.attributeQuery(attr, node=node, shortName=True)
            if f"{node}.{short_name}" not in data["sdk"][driver]["driven"]:
                continue

            data["sdk"][driver]["fcurve"].append(anim.serialize_fcurve(anim_curve))

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


class SDKManager(QtWidgets.QDialog):

    # 싱글톤 패턴
    _instance = None

    ui_name = "domino_sdk_ui"

    def __init__(self, parent=None):
        super(SDKManager, self).__init__(parent=parent)
        self.current_driver = None
        self.setObjectName(self.ui_name)
        self.setWindowTitle("SDK Manager")
        self.setWindowFlags(
            self.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint
        )

        # Layout
        layout = QtWidgets.QVBoxLayout(self)

        self.menu_bar = QtWidgets.QMenuBar()
        layout.setMenuBar(self.menu_bar)

        # menu
        self.file_menu = self.menu_bar.addMenu("File")
        self.import_sdk_action = QtGui.QAction("Import SDK")
        self.import_sdk_action.triggered.connect(self.import_sdk)
        self.export_sdk_action = QtGui.QAction("Export SDK")
        self.export_sdk_action.triggered.connect(self.export_sdk)
        self.file_menu.addAction(self.import_sdk_action)
        self.file_menu.addAction(self.export_sdk_action)

        # controls
        control_btn_layout = QtWidgets.QVBoxLayout()
        self.add_control_btn = QtWidgets.QPushButton("Add Control")
        self.add_control_btn.clicked.connect(self.add_controls)
        self.remove_control_btn = QtWidgets.QPushButton("Remove Control")
        self.remove_control_btn.clicked.connect(self.remove_controls)
        self.show_control_btn = QtWidgets.QPushButton("Show Control")
        self.show_control_btn.clicked.connect(self.show_controls)
        self.hide_control_btn = QtWidgets.QPushButton("Hide Control")
        self.hide_control_btn.clicked.connect(self.hide_controls)
        control_btn_layout.addWidget(self.add_control_btn)
        control_btn_layout.addWidget(self.remove_control_btn)
        control_btn_layout.addWidget(self.show_control_btn)
        control_btn_layout.addWidget(self.hide_control_btn)
        control_btn_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                20,
                40,
                QtWidgets.QSizePolicy.Policy.Minimum,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        )

        control_widget = QtWidgets.QWidget()
        control_widget.setMaximumHeight(150)
        control_layout = QtWidgets.QHBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 2)
        self.control_list_widget = QtWidgets.QListWidget()
        self.control_list_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.control_list_widget.itemDoubleClicked.connect(
            lambda x: cmds.select(x.text())
        )
        control_layout.addWidget(self.control_list_widget)
        control_layout.addLayout(control_btn_layout)

        layout.addWidget(control_widget)

        # driver / driven

        h_line = QtWidgets.QFrame()
        h_line.setGeometry(QtCore.QRect(170, 160, 118, 3))
        h_line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        h_line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)

        layout.addWidget(h_line)

        driver_widget = QtWidgets.QWidget()
        driver_widget.setMaximumHeight(150)
        driver_layout = QtWidgets.QHBoxLayout(driver_widget)
        driver_layout.setContentsMargins(0, 0, 0, 2)

        driver_list_btn_layout = QtWidgets.QHBoxLayout()

        self.driver_list_widget = QtWidgets.QListWidget()
        self.driver_list_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.driver_list_widget.setMaximumHeight(150)
        self.driver_list_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Maximum
        )
        self.driver_list_widget.itemDoubleClicked.connect(self.set_current_driver)
        self.driver_list_widget.itemClicked.connect(lambda x: cmds.select(x.text()))

        driver_list_btn_layout.addWidget(self.driver_list_widget)

        driver_btn_layout = QtWidgets.QVBoxLayout()

        self.add_driver_btn = QtWidgets.QPushButton("Add Driver")
        self.add_driver_btn.clicked.connect(self.add_driver)
        self.remove_driver_btn = QtWidgets.QPushButton("Remove Driver")
        self.remove_driver_btn.clicked.connect(self.remove_driver)
        self.mirror_driver_btn = QtWidgets.QPushButton("Mirror Driver")
        self.mirror_driver_btn.clicked.connect(self.mirror_driver)
        self.optimize_btn = QtWidgets.QPushButton("Optimize")

        driver_btn_layout.addWidget(self.add_driver_btn)
        driver_btn_layout.addWidget(self.remove_driver_btn)
        driver_btn_layout.addWidget(self.mirror_driver_btn)
        driver_btn_layout.addWidget(self.optimize_btn)
        driver_btn_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                20,
                40,
                QtWidgets.QSizePolicy.Policy.Minimum,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        )

        driver_list_btn_layout.addLayout(driver_btn_layout)
        driver_layout.addLayout(driver_list_btn_layout)
        layout.addWidget(driver_widget)

        sdk_btn_layout = QtWidgets.QVBoxLayout()
        self.set_key_btn = QtWidgets.QPushButton("Set Key")
        self.set_key_btn.clicked.connect(self.set_key)
        self.add_driven_btn = QtWidgets.QPushButton("Add Driven")
        self.add_driven_btn.clicked.connect(self.add_driven)
        self.remove_driven_btn = QtWidgets.QPushButton("Remove Driven")
        self.remove_driven_btn.clicked.connect(self.remove_driven)
        sdk_btn_layout.addWidget(self.set_key_btn)
        sdk_btn_layout.addWidget(self.add_driven_btn)
        sdk_btn_layout.addWidget(self.remove_driven_btn)
        sdk_btn_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                20,
                40,
                QtWidgets.QSizePolicy.Policy.Minimum,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        )

        driven_layout = QtWidgets.QHBoxLayout()

        self.driven_list_widget = QtWidgets.QListWidget()
        self.driven_list_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.driven_list_widget.itemClicked.connect(lambda x: cmds.select(x.text()))
        driven_layout.addWidget(self.driven_list_widget)
        driven_layout.addLayout(sdk_btn_layout)
        layout.addLayout(driven_layout)

        self.refresh_ui()

    def refresh_ui(self):
        self.control_list_widget.clear()
        self.driver_list_widget.clear()
        self.driven_list_widget.clear()

        sdk_node = get_sdk_node()
        if not sdk_node:
            self.current_driver = None
            return

        data = json.loads(cmds.getAttr(f"{sdk_node}._data"))

        for control in data["controls"]:
            item = QtWidgets.QListWidgetItem(control)
            self.control_list_widget.addItem(item)

        for driver in sorted(data["sdk"].keys()):
            item = QtWidgets.QListWidgetItem(driver)
            self.driver_list_widget.addItem(item)
            if self.current_driver == driver:
                item.setBackground(QtGui.QColor("#707070"))
                item.setForeground(QtGui.QColor("#cccccc"))

        if not self.current_driver:
            return

        for driven in data["sdk"][self.current_driver]["driven"]:
            item = QtWidgets.QListWidgetItem(driven)
            self.driven_list_widget.addItem(item)

    def set_current_driver(self):
        index = self.driver_list_widget.currentIndex()
        item = self.driver_list_widget.itemFromIndex(index)

        self.current_driver = item.text()
        self.refresh_ui()

    def add_controls(self):
        try:
            cmds.undoInfo(openChunk=True)
            selected = cmds.ls(selection=True)
            if not selected:
                return
            sdk_node = get_sdk_node()
            if not sdk_node:
                self.refresh_ui()
                sdk_node = create_sdk_node()
            add_sdk_control(selected)

            self.refresh_ui()
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)

    def remove_controls(self):
        try:
            cmds.undoInfo(openChunk=True)
            sdk_node = get_sdk_node()
            if not sdk_node:
                self.refresh_ui()
                return

            items = self.control_list_widget.selectedItems()
            remove_sdk_control(
                [i.text().removesuffix(f"_{Name.sdk_extension}") for i in items]
            )

            self.refresh_ui()
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)

    def show_controls(self):
        try:
            cmds.undoInfo(openChunk=True)
            sdk_node = get_sdk_node()
            if not sdk_node:
                self.refresh_ui()
                return
            selected = cmds.ls(selection=True)

            data = json.loads(cmds.getAttr(f"{sdk_node}._data"))

            for control in data["controls"]:
                for shape in cmds.listRelatives(control, shapes=True) or []:
                    cmds.setAttr(f"{shape}.v", True)
            if selected:
                cmds.select(selected)
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)

    def hide_controls(self):
        try:
            cmds.undoInfo(openChunk=True)
            sdk_node = get_sdk_node()
            if not sdk_node:
                self.refresh_ui()
                return
            selected = cmds.ls(selection=True)

            data = json.loads(cmds.getAttr(f"{sdk_node}._data"))

            for control in data["controls"]:
                for shape in cmds.listRelatives(control, shapes=True) or []:
                    cmds.setAttr(f"{shape}.v", False)
            if selected:
                cmds.select(selected)
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)

    def add_driver(self):
        try:
            cmds.undoInfo(openChunk=True)
            sdk_node = get_sdk_node()
            if not sdk_node:
                self.refresh_ui()
                sdk_node = create_sdk_node()

            add_sdk_driver()

            self.refresh_ui()
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)

    def remove_driver(self):
        try:
            cmds.undoInfo(openChunk=True)
            sdk_node = get_sdk_node()
            if not sdk_node:
                self.refresh_ui()
                return

            items = self.driver_list_widget.selectedItems()
            drivers = [item.text() for item in items]
            remove_sdk_driver(drivers)

            if self.current_driver in drivers:
                self.current_driver = None

            self.refresh_ui()
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)

    def mirror_driver(self):
        try:
            cmds.undoInfo(openChunk=True)
            sdk_node = get_sdk_node()
            if not sdk_node:
                self.refresh_ui()
                return

            items = self.driver_list_widget.selectedItems()
            drivers = [item.text() for item in items]
            mirror_sdk_driver(drivers)

            self.refresh_ui()
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)

    def add_driven(self):
        if not self.current_driver:
            return

        try:
            cmds.undoInfo(openChunk=True)
            sdk_node = get_sdk_node()
            if not sdk_node:
                self.refresh_ui()
                return

            add_sdk_driven(self.current_driver)

            self.refresh_ui()
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)

    def remove_driven(self):
        if not self.current_driver:
            return

        try:
            cmds.undoInfo(openChunk=True)
            sdk_node = get_sdk_node()
            if not sdk_node:
                self.refresh_ui()
                return

            items = self.driven_list_widget.selectedItems()
            drivens = [item.text() for item in items]
            remove_sdk_driven(self.current_driver, drivens)

            self.refresh_ui()
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)

    def set_key(self):
        if not self.current_driver:
            return

        try:
            cmds.undoInfo(openChunk=True)
            sdk_node = get_sdk_node()
            if not sdk_node:
                self.refresh_ui()
                return

            drivens = []
            for i in range(self.driven_list_widget.count()):
                item = self.driven_list_widget.item(i)
                drivens.append(item.text())
            set_key(self.current_driver, drivens)

            self.refresh_ui()
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)

    def optimize_driven(self):
        try:
            cmds.undoInfo(openChunk=True)
            sdk_node = get_sdk_node()
            if not sdk_node:
                self.refresh_ui()
                return

            self.refresh_ui()
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)

    def import_sdk(self):
        try:
            cmds.undoInfo(openChunk=True)
            sdk_node = get_sdk_node()
            if sdk_node:
                logger.warning("이미 SDK 노드가 존재합니다.")
                self.refresh_ui()
                return

            file_path = cmds.fileDialog2(
                dialogStyle=2,
                fileMode=1,
                caption="Import SDK",
                okCaption="Import",
                cancelCaption="Cancel",
                startingDirectory=cmds.workspace(query=True, rootDirectory=True),
                fileFilter="Domino SDK Files (*.sdk)",
            )
            if not file_path:
                return

            import_sdk(file_path[0])
            self.refresh_ui()
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)

    def export_sdk(self):
        sdk_node = get_sdk_node()
        if not sdk_node:
            logger.warning("SDK 노드가 존재하지 않습니다.")
            self.refresh_ui()
            return

        file_path = cmds.fileDialog2(
            dialogStyle=2,
            fileMode=0,
            caption="Export SDK",
            okCaption="Export",
            cancelCaption="Cancel",
            startingDirectory=cmds.workspace(query=True, rootDirectory=True),
            fileFilter="Domino SDK Files (*.sdk)",
        )
        if not file_path:
            return

        export_sdk(file_path[0])
        self.refresh_ui()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
