# maya
from maya import cmds

# built-ins
from functools import partial
from typing import Iterable

ID = "dominoValidationUI"


def show(*args) -> None:
    if cmds.window(ID, query=True, exists=True):
        cmds.deleteUI(ID)
    cmds.workspaceControl(
        ID,
        retain=False,
        floating=True,
        label="Validate Rig Scene",
        uiScript="from domino import validation;validation.ui()",
    )


def ui(*args, **kwargs) -> None:
    layout = cmds.scrollLayout(parent=ID, childResizable=True)

    # total node count
    nodes = list(set(cmds.ls()) - set(cmds.ls(defaultNodes=True)))
    mesh_nodes = len(cmds.ls(type="mesh"))
    cmds.text(f"total node count : {len(nodes)}")
    cmds.text(f"total mesh count : {mesh_nodes}")

    # clashes
    clashes_ins = ValidateClashes()
    clashes_ins.create_ui(layout)
    clashes_ins.is_valid()

    # same name
    same_name_ins = ValidateSameName()
    same_name_ins.create_ui(layout)
    same_name_ins.is_valid()

    # namespace
    namespace_ins = ValidateNamespace()
    namespace_ins.create_ui(layout)
    namespace_ins.is_valid()

    # display layer
    display_layer_ins = ValidateDiaplayLayer()
    display_layer_ins.create_ui(layout)
    display_layer_ins.is_valid()

    # anim layer
    anim_layer_ins = ValidateAnimLayer()
    anim_layer_ins.create_ui(layout)
    anim_layer_ins.is_valid()

    # unknown plug-ins
    unknown_plugin_ins = ValidateUnknownPlugins()
    unknown_plugin_ins.create_ui(layout)
    unknown_plugin_ins.is_valid()

    # unknown nodes
    unknown_node_ins = ValidateUnknownNode()
    unknown_node_ins.create_ui(layout)
    unknown_node_ins.is_valid()

    # expression
    expression_ins = ValidateExpression()
    expression_ins.create_ui(layout)
    expression_ins.is_valid()

    # script
    script_ins = ValidateScript()
    script_ins.create_ui(layout)
    script_ins.is_valid()

    # orig shape
    orig_shape_ins = ValidateOrigShape()
    orig_shape_ins.create_ui(layout)
    orig_shape_ins.is_valid()

    # default controller
    default_value_controller_ins = ValidateController()
    default_value_controller_ins.create_ui(layout)
    default_value_controller_ins.is_valid()

    # keyframe
    keyframe_ins = ValidateKeyframe()
    keyframe_ins.create_ui(layout)
    keyframe_ins.is_valid()

    # groupID, groupParts
    groupID_parts_ins = ValidateGroupIDParts()
    groupID_parts_ins.create_ui(layout)
    groupID_parts_ins.is_valid()

    # validate All
    def validate(ins_list: list, *args) -> None:
        for ins in ins_list:
            ins.is_valid()

    ins_list = []
    for key, value in locals().items():
        if key.endswith("_ins"):
            ins_list.append(value)
    cmds.separator(parent=layout, height=10)
    cmds.button(
        "Validate",
        parent=layout,
        command=partial(validate, ins_list),
    )


class Validate:

    def set_color_frame_layout(self, is_valid: bool, level: int) -> None:
        def set_color_from_level(level: int) -> None:
            if level == 0:
                cmds.frameLayout(
                    self.layout,
                    edit=True,
                    backgroundColor=(0, 1, 0),
                    collapse=True,
                )
            elif level == 1:
                cmds.frameLayout(
                    self.layout,
                    edit=True,
                    backgroundColor=(1, 1, 0),
                    collapse=False,
                )
            elif level == 2:
                cmds.frameLayout(
                    self.layout,
                    edit=True,
                    backgroundColor=(1, 0, 0),
                    collapse=False,
                )

        if is_valid:
            set_color_from_level(level=0)
        else:
            set_color_from_level(level=level)

    def callback_select_items(self, *args) -> None:
        nodes = cmds.textScrollList(self.text_scroll_list, query=True, selectItem=True)
        cmds.select(nodes)

    def _is_valid(self, data: Iterable) -> bool:
        return False if data else True


