# domino
from domino import component
from domino.core import attribute, Name, Transform, Joint
from domino.core.utils import build_log

# maya
from maya.api import OpenMaya as om
from maya import cmds

# built-ins
import logging


# region Initialize Settings
ORIGINMATRIX = om.MMatrix()
matrices = [list(ORIGINMATRIX) for _ in range(2)]
DATA = [
    attribute.String(longName="component", value="fk01"),
    attribute.String(longName="name", value="fk"),
    attribute.Enum(longName="side", enumName=Name.side_list, value=0),
    attribute.Integer(longName="index", minValue=0),
    attribute.Matrix(longName="guide_matrix", multi=True, value=matrices),
    attribute.Matrix(longName="npo_matrix", multi=True, value=matrices),
    attribute.Matrix(
        longName="initialize_output_matrix",
        multi=True,
        value=matrices,
    ),
    attribute.Matrix(
        longName="initialize_output_inverse_matrix",
        multi=True,
        value=matrices,
    ),
    attribute.Integer(longName="guide_mirror_type", multi=True, value=[1, 1]),
    # 부모로 사용할 상위 component 의 output index
    attribute.Integer(
        longName="parent_output_index", minValue=-1, defaultValue=-1, value=-1
    ),
    # output joint 생성 option
    attribute.Bool(longName="create_output_joint", value=1),
    # root 수.
    attribute.Integer(longName="root_count", minValue=1, value=1),
    # root 당 chain 수.
    attribute.Integer(longName="chain_count", minValue=2, value=[2], multi=True),
    # offset output rotate
    attribute.DoubleAngle(
        longName="offset_output_rotate_x", minValue=-360, maxValue=360
    ),
    attribute.DoubleAngle(
        longName="offset_output_rotate_y", minValue=-360, maxValue=360
    ),
    attribute.DoubleAngle(
        longName="offset_output_rotate_z", minValue=-360, maxValue=360
    ),
]

description = """## fk01
---

fk chain 을 생성합니다.

#### Settings
- Root Count
> Fk chain 의 수입니다.
- chain count
> chiain 당 controller 수입니다"""

# endregion


