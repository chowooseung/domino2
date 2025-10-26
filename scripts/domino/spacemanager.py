# maya
from maya import cmds
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

# Qt
from PySide6 import QtWidgets, QtCore, QtGui

# built-ins
from functools import partial
from pathlib import Path
import json

# domino
from domino.core import left, right
from domino.core.utils import logger

SPACE_MANAGER = "space_manager"
L_MIRROR_TOKEN = f"_{left}"
R_MIRROR_TOKEN = f"_{right}"


CONS_FUNC = [
    cmds.pointConstraint,
    cmds.orientConstraint,
    cmds.parentConstraint,
    cmds.scaleConstraint,
]


def initialize():
    if not cmds.objExists(SPACE_MANAGER):
        cmds.createNode("transform", name=SPACE_MANAGER)
        cmds.addAttr(SPACE_MANAGER, longName="_data", dataType="string")
        set_data([])


def get_data():
    return json.loads(cmds.getAttr(f"{SPACE_MANAGER}._data"))


def set_data(data):
    try:
        cmds.undoInfo(stateWithoutFlush=False)
        cmds.setAttr(f"{SPACE_MANAGER}._data", json.dumps(data), type="string")
    except Exception as e:
        logger.error(e, exc_info=True)
    finally:
        cmds.undoInfo(stateWithoutFlush=True)


def mirror(
    sources,
    destination,
    host,
):
    mirrored_sources = []
    for src in sources:
        if L_MIRROR_TOKEN in src:
            mirrored_sources.append(src.replace(L_MIRROR_TOKEN, R_MIRROR_TOKEN))
        elif R_MIRROR_TOKEN in src:
            mirrored_sources.append(src.replace(R_MIRROR_TOKEN, L_MIRROR_TOKEN))
        else:
            mirrored_sources.append(src)

    mirrored_destination = destination
    if L_MIRROR_TOKEN in destination:
        mirrored_destination = destination.replace(L_MIRROR_TOKEN, R_MIRROR_TOKEN)
    elif R_MIRROR_TOKEN in destination:
        mirrored_destination = destination.replace(R_MIRROR_TOKEN, L_MIRROR_TOKEN)

    mirrored_host = host
    if L_MIRROR_TOKEN in host:
        mirrored_host = host.replace(L_MIRROR_TOKEN, R_MIRROR_TOKEN)
    elif R_MIRROR_TOKEN in host:
        mirrored_host = host.replace(R_MIRROR_TOKEN, L_MIRROR_TOKEN)

    return (
        mirrored_sources,
        mirrored_destination,
        mirrored_host,
    )


