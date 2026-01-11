# maya
from maya import cmds
from maya import mel
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

# built-ins
import json

# gui
from PySide6 import QtWidgets, QtCore, QtGui

# domino
from domino.core.utils import logger

DYNAMIC_MANAGER = "dynamic_manager"


def initialize():
    if not cmds.objExists(DYNAMIC_MANAGER):
        cmds.createNode("transform", name=DYNAMIC_MANAGER)
        cmds.addAttr(DYNAMIC_MANAGER, longName="_data", dataType="string")
        set_data({})


def get_data(namespace=""):
    return json.loads(cmds.getAttr(f"{namespace}:{DYNAMIC_MANAGER}._data"))


def set_data(data):
    try:
        cmds.undoInfo(stateWithoutFlush=False)
        cmds.setAttr(f"{DYNAMIC_MANAGER}._data", json.dumps(data), type="string")
    except Exception as e:
        logger.error(e, exc_info=True)
    finally:
        cmds.undoInfo(stateWithoutFlush=True)


def add_envelope(envelope_attr, solver=[]):
    if not cmds.objExists(DYNAMIC_MANAGER):
        initialize()

    data = get_data()
    data[envelope_attr] = {"solver": solver, "target_controllers": []}
    set_data(data)


def replace_target_controllers(envelope_attr, controllers):
    if not cmds.objExists(DYNAMIC_MANAGER):
        return

    data = get_data()
    if envelope_attr not in data:
        return
    data[envelope_attr]["target_controllers"] = controllers
    set_data(data)


def add_collide(solvers, meshes):
    for solver in solvers:
        for mesh in meshes:
            temp_shape = cmds.polyCube(constructionHistory=False)[0]
            cmds.connectAttr(f"{mesh}.worldMesh[0]", f"{temp_shape}.inMesh")
            dup_mesh = cmds.duplicate(temp_shape, name=f"{solver}_{mesh}_collide")[0]
            dup_mesh = cmds.parent(dup_mesh, mesh)[0]
            cmds.setAttr(f"{dup_mesh}.t", 0, 0, 0)
            cmds.setAttr(f"{dup_mesh}.r", 0, 0, 0)
            cmds.setAttr(f"{dup_mesh}.s", 1, 1, 1)
            cmds.delete(temp_shape)
            cmds.connectAttr(f"{mesh}.worldMesh[0]", f"{dup_mesh}.inMesh")
            cmds.select([solver, dup_mesh])
            rigids = mel.eval("makeCollideNCloth")
            rigids = [cmds.listRelatives(r, parent=True)[0] for r in rigids]
            cmds.parent(rigids, mesh)
            cmds.hide(dup_mesh)


def add_volume_axis(envelope_attrs, namespace):
    data = get_data(namespace)

    solvers = []
    for attr in envelope_attrs:
        solvers.extend([f"{namespace}:{s}" for s in data[attr]["solver"]])

    hair_systems = []
    n_clothes = []
    for solver in solvers:
        hair_systems.extend(
            cmds.listConnections(
                solver, source=True, destination=True, type="hairSystem"
            )
            or []
        )
        n_clothes.extend(
            cmds.listConnections(solver, source=True, destination=True, type="nCloth")
            or []
        )
    # TODO controller 로 편의성 증가
    volume_axis = cmds.volumeAxis(
        position=(0, 0, 0),
        magnitude=5,
        attenuation=0,
        invertAttenuation=0,
        awayFromCenter=1,
        awayFromAxis=1,
        aroundAxis=0,
        alongAxis=0,
        directionalSpeed=0,
        directionX=1,
        directionY=0,
        directionZ=0,
        turbulence=0,
        turbulenceSpeed=0.2,
        turbulenceFrequencyX=1,
        turbulenceFrequencyY=1,
        turbulenceFrequencyZ=1,
        turbulenceOffsetX=0,
        turbulenceOffsetY=0,
        turbulenceOffsetZ=0,
        detailTurbulence=0,
        maxDistance=-1,
        volumeShape="cube",
        volumeOffset=(0, 0, 0),
        volumeSweep=360,
        torusSectionRadius=0.5,
    )[0]
    cmds.connectDynamic(hair_systems + n_clothes, fields=volume_axis)
    cmds.connectAttr("time1.outTime", f"{volume_axis}.time")

    # parallel 에서 특정 hair가 작동하지 않음. DG로 변경해서 평가 후 parallel 로 변경
    original_mode = cmds.evaluationManager(query=True, mode=True)[0]
    cmds.evaluationManager(mode="off")
    original_values = []
    for attr in envelope_attrs:
        original_values.append(cmds.getAttr(f"{namespace}:{attr}"))
        cmds.setAttr(f"{namespace}:{attr}", 1)
    current_time = cmds.currentTime(query=True)
    min_time = cmds.playbackOptions(query=True, minTime=True)
    cmds.currentTime(min_time)
    cmds.currentTime(min_time + 1)
    cmds.evaluationManager(mode=original_mode)
    for attr in envelope_attrs:
        cmds.setAttr(f"{namespace}:{attr}", 0)
    cmds.currentTime(current_time)
    for attr, value in zip(envelope_attrs, original_values):
        cmds.setAttr(f"{namespace}:{attr}", value)


