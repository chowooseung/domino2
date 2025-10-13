# domino
from domino import component
from domino.core import (
    attribute,
    Name,
    controller_extension,
    joint_extension,
    center,
    left,
    right,
)
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
    attribute.String(longName="component", value="assembly"),
    attribute.String(longName="side_c_str", value=center),
    attribute.String(longName="side_l_str", value=left),
    attribute.String(longName="side_r_str", value=right),
    attribute.String(longName="controller_extension", value=controller_extension),
    attribute.String(longName="joint_extension", value=joint_extension),
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
    attribute.Bool(longName="run_pre_custom_scripts", value=0),
    attribute.String(longName="pre_custom_scripts", multi=True),
    attribute.String(longName="pre_custom_scripts_str", multi=True),
    attribute.Bool(longName="run_post_custom_scripts", value=0),
    attribute.String(longName="post_custom_scripts", multi=True),
    attribute.String(longName="post_custom_scripts_str", multi=True),
    attribute.String(longName="domino_path"),
]

description = """## assembly
---

최상위 component.   

#### Guide
> guide 는 controller 를 조절하지 않습니다. 다른 guide를 drive하거나 할 때 사용됩니다.


#### Settings
- Custom Scripts  
> build 시 같이 실행되는 pre, post script 를 관리합니다.  
> Manager 에서 domino path 를 버전업 하게되면 script 또한 버전업 되어서 저장됩니다."""
# endregion


class Rig(component.Rig):

    @property
    def identifier(self):
        return "origin", "", ""

    def __init__(self):
        super().__init__(DATA)

    def populate_controller(self):
        if not self["controller"]:
            self._controller = []
            self.add_controller(description="", parent_controllers=[])
            self.add_controller(
                description="sub", parent_controllers=[(self.identifier, "")]
            )

    def populate_output(self):
        if not self["output"]:
            self.add_output(description="sub", extension=Name.controller_extension)

    def populate_output_joint(self):
        if not self["output_joint"]:
            self.add_output_joint(parent_description=None, description="")

    # region RIG
    @build_log(logging.INFO)
    def rig(self):
        super().rig(description=description)
        name, side, index = self.identifier

        Name.side_str_list = (
            self["side_c_str"]["value"],
            self["side_l_str"]["value"],
            self["side_r_str"]["value"],
        )
        Name.controller_extension = self["controller_extension"]["value"]
        Name.joint_extension = self["joint_extension"]["value"]

        # controller
        origin_npo, origin_ctl = self["controller"][0].create(
            parent=self.rig_root,
            shape=(
                self["controller"][0]["shape"]
                if "shape" in self["controller"][0]
                else "origin"
            ),
            color=17,
        )
        cmds.addAttr(
            origin_ctl,
            longName="global_scale",
            attributeType="float",
            minValue=0,
            keyable=True,
            defaultValue=1,
        )
        cmds.setAttr(f"{origin_ctl}.sx", lock=False)
        cmds.setAttr(f"{origin_ctl}.sy", lock=False)
        cmds.setAttr(f"{origin_ctl}.sz", lock=False)
        cmds.connectAttr(f"{origin_ctl}.global_scale", f"{origin_ctl}.sx")
        cmds.connectAttr(f"{origin_ctl}.global_scale", f"{origin_ctl}.sy")
        cmds.connectAttr(f"{origin_ctl}.global_scale", f"{origin_ctl}.sz")
        cmds.setAttr(f"{origin_ctl}.sx", lock=True, keyable=False)
        cmds.setAttr(f"{origin_ctl}.sy", lock=True, keyable=False)
        cmds.setAttr(f"{origin_ctl}.sz", lock=True, keyable=False)
        cmds.setAttr(f"{origin_ctl}.rx", lock=True, keyable=False)
        cmds.setAttr(f"{origin_ctl}.rz", lock=True, keyable=False)

        sub_npo, sub_ctl = self["controller"][1].create(
            parent=origin_ctl,
            shape=(
                self["controller"][1]["shape"]
                if "shape" in self["controller"][1]
                else "wave"
            ),
            color=21,
        )
        # output
        self["output"][0].connect()

        # output joint
        self["output_joint"][0].create()

    # endregion

    # region GUIDE
    @build_log(logging.INFO)
    def guide(self):
        super().guide(description=description)
        m = cmds.getAttr(f"{self.rig_root}.guide_matrix[0]")
        guide = self.add_guide(
            parent=self.guide_root,
            description="",
            m=m,
            mirror_type=self["guide_mirror_type"]["value"][0],
        )
        cmds.setAttr(f"{guide}.tx", lock=True, keyable=False)
        cmds.setAttr(f"{guide}.ty", lock=True, keyable=False)
        cmds.setAttr(f"{guide}.tz", lock=True, keyable=False)
        cmds.setAttr(f"{guide}.rx", lock=True, keyable=False)
        cmds.setAttr(f"{guide}.ry", lock=True, keyable=False)
        cmds.setAttr(f"{guide}.rz", lock=True, keyable=False)
        cmds.addAttr(
            guide,
            longName="asset_scale",
            attributeType="float",
            keyable=True,
            defaultValue=1,
        )
        cmds.connectAttr(f"{guide}.asset_scale", f"{self.guide_root}.asset_scale")
        pick_m = cmds.createNode("pickMatrix")
        cmds.setAttr(f"{pick_m}.useTranslate", 0)
        cmds.setAttr(f"{pick_m}.useRotate", 0)
        cmds.setAttr(f"{pick_m}.useScale", 0)
        cmds.setAttr(f"{pick_m}.useShear", 0)
        cmds.connectAttr(f"{guide}.worldMatrix[0]", f"{pick_m}.inputMatrix")
        cmds.connectAttr(f"{pick_m}.outputMatrix", f"{self.guide_root}.npo_matrix[0]")
        cmds.connectAttr(
            f"{pick_m}.outputMatrix",
            f"{self.guide_root}.initialize_output_matrix[0]",
        )

        inv_m = cmds.createNode("inverseMatrix")
        cmds.connectAttr(f"{pick_m}.outputMatrix", f"{inv_m}.inputMatrix")
        cmds.connectAttr(
            f"{inv_m}.outputMatrix",
            f"{self.guide_root}.initialize_output_inverse_matrix[0]",
        )

    # endregion
