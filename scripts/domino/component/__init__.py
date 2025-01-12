# domino
from domino.core import Name, Transform, Joint, Controller, Curve, attribute, nurbscurve
from domino.core.utils import build_log, logger, maya_version, used_plugins

# maya
from maya import cmds
from maya.api import OpenMaya as om  # type: ignore

# built-ins
from typing import TypeVar
from pathlib import Path
import copy
import json
import importlib
import logging
import sys


__all__ = [
    "assembly",
    "control01",
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
    def assembly(self) -> T:
        component = self
        while component.get_parent() is not None:
            component = component.get_parent()
        return component

    @property
    def identifier(self) -> tuple:
        return (
            self["name"]["value"],
            Name.side_list[self["side"]["value"]],
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

    @property
    def skel_graph(self) -> str:
        return SKEL + "_bifGraph"

    def get_parent(self) -> T:
        return self._parent

    def set_parent(self, parent: T | None) -> None:
        # parent 를 변경시 rig root hierarchy 도 가능하면 변경.
        if self._parent:
            self._parent["children"].remove(self)
        self._parent = parent
        parent["children"].append(self)
        if cmds.objExists(self.rig_root):
            parent_output_index = self["parent_output_index"]["value"]
            try:
                output = parent["output"][parent_output_index]
            except IndexError:
                output = parent["output"][-1]
            name, side, index = parent.identifier
            output_name = Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description=output["description"],
                extension=output["extension"],
            )
            old_parent = cmds.listRelatives(self.rig_root, parent=True) or []
            if cmds.objExists(output_name) and output_name != old_parent[0]:
                _, source = cmds.listConnections(
                    self.rig_root + ".parent",
                    source=True,
                    destination=False,
                    connections=True,
                    plugs=True,
                )
                if source != self._parent.rig_root + ".children":
                    cmds.connectAttr(
                        self._parent.rig_root + ".children",
                        self.rig_root + ".parent",
                        force=True,
                    )
                cmds.parent(self.rig_root, output_name)

    @build_log(logging.DEBUG)
    def add_guide_root(self) -> None:
        cmds.createNode("transform", name=self.guide_root, parent=GUIDE)
        cmds.addAttr(
            self.guide_root, longName="is_domino_guide_root", attributeType="bool"
        )
        cmds.addAttr(
            self.guide_root, longName="_guides", attributeType="message", multi=True
        )

        for long_name, data in self.items():
            if not isinstance(data, dict):
                continue
            _type = data.get("dataType") or data.get("attributeType")
            if not _type:
                continue
            ins = attribute.TYPETABLE[_type](longName=long_name, **data)
            ins.node = self.guide_root
            ins.create()

    @build_log(logging.DEBUG)
    def add_rig_root(self) -> None:
        name, side, index = self.identifier
        parent = RIG
        if self.get_parent():
            parent_output = cmds.listConnections(
                self.get_parent().rig_root + ".output", source=True, destination=False
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
        cmds.addAttr(rig_root, longName="output", attributeType="message", multi=True)
        cmds.addAttr(
            rig_root, longName="output_joint", attributeType="message", multi=True
        )
        cmds.setAttr(rig_root + ".useOutlinerColor", 1)
        cmds.setAttr(rig_root + ".outlinerColor", 0.375, 0.75, 0.75)

        # data
        for long_name, data in self.items():
            if not isinstance(data, dict):
                continue
            _type = data.get("dataType") or data.get("attributeType")
            if not _type:
                continue
            ins = attribute.TYPETABLE[_type](longName=long_name, **data)
            ins.node = self.rig_root
            ins.create()

        # parent, child
        if self.get_parent():
            cmds.connectAttr(
                self.get_parent().rig_root + ".children", self.rig_root + ".parent"
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
        cmds.connectAttr(
            guide + ".message", self.guide_root + f"._guides[{next_index}]"
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
            shape: dict | str,
            color: int | om.MColor,
            npo_matrix_index: int | None = None,
            fkik_command_attr: str = "",
        ) -> tuple:
            parent_controllers_str = []
            for identifier, description in self["parent_controllers"]:
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
                # multi index 초과하는 범위를 초기화 없이 연결 할 경우
                # getAttr 로 npo_matrix[npo_matrix_index]를 query 시
                # None 값으로 return 됨.
                # 초기 값 세팅을 해줘야 함.
                if (
                    cmds.getAttr(
                        self.instance.rig_root + f".npo_matrix[{npo_matrix_index}]"
                    )
                    is None
                ):
                    cmds.setAttr(
                        self.instance.rig_root + f".npo_matrix[{npo_matrix_index}]",
                        ORIGINMATRIX,
                        type="matrix",
                    )
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
            self.node = ctl
            return npo, ctl

        def __init__(
            self,
            description: str,
            parent_controllers: list,
            rig_instance: T,
        ):
            self.instance = rig_instance
            self.instance["controller"].append(self)
            self["description"] = description
            self["parent_controllers"] = parent_controllers
            self._node = self.name

    def add_controller(self, description: str, parent_controllers: list) -> None:
        self._Controller(
            description=description,
            parent_controllers=parent_controllers,
            rig_instance=self,
        )

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
            if "offset_output_rotate_x" in self.instance:
                cmds.connectAttr(
                    self.instance.rig_root + ".offset_output_rotate_x",
                    self.name + ".rx",
                )
                cmds.connectAttr(
                    self.instance.rig_root + ".offset_output_rotate_y",
                    self.name + ".ry",
                )
                cmds.connectAttr(
                    self.instance.rig_root + ".offset_output_rotate_z",
                    self.name + ".rz",
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
            at_ins = attribute.Message(longName="output")
            at_ins.node = jnt
            attr = at_ins.create()
            cmds.connectAttr(output + ".message", attr)

            self._node = jnt
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
        cmds.vnnNode(
            graph, "/input", createOutputPort=("offset_output_rotate_x", "float")
        )
        cmds.vnnNode(
            graph, "/input", createOutputPort=("offset_output_rotate_y", "float")
        )
        cmds.vnnNode(
            graph, "/input", createOutputPort=("offset_output_rotate_z", "float")
        )

        guide_compound = cmds.vnnCompound(
            graph,
            "/",
            addNode="BifrostGraph,Domino::Components," + component + "_guide",
        )[0]

        cmds.vnnConnect(
            graph,
            "/input.offset_output_rotate_x",
            f"/{guide_compound}.offset_output_rotate_x",
        )
        cmds.vnnConnect(
            graph,
            "/input.offset_output_rotate_y",
            f"/{guide_compound}.offset_output_rotate_y",
        )
        cmds.vnnConnect(
            graph,
            "/input.offset_output_rotate_z",
            f"/{guide_compound}.offset_output_rotate_z",
        )
        cmds.vnnConnect(graph, "/input.guide_matrix", f"/{guide_compound}.guide_matrix")
        cmds.connectAttr(self.guide_root + ".guide_matrix", graph + ".guide_matrix")
        cmds.connectAttr(
            self.guide_root + ".offset_output_rotate_x",
            graph + ".offset_output_rotate_x",
        )
        cmds.connectAttr(
            self.guide_root + ".offset_output_rotate_y",
            graph + ".offset_output_rotate_y",
        )
        cmds.connectAttr(
            self.guide_root + ".offset_output_rotate_z",
            graph + ".offset_output_rotate_z",
        )
        cmds.vnnNode(
            graph,
            "/output",
            createInputPort=("npo_matrix", "array<Math::float4x4>"),
        )
        cmds.vnnConnect(
            graph,
            f"/{guide_compound}.npo_matrix",
            "/output.npo_matrix",
        )
        cmds.vnnNode(
            graph,
            "/output",
            createInputPort=("initialize_output_matrix", "array<Math::double4x4>"),
        )
        cmds.vnnConnect(
            graph,
            "/control01_guide.initialize_output_matrix",
            ".initialize_output_matrix",
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
            addNode="BifrostGraph,Domino::Components," + component + "_rig",
        )[0]
        cmds.vnnConnect(graph, "/input.driver_matrix", f"/{rig_compound}.driver_matrix")
        cmds.vnnNode(
            graph, "/output", createInputPort=("output", "array<Math::float4x4>")
        )
        cmds.vnnConnect(graph, f"/{rig_compound}.output", "/output.output")
        return graph

    def setup_skel_graph(self, joints: list) -> None:
        # output joint matrix
        count = 0
        for output_joint in joints:
            while cmds.connectionInfo(
                f"{self.skel_graph}.output_matrix[{count}]", getExactDestination=True
            ):
                count += 1
            parent = cmds.listRelatives(output_joint, parent=True)[0]
            # parent_output_matrix, initialize_parent_output_matrix
            if parent != "skel":
                parent_output = cmds.listConnections(
                    parent + ".output", destination=False, source=True
                )[0]
                parent_output_matrix = parent_output + ".worldMatrix[0]"
                plug = [
                    x
                    for x in cmds.listConnections(
                        parent_output + ".message",
                        destination=True,
                        source=False,
                        plugs=True,
                    )
                    if "[" in x
                ][0]
                parent_root = plug.split(".")[0]
                index = int(plug.split("[")[1].split("]")[0])
                initialize_parent_output_matrix = (
                    parent_root + f".initialize_output_matrix[{index}]"
                )
            else:
                initialize_parent_output_matrix = parent_output_matrix = (
                    "skel.worldMatrix[0]"
                )
            # output_matrix, initialize_output_matrix
            loc = cmds.listConnections(
                output_joint + ".output", destination=False, source=True
            )[0]
            output_matrix = loc + ".worldMatrix[0]"
            plugs = cmds.listConnections(
                loc + ".message",
                destination=True,
                source=False,
            )
            root = [
                plug for plug in plugs if cmds.objExists(plug + ".is_domino_rig_root")
            ][0]
            list_attr = cmds.listAttr(root + ".output", multi=True)
            for attr in list_attr:
                plug = cmds.listConnections(
                    root + "." + attr, source=True, destination=False
                )[0]
                if plug == loc:
                    break
            index = int(attr.split("[")[1].split("]")[0])
            initialize_output_matrix = root + f".initialize_output_matrix[{index}]"

            # connect bifrost graph
            cmds.connectAttr(output_matrix, f"{self.skel_graph}.output_matrix[{count}]")
            cmds.connectAttr(
                initialize_output_matrix,
                f"{self.skel_graph}.initialize_output_matrix[{count}]",
            )
            cmds.connectAttr(
                parent_output_matrix, f"{self.skel_graph}.parent_output_matrix[{count}]"
            )
            cmds.connectAttr(
                initialize_parent_output_matrix,
                f"{self.skel_graph}.initialize_parent_output_matrix[{count}]",
            )
            cmds.connectAttr(
                f"{self.skel_graph}.output_translate[{count}]", output_joint + ".t"
            )
            cmds.connectAttr(
                f"{self.skel_graph}.output_rotate[{count}]", output_joint + ".r"
            )
            cmds.connectAttr(
                f"{self.skel_graph}.output_scale[{count}]", output_joint + ".s"
            )
            cmds.connectAttr(
                f"{self.skel_graph}.output_shear[{count}]", output_joint + ".shear"
            )
            cmds.connectAttr(
                f"{self.skel_graph}.output_joint_orient[{count}]",
                output_joint + ".jointOrient",
            )

    def __init__(self, data: list = []) -> None:
        """initialize 시 component 의 데이터를 instance 에 업데이트 합니다."""
        self._parent = None
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
        if not cmds.objExists(SKEL + "_bif"):
            parent = cmds.createNode(
                "transform",
                name=SKEL + "_bif",
                parent=SKEL,
            )
            graph = cmds.createNode(
                "bifrostGraphShape", name=self.skel_graph, parent=parent
            )
            cmds.vnnCompound(
                graph,
                "/",
                addNode="BifrostGraph,Domino::Compounds,connect_output_to_output_joint",
            )
            cmds.vnnCompound(
                graph, "/connect_output_to_output_joint", setIsReferenced=False
            )
            cmds.vnnNode(
                graph,
                "/output",
                createInputPort=("output_translate", "array<Math::float3>"),
            )
            cmds.vnnNode(
                graph,
                "/output",
                createInputPort=("output_rotate", "array<Math::float3>"),
            )
            cmds.vnnNode(
                graph,
                "/output",
                createInputPort=("output_scale", "array<Math::float3>"),
            )
            cmds.vnnNode(
                graph,
                "/output",
                createInputPort=("output_shear", "array<Math::float3>"),
            )
            cmds.vnnNode(
                graph,
                "/output",
                createInputPort=("output_joint_orient", "array<Math::float3>"),
            )

            cmds.vnnConnect(
                graph,
                "/connect_output_to_output_joint.output_translate",
                ".output_translate",
            )
            cmds.vnnConnect(
                graph, "/connect_output_to_output_joint.output_rotate", ".output_rotate"
            )
            cmds.vnnConnect(
                graph, "/connect_output_to_output_joint.output_scale", ".output_scale"
            )
            cmds.vnnConnect(
                graph, "/connect_output_to_output_joint.output_shear", ".output_shear"
            )
            cmds.vnnConnect(
                graph,
                "/connect_output_to_output_joint.output_joint_orient",
                ".output_joint_orient",
            )
            cmds.vnnNode(
                graph,
                "/input",
                createOutputPort=("initialize_output_matrix", "array<Math::float4x4>"),
            )
            cmds.vnnNode(
                graph,
                "/input",
                createOutputPort=("output_matrix", "array<Math::float4x4>"),
            )
            cmds.vnnNode(
                graph,
                "/input",
                createOutputPort=(
                    "initialize_parent_output_matrix",
                    "array<Math::float4x4>",
                ),
            )
            cmds.vnnNode(
                graph,
                "/input",
                createOutputPort=("parent_output_matrix", "array<Math::float4x4>"),
            )
            cmds.vnnConnect(
                graph,
                ".initialize_output_matrix",
                "/connect_output_to_output_joint.initialize_output_matrix",
                copyMetaData=True,
            )
            cmds.vnnConnect(
                graph,
                ".output_matrix",
                "/connect_output_to_output_joint.output_matrix",
                copyMetaData=True,
            )
            cmds.vnnConnect(
                graph,
                ".initialize_parent_output_matrix",
                "/connect_output_to_output_joint.initialize_parent_output_matrix",
                copyMetaData=True,
            )
            cmds.vnnConnect(
                graph,
                ".parent_output_matrix",
                "/connect_output_to_output_joint.parent_output_matrix",
                copyMetaData=True,
            )
            cmds.vnnCompound(
                graph,
                "/",
                addNode="BifrostGraph,Core::Array,array_size",
            )
            cmds.vnnConnect(graph, ".initialize_output_matrix", "/array_size.array")
            cmds.vnnConnect(
                graph,
                "/array_size.size",
                "/connect_output_to_output_joint.max_iterations",
            )

        self.add_rig_root()
        cmds.addAttr(self.rig_root, longName="notes", dataType="string")
        cmds.setAttr(self.rig_root + ".notes", description, type="string")
        cmds.setAttr(self.rig_root + ".notes", lock=True)
        for i, m in enumerate(self["guide_matrix"]["value"]):
            cmds.setAttr(self.rig_root + f".guide_matrix[{i}]", m, type="matrix")

    def populate(self) -> None:
        stack = [self]
        while stack:
            component = stack.pop(0)
            component.populate_controller()
            component.populate_output()
            component.populate_output_joint()
            stack.extend(component["children"])

    def get_valid_component_index(self, name: str, side: int) -> int:
        identifiers = []
        stack = [self.assembly]
        while stack:
            component = stack.pop(0)
            identifiers.append(component.identifier)
            stack.extend(component["children"])

        indices = []
        for identifier in identifiers:
            if name == identifier[0] and Name.side_str_list[side] == identifier[1]:
                indices.append(identifier[2])
        index = 0
        while index in indices:
            index += 1
        return index

    def attach_guide(self) -> None:
        if cmds.objExists(self.guide_root):
            self.detach_guide()
        self.guide()
        for long_name, data in self.items():
            if not isinstance(data, dict):
                continue
            _type = data.get("dataType") or data.get("attributeType")
            if not _type:
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
        cmds.parentConstraint(GUIDE, self.rig_root)

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
                child_cons = cmds.parentConstraint(child, query=True)
                if child_cons:
                    cons.append(child_cons)
        self_cons = cmds.parentConstraint(self.rig_root, query=True)
        if self_cons:
            cons.append(self_cons)
        # constraint 삭제시 마지막 값으로 남지않는 문제.
        attrs = cmds.listAttr(self.rig_root + ".guide_matrix", multi=True) or []
        attrs += cmds.listAttr(self.rig_root + ".npo_matrix", multi=True) or []
        for attr in attrs:
            source_plug = cmds.listConnections(
                self.rig_root + "." + attr, source=True, destination=False, plugs=True
            )[0]
            cmds.disconnectAttr(source_plug, self.rig_root + "." + attr)
        # output 아래 rigRoot 가 offset 되는 문제. constaint 먼저 삭제.
        if cons:
            cmds.delete(cons)
        cmds.delete(self.guide_root)
        if not cmds.listRelatives(GUIDE):
            cmds.delete(GUIDE)

    def mirror_guide_matrices(self) -> list:
        guide_matrices = self["guide_matrix"]["value"]
        guide_mirror_types = self["guide_mirror_type"]["value"]
        mirror_matrices = []
        for m, _type in zip(guide_matrices, guide_mirror_types):
            mirror_matrices.append(
                list(Transform.get_mirror_matrix(m, mirror_type=_type))
            )
        return mirror_matrices

    def rename_component(
        self, new_name: str, new_side: int, new_index: int, apply_to_output=False
    ):
        identifiers = []
        stack = [self.assembly]
        while stack:
            component = stack.pop(0)
            identifiers.append(component.identifier)
            stack.extend(component["children"])

        validation = True
        for identifier in identifiers:
            if (
                identifier[0] == new_name
                and identifier[1] == Name.side_str_list[new_side]
                and identifier[2] == new_index
            ):
                validation = False
        if not validation:
            return

        name, side, index = self.identifier

        self["name"]["value"] = new_name
        self["side"]["value"] = new_side
        self["index"]["value"] = new_index

        if not apply_to_output:
            return

        # rename
        for node in cmds.ls(type="transform"):
            name_list = node.split("_")
            if len(name_list) < 2:
                continue
            node_name = name_list[0]
            node_side_index = name_list[1]
            if (
                name == node_name
                and node_side_index.startswith(side)
                and node_side_index.endswith(str(index))
            ):
                etc = "_".join(name_list[2:])
                new_side_str = Name.side_str_list[new_side]
                replace_name = f"{new_name}_{new_side_str}{new_index}_{etc}"
                cmds.rename(node, replace_name)

        # edit joint label
        if cmds.objExists(self.rig_root):
            output_joints = (
                cmds.listConnections(
                    self.rig_root + ".output_joint", source=True, destination=False
                )
                or []
            )
            for output_joint in output_joints:
                description = cmds.getAttr(output_joint + ".description")
                jnt_ins = Joint(node=output_joint)
                jnt_ins.set_label(
                    new_side,
                    Name.create_joint_label(
                        new_name,
                        Name.side_str_list[new_side],
                        new_index,
                        description,
                    ),
                )

        if cmds.objExists(self.guide_root):
            cmds.setAttr(self.guide_root + ".name", new_name, type="string")
            cmds.setAttr(self.guide_root + ".side", new_side)
            cmds.setAttr(self.guide_root + ".index", new_index)
        elif cmds.objExists(self.rig_root):
            cmds.setAttr(self.rig_root + ".name", new_name, type="string")
            cmds.setAttr(self.rig_root + ".side", new_side)
            cmds.setAttr(self.rig_root + ".index", new_index)

    def duplicate_component(self, apply_to_output: bool = False) -> None:
        stack = [(self, self.get_parent())]
        while stack:
            component, parent_component = stack.pop(0)
            duplicate_component = copy.deepcopy(component)
            duplicate_component["children"] = []
            index = self.get_valid_component_index(
                duplicate_component["name"]["value"],
                duplicate_component["side"]["value"],
            )
            duplicate_component["index"]["value"] = index
            duplicate_component.set_parent(parent_component)
            if apply_to_output:
                duplicate_component.rig()
                output_joints = []
                name, side, index = duplicate_component.identifier
                for data in duplicate_component["output_joint"]:
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
                duplicate_component.setup_skel_graph(output_joints)

            stack.extend([(c, duplicate_component) for c in component["children"]])

    def mirror_component(
        self, reuse_exists: bool, apply_to_output: bool = False
    ) -> None:
        # side 가 center 이거나 하위 component 모두 똑같지 않은 경우 return.
        this_component_side = self["side"]["value"]
        stack = [self]
        while stack:
            component = stack.pop(0)
            side = component["side"]["value"]
            if side != this_component_side or side == 0:
                return
            stack.extend(component["children"])

        # 0 is center, 1 is left, 2 is right
        target_side = 2 if this_component_side == 1 else 1

        if reuse_exists:
            # already exists case

            ## collect target data
            target_data = []
            stack = [self]
            while stack:
                component = stack.pop(0)
                name, _, index = component.identifier
                target_data.append(
                    (
                        (name, Name.side_str_list[target_side], index),
                        component.mirror_guide_matrices(),
                        (
                            component["guide_mirror_type"]["value"]
                            if "guide_mirror_type" in component
                            else None
                        ),
                    )
                )
                stack.extend(component["children"])

            ## mirror
            stack = [self.assembly]
            while stack:
                component = stack.pop(0)
                for d in target_data:
                    identifier, matrices, mirror_type = d
                    if component.identifier == identifier:
                        component["guide_matrix"]["value"] = matrices
                        if mirror_type:
                            component["guide_mirror_type"]["value"] = mirror_type
                        if apply_to_output:
                            component.attach_guide()
                stack.extend(component["children"])
        else:
            # all new case
            stack = [(self, self.get_parent())]
            while stack:
                component, parent_component = stack.pop(0)
                duplicate_component = copy.deepcopy(component)
                duplicate_component["children"] = []
                duplicate_component["side"]["value"] = target_side
                index = self.get_valid_component_index(
                    duplicate_component["name"]["value"],
                    duplicate_component["side"]["value"],
                )
                duplicate_component["index"]["value"] = index
                duplicate_component.set_parent(parent_component)

                matrices = component.mirror_guide_matrices()
                duplicate_component["guide_matrix"]["value"] = matrices
                if apply_to_output:
                    duplicate_component.rig()
                    duplicate_component.attach_guide()
                    output_joints = []
                    name, side, index = duplicate_component.identifier
                    for data in duplicate_component["output_joint"]:
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
                    duplicate_component.setup_skel_graph(output_joints)

                stack.extend([(c, duplicate_component) for c in component["children"]])

    def remove_component(self):
        stack = [(self.assembly, None)]
        while stack:
            component, parent_component = stack.pop(0)
            if component.identifier == self.identifier:
                index = parent_component["children"].index(self)
                parent_component["children"].pop(index)
                break
            stack.extend([(child, component) for child in component["children"]])

        name_parts = Name.joint_name_convention.split("_")
        for i, parts in enumerate(name_parts):
            if "name" in parts:
                name_index = i
            if "side" in parts:
                side_index = i
            if "index" in parts:
                index_index = i

        nodes = []
        stack = [self]
        while stack:
            component = stack.pop(0)
            name, side, index = component.identifier
            for node in cmds.ls(type="transform"):
                node_parts = node.split("_")
                if (
                    name in node_parts[name_index]
                    and side in node_parts[side_index]
                    and str(index) in node_parts[index_index]
                ):
                    nodes.append(node)
            stack.extend(component["children"])
        if nodes:
            cmds.delete(nodes)
        if cmds.objExists(self.rig_root):
            cmds.delete(self.rig_root)
        if cmds.objExists(self.guide_root):
            cmds.delete(self.guide_root)
        if self.get_parent() == None:
            if cmds.objExists(RIG):
                cmds.delete(RIG)
            if cmds.objExists(GUIDE):
                cmds.delete(GUIDE)

    def sync_from_scene(self):
        stack = [self.assembly]
        while stack:
            component = stack.pop(0)
            if not cmds.objExists(component.rig_root):
                continue
            module = importlib.import_module(
                "domino.component." + component["component"]["value"]
            )

            # attribute
            attribute_data = module.DATA
            for attr in attribute_data.copy():
                if attr[attr.long_name]["multi"]:
                    value = []
                    for a in (
                        cmds.listAttr(
                            component.rig_root + "." + attr.long_name, multi=True
                        )
                        or []
                    ):
                        value.append(cmds.getAttr(component.rig_root + "." + a))
                else:
                    value = cmds.getAttr(component.rig_root + "." + attr.long_name)
                component[attr.long_name]["value"] = value

            # controller data.
            component["controller"] = []
            for ctl in (
                cmds.listConnections(
                    component.rig_root + ".controller", source=True, destination=False
                )
                or []
            ):
                ctl_ins = component._Controller(
                    description="", parent_controllers=[], rig_instance=component
                )
                ctl_ins.node = ctl

            # output
            component["output"] = []
            for output in (
                cmds.listConnections(
                    component.rig_root + ".output", source=True, destination=False
                )
                or []
            ):
                description = cmds.getAttr(output + ".description")
                extension = cmds.getAttr(output + ".extension")
                component._Output(
                    description=description, extension=extension, rig_instance=component
                )

            # output joint
            component["output_joint"] = []
            for output_joint in (
                cmds.listConnections(
                    component.rig_root + ".output_joint", source=True, destination=False
                )
                or []
            ):
                output_joint_ins = component._OutputJoint(
                    description="", rig_instance=component
                )
                output_joint_ins.node = output_joint

            stack.extend(component["children"])


@build_log(logging.INFO)
def build(context: dict, component: T, attach_guide: bool = False) -> dict:
    context["_attach_guide"] = True if attach_guide else False
    # import modeling
    if "modeling" in component:
        if Path(component["modeling"]).exists():
            cmds.file(newFile=True, force=True)
            cmds.file(component["modeling"], i=True, namespace=":")

    for script_path in component["pre_custom_scripts"]["value"]:
        if not script_path:
            continue
        try:
            cmds.undoInfo(openChunk=True)
            name = Path(script_path).name.split(".")[0]
            spec = importlib.util.spec_from_file_location(name, script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[name] = module

            logger.info(f"Run {name} {script_path}")
            module.run(context=context)
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)

    try:
        cmds.undoInfo(openChunk=True)

        # rig build
        stack = [component]
        while stack:
            c = stack.pop(0)
            c.rig()
            if context["_attach_guide"]:
                c.attach_guide()
            identifier = "_".join([str(x) for x in c.identifier if str(x)])
            context[identifier] = {
                "controller": c["controller"],
                "output": c["output"],
                "output_joint": c["output_joint"],
            }
            stack.extend(c["children"])

        # TODO : custom curve data
        # TODO : custom polygon data

        # setup output joint
        output_joints = []
        color_index_list = [12, 14, 17, 18, 19, 21]
        color_index = 0
        stack = [component]
        while stack:
            c = stack.pop(0)
            if color_index > 5:
                color_index = 0
            name, side, index = c.identifier
            for output_joint in c["output_joint"]:
                joint_name = Name.create(
                    convention=Name.joint_name_convention,
                    name=name,
                    side=side,
                    index=index,
                    description=output_joint["description"],
                    extension=Name.joint_extension,
                )
                if "name" in output_joint and cmds.objExists(joint_name):
                    joint_name = cmds.rename(joint_name, output_joint["name"])
                parent = cmds.listRelatives(joint_name, parent=True)[0]
                if "parent" in output_joint and parent != output_joint["parent"]:
                    cmds.parent(joint_name, output_joint["parent"])
                cmds.setAttr(joint_name + ".overrideEnabled", 1)
                cmds.setAttr(joint_name + ".overrideEnabled", 1)
                cmds.color(joint_name, userDefined=color_index_list[color_index])
                output_joints.append(joint_name)
            color_index += 1
            stack.extend(c["children"])
        component.setup_skel_graph(output_joints)

        # TODO : pose manager
        # TODO : space manager
        # TODO : sdk manager
        cmds.select("rig")
    finally:
        cmds.undoInfo(closeChunk=True)

    for script_path in component["post_custom_scripts"]["value"]:
        if not script_path:
            continue
        try:
            cmds.undoInfo(openChunk=True)
            name = Path(script_path).name.split(".")[0]
            spec = importlib.util.spec_from_file_location(name, script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[name] = module

            logger.info(f"Run {name} {script_path}")
            module.run(context=context)
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)

    # rig build info
    cmds.undoInfo(openChunk=True)
    info = "mayaVersion : " + maya_version() + "\n"
    info += "usedPlugins : "
    plugins = used_plugins()
    for i in range(int(len(plugins) / 2)):
        info += "\n\t" + plugins[i * 2] + "\t" + plugins[i * 2 + 1]
    cmds.addAttr("rig", longName="notes", dataType="string")
    cmds.setAttr("rig.notes", info, type="string")
    cmds.setAttr("rig.notes", lock=True)
    cmds.undoInfo(closeChunk=True)

    # rig result logging
    @build_log(logging.DEBUG)
    def print_context(*args, **kwargs): ...

    for identifier, value in {
        k: context[k] for k in context.keys() if not k.startswith("_")
    }.items():
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

    stack = [(assembly_node, None)]
    rig = None
    while stack:
        node, parent = stack.pop(0)
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
            ctl_ins = component._Controller(
                description="", parent_controllers=[], rig_instance=component
            )
            ctl_ins.node = ctl

        # output
        for output in (
            cmds.listConnections(node + ".output", source=True, destination=False) or []
        ):
            description = cmds.getAttr(output + ".description")
            extension = cmds.getAttr(output + ".extension")
            component._Output(
                description=description, extension=extension, rig_instance=component
            )

        # output joint
        for output_joint in (
            cmds.listConnections(node + ".output_joint", source=True, destination=False)
            or []
        ):
            output_joint_ins = component._OutputJoint(
                description="", rig_instance=component
            )
            output_joint_ins.node = output_joint

        if parent:
            component.set_parent(parent)

        children = (
            cmds.listConnections(node + ".children", destination=True, source=False)
            or []
        )
        stack.extend([(child, component) for child in children])
        if module_name == "assembly":
            rig = component

    rig["pre_custom_scripts_str"]["value"] = []
    for script in rig["pre_custom_scripts"]["value"]:
        if not script:
            continue
        content = ""
        with open(script, "r") as f:
            content += f.read()
        rig["pre_custom_scripts_str"]["value"].append(content)

    rig["post_custom_scripts_str"]["value"] = []
    for script in rig["post_custom_scripts"]["value"]:
        if not script:
            continue
        content = ""
        with open(script, "r") as f:
            content += f.read()
        rig["post_custom_scripts_str"]["value"].append(content)

    # TODO : pose manager
    # TODO : space manager
    # TODO : sdk manager
    # TODO : custom curve data
    # TODO : custom polygon data
    return rig


def deserialize(data: dict, create=True) -> T:
    """직렬화 한 데이터를 마야 노드로 변환합니다."""
    stack = [(data, None)]
    rig = None
    while stack:
        component_data, parent = stack.pop(0)
        module_name = component_data["component"]["value"]
        module = importlib.import_module("domino.component." + module_name)
        component = module.Rig()

        for attr in module.DATA:
            component[attr.long_name]["value"] = component_data[attr.long_name]["value"]
        # controller
        for controller_data in component_data["controller"]:
            ins = component._Controller(
                description="", parent_controllers=[], rig_instance=component
            )
            ins.data = controller_data
        # output
        for output_data in component_data["output"]:
            ins = component._Output(
                description="", extension="", rig_instance=component
            )
            ins.data = output_data
        # output joint
        for output_joint_data in component_data["output_joint"]:
            ins = component._OutputJoint(description="", rig_instance=component)
            ins.data = output_joint_data

        if parent:
            component.set_parent(parent)

        stack.extend([child, component] for child in component_data["children"])
        if module_name == "assembly":
            rig = component
    if "modeling" in data:
        rig["modeling"] = data["modeling"]

    if create:
        build({}, component=rig)
    return rig


@build_log(logging.INFO)
def save(file_path: str, data: dict | None = None) -> None:
    """리그를 json 으로 저장합니다."""
    if not file_path:
        return

    if data is None:
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
