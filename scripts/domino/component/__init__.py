# domino
from domino.core import Name, Transform, Joint, Controller, Curve, attribute, nurbscurve
from domino.core.utils import build_log, logger

# maya
from maya import cmds
from maya.api import OpenMaya as om  # type: ignore

# built-ins
from typing import TypeVar
import copy
import json
import importlib
import logging

__all__ = [
    "assembly",
    "control01",
    "humanspine01",
    "humanneck01",
    "humanarm01",
    "humanleg01",
    "humanfinger01",
]

GUIDE = "guide"
RIG = "rig"
SKEL = "skel"
ORIGINMATRIX = om.MMatrix()


T = TypeVar("T", bound="Rig")


class Rig(dict):
    """
    Guide Matrix -> Bifrost -> initial Matrix(controller, output_joint) -> outputJoint

    Args:
        dict (_type_): _description_

    Returns:
        _type_: _description_
    """

    @property
    def data(self) -> dict:
        return self

    @data.setter
    def data(self, data: dict) -> None:
        self.clear()
        self.update(data)

    @property
    def parent(self) -> T:
        return self._parent if hasattr(self, "_parent") else None

    @parent.setter
    def parent(self, parent: T) -> None:
        self._parent = parent
        parent.children = self

    @property
    def children(self) -> list:
        return self["children"]

    @children.setter
    def children(self, child: T) -> None:
        self["children"].append(child)

    @property
    def assembly(self) -> T:
        component = self
        while component.parent is not None:
            component = self.parent
        return component

    @property
    def identifier(self) -> tuple:
        return (
            self["name"]["value"],
            Name.side_str_list[self["side"]["value"]],
            self["index"]["value"],
        )

    @property
    def guide_root(self) -> str:
        name, side, index = self.identifier
        return Name.create(
            convention=Name.controller_name_convention,
            name=name,
            side=side,
            index=index,
            extension="guideRoot",
        )

    @property
    def rig_root(self) -> str:
        name, side, index = self.identifier
        return Name.create(
            convention=Name.controller_name_convention,
            name=name,
            side=side,
            index=index,
            extension="rigRoot",
        )

    @property
    def guide_graph(self) -> str:
        name, side, index = self.identifier
        return Name.create(
            convention=Name.controller_name_convention,
            name=name,
            side=side,
            index=index,
            extension="bifGuideGraph",
        )

    @property
    def rig_graph(self) -> str:
        name, side, index = self.identifier
        return Name.create(
            convention=Name.controller_name_convention,
            name=name,
            side=side,
            index=index,
            extension="bifRigGraph",
        )

    @build_log(logging.DEBUG)
    def add_guide_root(self) -> None:
        if not cmds.pluginInfo("dominoNodes.py", loaded=True, query=True):
            cmds.loadPlugin("dominoNodes.py")

        component = self["component"]["value"].capitalize()
        cmds.createNode(f"d{component}", name=self.guide_root, parent=GUIDE)
        cmds.addAttr(
            self.guide_root, longName="is_domino_guideRoot", attributeType="bool"
        )
        cmds.addAttr(
            self.guide_root, longName="npo_matrix", attributeType="matrix", multi=True
        )

        for long_name, data in self.items():
            if "dataType" not in data and "attributeType" not in data:
                continue
            attrType = data["dataType"] if "dataType" in data else data["attributeType"]
            ins = attribute.TYPETABLE[attrType](longName=long_name, **data)
            ins.node = self.guide_root
            ins.create()

    @build_log(logging.DEBUG)
    def add_rig_root(self) -> None:
        name, side, index = self.identifier
        parent = RIG
        if self.parent:
            parent_output = cmds.listConnections(
                self.parent.rig_root + ".output", source=True, destination=False
            )
            parent = parent_output[-1]

        ins = Transform(
            parent=parent, name=name, side=side, index=index, extension="rigRoot"
        )
        rig_root = ins.create()
        cmds.addAttr(rig_root, longName="is_domino_rig_root", attributeType="bool")
        cmds.addAttr(rig_root, longName="parent", attributeType="message")
        cmds.addAttr(rig_root, longName="children", attributeType="message")
        cmds.addAttr(
            rig_root, longName="controller", attributeType="message", multi=True
        )
        cmds.addAttr(
            rig_root, longName="npo_matrix", attributeType="matrix", multi=True
        )
        cmds.addAttr(rig_root, longName="output", attributeType="message", multi=True)
        cmds.addAttr(
            rig_root, longName="output_joint", attributeType="message", multi=True
        )
        cmds.setAttr(rig_root + ".useOutlinerColor", 1)
        cmds.setAttr(rig_root + ".outlinerColor", 0.375, 0.75, 0.75)

        # data
        for long_name, data in self.items():
            if "dataType" not in data and "attributeType" not in data:
                continue
            attrType = data["dataType"] if "dataType" in data else data["attributeType"]
            ins = attribute.TYPETABLE[attrType](longName=long_name, **data)
            ins.node = self.rig_root
            ins.create()

        # parent, child
        if self.parent:
            cmds.connectAttr(
                self.parent.rig_root + ".children", self.rig_root + ".parent"
            )

    @build_log(logging.DEBUG)
    def add_guide(
        self, parent: str, description: str, m: list | om.MMatrix, mirror_type: int = 1
    ) -> str:
        """Guide -> rig root attribute
        ~~_guideRoot
         ~~_guide -> ~~_rigRoot.guide[0] -> bifrost.~~Data.guide_matrix[0]
          ~~_guide -> ~~_rigRoot.guide[1] -> bifrost.~~Data.guide_matrix[1]

        Args:
            parent (str): _description_
            description (str): _description_
            m (list | om.MMatrix): _description_

        Returns:
            str: _description_
        """
        name, side, index = self.identifier
        ins = Transform(
            parent=parent,
            name=name,
            side=side,
            index=index,
            description=description,
            extension="guide",
            m=m,
        )
        guide = ins.create()
        crv = nurbscurve.create("axis", 0)
        for shape in cmds.listRelatives(crv, shapes=True):
            shape = cmds.parent(shape, guide, relative=True, shape=True)
            cmds.rename(shape, guide + "Shape")
        cmds.delete(crv)
        cmds.setAttr(guide + ".displayHandle", 1)
        cmds.addAttr(guide, longName="is_domino_guide", attributeType="bool")
        next_index = len(
            cmds.listConnections(
                self.guide_root + ".guide_matrix", source=True, destination=False
            )
            or []
        )
        cmds.connectAttr(
            guide + ".worldMatrix[0]", self.guide_root + f".guide_matrix[{next_index}]"
        )
        at = attribute.Enum(
            longName="mirror_type",
            enumName=["orientation", "behavior", "inverse_scale"],
            defaultValue=1,
            value=mirror_type,
            keyable=True,
        )
        at.node = guide
        at.create()
        cmds.connectAttr(
            guide + ".mirror_type",
            self.guide_root + f".guide_mirror_type[{next_index}]",
        )
        cmds.setAttr(guide + ".sx", lock=True, keyable=False)
        cmds.setAttr(guide + ".sy", lock=True, keyable=False)
        cmds.setAttr(guide + ".sz", lock=True, keyable=False)
        cmds.setAttr(guide + ".v", lock=True, keyable=False)
        return guide

    class _Controller(dict):

        @property
        def name(self) -> str:
            name, side, index = self.instance.identifier
            return Name.create(
                convention=Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description=self["description"],
                extension=Name.controller_extension,
            )

        @property
        def node(self) -> str:
            return self._node

        @node.setter
        def node(self, n: str) -> None:
            self._node = n
            self["description"] = cmds.getAttr(self._node + ".description")

            # parent controllers 데이터 구하기.
            self["parent_controllers"] = []
            for parent_ctl in (
                cmds.listConnections(
                    self._node + ".parent_controllers", source=True, destination=False
                )
                or []
            ):
                ins = Controller(node=parent_ctl)
                parent_root = ins.root

                if cmds.getAttr(parent_root + ".component") == "assembly":
                    identifier = ("origin", "", "")
                else:
                    name = cmds.getAttr(parent_root + ".name")
                    side = cmds.getAttr(parent_root + ".side")
                    index = cmds.getAttr(parent_root + ".index")
                    identifier = (name, side, index)
                description = cmds.getAttr(parent_ctl + ".description")
                parent_controllers = (identifier, description)
                self["parent_controllers"].append(parent_controllers)

            # shape 데이터 구하기.
            ins = Curve(node=self._node)
            self["shape"] = ins.data

        @property
        def data(self) -> dict:
            return self

        @data.setter
        def data(self, d: dict) -> None:
            self.update(d)
            self._node = self.name

        @build_log(logging.DEBUG)
        def create(
            self,
            parent: str,
            parent_controllers: list,
            shape: dict | str,
            color: int | om.MColor,
            npo_matrix_index: int | None = None,
            fkik_command_attr: str = "",
        ) -> tuple:
            parent_controllers_str = []
            for identifier, description in parent_controllers:
                parent_controllers_str.append(
                    Name.create(
                        convention=Name.controller_name_convention,
                        name=identifier[0],
                        side=identifier[1],
                        index=identifier[2],
                        description=description,
                        extension=Name.controller_extension,
                    )
                )

            name, side, index = self.instance.identifier
            ins = Controller(
                parent=parent,
                parent_controllers=parent_controllers_str,
                name=name,
                side=side,
                index=index,
                description=self["description"],
                extension=Name.controller_extension,
                m=ORIGINMATRIX,
                shape=shape,
                color=color,
            )
            npo, ctl = ins.create()
            if npo_matrix_index is not None:
                cmds.connectAttr(
                    self.instance.rig_root
                    + ".npo_matrix[{0}]".format(npo_matrix_index),
                    npo + ".offsetParentMatrix",
                )
            next_index = len(
                cmds.listConnections(
                    self.instance.rig_root + ".controller",
                    source=True,
                    destination=False,
                )
                or []
            )
            cmds.addAttr(ctl, longName="component", dataType="string")
            cmds.setAttr(
                ctl + ".component", self.instance["component"]["value"], type="string"
            )
            cmds.setAttr(ctl + ".component", lock=True)
            cmds.connectAttr(
                ctl + ".message", self.instance.rig_root + f".controller[{next_index}]"
            )
            if fkik_command_attr:
                cmds.addAttr(ctl, longName="fkik_command_attr", dataType="message")
                cmds.connectAttr(fkik_command_attr, ctl + ".fkik_command_attr")
            return npo, ctl

        def __init__(
            self,
            description: str,
            rig_instance: T,
        ):
            self.instance = rig_instance
            self.instance["controller"].append(self)
            self["description"] = description
            self._node = self.name

    def add_controller(self, description: str) -> None:
        self._Controller(description=description, rig_instance=self)

    @build_log(logging.DEBUG)
    def add_driver_transform(self, description: str, source_plug: str) -> tuple:
        name, side, index = self.identifier

        multMatrix = cmds.createNode("multMatrix")
        cmds.connectAttr(source_plug, multMatrix + ".matrixIn[0]")
        cmds.connectAttr(
            self.rig_root + ".worldInverseMatrix[0]", multMatrix + ".matrixIn[1]"
        )

        ins = Transform(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description=description,
            extension="driver",
            m=ORIGINMATRIX,
        )
        driver = ins.create()
        cmds.connectAttr(multMatrix + ".matrixSum", driver + ".offsetParentMatrix")
        if cmds.objExists(self.rig_graph):
            next_index = len(
                cmds.listConnections(
                    self.rig_graph + ".driver_matrix", source=True, destination=False
                )
                or []
            )
            cmds.connectAttr(
                driver + ".dagLocalMatrix",
                self.rig_graph + f".driver_matrix[{next_index}]",
            )
        return driver

    @build_log(logging.DEBUG)
    def add_joint(
        self,
        parent: str,
        description: str,
        m: list | om.MMatrix,
    ) -> str:
        name, side, index = self.identifier
        ins = Joint(
            parent=parent,
            name=name,
            side=side,
            index=index,
            description=description,
            extension=Name.joint_extension,
            m=m,
            use_joint_convention=False,
        )
        return ins.create()

    class _Output(dict):

        @property
        def name(self) -> str:
            name, side, index = self.instance.identifier
            return Name.create(
                convention=Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description=self["description"],
                extension=self["extension"],
            )

        @property
        def data(self) -> dict:
            return self

        @data.setter
        def data(self, d: dict) -> None:
            self.update(d)

        def connect(self) -> tuple:
            next_index = len(
                cmds.listConnections(
                    self.instance.rig_root + ".output",
                    source=True,
                    destination=False,
                )
                or []
            )
            cmds.connectAttr(
                self.name + ".message",
                self.instance.rig_root + f".output[{next_index}]",
            )

        def __init__(
            self,
            description: str,
            extension: str,
            rig_instance: T,
        ):
            self.instance = rig_instance
            self.instance["output"].append(self)
            self["description"] = description
            self["extension"] = extension

    def add_output(self, description: str, extension: str) -> None:
        self._Output(description=description, extension=extension, rig_instance=self)

    class _OutputJoint(dict):

        @property
        def name(self) -> str:
            name, side, index = self.instance.identifier
            return Name.create(
                convention=Name.joint_name_convention,
                name=name,
                side=side,
                index=index,
                description=self["description"],
                extension=Name.joint_extension,
            )

        @property
        def node(self) -> str:
            return self._node

        @node.setter
        def node(self, n: str) -> None:
            self._node = n
            self["description"] = cmds.getAttr(self._node + ".description")
            self["parent"] = cmds.listRelatives(self._node, parent=True)[0]
            self["name"] = self._node

        @property
        def data(self) -> dict:
            return self

        @data.setter
        def data(self, d: dict) -> None:
            self.update(d)
            self._node = self.name

        @build_log(logging.DEBUG)
        def create(self, parent: str, output: str) -> str:
            name, side, index = self.instance.identifier
            ins = Joint(
                parent=parent if parent else SKEL,
                name=name,
                side=side,
                index=index,
                description=self["description"],
                extension=Name.joint_extension,
                m=cmds.xform(output, query=True, matrix=True, worldSpace=True),
                use_joint_convention=True,
            )
            next_index = len(
                cmds.listConnections(
                    self.instance.rig_root + ".output_joint",
                    source=True,
                    destination=False,
                )
                or []
            )
            jnt = ins.create()
            cmds.addAttr(
                jnt, longName="is_domino_skel", attributeType="bool", keyable=False
            )
            cmds.connectAttr(
                jnt + ".message",
                self.instance.rig_root + f".output_joint[{next_index}]",
            )
            cmds.parentConstraint(output, jnt)
            cmds.scaleConstraint(output, jnt)
            return jnt

        def __init__(
            self,
            description: str,
            rig_instance: T,
        ):
            self.instance = rig_instance
            self.instance["output_joint"].append(self)
            self["description"] = description
            self._node = self.name

    def add_output_joint(self, description: str) -> None:
        self._OutputJoint(description=description, rig_instance=self)

    @build_log(logging.DEBUG)
    def add_guide_graph(self) -> str:
        component = self["component"]["value"]

        parent = cmds.createNode(
            "transform",
            name=self.guide_graph.replace("Graph", ""),
            parent=self.guide_root,
        )
        graph = cmds.createNode(
            "bifrostGraphShape", name=self.guide_graph, parent=parent
        )

        cmds.vnnNode(
            graph,
            "/input",
            createOutputPort=("guide_matrix", "array<Math::float4x4>"),
        )

        guide_compound = cmds.vnnCompound(
            graph,
            "/",
            addNode="BifrostGraph,Domino::components," + component + "_guide",
        )[0]
        cmds.vnnConnect(graph, "/input.guide_matrix", f"/{guide_compound}.guide_matrix")
        cmds.connectAttr(self.rig_root + ".guide_matrix", graph + ".guide_matrix")
        cmds.vnnNode(
            graph,
            "/output",
            createInputPort=("initialize_transform", "array<Math::float4x4>"),
        )
        cmds.vnnConnect(
            graph,
            f"/{guide_compound}.initialize_transform",
            "/output.initialize_transform",
        )
        return graph

    @build_log(logging.DEBUG)
    def add_rig_graph(self) -> str:
        component = self["component"]["value"]

        parent = cmds.createNode(
            "transform", name=self.rig_graph.replace("Graph", ""), parent=self.rig_root
        )
        graph = cmds.createNode("bifrostGraphShape", name=self.rig_graph, parent=parent)
        cmds.vnnNode(
            graph,
            "/input",
            createOutputPort=("driver_matrix", "array<Math::float4x4>"),
        )
        rig_compound = cmds.vnnCompound(
            graph,
            "/",
            addNode="BifrostGraph,Domino::components," + component + "_rig",
        )[0]
        cmds.vnnConnect(graph, "/input.driver_matrix", f"/{rig_compound}.driver_matrix")
        cmds.vnnNode(
            graph, "/output", createInputPort=("output", "array<Math::float4x4>")
        )
        cmds.vnnConnect(graph, f"/{rig_compound}.output", "/output.output")
        return graph

    def __init__(self, data: list = []) -> None:
        """initialize 시 component 의 데이터를 instance 에 업데이트 합니다."""
        self["children"] = []
        self["controller"] = []
        self["output"] = []
        self["output_joint"] = []

        for d in data:
            if hasattr(d, "long_name") and d.long_name not in self:
                copydata = copy.deepcopy(d)
                self.update(copydata)
            else:
                self.update(d)

    def guide(self, description: str = "") -> None:
        attrs = [".tx", ".ty", ".tz", ".rx", ".ry", ".rz"]
        if not cmds.objExists(GUIDE):
            ins = Transform(parent=None, name="", side="", index="", extension=GUIDE)
            ins.create()
            for attr in attrs:
                cmds.setAttr(GUIDE + attr, lock=True, keyable=False)

        self.add_guide_root()
        cmds.addAttr(self.guide_root, longName="notes", dataType="string")
        cmds.setAttr(self.guide_root + ".notes", description, type="string")
        cmds.setAttr(self.guide_root + ".notes", lock=True)

    def rig(self, description: str = "") -> None:
        # TODO same name check

        attrs = [".tx", ".ty", ".tz", ".rx", ".ry", ".rz", ".sx", ".sy", ".sz"]
        if not cmds.objExists(RIG):
            ins = Transform(parent=None, name="", side="", index="", extension=RIG)
            rig = ins.create()
            cmds.addAttr(rig, longName="is_domino_rig", attributeType="bool")
            for attr in attrs:
                cmds.setAttr(RIG + attr, lock=True, keyable=False)
        if not cmds.objExists(SKEL):
            ins = Transform(parent=RIG, name="", side="", index="", extension=SKEL)
            ins.create()
            for attr in attrs:
                cmds.setAttr(SKEL + attr, lock=True, keyable=False)

        self.add_rig_root()
        cmds.addAttr(self.rig_root, longName="notes", dataType="string")
        cmds.setAttr(self.rig_root + ".notes", description, type="string")
        cmds.setAttr(self.rig_root + ".notes", lock=True)
        for i, m in enumerate(self["guide_matrix"]["value"]):
            cmds.setAttr(self.rig_root + f".guide_matrix[{i}]", m, type="matrix")

    def attach_guide(self) -> None:
        self.guide()
        for long_name, data in self.items():
            if "dataType" not in data and "attributeType" not in data:
                continue
            if "multi" in data:
                for attr in (
                    cmds.listAttr(self.rig_root + "." + long_name, multi=True) or []
                ):
                    cmds.connectAttr(
                        self.guide_root + "." + attr, self.rig_root + "." + attr
                    )
            else:
                cmds.connectAttr(
                    self.guide_root + "." + long_name, self.rig_root + "." + long_name
                )
        for attr in cmds.listAttr(self.rig_root + ".npo_matrix", multi=True) or []:
            cmds.connectAttr(self.guide_root + "." + attr, self.rig_root + "." + attr)

        for output in (
            cmds.listConnections(
                self.rig_root + ".output", source=True, destination=False
            )
            or []
        ):
            children = cmds.listRelatives(output, children=True, type="transform") or []
            for child in children:
                cmds.parentConstraint(GUIDE, child)

    def detach_guide(self) -> None:
        cons = []
        for output in (
            cmds.listConnections(
                self.rig_root + ".output", source=True, destination=False
            )
            or []
        ):
            children = cmds.listRelatives(output, children=True, type="transform") or []
            for child in children:
                cons.append(cmds.parentConstraint(child, query=True)[0])
        # constraint 삭제시 마지막 값으로 업데이트 되지 않는 문제. 강제 업데이트.
        for attr in cmds.listAttr(self.rig_root + ".guide_matrix", multi=True):
            cmds.getAttr(self.rig_root + "." + attr)
        # output 아래 rigRoot 가 offset 되는 문제. constaint 먼저 삭제.
        if cons:
            cmds.delete(cons)
        cmds.delete(self.guide_root)
        if not cmds.listRelatives(GUIDE):
            cmds.delete(GUIDE)

    def set_output_joint_hierarchy(self) -> None:
        pass

    def mirror_guide(self) -> None:
        guides = cmds.listConnections(
            self.guide_root + ".guide_matrix", source=True, destination=False
        )
        mirror_matrices = []
        for guide in guides:
            mirror_type = cmds.getAttr(guide + ".mirror_type")
            m = cmds.xform(guide, query=True, matrix=True, worldSpace=True)
            mirror_matrices.append(
                Transform.get_mirror_matrix(m, mirror_type=mirror_type)
            )
        for guide, mirror_m in zip(guides, mirror_matrices):
            cmds.xform(guide, matrix=mirror_m, worldSpace=True)


