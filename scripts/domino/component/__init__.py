# domino
from domino.dynamicmanager import DYNAMIC_MANAGER, export_dynamic, import_dynamic
from domino.psdmanager import PSD_MANAGER, export_psd, import_psd
from domino.sdkmanager import SDK_MANAGER, SDK_SETS, export_sdk, import_sdk
from domino.spacemanager import (
    SPACE_MANAGER,
    export_space_manager_data,
    import_space_manager_data,
)
from domino.core import (
    Name,
    Transform,
    Joint,
    Controller,
    NurbsCurve,
    NurbsSurface,
    Mesh,
    attribute,
    nurbscurve,
    rigkit,
)
from domino.core.utils import (
    build_log,
    logger,
    maya_version,
    used_plugins,
    bifrost_version,
)

# maya
from maya import cmds
from maya.api import OpenMaya as om

# built-ins
from pathlib import Path
import copy
import json
import time
import shutil
import importlib
import logging
import sys


COMPONENTLIST = [
    "assembly",
    "pivot01",
    "cog01",
    "control01",
    "uicontainer01",
    "fk01",
    "fkik2jnt01",
    "humanspine01",
    "humanneck01",
    "humanarm01",
    "humanleg01",
    "foot01",
    "psd01",
    "chain01",
]
GUIDE = "guide"
RIG = "rig"
SKEL = "skel"
ORIGINMATRIX = om.MMatrix()

RIG_SETS = "rig_sets"
MODEL_SETS = "model_sets"
SKEL_SETS = "skel_sets"
GEOMETRY_SETS = "geometry_sets"
CONTROLLER_SETS = "controller_sets"
BLENDSHAPE_SETS = "blendShape_sets"
DYNAMIC_SETS = "dynamic_sets"
DEFORMER_WEIGHTS_SETS = "deformerWeights_sets"
DEFORMER_ORDER_SETS = "deformerOrder_sets"

