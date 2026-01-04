# domino
from domino import component, psdmanager
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
    attribute.String(longName="component", value="psd01"),
    attribute.String(longName="name", value="psd"),
    attribute.Enum(longName="side", enumName=Name.side_list, value=0),
    attribute.Integer(longName="index", minValue=0),
    attribute.Matrix(longName="guide_matrix", multi=True, value=matrices),
    attribute.Matrix(longName="npo_matrix", multi=True, value=matrices),
    attribute.Matrix(
        longName="initialize_output_matrix",
        multi=True,
        value=matrices * 2,
    ),
    attribute.Matrix(
        longName="initialize_output_inverse_matrix",
        multi=True,
        value=matrices * 2,
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

description = """## psd01
---

psd 용 컨트롤러를 생성합니다.   

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
                self.add_output(
                    description=f"neutral{i}", extension=Name.output_extension
                )
                self.add_output(description=i, extension=Name.output_extension)

    def populate_output_joint(self):
        if not self["output_joint"]:
            for i in range(len(self["guide_matrix"]["value"])):
                self.add_output_joint(
                    parent_description=None, description=f"neutral{i}"
                )
                self.add_output_joint(parent_description=f"neutral{i}", description=i)

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
                    else "axis"
                ),
                color=12,
            )
            ctl = cmds.rename(
                ctl, ctl.replace(Name.controller_extension, Name.psd_extension)
            )
            cmds.addAttr(
                ctl, longName="is_psd_controller", attributeType="bool", keyable=False
            )
            cmds.setAttr(f"{ctl}.tx", channelBox=True)
            cmds.setAttr(f"{ctl}.ty", channelBox=True)
            cmds.setAttr(f"{ctl}.tz", channelBox=True)
            cmds.setAttr(f"{ctl}.rx", channelBox=True)
            cmds.setAttr(f"{ctl}.ry", channelBox=True)
            cmds.setAttr(f"{ctl}.rz", channelBox=True)
            cmds.setAttr(f"{ctl}.sx", channelBox=True, lock=False)
            cmds.setAttr(f"{ctl}.sy", channelBox=True, lock=False)
            cmds.setAttr(f"{ctl}.sz", channelBox=True, lock=False)
            cmds.setAttr(f"{ctl}.ro", channelBox=False)
            cmds.setAttr(f"{ctl}.v", keyable=False, channelBox=True)
            cmds.setAttr(f"{ctl}.v", False)
            cmds.connectAttr(
                f"{self.rig_root}.guide_mirror_type[{i}]", f"{ctl}.mirror_type"
            )
            cmds.connectAttr(
                f"{self.rig_root}.npo_matrix[{i}]", f"{npo}.offsetParentMatrix"
            )
            ins = Transform(
                parent=npo,
                name=name,
                side=side,
                index=index,
                description=f"neutral{i}",
                extension=Name.loc_extension,
                m=cmds.xform(npo, query=True, matrix=True, worldSpace=True),
            )
            npo_loc = ins.create()

            ins = Transform(
                parent=ctl,
                name=name,
                side=side,
                index=index,
                description=i,
                extension=Name.loc_extension,
                m=cmds.xform(ctl, query=True, matrix=True, worldSpace=True),
            )
            ctl_loc = ins.create()

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
            cmds.connectAttr(f"{condition}.outColorR", f"{npo_loc}.sz")
            cmds.connectAttr(f"{condition}.outColorR", f"{ctl_loc}.sz")

            if not cmds.objExists(psdmanager.PSD_SETS):
                cmds.sets(name=psdmanager.PSD_SETS, empty=True)
                cmds.sets(psdmanager.PSD_SETS, edit=True, addElement=component.RIG_SETS)
            cmds.sets(ctl, edit=True, addElement=psdmanager.PSD_SETS)

            # output
            ins = Joint(
                self.rig_root,
                name=name,
                side=side,
                index=index,
                description=f"neutral{i}",
                extension=Name.output_extension,
                m=ORIGINMATRIX,
            )
            npo_output = ins.create()
            self["output"][i * 2].connect(npo_loc)
            cmds.setAttr(f"{npo_output}.drawStyle", 2)

            ins = Joint(
                self.rig_root,
                name=name,
                side=side,
                index=index,
                description=i,
                extension=Name.output_extension,
                m=ORIGINMATRIX,
            )
            ctl_output = ins.create()
            self["output"][i * 2 + 1].connect(ctl_loc)
            cmds.setAttr(f"{ctl_output}.drawStyle", 2)

            # output joint
            if self["create_output_joint"]["value"]:
                self["output_joint"][i * 2].create()
                self["output_joint"][i * 2 + 1].create()

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

            decom_m = cmds.createNode("decomposeMatrix")
            cmds.connectAttr(
                f"{self.guide_graph}.npo_matrix[{i}]", f"{decom_m}.inputMatrix"
            )
            compose_m = cmds.createNode("composeMatrix")
            cmds.connectAttr(
                f"{decom_m}.outputTranslate", f"{compose_m}.inputTranslate"
            )
            cmds.connectAttr(f"{decom_m}.outputRotate", f"{compose_m}.inputRotate")
            cmds.connectAttr(f"{decom_m}.outputShear", f"{compose_m}.inputShear")
            for z in range(3):
                output_s = [".outputScaleX", ".outputScaleY", ".outputScaleZ"]
                input_s = [".inputScaleX", ".inputScaleY", ".inputScaleZ"]
                round = cmds.createNode("round")
                cmds.connectAttr(f"{decom_m}{output_s[z]}", f"{round}.input")
                cmds.connectAttr(f"{round}.output", f"{compose_m}{input_s[z]}")
            cmds.connectAttr(
                f"{compose_m}.outputMatrix", f"{self.guide_root}.npo_matrix[{i}]"
            )
            cmds.connectAttr(
                f"{self.guide_graph}.initialize_output_matrix[{i}]",
                f"{self.guide_root}.initialize_output_matrix[{i * 2}]",
            )
            cmds.connectAttr(
                f"{self.guide_graph}.initialize_output_matrix[{i}]",
                f"{self.guide_root}.initialize_output_matrix[{i * 2 + 1}]",
            )
            cmds.connectAttr(
                f"{self.guide_graph}.initialize_output_inverse_matrix[{i}]",
                f"{self.guide_root}.initialize_output_inverse_matrix[{i * 2}]",
            )
            cmds.connectAttr(
                f"{self.guide_graph}.initialize_output_inverse_matrix[{i}]",
                f"{self.guide_root}.initialize_output_inverse_matrix[{i * 2 + 1}]",
            )

    # endregion