class ValidateClashes(Validate):
    ui_name = "Validate Clash node"

    def __init__(self):
        self.layout = None
        self.text_scroll_list = None
        self.button = None

    def create_ui(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.ui_name,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 Clash 노드를 검사합니다.")
        self.text_scroll_list = cmds.textScrollList(
            selectCommand=self.callback_select_items, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.clean_up)

    def is_valid(self) -> tuple:
        cmds.textScrollList(self.text_scroll_list, edit=True, removeAll=True)
        nodes = cmds.ls("clash*") + cmds.ls("*:clash*")
        is_valid = self._is_valid(nodes)

        if not self.layout:
            return is_valid, nodes

        self.set_color_frame_layout(is_valid, 2)

        for node in nodes:
            cmds.textScrollList(self.text_scroll_list, edit=True, append=node)
        return is_valid, nodes

    def clean_up(self, *args) -> None:
        all_items = cmds.textScrollList(
            self.text_scroll_list, query=True, allItems=True
        )
        if all_items:
            cmds.delete(all_items)
        self.is_valid()


class ValidateSameName(Validate):
    ui_name = "Validate Same name"

    def __init__(self):
        self.layout = None
        self.text_scroll_list = None
        self.button = None

    def create_ui(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.ui_name,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 같은 이름의 노드를 검사합니다.")
        self.text_scroll_list = cmds.textScrollList(
            selectCommand=self.callback_select_items, allowMultiSelection=True
        )
        self.button = cmds.button("is valid?", command=self.is_valid)

    def is_valid(self, *args) -> tuple:
        cmds.textScrollList(self.text_scroll_list, edit=True, removeAll=True)
        nodes = []
        for node in cmds.ls():
            if "|" in node:
                nodes.append(node)
        is_valid = self._is_valid(nodes)

        if not self.layout:
            return is_valid, nodes

        self.set_color_frame_layout(is_valid, 2)

        for node in nodes:
            cmds.textScrollList(self.text_scroll_list, edit=True, append=node)
        return is_valid, nodes


class ValidateNamespace(Validate):
    ui_name = "Validate Namespace"

    def __init__(self):
        self.layout = None
        self.tree_view = None
        self.button = None

    def create_ui(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.ui_name,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 namespace 를 검사합니다.")
        self.tree_view = cmds.treeView(parent=self.layout, height=80)
        self.button = cmds.button("Cleaning", command=partial(self.clean_up))

    def get_namespace_hierarchy(self, parent: str = ":") -> dict:
        data = {parent: {}}
        for ns in cmds.namespaceInfo(parent, listOnlyNamespaces=True) or []:
            data[parent][ns] = self.get_namespace_hierarchy(ns)[ns]
        return data

    def populate_namespace(self, data, parent=":"):
        for key, value in data.items():
            label = key.split(":")[-1]
            cmds.treeView(self.tree_view, edit=True, addItem=(key, parent))
            cmds.treeView(self.tree_view, edit=True, displayLabel=(key, label))
            self.populate_namespace(value, key)

    def is_valid(self, *args) -> tuple:
        cmds.treeView(self.tree_view, edit=True, removeAll=True)

        hierarchy = self.get_namespace_hierarchy()
        hierarchy[":"].pop("UI", None)
        hierarchy[":"].pop("shared", None)
        is_valid = self._is_valid(hierarchy[":"])

        if not self.layout:
            return is_valid, hierarchy

        self.set_color_frame_layout(is_valid, 2)

        self.populate_namespace(hierarchy)
        return is_valid, hierarchy

    def clean_up(self, *args) -> None:
        hierarchy = self.get_namespace_hierarchy()
        hierarchy[":"].pop("UI", None)
        hierarchy[":"].pop("shared", None)

        cmds.namespace(setNamespace=":")

        def remove_namespace(data):
            for key, value in data.items():
                remove_namespace(value)
                if key != ":":
                    cmds.namespace(removeNamespace=key, mergeNamespaceWithRoot=True)

        remove_namespace(hierarchy)
        self.is_valid()


class ValidateDiaplayLayer(Validate):
    ui_name = "Validate Display layer"

    def __init__(self):
        self.layout = None
        self.text_scroll_list = None
        self.button = None

    def create_ui(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.ui_name,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 display layer 를 검사합니다.")
        self.text_scroll_list = cmds.textScrollList(
            selectCommand=self.callback_select_items, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.clean_up)

    def is_valid(self, *args) -> tuple:
        cmds.textScrollList(self.text_scroll_list, edit=True, removeAll=True)
        nodes = cmds.ls(type="displayLayer")[1:]
        is_valid = self._is_valid(nodes)

        if not self.layout:
            return is_valid, nodes

        self.set_color_frame_layout(is_valid, 1)

        for node in nodes:
            cmds.textScrollList(self.text_scroll_list, edit=True, append=node)
        return is_valid, nodes

    def clean_up(self, *args) -> None:
        all_items = cmds.textScrollList(
            self.text_scroll_list, query=True, allItems=True
        )
        if all_items:
            cmds.delete(all_items)
        self.is_valid()


class ValidateAnimLayer(Validate):
    ui_name = "Validate Anim layer"

    def __init__(self):
        self.layout = None
        self.text_scroll_list = None
        self.button = None

    def create_ui(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.ui_name,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 anim layer 를 검사합니다.")
        self.text_scroll_list = cmds.textScrollList(
            selectCommand=self.callback_select_items, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.clean_up)

    def is_valid(self, *args) -> tuple:
        cmds.textScrollList(self.text_scroll_list, edit=True, removeAll=True)
        nodes = cmds.ls(type="animLayer")
        is_valid = self._is_valid(nodes)

        if not self.layout:
            return is_valid, nodes

        self.set_color_frame_layout(is_valid, 2)

        for node in nodes:
            cmds.textScrollList(self.text_scroll_list, edit=True, append=node)
        return is_valid, nodes

    def clean_up(self, *args) -> None:
        all_items = cmds.textScrollList(
            self.text_scroll_list, query=True, allItems=True
        )
        if all_items:
            cmds.delete(all_items)
        self.is_valid()


class ValidateUnknownPlugins(Validate):
    ui_name = "Validate Unknown plug-ins"

    def __init__(self):
        self.layout = None
        self.text_scroll_list = None
        self.button = None

    def create_ui(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.ui_name,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 unknown plug-ins 를 검사합니다.")
        self.text_scroll_list = cmds.textScrollList()
        self.button = cmds.button("Cleaning", command=self.clean_up)

    def is_valid(self, *args) -> tuple:
        cmds.textScrollList(self.text_scroll_list, edit=True, removeAll=True)
        plugins = cmds.unknownPlugin(query=True, list=True) or []
        is_valid = self._is_valid(plugins)

        if not self.layout:
            return is_valid, plugins

        self.set_color_frame_layout(is_valid, 2)

        for plugin in plugins:
            cmds.textScrollList(self.text_scroll_list, edit=True, append=plugin)
        return is_valid, plugins

    def clean_up(self, *args) -> None:
        all_items = cmds.textScrollList(
            self.text_scroll_list, query=True, allItems=True
        )
        if all_items:
            cmds.delete(all_items)
        self.is_valid()


class ValidateUnknownNode(Validate):
    ui_name = "Validate Unknown node"

    def __init__(self):
        self.layout = None
        self.text_scroll_list = None
        self.button = None

    def create_ui(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.ui_name,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 unknown node 를 검사합니다.")
        self.text_scroll_list = cmds.textScrollList(
            selectCommand=self.callback_select_items, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.clean_up)

    def is_valid(self, *args) -> tuple:
        cmds.textScrollList(self.text_scroll_list, edit=True, removeAll=True)
        nodes = (
            cmds.ls(type="unknown")
            + cmds.ls(type="unknownDag")
            + cmds.ls(type="unknownTransform")
        )
        is_valid = self._is_valid(nodes)

        if not self.layout:
            return is_valid, nodes

        self.set_color_frame_layout(is_valid, 2)

        for node in nodes:
            cmds.textScrollList(self.text_scroll_list, edit=True, append=node)
        return is_valid, nodes

    def clean_up(self, *args) -> None:
        all_items = cmds.textScrollList(
            self.text_scroll_list, query=True, allItems=True
        )
        if all_items:
            cmds.delete(all_items)
        self.is_valid()


class ValidateExpression(Validate):
    ui_name = "Validate Expression"

    def __init__(self):
        self.layout = None
        self.text_scroll_list = None
        self.button = None

    def create_ui(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.ui_name,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 expression 를 검사합니다.")
        self.text_scroll_list = cmds.textScrollList(
            selectCommand=self.callback_select_items, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.clean_up)

    def is_valid(self, *args) -> tuple:
        cmds.textScrollList(self.text_scroll_list, edit=True, removeAll=True)
        expression = cmds.ls(type="expression")
        is_valid = self._is_valid(expression)

        if not self.layout:
            return is_valid, expression

        self.set_color_frame_layout(is_valid, 1)

        for exp in expression:
            cmds.textScrollList(self.text_scroll_list, edit=True, append=exp)
        return is_valid, expression

    def clean_up(self, *args) -> None:
        all_items = cmds.textScrollList(
            self.text_scroll_list, query=True, allItems=True
        )
        if all_items:
            cmds.delete(all_items)
        self.is_valid()


class ValidateScript(Validate):
    ui_name = "Validate Script node"

    def __init__(self):
        self.layout = None
        self.text_scroll_list = None
        self.button = None

    def create_ui(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.ui_name,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 script node 를 검사합니다.")
        self.text_scroll_list = cmds.textScrollList(
            selectCommand=self.callback_select_items, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.clean_up)

    def is_valid(self, *args) -> tuple:
        cmds.textScrollList(self.text_scroll_list, edit=True, removeAll=True)
        nodes = cmds.ls(type="script")
        is_valid = self._is_valid(nodes)

        if not self.layout:
            return is_valid, nodes

        self.set_color_frame_layout(is_valid, 1)

        for node in nodes:
            cmds.textScrollList(self.text_scroll_list, edit=True, append=node)
        return is_valid, nodes

    def clean_up(self, *args) -> None:
        all_items = cmds.textScrollList(
            self.text_scroll_list, query=True, allItems=True
        )
        if all_items:
            cmds.delete(all_items)
        self.is_valid()


class ValidateOrigShape(Validate):
    ui_name = "Validate Orig shape"

    def __init__(self):
        self.layout = None
        self.text_scroll_list = None
        self.button = None

    def create_ui(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.ui_name,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 Orig shape 를 검사합니다.")
        self.text_scroll_list = cmds.textScrollList(
            selectCommand=self.callback_select_items, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.clean_up)

    def is_valid(self, *args) -> tuple:
        cmds.textScrollList(self.text_scroll_list, edit=True, removeAll=True)
        nodes = [
            x
            for x in cmds.ls("*Orig*", type="mesh", intermediateObjects=True)
            + cmds.ls("*Orig*", type="nurbsCurve", intermediateObjects=True)
            + cmds.ls("*Orig*", type="nurbsSurface", intermediateObjects=True)
            if not x.endswith("Orig")
        ]
        is_valid = self._is_valid(nodes)

        if not self.layout:
            return is_valid, nodes

        self.set_color_frame_layout(is_valid, 2)

        for node in nodes:
            cmds.textScrollList(self.text_scroll_list, edit=True, append=node)
        return is_valid, nodes

    def clean_up(self, *args) -> None:
        all_items = cmds.textScrollList(
            self.text_scroll_list, query=True, allItems=True
        )
        if all_items:
            cmds.delete(all_items)
        self.is_valid()


class ValidateController(Validate):
    ui_name = "Validate Controller"

    tr = (
        ".tx",
        ".ty",
        ".tz",
        ".rx",
        ".ry",
        ".rz",
        ".shearXY",
        ".shearXZ",
        ".shearYZ",
    )
    s = [".sx", ".sy", ".sz"]

    def __init__(self):
        self.layout = None
        self.text_scroll_list = None
        self.button = None

    def create_ui(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.ui_name,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 controller default value 를 검사합니다.")
        self.text_scroll_list = cmds.textScrollList(
            selectCommand=self.callback_select_items, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.clean_up)

    def is_valid(self, *args) -> tuple:
        cmds.textScrollList(self.text_scroll_list, edit=True, removeAll=True)
        controllers = cmds.controller(query=True, allControllers=True)

        result = []
        for ctl in controllers:
            keyable = cmds.listAttr(ctl, userDefined=True, keyable=True) or []
            channelbox = cmds.listAttr(ctl, userDefined=True, channelBox=True) or []
            for attr in self.tr:
                if cmds.getAttr(ctl + attr) != 0.0:
                    result.append(ctl + attr)
            for attr in self.s:
                if cmds.getAttr(ctl + attr) != 1.0:
                    result.append(ctl + attr)
            attrs = keyable + channelbox
            for attr in ["." + x for x in attrs]:
                default_value = cmds.addAttr(ctl + attr, query=True, defaultValue=True)
                if default_value != cmds.getAttr(ctl + attr):
                    result.append(ctl + attr)
        is_valid = self._is_valid(result)

        if not self.layout:
            return is_valid, result

        self.set_color_frame_layout(is_valid, 2)

        for attr in result:
            cmds.textScrollList(self.text_scroll_list, edit=True, append=attr)
        return is_valid, result

    def clean_up(self, *args) -> None:
        items = cmds.textScrollList(self.text_scroll_list, query=True, selectItem=True)
        for attr in items:
            if "." + attr.split(".")[-1] in self.tr:
                cmds.setAttr(attr, 0.0)
            elif "." + attr.split(".")[-1] in self.s:
                cmds.setAttr(attr, 1.0)
            else:
                default_value = cmds.addAttr(attr, query=True, defaultValue=True)
                cmds.setAttr(attr, default_value)
        self.is_valid()


class ValidateKeyframe(Validate):
    ui_name = "Validate Keyframe"

    def __init__(self):
        self.layout = None
        self.text_scroll_list = None
        self.button = None

    def create_ui(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.ui_name,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 keyframe 를 검사합니다.")
        self.text_scroll_list = cmds.textScrollList(
            selectCommand=self.callback_select_items, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.clean_up)

    def is_valid(self, *args) -> tuple:
        cmds.textScrollList(self.text_scroll_list, edit=True, removeAll=True)
        translate = cmds.ls(type="animCurveTL")
        rotate = cmds.ls(type="animCurveTA")
        scale = cmds.ls(type="animCurveTU")
        nodes = translate + rotate + scale
        is_valid = self._is_valid(nodes)

        if not self.layout:
            return is_valid, nodes

        self.set_color_frame_layout(is_valid, 2)

        for node in nodes:
            cmds.textScrollList(self.text_scroll_list, edit=True, append=node)
        return is_valid, nodes

    def clean_up(self, *args) -> None:
        all_items = cmds.textScrollList(
            self.text_scroll_list, query=True, allItems=True
        )
        if all_items:
            cmds.delete(all_items)
        self.is_valid()


class ValidateGroupIDParts(Validate):
    ui_name = "Validate GroupID, GroupParts"

    def __init__(self):
        self.layout = None
        self.text_scroll_list = None
        self.button = None

    def create_ui(self, parent: str) -> None:
        self.layout = cmds.frameLayout(
            parent=parent,
            collapsable=True,
            label=self.ui_name,
            backgroundShade=True,
        )
        cmds.text("Scene 내 의 groupId, groupParts 를 검사합니다.")
        self.text_scroll_list = cmds.textScrollList(
            selectCommand=self.callback_select_items, allowMultiSelection=True
        )
        self.button = cmds.button("Cleaning", command=self.clean_up)

    def is_valid(self, *args) -> tuple:
        cmds.textScrollList(self.text_scroll_list, edit=True, removeAll=True)
        nodes = []
        for node in cmds.ls(type="groupId") + cmds.ls(type="groupParts"):
            connections = (
                cmds.listConnections(node, source=True, destination=True) or []
            )
            if not connections:
                nodes.append(node)
        is_valid = self._is_valid(nodes)

        if not self.layout:
            return is_valid, nodes

        self.set_color_frame_layout(is_valid, 2)

        for node in nodes:
            cmds.textScrollList(self.text_scroll_list, edit=True, append=node)
        return is_valid, nodes

    def clean_up(self, *args) -> None:
        all_items = cmds.textScrollList(
            self.text_scroll_list, query=True, allItems=True
        )
        if all_items:
            cmds.delete(all_items)
        self.is_valid()