@build_log(logging.INFO)
def build(context, component) -> dict:

    def recursive_build_component(component):
        component.populate_controller()
        component.populate_output()
        component.populate_output_joint()
        component.rig()
        identifier = "_".join([str(x) for x in component.identifier if x])
        context[identifier] = {
            "controller": component["controller"],
            "output": component["output"],
            "output_joint": component["output_joint"],
        }
        for child in component["children"]:
            recursive_build_component(child)

    # 하위 component 가 없는 상태로 attch guide 시 constraint 이 걸리지 않음.
    def recursive_attach_guide(component):
        component.attach_guide()
        for child in component["children"]:
            recursive_attach_guide(child)

    recursive_build_component(component=component)
    recursive_attach_guide(component=component)

    @build_log(logging.DEBUG)
    def print_context(*args, **kwargs): ...

    for identifier, value in context.items():
        print_context(
            identifier=identifier,
            controller=value["controller"],
            output=value["output"],
            output_joint=value["output_joint"],
        )
    return context


def serialize() -> T:
    """마야 노드에서 json 으로 저장 할 수 있는 데이터로 직렬화합니다."""
    assembly_node = ""
    for n in cmds.ls(type="transform"):
        if (
            cmds.objExists(n + ".is_domino_rig_root")
            and cmds.getAttr(n + ".component") == "assembly"
        ):
            assembly_node = n

    if not assembly_node:
        return

    def convert_node_to_component(node: str, parent: T) -> T:
        module_name = cmds.getAttr(node + ".component")
        module = importlib.import_module("domino.component." + module_name)
        component = module.Rig()

        attribute_data = module.DATA
        for attr in attribute_data.copy():
            if attr[attr.long_name]["multi"]:
                value = []
                for a in cmds.listAttr(node + "." + attr.long_name, multi=True) or []:
                    value.append(cmds.getAttr(node + "." + a))
            else:
                value = cmds.getAttr(node + "." + attr.long_name)
            component[attr.long_name]["value"] = value

        # controller data.
        for ctl in (
            cmds.listConnections(node + ".controller", source=True, destination=False)
            or []
        ):
            ctl_ins = component._Controller("", component)
            ctl_ins.node = ctl

        if parent:
            component.parent = parent

        children = (
            cmds.listConnections(node + ".children", destination=True, source=False)
            or []
        )
        for child in children:
            convert_node_to_component(child, component)
        return component

    return convert_node_to_component(assembly_node, None)