def generate():
    try:
        cmds.undoInfo(openChunk=True)
        selected = cmds.ls(selection=True)
        data = get_data()
        for (
            sources,
            destination,
            cons_type,
            attribute_type,
            attribute_name,
            enum_name,
            host,
            default_value,
        ) in data:
            check = False
            if not sources:
                check = True
            for src in sources:
                if not cmds.objExists(src):
                    logger.warning(f"sources `{src}` 가 없습니다.")
                    check = True
            if check:
                continue

            if not cmds.objExists(destination):
                logger.warning(f"destination `{destination}` 가 없습니다.")
                continue

            if not cmds.objExists(host):
                logger.warning(f"host `{host}` 가 없습니다.")
                continue

            if attribute_type == 0:
                if not attribute_name:
                    logger.warning(
                        f"attribute_name `{attribute_name}` 가 유효하지 않습니다."
                    )
                    continue

                for en in enum_name.split(":"):
                    if not en:
                        logger.warning(f"enum name `{en}` 가 유효하지 않습니다.")
                        continue

                if attribute_name in (cmds.listAttr(host, userDefined=True) or []):
                    logger.warning(
                        f"{host}.{attribute_name} 이 이미 존재하기 때문에 삭제 후 생성합니다."
                    )
                    cmds.deleteAttr(host, attribute=attribute_name)
            elif attribute_type == 1:
                for src in sources:
                    if src in (cmds.listAttr(host, userDefined=True) or []):
                        logger.warning(
                            f"{host}.{src} 이 이미 존재하기 때문에 삭제 후 생성합니다."
                        )
                        cmds.deleteAttr(host, attribute=src)

            func = CONS_FUNC[int(cons_type)]

            cons = func(sources, destination, maintainOffset=True)[0]
            alias_list = func(cons, query=True, weightAliasList=True)

            if attribute_type == 0:  # enum
                cmds.addAttr(
                    host,
                    longName=attribute_name,
                    attributeType="enum",
                    enumName=f"local:{enum_name}",
                    keyable=True,
                    defaultValue=int(default_value),
                )
                enum_name_list = enum_name.split(":")
                for i, en in enumerate(enum_name_list):
                    choice = cmds.createNode("choice")
                    cmds.setAttr(f"{choice}.input[0]", False)
                    for x in range(len(enum_name_list)):
                        cmds.setAttr(
                            f"{choice}.input[{x + 1}]", True if i == x else False
                        )
                    cmds.connectAttr(f"{host}.{attribute_name}", f"{choice}.selector")
                    cmds.connectAttr(f"{choice}.output", f"{cons}.{alias_list[i]}")
            elif attribute_type == 1:  # float
                for i, src in enumerate(sources):
                    cmds.addAttr(
                        host,
                        longName=src,
                        attributeType="float",
                        keyable=True,
                        minValue=0,
                        maxValue=1,
                        defaultValue=1,
                    )
                    cmds.connectAttr(f"{host}.{src}", f"{cons}.{alias_list[i]}")
        if selected:
            cmds.select(selected)
    except Exception as e:
        logger.error(e, exc_info=True)
    finally:
        cmds.undoInfo(closeChunk=True)


def rollback():
    try:
        cmds.undoInfo(openChunk=True)
        data = get_data()
        for (
            sources,
            destination,
            cons_type,
            attribute_type,
            attribute_name,
            _,
            host,
            _,
        ) in data:
            # constraint
            func = CONS_FUNC[int(cons_type)]
            cmds.delete(func(destination, query=True))

            # host attribute
            if attribute_type == 0:
                if cmds.objExists(f"{host}.{attribute_name}"):
                    cmds.deleteAttr(host, attribute=attribute_name)
                    logger.info(f"Rollback `{host}.{attribute_name}`")
            elif attribute_type == 1:
                for src in sources:
                    if src in (cmds.listAttr(host, userDefined=True) or []):
                        cmds.deleteAttr(host, attribute=src)
                        logger.info(f"Rollback `{host}.{src}`")
    except Exception as e:
        logger.error(e, exc_info=True)
    finally:
        cmds.undoInfo(closeChunk=True)


def import_space_manager_data(file_path, _generate=True):
    if not Path(file_path).exists():
        return

    if cmds.objExists(SPACE_MANAGER):
        rollback()

    with open(file_path, "r") as f:
        data = json.load(f)

    initialize()
    set_data(data)
    if _generate:
        generate()

    logger.info(f"Import Space Manager File `{file_path}`")


def export_space_manager_data(file_path):
    if not Path(file_path).parent.exists():
        return

    data = get_data()
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    logger.info(f"Export Space Manager File `{file_path}`")