def bake_dynamic(envelope_attrs, start_frame, end_frame, target_controllers):
    for attr in envelope_attrs:
        cmds.setAttr(attr, 1)

    locs = []
    constraints = []
    bake_grp = cmds.createNode("transform", name="bake_grp")
    for ctl in target_controllers:
        loc = cmds.createNode("transform", parent=bake_grp)
        cons = cmds.parentConstraint(ctl, loc)[0]
        locs.append(loc)
        constraints.append(cons)

    cmds.bakeResults(
        locs,
        simulation=True,
        t=(start_frame, end_frame),
        sampleBy=1,
        oversamplingRate=1,
        disableImplicitControl=True,
        preserveOutsideKeys=True,
        sparseAnimCurveBake=False,
        removeBakedAttributeFromLayer=False,
        removeBakedAnimFromLayer=False,
        bakeOnOverrideLayer=False,
        minimizeRotation=True,
        at=("tx", "ty", "tz", "rx", "ry", "rz"),
    )

    for attr in envelope_attrs:
        cmds.setAttr(attr, 0)

    cmds.delete(constraints)
    for loc, ctl in zip(locs, target_controllers):
        cons = cmds.parentConstraint(loc, ctl)

    cmds.bakeResults(
        target_controllers,
        simulation=True,
        t=(start_frame, end_frame),
        sampleBy=1,
        oversamplingRate=1,
        disableImplicitControl=True,
        preserveOutsideKeys=True,
        sparseAnimCurveBake=False,
        removeBakedAttributeFromLayer=False,
        removeBakedAnimFromLayer=False,
        bakeOnOverrideLayer=True,
        minimizeRotation=True,
        at=("tx", "ty", "tz", "rx", "ry", "rz"),
    )
    cmds.delete(bake_grp)


def import_dynamic(file_path):
    if not cmds.objExists(DYNAMIC_MANAGER):
        initialize()

    with open(file_path, "r") as f:
        data = json.load(f)

    set_data(data)
    logger.info(f"Import Dynamic RelationShip : {file_path}")


def export_dynamic(file_path):
    if not cmds.objExists(DYNAMIC_MANAGER):
        return
    data = get_data()

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Export Dynamic RelationShip : {file_path}")