def deserialize(data: dict, create=True) -> T:
    """직렬화 한 데이터를 마야 노드로 변환합니다."""

    def convert_data_to_component(component_data: dict, parent: T) -> T:
        module_name = component_data["component"]["value"]
        module = importlib.import_module("domino.component." + module_name)
        component = module.Rig()

        for attr in module.DATA:
            component[attr.long_name]["value"] = component_data[attr.long_name]["value"]

        for controller_data in component_data["controller"]:
            ins = component._Controller("", component)
            ins.data = controller_data
        component["output"] = component_data["output"]
        component["output_joint"] = component_data["output_joint"]

        if parent:
            component.parent = parent

        for child in component_data["children"]:
            convert_data_to_component(child, component)

        return component

    component = convert_data_to_component(data, None)
    if create:
        build({}, component=component)
    return component


@build_log(logging.INFO)
def save(file_path: str) -> None:
    """리그를 json 으로 저장합니다."""
    if not file_path:
        return

    data = serialize()

    if not data:
        return

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Save filePath: {file_path}")


@build_log(logging.INFO)
def load(file_path: str, create=True) -> T:
    """json 을 리그로 불러옵니다."""
    if not file_path:
        return

    with open(file_path, "r") as f:
        data = json.load(f)

    logger.info(f"Load filePath: {file_path}")

    return deserialize(data, create)
