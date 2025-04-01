# domino
from domino import component
from domino.core import (
    attribute,
    Name,
    Transform,
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
DATA = [
    attribute.String(longName="component", value="assembly"),
    attribute.String(longName="side_c_str", value=center),
    attribute.String(longName="side_l_str", value=left),
    attribute.String(longName="side_r_str", value=right),
    attribute.String(longName="controller_extension", value=controller_extension),
    attribute.String(longName="joint_extension", value=joint_extension),
    attribute.Matrix(longName="guide_matrix", multi=True, value=[list(ORIGINMATRIX)]),
    attribute.Matrix(longName="npo_matrix", multi=True, value=[list(ORIGINMATRIX)]),
    attribute.Matrix(
        longName="initialize_output_matrix",
        multi=True,
        value=[list(ORIGINMATRIX) for _ in range(2)],
    ),
    attribute.Matrix(
        longName="initialize_output_inverse_matrix",
        multi=True,
        value=[list(ORIGINMATRIX) for _ in range(2)],
    ),
    attribute.Integer(longName="guide_mirror_type", multi=True, value=[1]),
    attribute.Bool(longName="run_pre_custom_scripts", value=0),
    attribute.String(longName="pre_custom_scripts", multi=True),
    attribute.String(longName="pre_custom_scripts_str", multi=True),
    attribute.Bool(longName="run_post_custom_scripts", value=0),
    attribute.String(longName="post_custom_scripts", multi=True),
    attribute.String(longName="post_custom_scripts_str", multi=True),
    attribute.String(longName="domino_path"),
    attribute.Bool(longName="run_import_modeling", value=1),
    attribute.String(longName="modeling_path"),
    attribute.Bool(longName="run_import_dummy", value=1),
    attribute.String(longName="dummy_path"),
    attribute.Bool(longName="run_import_blendshape_manager", value=1),
    attribute.String(longName="blendshape_manager_path"),
    attribute.Bool(longName="run_import_deformer_weights_manager", value=1),
    attribute.String(longName="deformer_weights_manager_path"),
    attribute.Bool(longName="run_import_pose_manager", value=1),
    attribute.String(longName="pose_manager_path"),
    attribute.Bool(longName="run_import_sdk_manager", value=1),
    attribute.String(longName="sdk_manager_path"),
    attribute.Bool(longName="run_import_space_manager", value=1),
    attribute.String(longName="space_manager_path"),
]

description = """## assembly
---

최상위 component.   

#### Guide
- COG 는 무게중심점입니다.

#### Settings
- Modeling  
> build 시 먼저 modeling 을 불러옵니다.
- Dummy  
> build 시 먼저 dummy 를 불러옵니다.
- Blendshape Manager
> build 시 blendshape manager 를 로드합니다.
- Pose Manager
> build 시 pose manager 를 로드합니다.
- SDK Manager
> build 시 sdk manager 를 로드합니다.
- Space Manager
> build 시 space manager 를 로드합니다.
- Deformer Weights Manager
> build 시 deformer weights manager 를 로드합니다.
- Custom Scripts  
> build 시 같이 실행되는 pre, post script 를 관리합니다.
> Manager 에서 domino path 를 버전업 하게되면 script 또한 버전업 되어서 저장됩니다."""
# endregion


class Rig(component.Rig):

    @property
    def identifier(self) -> tuple:
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
            self.add_controller(
                description="COG", parent_controllers=[(self.identifier, "sub")]
            )

    def populate_output(self):
        if not self["output"]:
            self.add_output(description="sub", extension=Name.controller_extension)
            self.add_output(description="", extension="output")

    def populate_output_joint(self):
        if not self["output_joint"]:
            self.add_output_joint(parent_description=None, description="")
            self.add_output_joint(parent_description="", description="COG")

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

        sub_npo, sub_ctl = self["controller"][1].create(
            parent=origin_ctl,
            shape=(
                self["controller"][1]["shape"]
                if "shape" in self["controller"][1]
                else "wave"
            ),
            color=21,
        )
        self["output"][0].connect()

        COG_npo, COG_ctl = self["controller"][2].create(
            parent=sub_ctl,
            shape=(
                self["controller"][2]["shape"]
                if "shape" in self["controller"][2]
                else "cylinder"
            ),
            color=17,
            npo_matrix_index=0,
        )

        # output
        ins = Transform(
            parent=COG_ctl,
            name=name,
            side=side,
            index=index,
            extension="output",
            m=cmds.xform(COG_ctl, query=True, matrix=True, worldSpace=True),
        )
        output = ins.create()
        self["output"][1].connect()

        # output joint
        self["output_joint"][0].create()
        self["output_joint"][1].create()

    # endregion

    # region GUIDE
    @build_log(logging.INFO)
    def guide(self):
        super().guide(description=description)
        m = cmds.getAttr(self.rig_root + ".guide_matrix[0]")
        guide = self.add_guide(
            parent=self.guide_root,
            description="COG",
            m=m,
            mirror_type=self["guide_mirror_type"]["value"][0],
        )
        pick_m = cmds.createNode("pickMatrix")
        cmds.setAttr(pick_m + ".useScale", 0)
        cmds.setAttr(pick_m + ".useShear", 0)
        cmds.connectAttr(guide + ".worldMatrix[0]", pick_m + ".inputMatrix")
        cmds.connectAttr(pick_m + ".outputMatrix", self.guide_root + ".npo_matrix[0]")
        cmds.connectAttr(
            pick_m + ".outputMatrix",
            self.guide_root + ".initialize_output_matrix[1]",
        )

        inv_m = cmds.createNode("inverseMatrix")
        cmds.connectAttr(pick_m + ".outputMatrix", inv_m + ".inputMatrix")
        cmds.connectAttr(
            inv_m + ".outputMatrix",
            self.guide_root + ".initialize_output_inverse_matrix[1]",
        )

    # endregion
