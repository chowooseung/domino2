# domino
from domino.core import (
    Name,
    Transform,
    Joint,
    Controller,
    Curve,
    attribute,
    nurbscurve,
)
from domino.core.utils import build_log, logger, maya_version, used_plugins

# maya
from maya import cmds
from maya.api import OpenMaya as om

# built-ins
from pathlib import Path
import copy
import json
import shutil
import importlib
import logging
import sys


__all__ = ["assembly", "control01", "fk01", "uicontainer01"]

GUIDE = "guide"
RIG = "rig"
SKEL = "skel"
ORIGINMATRIX = om.MMatrix()


# region RIG
class Rig(dict):
    """
    Guide Matrix -> Bifrost -> initial Matrix(controller, output_joint) -> outputJoint

    Args:
        dict (_type_): _description_

    Returns:
        _type_: _description_
    """

    # region -    RIG / PROPERTY
    @property
    def assembly(self):
        component = self
        while component.get_parent() is not None:
            component = component.get_parent()
        return component

    @property
    def identifier(self):
        return (
            self["name"]["value"],
            Name.side_str_list[self["side"]["value"]],
            self["index"]["value"],
        )

    @property
    def guide_root(self):
        name, side, index = self.identifier
        return Name.create(
            convention=Name.controller_name_convention,
            name=name,
            side=side,
            index=index,
            extension="guideRoot",
        )

    @property
    def rig_root(self):
        name, side, index = self.identifier
        return Name.create(
            convention=Name.controller_name_convention,
            name=name,
            side=side,
            index=index,
            extension="rigRoot",
        )

    @property
    def guide_graph(self):
        name, side, index = self.identifier
        return Name.create(
            convention=Name.controller_name_convention,
            name=name,
            side=side,
            index=index,
            extension="bifGuideGraph",
        )

    @property
    def rig_graph(self):
        name, side, index = self.identifier
        return Name.create(
            convention=Name.controller_name_convention,
            name=name,
            side=side,
            index=index,
            extension="bifRigGraph",
        )

    @property
    def skel_graph(self):
        return SKEL + "_bifGraph"

    # endregion

    # region -    RIG / componnet parent
    def get_parent(self):
        return self._parent

    def set_parent(self, parent):
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

    # endregion

    # region -    RIG / Add root
    @build_log(logging.DEBUG)
    def add_guide_root(self):
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
    def add_rig_root(self):
        name, side, index = self.identifier
        parent = RIG
        if self.get_parent():
            parent_output = cmds.listConnections(
                f"{self.get_parent().rig_root}.output", source=True, destination=False
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
        cmds.setAttr(f"{rig_root}.useOutlinerColor", 1)
        cmds.setAttr(f"{rig_root}.outlinerColor", 0.375, 0.75, 0.75)

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
                f"{self.get_parent().rig_root}.children", f"{self.rig_root}.parent"
            )

    @build_log(logging.DEBUG)
    def add_guide(self, parent, description, m, mirror_type=1):
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
            cmds.rename(shape, f"{guide}Shape")
        cmds.delete(crv)
        cmds.setAttr(f"{guide}.displayHandle", 1)
        cmds.addAttr(guide, longName="is_domino_guide", attributeType="bool")
        next_index = len(
            cmds.listConnections(
                f"{self.guide_root}.guide_matrix", source=True, destination=False
            )
            or []
        )
        cmds.connectAttr(
            f"{guide}.worldMatrix[0]", f"{self.guide_root}.guide_matrix[{next_index}]"
        )
        cmds.connectAttr(f"{guide}.message", f"{self.guide_root}._guides[{next_index}]")
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
            f"{guide}.mirror_type",
            f"{self.guide_root}.guide_mirror_type[{next_index}]",
        )
        cmds.setAttr(f"{guide}.sx", lock=True, keyable=False)
        cmds.setAttr(f"{guide}.sy", lock=True, keyable=False)
        cmds.setAttr(f"{guide}.sz", lock=True, keyable=False)
        cmds.setAttr(f"{guide}.v", lock=True, keyable=False)
        return guide

    # endregion

    # region -    RIG / _Controller
    class _Controller(dict):

        @property
        def name(self):
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
        def node(self):
            return self._node

        @node.setter
        def node(self, n):
            self._node = n
            self["description"] = cmds.getAttr(self._node + ".description")

            # parent controllers 데이터 구하기.
            self["parent_controllers"] = []
            for parent_ctl in (
                cmds.listConnections(
                    f"{self._node}.parent_controllers", source=True, destination=False
                )
                or []
            ):
                ins = Controller(node=parent_ctl)
                parent_root = ins.root

                if cmds.getAttr(f"{parent_root}.component") == "assembly":
                    identifier = ("origin", "", "")
                elif cmds.getAttr(f"{parent_root}.component") == "uicontainer01":
                    name = cmds.getAttr(f"{parent_root}.name")
                    identifier = (name, "", "")
                else:
                    name = cmds.getAttr(f"{parent_root}.name")
                    side = cmds.getAttr(f"{parent_root}.side")
                    side_str = Name.side_str_list[side]
                    index = cmds.getAttr(f"{parent_root}.index")
                    identifier = (name, side_str, index)
                description = cmds.getAttr(f"{parent_ctl}.description")
                parent_controllers = (identifier, description)
                self["parent_controllers"].append(parent_controllers)

            # shape 데이터 구하기.
            ins = Curve(node=self._node)
            self["shape"] = ins.data

        @property
        def data(self):
            return self

        @data.setter
        def data(self, d):
            self.update(d)
            self._node = self.name

        @build_log(logging.DEBUG)
        def create(
            self,
            parent,
            shape,
            color,
            npo_matrix_index=None,
            fkik_command_attr="",
        ):
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
            cmds.setAttr(f"{npo}.t", 0, 0, 0)
            cmds.setAttr(f"{npo}.r", 0, 0, 0)
            cmds.setAttr(f"{npo}.s", 1, 1, 1)
            if npo_matrix_index is not None:
                # multi index 초과하는 범위를 초기화 없이 연결 할 경우
                # getAttr 로 npo_matrix[npo_matrix_index]를 query 시
                # None 값으로 return 됨.
                # 초기 값 세팅을 해줘야 함.
                if (
                    cmds.getAttr(
                        f"{self.instance.rig_root}.npo_matrix[{npo_matrix_index}]"
                    )
                    is None
                ):
                    cmds.setAttr(
                        f"{self.instance.rig_root}.npo_matrix[{npo_matrix_index}]",
                        ORIGINMATRIX,
                        type="matrix",
                    )
                cmds.connectAttr(
                    f"{self.instance.rig_root}.npo_matrix[{npo_matrix_index}]",
                    f"{npo}.offsetParentMatrix",
                )
            next_index = len(
                cmds.listConnections(
                    f"{self.instance.rig_root}.controller",
                    source=True,
                    destination=False,
                )
                or []
            )
            cmds.addAttr(ctl, longName="component", dataType="string")
            cmds.setAttr(
                f"{ctl}.component", self.instance["component"]["value"], type="string"
            )
            cmds.setAttr(f"{ctl}.component", lock=True)
            cmds.connectAttr(
                f"{ctl}.message", f"{self.instance.rig_root}.controller[{next_index}]"
            )
            if fkik_command_attr:
                cmds.addAttr(ctl, longName="fkik_command_attr", dataType="message")
                cmds.connectAttr(fkik_command_attr, f"{ctl}.fkik_command_attr")
            self.node = ctl

            cmds.setAttr(f"{ctl}.sx", lock=True, keyable=False)
            cmds.setAttr(f"{ctl}.sy", lock=True, keyable=False)
            cmds.setAttr(f"{ctl}.sz", lock=True, keyable=False)
            return npo, ctl

        def __init__(self, description, parent_controllers, rig_instance):
            self.instance = rig_instance
            self.instance["controller"].append(self)
            self["description"] = description
            self["parent_controllers"] = parent_controllers
            self._node = self.name

    # endregion

    def add_controller(self, description, parent_controllers):
        self._Controller(
            description=description,
            parent_controllers=parent_controllers,
            rig_instance=self,
        )

    @build_log(logging.DEBUG)
    def add_joint(self, parent, description, m):
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

    # region -    RIG / _Output
    class _Output(dict):

        @property
        def name(self):
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
        def data(self):
            return self

        @data.setter
        def data(self, d):
            self.update(d)

        def connect(self):
            next_index = len(
                cmds.listConnections(
                    f"{self.instance.rig_root}.output",
                    source=True,
                    destination=False,
                )
                or []
            )
            cmds.connectAttr(
                f"{self.name}.message",
                f"{self.instance.rig_root}.output[{next_index}]",
            )
            if "offset_output_rotate_x" in self.instance:
                cmds.connectAttr(
                    f"{self.instance.rig_root}.offset_output_rotate_x",
                    f"{self.name}.rx",
                )
                cmds.connectAttr(
                    f"{self.instance.rig_root}.offset_output_rotate_y",
                    f"{self.name}.ry",
                )
                cmds.connectAttr(
                    f"{self.instance.rig_root}.offset_output_rotate_z",
                    f"{self.name}.rz",
                )

        def __init__(self, description, extension, rig_instance):
            self.instance = rig_instance
            self.instance["output"].append(self)
            self["description"] = description
            self["extension"] = extension

    # endregion

    def add_output(self, description, extension):
        self._Output(description=description, extension=extension, rig_instance=self)

    # region -    RIG / _OutputJoint
    class _OutputJoint(dict):

        @property
        def name(self):
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
        def node(self):
            return self._node

        @node.setter
        def node(self, n):
            self._node = n
            self["description"] = cmds.getAttr(f"{self._node}.description")
            self["parent"] = cmds.listRelatives(self._node, parent=True)[0]
            self["name"] = self._node
            self["radius"] = cmds.getAttr(f"{self._node}.radius")
            self["draw_style"] = cmds.getAttr(f"{self._node}.drawStyle")

        @property
        def data(self):
            return self

        @data.setter
        def data(self, d):
            self.update(d)
            self._node = self.name

        @build_log(logging.DEBUG)
        def create(self):
            name, side, index = self.instance.identifier
            parent = SKEL
            if self["parent"] is not None:
                parent = self["parent"]
            elif self["parent_description"] is not None:
                parent = Name.create(
                    convention=Name.joint_name_convention,
                    name=name,
                    side=side,
                    index=index,
                    description=self["parent_description"],
                    extension=Name.joint_extension,
                )
            ins = Joint(
                parent=parent,
                name=name,
                side=side,
                index=index,
                description=self["description"],
                extension=Name.joint_extension,
                m=ORIGINMATRIX,
                use_joint_convention=True,
            )
            next_index = len(
                cmds.listConnections(
                    f"{self.instance.rig_root}.output_joint",
                    source=True,
                    destination=False,
                )
                or []
            )
            jnt = ins.create()
            cmds.addAttr(
                jnt, longName="is_domino_skel", attributeType="bool", keyable=False
            )
            cmds.addAttr(jnt, longName="skel_index", attributeType="long")
            cmds.connectAttr(
                f"{jnt}.message",
                f"{self.instance.rig_root}.output_joint[{next_index}]",
            )
            at_ins = attribute.Message(longName="output")
            at_ins.node = jnt
            attr = at_ins.create()

            output = cmds.listConnections(
                f"{self.instance.rig_root}.output[{next_index}]",
                source=True,
                destination=False,
            )[0]
            cmds.connectAttr(f"{output}.message", attr)
            cmds.setAttr(f"{jnt}.rotateAxis", lock=True)

            self._node = jnt
            return jnt

        def __init__(self, parent_description, description, rig_instance):
            self.instance = rig_instance
            self.instance["output_joint"].append(self)
            self["parent"] = None
            self["parent_description"] = parent_description
            self["description"] = description
            self._node = self.name

    # endregion

    def add_output_joint(self, parent_description, description):
        self._OutputJoint(
            parent_description=parent_description,
            description=description,
            rig_instance=self,
        )

    # region -    RIG / Add Bifrost Graph
    @build_log(logging.DEBUG)
    def add_guide_graph(self):
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
            addNode=f"BifrostGraph,Domino::Components,{component}_guide",
        )[0]

        cmds.vnnConnect(graph, "/input.guide_matrix", f"/{guide_compound}.guide_matrix")
        cmds.connectAttr(f"{self.guide_root}.guide_matrix", f"{graph}.guide_matrix")
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
            createInputPort=(
                "initialize_output_matrix",
                "array<Math::double4x4>",
            ),
        )
        cmds.vnnNode(
            graph,
            "/output",
            createInputPort=(
                "initialize_output_inverse_matrix",
                "array<Math::double4x4>",
            ),
        )
        cmds.vnnConnect(
            graph,
            f"/{guide_compound}.initialize_output_matrix",
            ".initialize_output_matrix",
        )
        cmds.vnnConnect(
            graph,
            f"/{guide_compound}.initialize_output_inverse_matrix",
            ".initialize_output_inverse_matrix",
        )
        if cmds.objExists(f"{self.guide_root}.offset_output_rotate_x"):
            cmds.vnnNode(
                graph, "/input", createOutputPort=("offset_output_rotate_x", "float")
            )
            cmds.vnnNode(
                graph, "/input", createOutputPort=("offset_output_rotate_y", "float")
            )
            cmds.vnnNode(
                graph, "/input", createOutputPort=("offset_output_rotate_z", "float")
            )
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
            cmds.connectAttr(
                f"{self.guide_root}.offset_output_rotate_x",
                f"{graph}.offset_output_rotate_x",
            )
            cmds.connectAttr(
                f"{self.guide_root}.offset_output_rotate_y",
                f"{graph}.offset_output_rotate_y",
            )
            cmds.connectAttr(
                f"{self.guide_root}.offset_output_rotate_z",
                f"{graph}.offset_output_rotate_z",
            )
        return graph, guide_compound

    @build_log(logging.DEBUG)
    def add_rig_graph(self):
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
            addNode=f"BifrostGraph,Domino::Components,{component}_rig",
        )[0]
        cmds.vnnConnect(graph, "/input.driver_matrix", f"/{rig_compound}.driver_matrix")
        cmds.vnnNode(
            graph, "/output", createInputPort=("output", "array<Math::float4x4>")
        )
        cmds.vnnConnect(graph, f"/{rig_compound}.output", "/output.output")
        return graph

    def setup_skel(self, joints):
        for output_joint in joints:
            parent = cmds.listRelatives(output_joint, parent=True)[0]
            # parent_inverse_matrix, initialize_parent_inverse_matrix
            if parent != "skel":
                parent_output = cmds.listConnections(
                    f"{parent}.output", destination=False, source=True
                )[0]
                parent_inverse_matrix = f"{parent_output}.worldInverseMatrix[0]"
                plugs = [
                    x
                    for x in cmds.listConnections(
                        f"{parent_output}.message",
                        destination=True,
                        source=False,
                        plugs=True,
                    )
                    if "[" in x
                ]
                plug = [x for x in plugs if "output[" in x][0]
                parent_root = plug.split(".")[0]
                index = int(plug.split("[")[1].split("]")[0])
                initialize_parent_inverse_matrix = (
                    f"{parent_root}.initialize_output_inverse_matrix[{index}]"
                )
            else:
                initialize_parent_inverse_matrix = parent_inverse_matrix = (
                    "skel.worldInverseMatrix[0]"
                )
            # output_matrix, initialize_output_matrix, initialize_output_inverse_matrix
            loc = cmds.listConnections(
                f"{output_joint}.output", destination=False, source=True
            )[0]
            output_matrix = f"{loc}.worldMatrix[0]"
            plugs = cmds.listConnections(
                f"{loc}.message",
                destination=True,
                source=False,
            )
            root = [
                plug for plug in plugs if cmds.objExists(f"{plug}.is_domino_rig_root")
            ][0]
            list_attr = cmds.listAttr(f"{root}.output", multi=True)
            for attr in list_attr:
                plug = cmds.listConnections(
                    f"{root}.{attr}", source=True, destination=False
                )[0]
                if plug == loc:
                    break
            index = int(attr.split("[")[1].split("]")[0])
            initialize_output_matrix = f"{root}.initialize_output_matrix[{index}]"
            initialize_output_inverse_matrix = (
                f"{root}.initialize_output_inverse_matrix[{index}]"
            )

            # connect
            index = len(
                cmds.listConnections(
                    f"{SKEL}.parent_inverse_matrix", source=True, destination=False
                )
                or []
            )
            cmds.setAttr(f"{output_joint}.skel_index", index)
            cmds.connectAttr(
                parent_inverse_matrix,
                f"{SKEL}.parent_inverse_matrix[{index}]",
                force=True,
            )
            cmds.connectAttr(
                initialize_parent_inverse_matrix,
                f"{SKEL}.initialize_parent_inverse_matrix[{index}]",
                force=True,
            )
            cmds.connectAttr(
                initialize_output_matrix,
                f"{SKEL}.initialize_output_matrix[{index}]",
                force=True,
            )
            cmds.connectAttr(
                initialize_output_inverse_matrix,
                f"{SKEL}.initialize_output_inverse_matrix[{index}]",
                force=True,
            )
            parent_inverse_matrix = f"{SKEL}.parent_inverse_matrix[{index}]"
            initialize_parent_inverse_matrix = (
                f"{SKEL}.initialize_parent_inverse_matrix[{index}]"
            )
            initialize_output_matrix = f"{SKEL}.initialize_output_matrix[{index}]"
            initialize_output_inverse_matrix = (
                f"{SKEL}.initialize_output_inverse_matrix[{index}]"
            )

            mult_m = cmds.createNode("multMatrix")
            cmds.connectAttr(output_matrix, f"{mult_m}.matrixIn[0]")
            cmds.connectAttr(parent_inverse_matrix, f"{mult_m}.matrixIn[1]")

            decom_m = cmds.createNode("decomposeMatrix")
            cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
            cmds.connectAttr(f"{decom_m}.outputTranslate", f"{output_joint}.t")
            output_scale_attrs = [f"{decom_m}.outputScale{a}" for a in ["X", "Y", "Z"]]
            scale_attrs = [f"{output_joint}.s{a}" for a in ["x", "y", "z"]]
            for output_attr, attr in zip(output_scale_attrs, scale_attrs):
                abs = cmds.createNode("absolute")
                cmds.connectAttr(output_attr, f"{abs}.input")
                sub = cmds.createNode("subtract")
                cmds.connectAttr(f"{abs}.output", f"{sub}.input1")
                cmds.setAttr(f"{sub}.input2", 1)
                abs = cmds.createNode("absolute")
                cmds.connectAttr(f"{sub}.output", f"{abs}.input")
                condition = cmds.createNode("condition")
                cmds.connectAttr(f"{abs}.output", f"{condition}.firstTerm")
                cmds.setAttr(f"{condition}.secondTerm", 0.000001)
                cmds.setAttr(f"{condition}.operation", 5)
                cmds.setAttr(f"{condition}.colorIfTrueR", 1)
                cmds.connectAttr(output_attr, f"{condition}.colorIfFalseR")
                cmds.connectAttr(f"{condition}.outColorR", attr)

            output_shear_attrs = [f"{decom_m}.outputShear{a}" for a in ["X", "X", "Y"]]
            shear_attrs = [f"{output_joint}.shear{a}" for a in ["XY", "XZ", "YZ"]]
            for output_attr, attr in zip(output_shear_attrs, shear_attrs):
                abs = cmds.createNode("absolute")
                cmds.connectAttr(output_attr, f"{abs}.input")
                condition = cmds.createNode("condition")
                cmds.connectAttr(f"{abs}.output", f"{condition}.firstTerm")
                cmds.setAttr(f"{condition}.secondTerm", 0.000001)
                cmds.setAttr(f"{condition}.operation", 5)
                cmds.setAttr(f"{condition}.colorIfTrueR", 0)
                cmds.connectAttr(output_attr, f"{condition}.colorIfFalseR")
                cmds.connectAttr(f"{condition}.outColorR", attr)

            mult_m = cmds.createNode("multMatrix")
            cmds.connectAttr(initialize_output_matrix, f"{mult_m}.matrixIn[0]")
            cmds.connectAttr(initialize_parent_inverse_matrix, f"{mult_m}.matrixIn[1]")

            decom_m = cmds.createNode("decomposeMatrix")
            cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
            cmds.connectAttr(f"{decom_m}.outputRotate", f"{output_joint}.jointOrient")

            mult_m = cmds.createNode("multMatrix")
            cmds.connectAttr(initialize_output_matrix, f"{mult_m}.matrixIn[0]")
            cmds.connectAttr(initialize_parent_inverse_matrix, f"{mult_m}.matrixIn[1]")

            inv_m = cmds.createNode("inverseMatrix")
            cmds.connectAttr(f"{mult_m}.matrixSum", f"{inv_m}.inputMatrix")

            mult_m = cmds.createNode("multMatrix")
            cmds.connectAttr(output_matrix, f"{mult_m}.matrixIn[0]")
            cmds.connectAttr(parent_inverse_matrix, f"{mult_m}.matrixIn[1]")
            cmds.connectAttr(f"{inv_m}.outputMatrix", f"{mult_m}.matrixIn[2]")

            decom_m = cmds.createNode("decomposeMatrix")
            cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
            cmds.connectAttr(f"{decom_m}.outputRotate", f"{output_joint}.r")

    # endregion

    # region -    RIG / Super method
    def __init__(self, data):
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

    def guide(self, description=""):
        attrs = [".tx", ".ty", ".tz", ".rx", ".ry", ".rz"]
        if not cmds.objExists(GUIDE):
            ins = Transform(parent=None, name="", side="", index="", extension=GUIDE)
            ins.create()
            for attr in attrs:
                cmds.setAttr(f"{GUIDE}{attr}", lock=True, keyable=False)

        self.add_guide_root()
        cmds.addAttr(self.guide_root, longName="notes", dataType="string")
        cmds.setAttr(f"{self.guide_root}.notes", description, type="string")
        cmds.setAttr(f"{self.guide_root}.notes", lock=True)

    def rig(self, description=""):
        attrs = [".tx", ".ty", ".tz", ".rx", ".ry", ".rz", ".sx", ".sy", ".sz"]
        if not cmds.objExists(RIG):
            ins = Transform(parent=None, name="", side="", index="", extension=RIG)
            rig = ins.create()
            cmds.addAttr(rig, longName="is_domino_rig", attributeType="bool")
            for attr in attrs:
                cmds.setAttr(f"{RIG}{attr}", lock=True, keyable=False)

            model_sets = cmds.sets(name="model_sets", empty=True)
            skel_sets = cmds.sets(name="skel_sets", empty=True)
            geo_sets = cmds.sets(name="geometry_sets", empty=True)
            cmds.sets([model_sets, skel_sets, geo_sets], name="rig_sets")
        if not cmds.objExists(SKEL):
            ins = Transform(parent=RIG, name="", side="", index="", extension=SKEL)
            ins.create()
            for attr in attrs:
                cmds.setAttr(f"{SKEL}{attr}", lock=True, keyable=False)
            cmds.addAttr(
                SKEL,
                longName="initialize_output_matrix",
                attributeType="matrix",
                multi=True,
            )
            cmds.addAttr(
                SKEL,
                longName="initialize_output_inverse_matrix",
                attributeType="matrix",
                multi=True,
            )
            cmds.addAttr(
                SKEL,
                longName="parent_inverse_matrix",
                attributeType="matrix",
                multi=True,
            )
            cmds.addAttr(
                SKEL,
                longName="initialize_parent_inverse_matrix",
                attributeType="matrix",
                multi=True,
            )

        self.add_rig_root()
        cmds.addAttr(self.rig_root, longName="notes", dataType="string")
        cmds.setAttr(f"{self.rig_root}.notes", description, type="string")
        cmds.setAttr(f"{self.rig_root}.notes", lock=True)
        for i, m in enumerate(self["guide_matrix"]["value"]):
            cmds.setAttr(f"{self.rig_root}.guide_matrix[{i}]", m, type="matrix")

    # endregion

    def populate(self):
        stack = [self]
        while stack:
            component = stack.pop(0)
            component.populate_controller()
            component.populate_output()
            component.populate_output_joint()
            stack.extend(component["children"])

    def get_valid_component_index(self, name, side):
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

    # region -    RIG / Editing component
    def attach_guide(self):
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
                    cmds.listAttr(f"{self.rig_root}.{long_name}", multi=True) or []
                ):
                    cmds.connectAttr(
                        f"{self.guide_root}.{attr}", f"{self.rig_root}.{attr}"
                    )
            else:
                cmds.connectAttr(
                    f"{self.guide_root}.{long_name}", f"{self.rig_root}.{long_name}"
                )
        cmds.parentConstraint(GUIDE, self.rig_root)

    def detach_guide(self):
        cons = []
        for output in (
            cmds.listConnections(
                f"{self.rig_root}.output", source=True, destination=False
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
        attrs = cmds.listAttr(f"{self.rig_root}.guide_matrix", multi=True) or []
        attrs += cmds.listAttr(f"{self.rig_root}.npo_matrix", multi=True) or []
        for attr in attrs:
            source_plug = cmds.listConnections(
                f"{self.rig_root}.{attr}", source=True, destination=False, plugs=True
            )[0]
            cmds.disconnectAttr(source_plug, f"{self.rig_root}.{attr}")
        # output 아래 rigRoot 가 offset 되는 문제. constaint 먼저 삭제.
        if cons:
            cmds.delete(cons)
        cmds.delete(self.guide_root)
        if not cmds.listRelatives(GUIDE):
            cmds.delete(GUIDE)

    def mirror_guide_matrices(self):
        guide_matrices = self["guide_matrix"]["value"]
        guide_mirror_types = self["guide_mirror_type"]["value"]
        mirror_matrices = []
        for m, _type in zip(guide_matrices, guide_mirror_types):
            mirror_matrices.append(
                list(Transform.get_mirror_matrix(m, mirror_type=_type))
            )
        return mirror_matrices

    def rename_component(self, new_name, new_side, new_index, apply_to_output=False):
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
                    f"{self.rig_root}.output_joint", source=True, destination=False
                )
                or []
            )
            for output_joint in output_joints:
                description = cmds.getAttr(f"{output_joint}.description")
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
            cmds.setAttr(f"{self.guide_root}.name", new_name, type="string")
            cmds.setAttr(f"{self.guide_root}.side", new_side)
            cmds.setAttr(f"{self.guide_root}.index", new_index)
        elif cmds.objExists(self.rig_root):
            cmds.setAttr(f"{self.rig_root}.name", new_name, type="string")
            cmds.setAttr(f"{self.rig_root}.side", new_side)
            cmds.setAttr(f"{self.rig_root}.index", new_index)

    def duplicate_component(self, apply_to_output=False):
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
                duplicate_component.setup_skel(output_joints)

            stack.extend([(c, duplicate_component) for c in component["children"]])

    def mirror_component(self, reuse_exists, apply_to_output=False):
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
                    duplicate_component.setup_skel(output_joints)

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

    # endregion

    def sync_from_scene(self):
        stack = [self.assembly]
        while stack:
            component = stack.pop(0)
            if not cmds.objExists(component.rig_root):
                continue
            module = importlib.import_module(
                f"domino.component.{component['component']['value']}"
            )

            # attribute
            attribute_data = module.DATA
            for attr in attribute_data.copy():
                if attr[attr.long_name]["multi"]:
                    value = []
                    for a in (
                        cmds.listAttr(
                            f"{component.rig_root}.{attr.long_name}", multi=True
                        )
                        or []
                    ):
                        value.append(cmds.getAttr(f"{component.rig_root}.{a}"))
                else:
                    value = cmds.getAttr(f"{component.rig_root}.{attr.long_name}")
                component[attr.long_name]["value"] = value

            # controller data.
            component["controller"] = []
            for ctl in (
                cmds.listConnections(
                    f"{component.rig_root}.controller", source=True, destination=False
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
                    f"{component.rig_root}.output", source=True, destination=False
                )
                or []
            ):
                description = cmds.getAttr(f"{output}.description")
                extension = cmds.getAttr(f"{output}.extension")
                component._Output(
                    description=description, extension=extension, rig_instance=component
                )

            # output joint
            component["output_joint"] = []
            for output_joint in (
                cmds.listConnections(
                    f"{component.rig_root}.output_joint", source=True, destination=False
                )
                or []
            ):
                output_joint_ins = component._OutputJoint(
                    parent_description=None, description="", rig_instance=component
                )
                output_joint_ins.node = output_joint

            stack.extend(component["children"])