class Rig(component.Rig):

    def __init__(self):
        super().__init__(DATA)

    def populate_controller(self):
        if not self["controller"]:
            for root_i in range(self["root_count"]["value"]):
                parent_controllers = []
                for chain_i in range(self["chain_count"]["value"][root_i]):
                    self.add_controller(
                        description=f"{root_i}fk{chain_i}",
                        parent_controllers=parent_controllers,
                    )
                    parent_controllers = [(self.identifier, f"{root_i}fk{chain_i}")]

    def populate_output(self):
        if not self["output"]:
            for root_i in range(self["root_count"]["value"]):
                for chain_i in range(self["chain_count"]["value"][root_i]):
                    self.add_output(
                        description=f"{root_i}fk{chain_i}",
                        extension="output",
                    )

    def populate_output_joint(self):
        if not self["output_joint"]:
            for root_i in range(self["root_count"]["value"]):
                parent_description = None
                for chain_i in range(self["chain_count"]["value"][root_i]):
                    self.add_output_joint(
                        parent_description=parent_description,
                        description=f"{root_i}fk{chain_i}",
                    )
                    parent_description = f"{root_i}fk{chain_i}"

    # region RIG
    @build_log(logging.INFO)
    def rig(self):
        super().rig(description=description)

        name, side, index = self.identifier

        count = 0
        for root_i in range(self["root_count"]["value"]):
            parent = self.rig_root
            for chain_i in range(self["chain_count"]["value"][root_i]):
                # controller
                npo, ctl = self["controller"][count].create(
                    parent=parent,
                    shape=(
                        self["controller"][count]["shape"]
                        if "shape" in self["controller"][count]
                        else "cube"
                    ),
                    color=12,
                    npo_matrix_index=count,
                )
                cmds.connectAttr(
                    f"{self.rig_root}.guide_mirror_type[{count}]", f"{ctl}.mirror_type"
                )

                ins = Transform(
                    parent=ctl,
                    name=name,
                    side=side,
                    index=index,
                    description=f"{root_i}fk{chain_i}",
                    extension=Name.loc_extension,
                    m=cmds.xform(ctl, query=True, matrix=True, worldSpace=True),
                )
                loc = ins.create()

                # inverse scale 일 경우 output joint 에 -1 이 적용되지 않도록 loc scaleZ 설정.
                source = cmds.listConnections(
                    f"{npo}.offsetParentMatrix",
                    source=True,
                    destination=False,
                    plugs=True,
                )[0]
                decom_m = cmds.createNode("decomposeMatrix")
                cmds.connectAttr(source, decom_m + ".inputMatrix")

                condition = cmds.createNode("condition")
                cmds.setAttr(condition + ".operation", 4)
                cmds.setAttr(condition + ".colorIfTrueR", -1)
                cmds.connectAttr(decom_m + ".outputScaleZ", condition + ".firstTerm")
                cmds.connectAttr(condition + ".outColorR", loc + ".sz")

                # output
                ins = Joint(
                    parent=self.rig_root,
                    name=name,
                    side=side,
                    index=index,
                    description=f"{root_i}fk{chain_i}",
                    extension="output",
                    m=ORIGINMATRIX,
                )
                output = ins.create()
                mult_m = cmds.createNode("multMatrix")
                cmds.connectAttr(f"{loc}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
                cmds.connectAttr(
                    f"{self.rig_root}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
                )
                cmds.connectAttr(f"{mult_m}.matrixSum", f"{output}.offsetParentMatrix")
                cmds.setAttr(f"{output}.drawStyle", 2)
                self["output"][count].connect()

                # output joint
                if self["create_output_joint"]["value"]:
                    self["output_joint"][count].create()

                count += 1
                parent = loc

    # endregion

    # region GUIDE
    @build_log(logging.INFO)
    def guide(self):
        super().guide(description=description)
        graph, guide_compound = self.add_guide_graph()
        cmds.vnnNode(
            graph,
            "/input",
            createOutputPort=("root_count", "long"),
        )
        cmds.vnnNode(
            graph,
            "/input",
            createOutputPort=("chain_count", "array<long>"),
        )
        cmds.vnnConnect(
            graph,
            "/input.root_count",
            f"/{guide_compound}.root_count",
        )
        cmds.vnnConnect(
            graph,
            "/input.chain_count",
            f"/{guide_compound}.chain_count",
        )
        cmds.connectAttr(f"{self.guide_root}.root_count", f"{graph}.root_count")
        cmds.connectAttr(f"{self.guide_root}.chain_count", f"{graph}.chain_count")

        guide_count = len(self["guide_matrix"]["value"])
        if len(self["guide_mirror_type"]["value"]) != guide_count:
            self["guide_mirror_type"]["value"] = [1 for _ in range(guide_count)]

        count = 0
        for root_i in range(self["root_count"]["value"]):
            parent = self.guide_root
            for chain_i in range(self["chain_count"]["value"][root_i]):
                pass
                # guide
                guide = self.add_guide(
                    parent=parent,
                    description=f"{root_i}fk{chain_i}",
                    m=self["guide_matrix"]["value"][count],
                    mirror_type=self["guide_mirror_type"]["value"][count],
                )

                cmds.connectAttr(
                    f"{self.guide_graph}.npo_matrix[{count}]",
                    f"{self.guide_root}.npo_matrix[{count}]",
                )
                cmds.connectAttr(
                    f"{self.guide_graph}.initialize_output_matrix[{count}]",
                    f"{self.guide_root}.initialize_output_matrix[{count}]",
                )
                cmds.connectAttr(
                    f"{self.guide_graph}.initialize_output_inverse_matrix[{count}]",
                    f"{self.guide_root}.initialize_output_inverse_matrix[{count}]",
                )
                count += 1
                parent = guide

    # endregion