class SpaceManager(MayaQWidgetDockableMixin, QtWidgets.QDialog):

    # 싱글톤 패턴
    _instance = None

    ui_name = "domino_space_manager_ui"

    def __init__(self, parent=None):
        super(SpaceManager, self).__init__(parent=parent)
        self.setObjectName(self.ui_name)
        self.setWindowTitle("Space Manager")
        self.setWindowFlags(
            self.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint
        )

        self.resize(800, 400)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # menu
        self.menu_bar = QtWidgets.QMenuBar()
        layout.setMenuBar(self.menu_bar)

        self.file_menu = self.menu_bar.addMenu("File")
        self.import_space_data_action = QtGui.QAction("Import Space Manager Data")
        self.import_space_data_action.triggered.connect(self.import_sm)
        self.export_space_data_action = QtGui.QAction("Export Space Manager Data")
        self.export_space_data_action.triggered.connect(self.export_sm)
        self.file_menu.addAction(self.import_space_data_action)
        self.file_menu.addAction(self.export_space_data_action)

        self.table_widget = QtWidgets.QTableWidget(0, 8)
        self.table_widget.itemChanged.connect(self.edit_data)
        self.table_widget.setHorizontalHeaderLabels(
            [
                "Source Spaces",
                "Destination Space",
                "Cons Type",
                "Attribute Type",
                "Attribute Name",
                "Enum Name",
                "Host",
                "defaultValue",
            ]
        )
        self.table_widget.verticalHeader().setVisible(False)
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table_widget)

        btn_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(btn_layout)

        self.append_row_btn = QtWidgets.QPushButton("Append Row")
        self.append_row_btn.clicked.connect(self.append_row)
        self.remove_row_btn = QtWidgets.QPushButton("Remove Row")
        self.remove_row_btn.clicked.connect(self.remove_row)
        self.mirror_btn = QtWidgets.QPushButton("Mirror")
        self.mirror_btn.clicked.connect(self.mirror)
        self.generate_btn = QtWidgets.QPushButton("Generate")
        self.generate_btn.clicked.connect(generate)
        self.rollback_btn = QtWidgets.QPushButton("Rollback")
        self.rollback_btn.clicked.connect(rollback)
        btn_layout.addWidget(self.append_row_btn)
        btn_layout.addWidget(self.remove_row_btn)
        btn_layout.addWidget(self.mirror_btn)
        btn_layout.addWidget(self.generate_btn)
        btn_layout.addWidget(self.rollback_btn)

    def edit_data(self, item):
        row, col = item.row(), item.column()
        data = get_data()
        data[row][col] = item.text()
        set_data(data)

    def set_source(self, row):
        selected = cmds.ls(selection=True)
        data = get_data()
        data[row][0] = selected
        set_data(data)
        self.refresh()

    def set_source_menu(self, combobox, row, pos):
        menu = QtWidgets.QMenu(self)
        menu.addAction("Set Source", partial(self.set_source, row))
        menu.exec(combobox.mapToGlobal(pos))

    def set_attribute_type(self, row, index):
        data = get_data()
        data[row][3] = index
        attribute_name_item = self.table_widget.item(row, 4)
        enum_name_item = self.table_widget.item(row, 5)
        if index == 0:
            attribute_name_item.setFlags(
                attribute_name_item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable
            )
            enum_name_item.setFlags(
                enum_name_item.flags() | QtCore.Qt.ItemFlag.ItemIsEditable
            )
        elif index == 1:
            data[row][4] = ""
            data[row][5] = ""
            attribute_name_item.setText("")
            enum_name_item.setText("")
            attribute_name_item.setFlags(
                attribute_name_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable
            )
            enum_name_item.setFlags(
                enum_name_item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable
            )
        set_data(data)

    def set_constraint_type(self, row, index):
        data = get_data()
        data[row][2] = index
        set_data(data)

    def refresh(self):
        self.table_widget.setRowCount(0)
        self.table_widget.blockSignals(True)
        if not cmds.objExists(SPACE_MANAGER):
            self.table_widget.blockSignals(False)
            return
        data = get_data()
        for i, row_data in enumerate(data):
            self.table_widget.insertRow(i)

            source_combobox = QtWidgets.QComboBox()
            source_combobox.setContextMenuPolicy(
                QtCore.Qt.ContextMenuPolicy.CustomContextMenu
            )
            source_combobox.customContextMenuRequested.connect(
                partial(self.set_source_menu, source_combobox, i)
            )
            source_combobox.addItems(row_data[0])

            constraint_type_combobox = QtWidgets.QComboBox()
            constraint_type_combobox.addItems(["points", "orient", "parent", "scale"])
            constraint_type_combobox.setCurrentIndex(row_data[2])
            constraint_type_combobox.currentIndexChanged.connect(
                partial(self.set_constraint_type, i)
            )
            attribute_type_combobox = QtWidgets.QComboBox()
            attribute_type_combobox.addItems(["enum", "float"])
            attribute_type_combobox.setCurrentIndex(row_data[3])
            attribute_type_combobox.currentIndexChanged.connect(
                partial(self.set_attribute_type, i)
            )

            self.table_widget.setCellWidget(i, 0, source_combobox)
            self.table_widget.setItem(i, 1, QtWidgets.QTableWidgetItem(row_data[1]))
            self.table_widget.setCellWidget(i, 2, constraint_type_combobox)
            self.table_widget.setCellWidget(i, 3, attribute_type_combobox)
            self.table_widget.setItem(i, 4, QtWidgets.QTableWidgetItem(row_data[4]))
            self.table_widget.setItem(i, 5, QtWidgets.QTableWidgetItem(row_data[5]))
            self.table_widget.setItem(i, 6, QtWidgets.QTableWidgetItem(row_data[6]))
            self.table_widget.setItem(i, 7, QtWidgets.QTableWidgetItem(row_data[7]))

        self.table_widget.blockSignals(False)

    def append_row(self):
        if not cmds.objExists(SPACE_MANAGER):
            initialize()
        data = get_data()
        data.append([[], "", 0, 0, "", "", "", 0])
        set_data(data)
        self.refresh()

    def remove_row(self):
        selected_rows = sorted(
            set(index.row() for index in self.table_widget.selectedIndexes()),
            reverse=True,
        )

        data = get_data()
        for row in selected_rows:
            data.pop(row)
        set_data(data)
        self.refresh()

    def mirror(self):
        selected_rows = sorted(
            set(index.row() for index in self.table_widget.selectedIndexes()),
            reverse=True,
        )

        data = get_data()
        for row in selected_rows:
            (
                sources,
                destination,
                cons_type,
                attribute_type,
                attribute_name,
                enum_name,
                host,
            ) = data[row]
            mirrored_str = mirror(sources=sources, destination=destination, host=host)
            mirrored_data = [
                mirrored_str[0],
                mirrored_str[1],
                cons_type,
                attribute_type,
                attribute_name,
                enum_name,
                mirrored_str[2],
            ]
            if data[row] != mirrored_data:
                data.append(mirrored_data)
        set_data(data)
        self.refresh()

    def import_sm(self):
        file_path = cmds.fileDialog2(
            caption="Import Space Manager",
            startingDirectory=cmds.workspace(query=True, rootDirectory=True),
            fileFilter="Domino Space Manager Files (*.smf)",
            okCaption="Import",
            cancelCaption="Cancel",
            fileMode=1,
        )

        if file_path:
            try:
                cmds.undoInfo(openChunk=True)
                import_space_manager_data(file_path=file_path[0], _generate=True)
            except Exception as e:
                logger.error(e, exc_info=True)
            finally:
                cmds.undoInfo(closeChunk=True)
            self.refresh()

    def export_sm(self):
        if not cmds.objExists(SPACE_MANAGER):
            return logger.warning(f"{SPACE_MANAGER} 가 존재하지 않습니다.")

        file_path = cmds.fileDialog2(
            caption="Export Space Manager",
            startingDirectory=cmds.workspace(query=True, rootDirectory=True),
            fileFilter="Domino Space Manager Files (*.smf)",
            okCaption="Export",
            cancelCaption="Cancel",
            fileMode=0,
        )
        if file_path:
            export_space_manager_data(file_path=file_path[0])

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def showEvent(self, e):
        super(SpaceManager, self).showEvent(e)