BREAK_POINT_RIG = 0
BREAK_POINT_PRECUSTOMSCRIPTS = 1
BREAK_POINT_SPACEMANAGER = 2
BREAK_POINT_BLENDSHAPE = 3
BREAK_POINT_PSDMANAGER = 4
BREAK_POINT_SDKMANAGER = 5
BREAK_POINT_DYNAMICMANAGER = 6
BREAK_POINT_DEFORMERWEIGHTS = 7
BREAK_POINT_DEFORMERORDER = 8
BREAK_POINT_POSTCUSTOMSCRIPTS = 9


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
                    f"{self.rig_root}.parent",
                    source=True,
                    destination=False,
                    connections=True,
                    plugs=True,
                )
                if source != f"{self._parent.rig_root}.children":
                    cmds.connectAttr(
                        f"{self._parent.rig_root}.children",
                        f"{self.rig_root}.parent",
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

        cmds.setAttr(f"{self.guide_root}.tx", lock=True, keyable=False)
        cmds.setAttr(f"{self.guide_root}.ty", lock=True, keyable=False)
        cmds.setAttr(f"{self.guide_root}.tz", lock=True, keyable=False)
        cmds.setAttr(f"{self.guide_root}.rx", lock=True, keyable=False)
        cmds.setAttr(f"{self.guide_root}.ry", lock=True, keyable=False)
        cmds.setAttr(f"{self.guide_root}.rz", lock=True, keyable=False)
        cmds.setAttr(f"{self.guide_root}.sx", keyable=False)
        cmds.setAttr(f"{self.guide_root}.sy", keyable=False)
        cmds.setAttr(f"{self.guide_root}.sz", keyable=False)

        if self == self.assembly:
            cmds.addAttr(
                self.guide_root,
                longName="asset_scale",
                attributeType="float",
                defaultValue=1.0,
                keyable=False,
            )
        else:
            if cmds.objExists(f"{self.assembly.guide_root}"):
                cmds.connectAttr(
                    f"{self.assembly.guide_root}.asset_scale",
                    f"{self.guide_root}.sx",
                )
                cmds.connectAttr(
                    f"{self.assembly.guide_root}.asset_scale",
                    f"{self.guide_root}.sy",
                )
                cmds.connectAttr(
                    f"{self.assembly.guide_root}.asset_scale",
                    f"{self.guide_root}.sz",
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
        cmds.addAttr(rig_root, longName="host", attributeType="message")
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
            self["description"] = cmds.getAttr(f"{self._node}.description")

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
            ins = NurbsCurve(node=self._node)
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
            host=False,
            fkik_match_command="",
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
            self.node = ctl

            cmds.setAttr(f"{ctl}.sx", lock=True, keyable=False)
            cmds.setAttr(f"{ctl}.sy", lock=True, keyable=False)
            cmds.setAttr(f"{ctl}.sz", lock=True, keyable=False)
            if host:
                cmds.connectAttr(f"{ctl}.message", f"{self.instance.rig_root}.host")
                if fkik_match_command:
                    cmds.addAttr(ctl, longName="fkik_match_command", dataType="string")
                    cmds.setAttr(
                        f"{ctl}.fkik_match_command", fkik_match_command, type="string"
                    )
                    cmds.addAttr(
                        ctl,
                        longName="ik_match_sources",
                        attributeType="message",
                        multi=True,
                    )
                    cmds.addAttr(
                        ctl,
                        longName="ik_match_targets",
                        attributeType="message",
                        multi=True,
                    )
                    cmds.addAttr(
                        ctl,
                        longName="fk_match_sources",
                        attributeType="message",
                        multi=True,
                    )
                    cmds.addAttr(
                        ctl,
                        longName="fk_match_targets",
                        attributeType="message",
                        multi=True,
                    )
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

        def connect(self, source=None):
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
                comp_m = cmds.createNode("composeMatrix")
                cmds.connectAttr(
                    f"{self.instance.rig_root}.offset_output_rotate_x",
                    f"{comp_m}.inputRotateX",
                )
                cmds.connectAttr(
                    f"{self.instance.rig_root}.offset_output_rotate_y",
                    f"{comp_m}.inputRotateY",
                )
                cmds.connectAttr(
                    f"{self.instance.rig_root}.offset_output_rotate_z",
                    f"{comp_m}.inputRotateZ",
                )
                mult_m = cmds.createNode("multMatrix")
                cmds.connectAttr(f"{comp_m}.outputMatrix", f"{mult_m}.matrixIn[0]")
                cmds.connectAttr(f"{source}.worldMatrix[0]", f"{mult_m}.matrixIn[1]")
                cmds.connectAttr(
                    f"{self.instance.rig_root}.worldInverseMatrix[0]",
                    f"{mult_m}.matrixIn[2]",
                )
                decom_m = cmds.createNode("decomposeMatrix")
                cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
                cmds.connectAttr(f"{decom_m}.outputTranslate", f"{self.name}.t")
                cmds.connectAttr(f"{decom_m}.outputRotate", f"{self.name}.r")
                cmds.connectAttr(f"{decom_m}.outputScale", f"{self.name}.s")

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
            # initialize_parent_inverse_matrix
            if parent != "skel":
                parent_output = cmds.listConnections(
                    f"{parent}.output", destination=False, source=True
                )[0]
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
                initialize_parent_inverse_matrix = "skel.worldInverseMatrix[0]"
            # initialize_output_matrix
            output = cmds.listConnections(
                f"{output_joint}.output", destination=False, source=True
            )[0]
            plugs = cmds.listConnections(
                f"{output}.message",
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
                if plug == output:
                    break
            index = int(attr.split("[")[1].split("]")[0])
            initialize_output_matrix = f"{root}.initialize_output_matrix[{index}]"

            # connect
            index = len(
                cmds.listAttr(f"{SKEL}.initialize_parent_inverse_matrix", multi=True)
                or []
            )
            cmds.setAttr(f"{output_joint}.skel_index", index)
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
            initialize_parent_inverse_matrix = (
                f"{SKEL}.initialize_parent_inverse_matrix[{index}]"
            )
            initialize_output_matrix = f"{SKEL}.initialize_output_matrix[{index}]"

            # jointOrient
            mult_m = cmds.createNode("multMatrix")
            cmds.connectAttr(initialize_output_matrix, f"{mult_m}.matrixIn[0]")
            cmds.connectAttr(initialize_parent_inverse_matrix, f"{mult_m}.matrixIn[1]")

            decom_m = cmds.createNode("decomposeMatrix")
            cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
            cmds.connectAttr(f"{decom_m}.outputRotate", f"{output_joint}.jointOrient")

            # constraint
            cons = cmds.parentConstraint(output, output_joint, maintainOffset=False)[0]
            cmds.parent(cons, SKEL)
            cmds.setAttr(f"{cons}.hiddenInOutliner", True)
            cmds.connectAttr(
                f"{decom_m}.outputRotate", f"{cons}.constraintJointOrient", force=True
            )
            mult_m = cmds.createNode("multMatrix")
            cmds.connectAttr(f"{output}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
            cmds.connectAttr(
                f"{output_joint}.parentInverseMatrix", f"{mult_m}.matrixIn[1]"
            )
            decom_m = cmds.createNode("decomposeMatrix")
            cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
            cmds.connectAttr(f"{decom_m}.outputScaleX", f"{output_joint}.sx")
            cmds.connectAttr(f"{decom_m}.outputScaleY", f"{output_joint}.sy")
            cmds.connectAttr(f"{decom_m}.outputScaleZ", f"{output_joint}.sz")

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
            cmds.addAttr(
                RIG,
                longName="custom_nurbscurve_data",
                attributeType="message",
                multi=True,
            )
            cmds.addAttr(
                RIG,
                longName="custom_nurbssurface_data",
                attributeType="message",
                multi=True,
            )
            cmds.addAttr(
                RIG,
                longName="custom_mesh_data",
                attributeType="message",
                multi=True,
            )
            for attr in attrs:
                cmds.setAttr(f"{RIG}{attr}", lock=True, keyable=False)

            model_sets = cmds.sets(name=MODEL_SETS, empty=True)
            skel_sets = cmds.sets(name=SKEL_SETS, empty=True)
            geo_sets = cmds.sets(name=GEOMETRY_SETS, empty=True)
            controller_sets = cmds.sets(name=CONTROLLER_SETS, empty=True)
            blendshape_sets = cmds.sets(name=BLENDSHAPE_SETS, empty=True)
            sdk_sets = cmds.sets(name=SDK_SETS, empty=True)
            deformer_weights_sets = cmds.sets(name=DEFORMER_WEIGHTS_SETS, empty=True)
            deformer_order_sets = cmds.sets(name=DEFORMER_ORDER_SETS, empty=True)
            cmds.sets(
                [
                    model_sets,
                    skel_sets,
                    geo_sets,
                    controller_sets,
                    blendshape_sets,
                    sdk_sets,
                    deformer_weights_sets,
                    deformer_order_sets,
                ],
                name=RIG_SETS,
            )
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
        # guide 삭제시 warning이나 error가 발생하지 않도록 root 간에 disconnect
        attrs = cmds.listAttr(self.rig_root, userDefined=True) or []
        for attr in attrs:
            plugs = cmds.listConnections(
                f"{self.rig_root}.{attr}",
                source=True,
                destination=False,
                connections=True,
                plugs=True,
            )
            while plugs:
                destination = plugs.pop(0)
                source = plugs.pop(0)
                if source.startswith(self.guide_root):
                    cmds.disconnectAttr(source, destination)
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
        # geometryFilter 는 전체 deformer
        for node in cmds.ls(type="transform") + cmds.ls(type="geometryFilter"):
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
            duplicate_component["controller"] = []
            duplicate_component.populate_controller()
            duplicate_component["output"] = []
            duplicate_component.populate_output()
            duplicate_component["output_joint"] = []
            duplicate_component.populate_output_joint()
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
                duplicate_component["controller"] = []
                duplicate_component.populate_controller()
                duplicate_component["output"] = []
                duplicate_component.populate_output()
                duplicate_component["output_joint"] = []
                duplicate_component.populate_output_joint()
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
        if cmds.objExists(self.rig_root):
            nodes += [self.rig_root]
        if cmds.objExists(self.guide_root):
            nodes += [self.guide_root]
        if nodes:
            curve_infos = cmds.ls(type="curveInfo")
            for ci in curve_infos:
                cmds.setAttr(f"{ci}.nodeState", 2)
            cmds.delete(nodes)
            for ci in curve_infos:
                if cmds.objExists(ci):
                    cmds.setAttr(f"{ci}.nodeState", 0)
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
                if hasattr(attr, "data_type") and attr.data_type == "nurbsCurve":
                    temp_crv = cmds.circle(name="temp1", constructionHistory=False)[0]
                    cmds.connectAttr(
                        f"{component.rig_root}.{attr.long_name}", f"{temp_crv}.create"
                    )
                    ins = NurbsCurve(node=temp_crv)
                    component[attr.long_name]["value"] = ins.data
                    cmds.delete(temp_crv)
                    continue
                elif hasattr(attr, "data_type") and attr.data_type == "nurbsSurface":
                    temp_surface = cmds.nurbsPlane(
                        name="temp1", constructionHistory=False
                    )[0]
                    cmds.connectAttr(
                        f"{component.rig_root}.{attr.long_name}",
                        f"{temp_surface}.create",
                    )
                    ins = NurbsSurface(node=temp_surface)
                    component[attr.long_name]["value"] = ins.data
                    cmds.delete(temp_surface)
                    continue
                elif hasattr(attr, "data_type") and attr.data_type == "mesh":
                    temp_mesh = cmds.polySphere(
                        name="temp1", constructionHistory=False
                    )[0]
                    cmds.connectAttr(
                        f"{component.rig_root}.{attr.long_name}", f"{temp_mesh}.inMesh"
                    )
                    ins = Mesh(node=temp_mesh)
                    component[attr.long_name]["value"] = ins.data
                    cmds.delete(temp_mesh)
                    continue
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
    try:
        cmds.ogs(pause=True)
        cmds.undoInfo(openChunk=True)
        start_time = time.perf_counter()

        if "break_point" not in component:
            component["break_point"] = BREAK_POINT_POSTCUSTOMSCRIPTS

        # rig build
        stack = [component]
        while stack:
            c = stack.pop(0)
            c.rig()
            if attach_guide:
                c.attach_guide()
            identifier = "_".join([str(x) for x in c.identifier if str(x)])
            context[identifier] = {
                "controller": c["controller"],
                "output": c["output"],
                "output_joint": c["output_joint"],
            }
            stack.extend(c["children"])

        # custom data
        if "custom_nurbscurve_data" in component:
            for i, data in enumerate(component["custom_nurbscurve_data"]):
                ins = NurbsCurve(data=data)
                crv = ins.create_from_data()
                cmds.connectAttr(f"{crv}.message", f"{RIG}.custom_nurbscurve_data[{i}]")
        if "custom_nurbssurface_data" in component:
            for i, data in enumerate(component["custom_nurbssurface_data"]):
                ins = NurbsSurface(data=data)
                surface = ins.create_from_data()
                cmds.connectAttr(
                    f"{surface}.message", f"{RIG}.custom_nurbssurface_data[{i}]"
                )
        if "custom_mesh_data" in component:
            for i, data in enumerate(component["custom_mesh_data"]):
                ins = Mesh(data=data)
                mesh = ins.create_from_data()
                cmds.connectAttr(f"{mesh}.message", f"{RIG}.custom_mesh_data[{i}]")

        # setup controller sets
        all_controllers = [x.split(".")[0] for x in cmds.ls("*.is_domino_controller")]
        # remove psd controller
        domino_controllers = [
            x for x in all_controllers if not cmds.objExists(f"{x}.is_psd_controller")
        ]
        cmds.sets(domino_controllers, edit=True, addElement=CONTROLLER_SETS)

        # setup output joint
        domino_skel = [x.split(".")[0] for x in cmds.ls("*.is_domino_skel")]
        cmds.sets(domino_skel, edit=True, addElement=SKEL_SETS)

        output_joints = []
        color_index = 1
        stack = [component]
        while stack:
            c = stack.pop(0)
            if color_index > 8:
                # color index 1~8
                color_index = 1
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
                if output_joint["name"] != joint_name and cmds.objExists(joint_name):
                    joint_name = cmds.rename(joint_name, output_joint["name"])
                parent = cmds.listRelatives(joint_name, parent=True) or []
                if parent:
                    parent = parent[0]
                if parent != output_joint["parent"]:
                    cmds.parent(joint_name, output_joint["parent"])
                cmds.setAttr(f"{joint_name}.radius", output_joint["radius"])
                cmds.setAttr(f"{joint_name}.drawStyle", output_joint["draw_style"])
                cmds.color(joint_name, userDefined=color_index)
                output_joints.append(joint_name)
            color_index += 1
            stack.extend(c["children"])
        component.setup_skel(output_joints)

        # BREAK POINT RIG
        if component["break_point"] == BREAK_POINT_RIG:
            return context

        # pre custom scripts
        for script_path in component["pre_custom_scripts"]["value"]:
            if not script_path:
                continue
            name = Path(script_path).name.split(".")[0]
            spec = importlib.util.spec_from_file_location(name, script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[name] = module

            logger.info(f"Run {name} {script_path}")
            module.run(context=context)

        # BREAK POINT PRECUSTOMSCRIPTS
        if component["break_point"] == BREAK_POINT_PRECUSTOMSCRIPTS:
            return context

        # metadata dir
        if component["domino_path"]["value"]:
            domino_path = component["domino_path"]["value"]
            metadata_dir = Path(domino_path).parent / (
                f"{Path(domino_path).name.split('.')[0]}.metadata"
            )

        # SPACEMANAGER
        if component["domino_path"]["value"]:
            space_dir = metadata_dir / "space"
            if space_dir.exists():
                import_space_manager_data((space_dir / "space.smf").as_posix())
                cmds.parent(SPACE_MANAGER, RIG)

        # BREAK POINT SPACEMANAGER
        if component["break_point"] == BREAK_POINT_SPACEMANAGER:
            return context

        # blendshape
        if component["domino_path"]["value"]:
            blendshape_dir = metadata_dir / "blendshape"
            if blendshape_dir.exists():
                rigkit.import_blendshape(blendshape_dir.as_posix())

            blendshape_sets = cmds.sets(BLENDSHAPE_SETS, query=True) or []
            for bs in component["blendshape"]:
                if not cmds.objExists(bs):
                    logger.warning(
                        f"{bs} 가 존재하지 않습니다. 설정이 뭔가 바뀌었나요?"
                    )
                    continue

                if bs not in blendshape_sets:
                    cmds.sets(bs, edit=True, addElement=BLENDSHAPE_SETS)

        # BREAK POINT BLENDSHAPE
        if component["break_point"] == BREAK_POINT_BLENDSHAPE:
            return context

        # PSD
        if component["domino_path"]["value"]:
            psd_dir = metadata_dir / "pose"
            if psd_dir.exists():
                import_psd((psd_dir / "poseSpaceDeformation.psd").as_posix())
                cmds.parent(PSD_MANAGER, RIG)

        # BREAK POINT PSD
        if component["break_point"] == BREAK_POINT_PSDMANAGER:
            return context

        # SDK
        if component["domino_path"]["value"]:
            sdk_dir = metadata_dir / "sdk"
            if sdk_dir.exists():
                import_sdk((sdk_dir / "setDriven.sdk").as_posix())
                cmds.parent(SDK_MANAGER, RIG)

        # BREAK POINT SDK
        if component["break_point"] == BREAK_POINT_SDKMANAGER:
            return context

        # DYNAMICMANAGER
        if component["domino_path"]["value"]:
            dynamic_dir = metadata_dir / "dynamic"
            if dynamic_dir.exists():
                import_dynamic((dynamic_dir / "dynamic.dyn").as_posix())
                cmds.parent(DYNAMIC_MANAGER, RIG)

        # BREAK POINT DYNAMICMANAGER
        if component["break_point"] == BREAK_POINT_DYNAMICMANAGER:
            return context

        # deformer weights
        if component["domino_path"]["value"]:
            deformer_weights_dir = metadata_dir / "deformerWeights"
            if deformer_weights_dir.exists():
                rigkit.import_weights_from_directory(deformer_weights_dir.as_posix())

            deformers_sets = cmds.sets(DEFORMER_WEIGHTS_SETS, query=True) or []
            for deformer in component["deformer_weights"]:
                if not cmds.objExists(deformer):
                    logger.warning(
                        f"{deformer} 가 존재하지 않습니다. 설정이 뭔가 바뀌었나요?"
                    )
                    continue

                if deformer not in deformers_sets:
                    cmds.sets(deformer, edit=True, addElement=DEFORMER_WEIGHTS_SETS)

        # BREAK POINT DEFORMERWEIGHTS
        if component["break_point"] == BREAK_POINT_DEFORMERWEIGHTS:
            return context

        # deformer order
        if component["deformer_order"]:
            order_sets = cmds.sets(DEFORMER_ORDER_SETS, query=True) or []
            for geo, chain in component["deformer_order"].items():
                if not cmds.objExists(geo):
                    logger.warning(
                        f"{geo} 가 존재하지 않습니다. 설정이 뭔가 바뀌었나요?"
                    )
                    continue

                rigkit.set_deformer_chain(geo, chain)

                if geo not in order_sets:
                    cmds.sets(geo, edit=True, addElement=DEFORMER_ORDER_SETS)

        # BREAK POINT DEFORMERORDER
        if component["break_point"] == BREAK_POINT_DEFORMERORDER:
            return context

        # post custom scripts
        for script_path in component["post_custom_scripts"]["value"]:
            if not script_path:
                continue
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
        execution_time = time.perf_counter() - start_time
        minutes, seconds = divmod(execution_time, 60)
        hours, minutes = divmod(minutes, 60)

        # rig build info
        info = "Maya Version\n\t" + maya_version()
        info += "\nBifrost Version\n\t"
        info += bifrost_version()
        info += "\n\nUsed Plug-ins"
        plugins = used_plugins()
        for i in range(int(len(plugins) / 2)):
            info += f"\n\t{plugins[i * 2]:<20}{plugins[i * 2 + 1]}"
        info += f"\n\nTotal Build Time : {int(hours):01d}h {int(minutes):01d}m {seconds:4f}s"
        cmds.addAttr(RIG, longName="notes", dataType="string")
        cmds.setAttr(f"{RIG}.notes", info, type="string")
        cmds.setAttr(f"{RIG}.notes", lock=True)
        cmds.select(RIG)

        cmds.undoInfo(closeChunk=True)
        cmds.ogs(pause=True)

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
            break

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
            if hasattr(attr, "data_type") and attr.data_type == "nurbsCurve":
                temp_crv = cmds.circle(name="temp1", constructionHistory=False)[0]
                cmds.connectAttr(f"{node}.{attr.long_name}", f"{temp_crv}.create")
                ins = NurbsCurve(node=temp_crv)
                component[attr.long_name]["value"] = ins.data
                cmds.delete(temp_crv)
                continue
            elif hasattr(attr, "data_type") and attr.data_type == "nurbsSurface":
                temp_surface = cmds.nurbsPlane(name="temp1", constructionHistory=False)[
                    0
                ]
                cmds.connectAttr(f"{node}.{attr.long_name}", f"{temp_surface}.create")
                ins = NurbsSurface(node=temp_surface)
                component[attr.long_name]["value"] = ins.data
                cmds.delete(temp_surface)
                continue
            elif hasattr(attr, "data_type") and attr.data_type == "mesh":
                temp_mesh = cmds.polySphere(name="temp1", constructionHistory=False)[0]
                cmds.connectAttr(f"{node}.{attr.long_name}", f"{temp_mesh}.inMesh")
                ins = Mesh(node=temp_mesh)
                component[attr.long_name]["value"] = ins.data
                cmds.delete(temp_mesh)
                continue
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

    rig["custom_nurbscurve_data"] = []
    rig["custom_nurbssurface_data"] = []
    rig["custom_mesh_data"] = []
    for n in (
        cmds.listConnections(
            f"{RIG}.custom_nurbscurve_data", source=True, destination=False
        )
        or []
    ):
        ins = NurbsCurve(node=n)
        rig["custom_nurbscurve_data"].append(ins.data)
    for n in (
        cmds.listConnections(
            f"{RIG}.custom_nurbssurface_data", source=True, destination=False
        )
        or []
    ):
        ins = NurbsSurface(node=n)
        rig["custom_nurbssurface_data"].append(ins.data)
    for n in (
        cmds.listConnections(f"{RIG}.custom_mesh_data", source=True, destination=False)
        or []
    ):
        ins = Mesh(node=n)
        rig["custom_mesh_data"].append(ins.data)

    if not cmds.objExists(BLENDSHAPE_SETS):
        rig["blendshape"] = []
    else:
        rig["blendshape"] = cmds.sets(BLENDSHAPE_SETS, query=True) or []
    if not cmds.objExists(DEFORMER_WEIGHTS_SETS):
        rig["deformer_weights"] = []
    else:
        rig["deformer_weights"] = cmds.sets(DEFORMER_WEIGHTS_SETS, query=True) or []
    rig["deformer_order"] = {}
    if cmds.objExists(DEFORMER_ORDER_SETS):
        for geo in cmds.sets(DEFORMER_ORDER_SETS, query=True) or []:
            rig["deformer_order"][geo] = rigkit.get_deformer_chain(geo)
    return rig


def deserialize(data, create=True):
    """직렬화 한 데이터를 마야 노드로 변환합니다."""
    stack = [(data, None)]
    rig = None
    while stack:
        component_data, parent = stack.pop(0)
        module_name = component_data["component"]["value"]
        module = importlib.import_module(f"domino.component.{module_name}")
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

    rig["custom_nurbscurve_data"] = data["custom_nurbscurve_data"]
    rig["custom_nurbssurface_data"] = data["custom_nurbssurface_data"]
    rig["custom_mesh_data"] = data["custom_mesh_data"]
    rig["blendshape"] = data["blendshape"]
    rig["deformer_weights"] = data["deformer_weights"]
    rig["deformer_order"] = data["deformer_order"]
    rig["break_point"] = data["break_point"]

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

    # custom scripts 를 버전 업 된 path 로 수정합니다.
    # 수동으로 모든 파일을 버전업 하지 않게 하기 위함입니다.
    path = Path(file_path)
    metadata_dir = path.parent / (f"{path.name.split('.')[0]}.metadata")
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
        cmds.setAttr(f"{root}.pre_custom_scripts[{i}]", path, type="string")
    for i, path in enumerate(data["post_custom_scripts"]["value"]):
        cmds.setAttr(f"{root}.post_custom_scripts[{i}]", path, type="string")

    # blendshape
    if data["blendshape"]:
        blendshape_dir = metadata_dir / "blendshape"
        if not blendshape_dir.exists():
            blendshape_dir.mkdir()

        for bs in data["blendshape"]:
            rigkit.export_blendshape(blendshape_dir.as_posix(), bs)

    # space
    if cmds.objExists(SPACE_MANAGER):
        space_dir = metadata_dir / "space"
        if not space_dir.exists():
            space_dir.mkdir()
        export_space_manager_data((space_dir / "space.smf").as_posix())

    # PSD
    if cmds.objExists(PSD_MANAGER):
        pose_dir = metadata_dir / "pose"
        if not pose_dir.exists():
            pose_dir.mkdir()
        export_psd((pose_dir / "poseSpaceDeformation.psd").as_posix())

    # SDK
    if cmds.objExists(SDK_MANAGER):
        sdk_dir = metadata_dir / "sdk"
        if not sdk_dir.exists():
            sdk_dir.mkdir()
        export_sdk((sdk_dir / "setDriven.sdk").as_posix())

    # DYNAMIC
    if cmds.objExists(DYNAMIC_MANAGER):
        dynamic_dir = metadata_dir / "dynamic"
        if not dynamic_dir.exists():
            dynamic_dir.mkdir()
        export_dynamic((dynamic_dir / "dynamic.dyn").as_posix())

    # deformerWeights
    if data["deformer_weights"]:
        deformer_weights_dir = metadata_dir / "deformerWeights"
        if not deformer_weights_dir.exists():
            deformer_weights_dir.mkdir()

        rigkit.export_weights_to_directory(
            deformer_weights_dir.as_posix(), data["deformer_weights"]
        )

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Save filePath: {file_path}")


@build_log(logging.INFO)
def load(file_path, create=True, break_point=BREAK_POINT_POSTCUSTOMSCRIPTS):
    """json 을 리그로 불러옵니다."""
    if not file_path:
        return

    with open(file_path, "r") as f:
        data = json.load(f)

    logger.info(f"Load filePath: {file_path}")

    data["domino_path"]["value"] = file_path
    data["break_point"] = break_point
    rig = deserialize(data, create)

    return rig


# endregion