class DynamicManager(MayaQWidgetDockableMixin, QtWidgets.QDialog):

    # 싱글톤 패턴
    _instance = None

    ui_name = "domino_dynamic_ui"

    def __init__(self, parent=None):
        super(DynamicManager, self).__init__(parent=parent)
        self.current_intp = None
        self.setObjectName(self.ui_name)
        self.setWindowTitle("Dynamic Manager")
        self.setWindowFlags(
            self.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint
        )

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        # menu
        self.menu_bar = QtWidgets.QMenuBar()
        layout.setMenuBar(self.menu_bar)

        self.file_menu = self.menu_bar.addMenu("File")
        self.import_dynamic_action = QtGui.QAction("Import Dynamic Relationship")
        self.import_dynamic_action.triggered.connect(self.import_dynamic)
        self.export_dynamic_action = QtGui.QAction("Export Dynamic Relationship")
        self.export_dynamic_action.triggered.connect(self.export_dynamic)
        self.file_menu.addAction(self.import_dynamic_action)
        self.file_menu.addAction(self.export_dynamic_action)

        self.envelope_list_widget = QtWidgets.QListWidget()
        self.envelope_list_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.envelope_list_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        layout.addWidget(self.envelope_list_widget)

        btn_layout = QtWidgets.QVBoxLayout()
        self.add_envelope_btn = QtWidgets.QPushButton("Add Envelope")
        self.add_envelope_btn.clicked.connect(self.add_envelope)
        self.add_envelope_btn.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.remove_envelope_btn = QtWidgets.QPushButton("Remove Envelope")
        self.remove_envelope_btn.clicked.connect(self.remove_envelope)
        self.remove_envelope_btn.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.replace_target_ctl_btn = QtWidgets.QPushButton(
            "Replace Target Controllers"
        )
        self.replace_target_ctl_btn.clicked.connect(self.replace_target_controllers)
        self.replace_target_ctl_btn.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.select_target_ctl_btn = QtWidgets.QPushButton("Select Target Controllers")
        self.select_target_ctl_btn.clicked.connect(self.select_target_controllers)
        self.select_target_ctl_btn.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        btn_layout.addWidget(self.add_envelope_btn)
        btn_layout.addWidget(self.remove_envelope_btn)
        btn_layout.addWidget(self.replace_target_ctl_btn)
        btn_layout.addWidget(self.select_target_ctl_btn)
        btn_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                20,
                40,
                QtWidgets.QSizePolicy.Policy.Minimum,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        )
        layout.addLayout(btn_layout)
        self.refresh()
        self.resize(350, 200)

    def refresh(self):
        self.envelope_list_widget.clear()
        if not cmds.objExists(DYNAMIC_MANAGER):
            return

        data = get_data()
        for envelope_attr in data.keys():
            self.envelope_list_widget.addItem(envelope_attr)

    def add_envelope(self):
        main_objects = cmds.channelBox(
            "mainChannelBox", query=True, mainObjectList=True
        )
        attributes = cmds.channelBox(
            "mainChannelBox", query=True, selectedMainAttributes=True
        )
        if not main_objects or not attributes:
            return logger.warning("채널박스에서 envelope attribute 를 선택해주세요.")
        envelope_attr = f"{main_objects[0]}.{attributes[0]}"
        nucleus = (
            cmds.listConnections(
                envelope_attr, source=False, destination=True, type="nucleus"
            )
            or []
        )
        add_envelope(envelope_attr, solver=nucleus)
        self.refresh()

    def remove_envelope(self):
        selected_items = self.envelope_list_widget.selectedItems()
        if not selected_items:
            return logger.warning("제거 할 envelope 을 선택해주세요.")
        data = get_data()
        for item in selected_items:
            envelope_attr = item.text()
            if envelope_attr in data:
                del data[envelope_attr]
        set_data(data)
        self.refresh()

    def replace_target_controllers(self):
        selected_items = self.envelope_list_widget.selectedItems()
        if not selected_items:
            return logger.warning("교체 할 envelope 을 선택해주세요.")

        envelope_attr = selected_items[0].text()
        controllers = cmds.ls(selection=True)
        replace_target_controllers(envelope_attr, controllers)
        self.refresh()

    def select_target_controllers(self):
        selected_items = self.envelope_list_widget.selectedItems()
        if not selected_items:
            return logger.warning("선택 할 envelope 을 선택해주세요.")

        data = get_data()
        cmds.select(data[selected_items[0].text()]["target_controllers"])

    def import_dynamic(self):
        file_path = cmds.fileDialog2(
            caption="Import Dynamic RelationShip",
            startingDirectory=cmds.workspace(query=True, rootDirectory=True),
            fileFilter="Domino Dynamic Files (*.dyn)",
            okCaption="Import",
            cancelCaption="Cancel",
            fileMode=1,
        )
        if file_path:
            try:
                cmds.undoInfo(openChunk=True)
                import_dynamic(file_path[0])
            except Exception as e:
                logger.error(e, exc_info=True)
            finally:
                cmds.undoInfo(closeChunk=True)
            self.refresh()

    def export_dynamic(self):
        file_path = cmds.fileDialog2(
            caption="Export Dynamic RelationShip",
            startingDirectory=cmds.workspace(query=True, rootDirectory=True),
            fileFilter="Domino Dynamic Files (*.dyn)",
            okCaption="Export",
            cancelCaption="Cancel",
            fileMode=0,
        )
        if not file_path:
            return
        export_dynamic(file_path=file_path[0])

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def show_dynamic_tools_ui():

    def _select_bake_controllers(_tree_view, _namespace):
        _items = cmds.treeView(_tree_view, query=True, selectItem=True)
        _controllers = []
        for _item in _items:
            _data = get_data(_namespace)
            _controllers.extend(
                [f"{_namespace}:{_x}" for _x in _data[_item]["target_controllers"]]
            )
        cmds.select(_controllers)

    def _add_collide(_tree_view, _namespace):
        _selected = cmds.ls(selection=True)
        if not _selected:
            return
        _meshes = [
            _y
            for _sel in _selected
            for _y in cmds.listRelatives(_sel, children=True, type="mesh") or []
        ]
        if not _meshes:
            return
        _meshes = [cmds.listRelatives(_m, parent=True)[0] for _m in _meshes]

        _items = cmds.treeView(_tree_view, query=True, selectItem=True) or []
        _data = get_data(_namespace)
        _solvers = []
        for _item in _items:
            _solvers.extend([f"{namespace}:{_s}" for _s in _data[_item]["solver"]])
        add_collide(_solvers, _meshes)

    def _add_volume_axis(_tree_view, _namespace):
        _items = cmds.treeView(_tree_view, query=True, selectItem=True) or []
        add_volume_axis(_items, _namespace)

    def _bake_dynamic(_tree_view, _namespace):
        _items = cmds.treeView(_tree_view, query=True, selectItem=True)
        _controllers = []
        for _item in _items:
            _data = get_data(_namespace)
            _controllers.extend(
                [f"{_namespace}:{_x}" for _x in _data[_item]["target_controllers"]]
            )
        bake_dynamic(
            [f"{namespace}:{_x}" for _x in _items],
            int(cmds.playbackOptions(query=True, minTime=True)),
            int(cmds.playbackOptions(query=True, maxTime=True)),
            _controllers,
        )

    _, namespace = cmds.ls(selection=True, showNamespace=True)
    if namespace == ":":
        namespace = ""

    if not cmds.objExists(f"{namespace}:{DYNAMIC_MANAGER}"):
        return

    window_name = "domino_dynamic_tools_window"
    button_width = 150

    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

    window = cmds.window(
        window_name,
        title=f"Domino Dynamic Tools | {namespace}",
        widthHeight=(400, 280),
        sizeable=True,
    )

    main_form = cmds.formLayout(numberOfDivisions=100)

    data = get_data(namespace)

    left_tree = cmds.treeView(
        numberOfButtons=0,
        attachButtonRight=False,
        allowMultiSelection=True,
        itemDblClickCommand=lambda x: cmds.select(f"{namespace}:{x}"),
    )
    for envelope_attr in data.keys():
        cmds.treeView(left_tree, edit=True, addItem=(envelope_attr, ""))

    right_column = cmds.columnLayout(
        adjustableColumn=False, rowSpacing=6, width=button_width
    )
    cmds.button(
        label="Select Bake Controller",
        width=button_width,
        height=24,
        backgroundColor=[0.3, 0.4, 0.5],
        command=lambda _: _select_bake_controllers(left_tree, namespace),
    )
    cmds.button(
        label="Add Collision",
        width=button_width,
        height=24,
        backgroundColor=[0.3, 0.45, 0.35],
        command=lambda _: _add_collide(left_tree, namespace),
    )
    cmds.button(
        label="Add VolumeAxis",
        width=button_width,
        height=24,
        backgroundColor=[0.5, 0.45, 0.25],
        command=lambda _: _add_volume_axis(left_tree, namespace),
    )
    cmds.button(
        label="Bake Simulation",
        width=button_width,
        height=24,
        backgroundColor=[0.45, 0.3, 0.3],
        command=lambda _: _bake_dynamic(left_tree, namespace),
    )

    cmds.setParent("..")

    cmds.formLayout(
        main_form,
        edit=True,
        attachForm=[
            (left_tree, "top", 10),
            (left_tree, "left", 10),
            (left_tree, "bottom", 10),
            (right_column, "top", 10),
            (right_column, "right", 10),
            (right_column, "bottom", 10),
        ],
        attachControl=[(left_tree, "right", 10, right_column)],
    )

    cmds.showWindow(window)