# endregion


# region BUILD
@build_log(logging.INFO)
def build(context, component, attach_guide=False):
    context["_attach_guide"] = True if attach_guide else False
    # import modeling
    if "modeling" in component:
        if Path(component["modeling"]).exists():
            cmds.file(newFile=True, force=True)
            cmds.file(component["modeling"], i=True, namespace=":")

    if component["run_import_dummy"]:
        dummy_path = Path(component["dummy_path"]["value"])
        for path in [
            p
            for p in dummy_path.iterdir()
            if str(p).endswith(".mb") or str(p).endswith(".ma")
        ]:
            cmds.file(path, i=True, namespace=":")
            logger.info(f"Imported Dummy {path}")

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
                cmds.setAttr(f"{joint_name}.radius", output_joint["radius"])
                cmds.setAttr(f"{joint_name}.drawStyle", output_joint["draw_style"])
                cmds.color(joint_name, userDefined=color_index_list[color_index])
                output_joints.append(joint_name)
            color_index += 1
            stack.extend(c["children"])
        component.setup_skel(output_joints)
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
    info = "maya version\n\t" + maya_version()
    info += "\nused plugins"
    plugins = used_plugins()
    for i in range(int(len(plugins) / 2)):
        info += f"\n\t{plugins[i * 2]:<20}{plugins[i * 2 + 1]}"
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


