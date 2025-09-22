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
matrices = [list(ORIGINMATRIX)]
DATA = [
    attribute.String(longName="component", value="control01"),
    attribute.String(longName="name", value="control"),
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
    attribute.Integer(longName="guide_mirror_type", multi=True, value=[1]),
    # 부모로 사용할 상위 component 의 output index
    attribute.Integer(
        longName="parent_output_index", minValue=-1, defaultValue=-1, value=-1
    ),
    # output joint 생성 option
    attribute.Bool(longName="create_output_joint", value=1),
    # controlelr 갯수.
    attribute.Integer(longName="controller_count", minValue=1, value=1),
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

description = """## control01
---

개별 컨트롤러를 생성합니다.   

#### Settings
- Controller count
> Controller 의 수입니다."""

# endregion


class Rig(component.Rig):

    def __init__(self):
        super().__init__(DATA)

    def populate_controller(self):
        if not self["controller"]:
            for i in range(len(self["guide_matrix"]["value"])):
                self.add_controller(description=i, parent_controllers=[])

    def populate_output(self):
        if not self["output"]:
            for i in range(len(self["guide_matrix"]["value"])):
                self.add_output(description=i, extension=Name.output_extension)

    def populate_output_joint(self):
        if not self["output_joint"]:
            for i in range(len(self["guide_matrix"]["value"])):
                self.add_output_joint(parent_description=None, description=i)

    # region RIG
    @build_log(logging.INFO)
    def rig(self):
        super().rig(description=description)

        name, side, index = self.identifier

        for i, m in enumerate(self["guide_matrix"]["value"]):
            # controller
            npo, ctl = self["controller"][i].create(
                parent=self.rig_root,
                shape=(
                    self["controller"][i]["shape"]
                    if "shape" in self["controller"][i]
                    else "cube"
                ),
                color=12,
                npo_matrix_index=i,
            )
            cmds.connectAttr(
                f"{self.rig_root}.guide_mirror_type[{i}]", f"{ctl}.mirror_type"
            )

            ins = Transform(
                parent=ctl,
                name=name,
                side=side,
                index=index,
                description=i,
                extension=Name.loc_extension,
                m=cmds.xform(ctl, query=True, matrix=True, worldSpace=True),
            )
            loc = ins.create()

            # inverse scale 일 경우 output joint 에 -1 이 적용되지 않도록 loc scaleZ 설정.
            source = cmds.listConnections(
                f"{npo}.offsetParentMatrix", source=True, destination=False, plugs=True
            )[0]
            decom_m = cmds.createNode("decomposeMatrix")
            cmds.connectAttr(source, f"{decom_m}.inputMatrix")

            condition = cmds.createNode("condition")
            cmds.setAttr(f"{condition}.operation", 4)
            cmds.setAttr(f"{condition}.colorIfTrueR", -1)
            cmds.connectAttr(f"{decom_m}.outputScaleZ", f"{condition}.firstTerm")
            cmds.connectAttr(f"{condition}.outColorR", f"{loc}.sz")

            # output
            ins = Joint(
                self.rig_root,
                name=name,
                side=side,
                index=index,
                description=i,
                extension=Name.output_extension,
                m=ORIGINMATRIX,
            )
            output = ins.create()
            self["output"][i].connect()
            mult_m = cmds.createNode("multMatrix")
            cmds.connectAttr(f"{loc}.worldMatrix[0]", f"{mult_m}.matrixIn[0]")
            cmds.connectAttr(
                f"{self.rig_root}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
            )
            cmds.connectAttr(f"{mult_m}.matrixSum", f"{output}.offsetParentMatrix")
            cmds.setAttr(f"{output}.drawStyle", 2)

            # output joint
            if self["create_output_joint"]["value"]:
                self["output_joint"][i].create()

    # endregion

    # region GUIDE
    @build_log(logging.INFO)
    def guide(self):
        super().guide(description=description)
        self.add_guide_graph()
        guide_count = len(self["guide_matrix"]["value"])
        if len(self["guide_mirror_type"]["value"]) != guide_count:
            self["guide_mirror_type"]["value"] = [1 for _ in range(guide_count)]

        for i, m in enumerate(self["guide_matrix"]["value"]):
            # guide
            guide = self.add_guide(
                parent=self.guide_root,
                description=i,
                m=m,
                mirror_type=self["guide_mirror_type"]["value"][i],
            )

            cmds.connectAttr(
                f"{self.guide_graph}.npo_matrix[{i}]",
                f"{self.guide_root}.npo_matrix[{i}]",
            )
            cmds.connectAttr(
                f"{self.guide_graph}.initialize_output_matrix[{i}]",
                f"{self.guide_root}.initialize_output_matrix[{i}]",
            )
            cmds.connectAttr(
                f"{self.guide_graph}.initialize_output_inverse_matrix[{i}]",
                f"{self.guide_root}.initialize_output_inverse_matrix[{i}]",
            )

    # endregion
