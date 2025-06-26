# domino
from domino import component
from domino.core import attribute, Name, Transform, nurbscurve
from domino.core.utils import build_log

# maya
from maya.api import OpenMaya as om
from maya import cmds

# built-ins
import logging


# region Initialize Settings
ORIGINMATRIX = om.MMatrix()
matrices = [list(ORIGINMATRIX) for _ in range(3)]
DATA = [
    attribute.String(longName="component", value="uicontainer01"),
    attribute.String(longName="name", value="uiContainer"),
    attribute.Matrix(longName="guide_matrix", multi=True, value=matrices),
    attribute.Matrix(longName="npo_matrix", multi=True, value=matrices),
    attribute.Matrix(
        longName="initialize_output_matrix",
        multi=True,
        value=[list(ORIGINMATRIX)],
    ),
    attribute.Matrix(
        longName="initialize_output_inverse_matrix",
        multi=True,
        value=[list(ORIGINMATRIX)],
    ),
    attribute.Integer(longName="guide_mirror_type", multi=True, value=[2, 2]),
    # 부모로 사용할 상위 component 의 output index
    attribute.Integer(
        longName="parent_output_index", minValue=-1, defaultValue=-1, value=-1
    ),
    # output joint 생성 option
    attribute.Bool(longName="create_output_joint", value=1),
    # text.
    attribute.String(longName="container_text", value="uiConatinerText"),
    # slider 갯수.
    attribute.Integer(longName="slider_count", minValue=1, value=1),
    # slider side. ["", "L", "R"]
    attribute.Integer(longName="slider_side", multi=True, value=[0, 0]),
    # slider description.
    attribute.String(longName="slider_description", multi=True, value=["slider0"]),
    # slider keyable attribute. +tx, -tx, +ty, -ty. 1 은 on 0 은 off.
    attribute.String(
        longName="slider_keyable_attribute", multi=True, value=["1,1,1,1"]
    ),
    # slider keyable attribute 이름. +tx, -tx, +ty, -ty.
    attribute.String(
        longName="slider_keyable_attribute_name",
        multi=True,
        value=[",,,"],
    ),
]

description = """## uicontainer01
---

ui 을 생성합니다.

#### Settings
- container text
> 텍스트
- slider count
> slider controller 의 개수입니다.
- slider_side
> slider controller 의 side 입니다. 
- slider_description
> slider 의 설명 입니다.
- slider_keyable_attribute
> slider 가 +tx, -tx, +ty, -ty 중 어떤것을 사용할지 정합니다.
- slider_keyable_attribute_name
> slider 의 각 attribute에 대한 description 입니다.

controller 의 값은 바로 사용 할 수 있도록 output joint 로 연결됩니다.  

output joint 의 attribute name 은 다음과 같이 결정됩니다.  
1. attribute name 이 없을때  
> {slider_description}{side}_tx_plus
2. attribute name 이 있을때
> {attribute_name}{side}
"""


# endregion