# endregion


# region EXPORT / IMPORT
def serialize():
    """마야 노드에서 json 으로 저장 할 수 있는 데이터로 직렬화합니다."""
    assembly_node = ""
    for n in cmds.ls(type="transform"):
        if (
            cmds.objExists(f"{n}.is_domino_rig_root")
            and cmds.getAttr(f"{n}.component") == "assembly"
        ):
            assembly_node = n

    if not assembly_node:
        return

    stack = [(assembly_node, None)]
    rig = None
    while stack:
        node, parent = stack.pop(0)
        module_name = cmds.getAttr(f"{node}.component")
        module = importlib.import_module(f"domino.component.{module_name}")
        component = module.Rig()

        attribute_data = module.DATA
        for attr in attribute_data.copy():
            if attr[attr.long_name]["multi"]:
                value = []
                for a in cmds.listAttr(f"{node}.{attr.long_name}", multi=True) or []:
                    value.append(cmds.getAttr(f"{node}.{a}"))
            else:
                value = cmds.getAttr(f"{node}.{attr.long_name}")
            component[attr.long_name]["value"] = value

        # controller data.
        for ctl in (
            cmds.listConnections(f"{node}.controller", source=True, destination=False)
            or []
        ):
            ctl_ins = component._Controller(
                description="", parent_controllers=[], rig_instance=component
            )
            ctl_ins.node = ctl

        # output
        for output in (
            cmds.listConnections(f"{node}.output", source=True, destination=False) or []
        ):
            description = cmds.getAttr(f"{output}.description")
            extension = cmds.getAttr(f"{output}.extension")
            component._Output(
                description=description, extension=extension, rig_instance=component
            )

        # output joint
        for output_joint in (
            cmds.listConnections(f"{node}.output_joint", source=True, destination=False)
            or []
        ):
            output_joint_ins = component._OutputJoint(
                parent_description=None, description="", rig_instance=component
            )
            output_joint_ins.node = output_joint

        if parent:
            component.set_parent(parent)

        children = (
            cmds.listConnections(f"{node}.children", destination=True, source=False)
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


def deserialize(data, create=True):
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
            ins = component._OutputJoint(
                parent_description=None, description="", rig_instance=component
            )
            ins.data = output_joint_data

        if parent:
            component.set_parent(parent)

        stack.extend([child, component] for child in component_data["children"])
        if module_name == "assembly":
            rig = component

    if create:
        build({}, component=rig)
    return rig


@build_log(logging.INFO)
def save(file_path, data=None):
    """리그를 json 으로 저장합니다."""
    if not file_path:
        return

    if data is None:
        data = serialize()

    if not data:
        return

    # scripts, dummy, blendshape, deformerWeights 를 버전 업 된 path 로 수정합니다.
    # 수동으로 모든 파일을 버전업 하지 않게 하기 위함입니다.
    path = Path(file_path)
    metadata_dir = path.parent / (path.name.split(".")[0] + ".metadata")
    if not metadata_dir.exists():
        metadata_dir.mkdir()

    # scripts version up
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

    scripts_dir = metadata_dir / "scripts"
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

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Save filePath: {file_path}")


@build_log(logging.INFO)
def load(file_path, create=True):
    """json 을 리그로 불러옵니다."""
    if not file_path:
        return

    with open(file_path, "r") as f:
        data = json.load(f)

    logger.info(f"Load filePath: {file_path}")

    return deserialize(data, create)


# endregion