class Rig(component.Rig):

    @property
    def identifier(self):
        return self["name"]["value"], "", ""

    def __init__(self):
        super().__init__(DATA)

    def populate_controller(self):
        if not self["controller"]:
            self.add_controller(description="frame", parent_controllers=[])
            self.add_controller(
                description="text", parent_controllers=[(self.identifier, "frame")]
            )
            for i in range(self["slider_count"]["value"]):
                side = Name.side_str_list[self["slider_side"]["value"][i]]
                if side == "C":
                    side = ""
                description = self["slider_description"]["value"][i]
                self.add_controller(
                    description=f"{description}{side}",
                    parent_controllers=[(self.identifier, "frame")],
                )

    def populate_output(self):
        if not self["output"]:
            self.add_output(description="frame", extension=Name.controller_extension)

    def populate_output_joint(self):
        if not self["output_joint"]:
            self.add_output_joint(parent_description=None, description="")

    # region RIG
    @build_log(logging.INFO)
    def rig(self):
        super().rig(description=description)

        name, _, _ = self.identifier
        # frame
        frame_npo, frame_ctl = self["controller"][0].create(
            parent=self.rig_root,
            shape=(
                self["controller"][0]["shape"]
                if "shape" in self["controller"][0]
                else "uicontainer"
            ),
            color=12,
            npo_matrix_index=0,
        )
        cmds.setAttr(f"{frame_ctl}.sx", keyable=True)
        cmds.setAttr(f"{frame_ctl}.sy", keyable=True)
        cmds.setAttr(f"{frame_ctl}.sz", keyable=True)
        cmds.setAttr(f"{frame_ctl}.rotateOrder", keyable=False, channelBox=False)
        # output
        self["output"][0].connect()
        # output joint
        if self["create_output_joint"]["value"]:
            output_joint = self["output_joint"][0].create()

        # text
        text_npo, text_ctl = self["controller"][1].create(
            parent=frame_ctl,
            shape=(
                self["controller"][1]["shape"]
                if "shape" in self["controller"][1]
                else "cube"
            ),
            color=12,
            npo_matrix_index=1,
        )
        grp, temp = cmds.textCurves(
            name="uicontainer_text", text=self["container_text"]["value"]
        )
        cmds.setAttr(f"{grp}.t", lock=True, keyable=False)
        cmds.setAttr(f"{grp}.r", lock=True, keyable=False)
        cmds.setAttr(f"{grp}.s", lock=True, keyable=False)
        cmds.parent(grp, text_ctl)
        cmds.setAttr(f"{grp}.overrideEnabled", 1)
        cmds.setAttr(f"{grp}.overrideDisplayType", 2)
        cmds.delete(temp)

        shapes = cmds.listRelatives(text_ctl, shapes=True)
        if shapes:
            cmds.delete(shapes)
        cmds.setAttr(text_ctl + ".t", lock=True)
        cmds.setAttr(text_ctl + ".r", lock=True)
        cmds.setAttr(text_ctl + ".s", lock=True)

        for i in range(self["slider_count"]["value"]):
            # controller
            npo, ctl = self["controller"][i + 2].create(
                parent=frame_ctl,
                shape="uislidercontrol",
                color=12,
                npo_matrix_index=i + 2,
            )
            cmds.setAttr(f"{ctl}.tz", lock=True, keyable=False)
            cmds.setAttr(f"{ctl}.rx", lock=True, keyable=False)
            cmds.setAttr(f"{ctl}.ry", lock=True, keyable=False)
            cmds.setAttr(f"{ctl}.rz", lock=True, keyable=False)
            cmds.setAttr(f"{ctl}.sx", lock=True, keyable=False)
            cmds.setAttr(f"{ctl}.sy", lock=True, keyable=False)
            cmds.setAttr(f"{ctl}.sz", lock=True, keyable=False)
            cmds.setAttr(f"{ctl}.rotateOrder", keyable=False, channelBox=False)
            # mirror ctl name
            _side = Name.side_str_list[self["slider_side"]["value"][i]]
            if _side == "C":
                _side = ""
            _description = f"{self['slider_description']['value'][i]}{_side}"
            mirror_ctl_name = Name.create(
                convention=Name.controller_name_convention,
                name=self["name"]["value"],
                side="",
                index="",
                description=_description,
                extension=Name.controller_extension,
            )
            cmds.setAttr(
                f"{ctl}.mirror_controller_name", mirror_ctl_name, type="string"
            )
            npo_m = cmds.xform(npo, query=True, matrix=True, worldSpace=True)
            ins = Transform(
                parent=npo,
                name=self["name"]["value"],
                side="",
                index="",
                description=_description,
                extension="frame",
                m=npo_m,
            )
            t = ins.create()
            f = nurbscurve.create("uisliderframe", color=om.MColor((1, 1, 0)), m=npo_m)
            nurbscurve.replace_shape(f, t)
            cmds.delete(f)
            cmds.setAttr(f"{t}Shape.overrideEnabled", 1)
            cmds.setAttr(f"{t}Shape.overrideDisplayType", 2)
            line = nurbscurve.create(
                "uisliderguideline", color=om.MColor((1, 1, 0)), m=npo_m
            )
            line = cmds.rename(line, f"{name}_{_description}{_side}_mtxline")
            cmds.setAttr(f"{line}.template", 1)
            cmds.parent(line, t)
            line = nurbscurve.create(
                "uisliderguideline", color=om.MColor((1, 1, 0)), m=npo_m
            )
            line = cmds.rename(line, f"{name}_{_description}{_side}_mtyline")
            cmds.setAttr(f"{line}.rz", 90)
            cmds.setAttr(f"{line}.template", 1)
            cmds.parent(line, t)
            line = nurbscurve.create(
                "uisliderguideline", color=om.MColor((1, 1, 0)), m=npo_m
            )
            line = cmds.rename(line, f"{name}_{_description}{_side}_ptxline")
            cmds.setAttr(f"{line}.rz", 180)
            cmds.setAttr(f"{line}.template", 1)
            cmds.parent(line, t)
            line = nurbscurve.create(
                "uisliderguideline", color=om.MColor((1, 1, 0)), m=npo_m
            )
            line = cmds.rename(line, f"{name}_{_description}{_side}_ptyline")
            cmds.setAttr(f"{line}.rz", 270)
            cmds.setAttr(f"{line}.template", 1)
            cmds.parent(line, t)

            max_tx, min_tx, max_ty, min_ty = self["slider_keyable_attribute"]["value"][
                i
            ].split(",")
            attribute_names = self["slider_keyable_attribute_name"]["value"][i].split(
                ","
            )

            cmds.transformLimits(
                ctl,
                translationX=(-1 * int(min_tx), int(max_tx)),
                enableTranslationX=(1, 1),
            )
            cmds.transformLimits(
                ctl,
                translationY=(-1 * int(min_ty), int(max_ty)),
                enableTranslationY=(1, 1),
            )

            rv_setup = [(".tx", 1), (".tx", -1), (".ty", 1), (".ty", -1)]
            states = [int(min_tx), int(max_tx), int(min_ty), int(max_ty)]

            c = -1
            for s, state, attr_name in zip(rv_setup, states, attribute_names):
                c += 1
                if not state:
                    if c == 0:
                        cmds.move(
                            1,
                            0,
                            0,
                            [f"{t}.cv[0]", f"{t}.cv[4]", f"{t}.cv[3]"],
                            objectSpace=True,
                            relative=True,
                        )
                    if c == 1:
                        cmds.move(
                            -1,
                            0,
                            0,
                            [f"{t}.cv[1]", f"{t}.cv[2]"],
                            objectSpace=True,
                            relative=True,
                        )
                    if c == 2:
                        cmds.move(
                            0,
                            1,
                            0,
                            [f"{t}.cv[2]", f"{t}.cv[3]"],
                            objectSpace=True,
                            relative=True,
                        )
                    if c == 3:
                        cmds.move(
                            0,
                            -1,
                            0,
                            [f"{t}.cv[0]", f"{t}.cv[4]", f"{t}.cv[1]"],
                            objectSpace=True,
                            relative=True,
                        )
                    continue
                if attr_name:
                    attr_name = f"{attr_name}{_side}"
                elif not attr_name:
                    attr_name = f"{_description}{_side}{s[0].replace('.', '_')}_{('plus' if s[1] == 1 else 'minus')}"
                cmds.addAttr(
                    output_joint,
                    longName=attr_name,
                    attributeType="float",
                    keyable=True,
                )
                rv = cmds.createNode("remapValue")
                cmds.setAttr(f"{rv}.inputMax", s[1])
                cmds.connectAttr(f"{ctl}{s[0]}", f"{rv}.inputValue")
                cmds.connectAttr(f"{rv}.outValue", f"{output_joint}.{attr_name}")

    # endregion

    # region GUIDE
    @build_log(logging.INFO)
    def guide(self):
        super().guide(description=description)
        self.add_guide_graph()
        guide_count = len(self["guide_matrix"]["value"])
        if len(self["guide_mirror_type"]["value"]) != guide_count:
            self["guide_mirror_type"]["value"] = [1 for _ in range(guide_count)]

        frame_guide = self.add_guide(
            parent=self.guide_root,
            description="frame",
            m=self["guide_matrix"]["value"][0],
            mirror_type=self["guide_mirror_type"]["value"][0],
        )
        cmds.connectAttr(
            f"{self.guide_graph}.npo_matrix[0]",
            f"{self.guide_root}.npo_matrix[0]",
        )
        cmds.connectAttr(
            f"{self.guide_graph}.initialize_output_matrix[0]",
            f"{self.guide_root}.initialize_output_matrix[0]",
        )
        cmds.connectAttr(
            f"{self.guide_graph}.initialize_output_inverse_matrix[0]",
            f"{self.guide_root}.initialize_output_inverse_matrix[0]",
        )
        text_guide = self.add_guide(
            parent=frame_guide,
            description="text",
            m=self["guide_matrix"]["value"][1],
            mirror_type=self["guide_mirror_type"]["value"][1],
        )
        cmds.connectAttr(
            f"{self.guide_graph}.npo_matrix[1]",
            f"{self.guide_root}.npo_matrix[1]",
        )
        cmds.connectAttr(
            f"{self.guide_graph}.initialize_output_matrix[1]",
            f"{self.guide_root}.initialize_output_matrix[1]",
        )
        cmds.connectAttr(
            f"{self.guide_graph}.initialize_output_inverse_matrix[1]",
            f"{self.guide_root}.initialize_output_inverse_matrix[1]",
        )
        cmds.setAttr(f"{frame_guide}.sx", lock=False, keyable=True)
        cmds.setAttr(f"{frame_guide}.sy", lock=False, keyable=True)
        cmds.setAttr(f"{frame_guide}.sz", lock=False, keyable=True)
        cmds.setAttr(f"{text_guide}.sx", lock=False, keyable=True)
        cmds.setAttr(f"{text_guide}.sy", lock=False, keyable=True)
        cmds.setAttr(f"{text_guide}.sz", lock=False, keyable=True)
        for i in range(self["slider_count"]["value"]):
            _side = Name.side_str_list[self["slider_side"]["value"][i]]
            if _side == "C":
                _side = ""
            _description = f"{self['slider_description']['value'][i]}{_side}"
            # guide
            guide = self.add_guide(
                parent=frame_guide,
                description=_description,
                m=self["guide_matrix"]["value"][i + 2],
                mirror_type=self["guide_mirror_type"]["value"][i + 2],
            )

            cmds.connectAttr(
                f"{self.guide_graph}.npo_matrix[{i + 2}]",
                f"{self.guide_root}.npo_matrix[{i + 2}]",
            )
            cmds.connectAttr(
                f"{self.guide_graph}.initialize_output_matrix[{i + 2}]",
                f"{self.guide_root}.initialize_output_matrix[{i + 2}]",
            )
            cmds.connectAttr(
                f"{self.guide_graph}.initialize_output_inverse_matrix[{i + 2}]",
                f"{self.guide_root}.initialize_output_inverse_matrix[{i + 2}]",
            )
            cmds.setAttr(f"{guide}.sx", lock=False, keyable=True)
            cmds.setAttr(f"{guide}.sy", lock=False, keyable=True)
            cmds.setAttr(f"{guide}.sz", lock=False, keyable=True)

    # endregion
