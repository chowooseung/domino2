# domino
from domino import component
from domino.core import attribute, Name, Joint
from domino.core.utils import build_log

# maya
from maya.api import OpenMaya as om
from maya import cmds

# built-ins
import logging


# region Initialize Settings
ORIGINMATRIX = om.MMatrix()
matrices = [list(ORIGINMATRIX)]
m = om.MMatrix()
tm0 = om.MTransformationMatrix(m)
tm0.setTranslation(om.MVector((1, 0, 0)), om.MSpace.kObject)
matrices.append(list(tm0.asMatrix()))
DATA = [
    attribute.String(longName="component", value="sc01"),
    attribute.String(longName="name", value="sc"),
    attribute.Enum(longName="side", enumName=Name.side_list, value=0),
    attribute.Integer(longName="index", minValue=0),
    attribute.Matrix(longName="guide_matrix", multi=True, value=matrices),
    attribute.Matrix(longName="npo_matrix", multi=True, value=matrices),
    attribute.Matrix(
        longName="initialize_output_matrix",
        multi=True,
        value=[list(ORIGINMATRIX) for _ in range(3)],
    ),
    attribute.Matrix(
        longName="initialize_output_inverse_matrix",
        multi=True,
        value=[list(ORIGINMATRIX) for _ in range(3)],
    ),
    attribute.Integer(longName="guide_mirror_type", multi=True, value=[1, 1]),
    # 부모로 사용할 상위 component 의 output index
    attribute.Integer(
        longName="parent_output_index", minValue=-1, defaultValue=-1, value=-1
    ),
    # output joint 생성 option
    attribute.Bool(longName="create_output_joint", value=1),
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
    attribute.Bool(longName="nonkeyable", value=0),
    attribute.Float(longName="length", value=1),
]

description = """## COG01
---

COG 컨트롤러 입니다."""

# endregion


class Rig(component.Rig):

    def __init__(self):
        super().__init__(DATA)

    def populate_controller(self):
        if not self["controller"]:
            self.add_controller(description="base", parent_controllers=[])
            self.add_controller(
                description="tip", parent_controllers=[(self.identifier, "base")]
            )

    def populate_output(self):
        if not self["output"]:
            self.add_output(description="base", extension=Name.output_extension)
            self.add_output(description="tip", extension=Name.output_extension)
            self.add_output(description="stretchedTip", extension=Name.output_extension)

    def populate_output_joint(self):
        if not self["output_joint"]:
            self.add_output_joint(parent_description=None, description="base")
            self.add_output_joint(parent_description="base", description="tip")
            self.add_output_joint(parent_description="base", description="stretchedTip")

    # region RIG
    @build_log(logging.INFO)
    def rig(self):
        super().rig(description=description)

        name, side, index = self.identifier

        # controller
        base_npo, base_ctl = self["controller"][0].create(
            parent=self.rig_root,
            shape=(
                self["controller"][0]["shape"]
                if "shape" in self["controller"][0]
                else "circle"
            ),
            color=12,
            npo_matrix_index=0,
        )
        cmds.setAttr(f"{base_npo}.rx", lock=True, keyable=False)
        cmds.setAttr(f"{base_npo}.ry", lock=True, keyable=False)
        cmds.setAttr(f"{base_npo}.rz", lock=True, keyable=False)
        cmds.setAttr(f"{base_ctl}.mirror_type", 1)
        tip_npo, tip_ctl = self["controller"][1].create(
            parent=self.rig_root,
            shape=(
                self["controller"][1]["shape"]
                if "shape" in self["controller"][1]
                else "circle"
            ),
            color=12,
            npo_matrix_index=1,
        )
        cmds.setAttr(f"{tip_ctl}.mirror_type", 1)

        sc0_jnt = cmds.createNode(
            "joint",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="sc0",
                extension=Name.joint_extension,
            ),
            parent=self.rig_root,
        )
        cmds.hide(sc0_jnt)
        sc1_jnt = cmds.createNode(
            "joint",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="sc1",
                extension=Name.joint_extension,
            ),
            parent=sc0_jnt,
        )
        cmds.connectAttr(f"{self.rig_root}.length", f"{sc1_jnt}.tx")
        ikh = cmds.ikHandle(
            startJoint=sc0_jnt,
            endEffector=sc1_jnt,
            solver="ikSCsolver",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                extension=Name.ikh_extension,
            ),
        )[0]
        ikh = cmds.parent(ikh, self.rig_root)[0]
        cmds.setAttr(f"{ikh}.v", 0)
        cmds.pointConstraint(base_ctl, sc0_jnt, maintainOffset=False)
        cmds.parentConstraint(tip_ctl, ikh, maintainOffset=False)
        stretched_loc = cmds.createNode(
            "transform",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="stretched",
                extension=Name.loc_extension,
            ),
            parent=sc0_jnt,
        )
        cmds.pointConstraint(tip_ctl, stretched_loc, maintainOffset=False)

        # output
        ins = Joint(
            self.rig_root,
            name=name,
            side=side,
            index=index,
            description="base",
            extension=Name.output_extension,
            m=ORIGINMATRIX,
        )
        output = ins.create()
        self["output"][0].connect(sc0_jnt)
        cmds.setAttr(f"{output}.drawStyle", 2)

        ins = Joint(
            self.rig_root,
            name=name,
            side=side,
            index=index,
            description="tip",
            extension=Name.output_extension,
            m=ORIGINMATRIX,
        )
        output = ins.create()
        self["output"][1].connect(sc1_jnt)
        cmds.setAttr(f"{output}.drawStyle", 2)

        ins = Joint(
            self.rig_root,
            name=name,
            side=side,
            index=index,
            description="stretchedTip",
            extension=Name.output_extension,
            m=ORIGINMATRIX,
        )
        output = ins.create()
        self["output"][2].connect(stretched_loc)
        cmds.setAttr(f"{output}.drawStyle", 2)

        # output joint
        if self["create_output_joint"]["value"]:
            self["output_joint"][0].create()
            self["output_joint"][1].create()
            self["output_joint"][2].create()

    # endregion

    # region GUIDE
    @build_log(logging.INFO)
    def guide(self):
        super().guide(description=description)

        name, side, index = self.identifier

        # guide
        base_guide = self.add_guide(
            parent=self.guide_root,
            description="base",
            m=self["guide_matrix"]["value"][0],
            mirror_type=self["guide_mirror_type"]["value"][0],
        )
        tip_guide = self.add_guide(
            parent=base_guide,
            description="tip",
            m=self["guide_matrix"]["value"][1],
            mirror_type=self["guide_mirror_type"]["value"][1],
        )
        cmds.setAttr(f"{tip_guide}.ty", lock=True, keyable=False)
        cmds.setAttr(f"{tip_guide}.tz", lock=True, keyable=False)
        cmds.setAttr(f"{tip_guide}.rx", lock=True, keyable=False)
        cmds.setAttr(f"{tip_guide}.ry", lock=True, keyable=False)
        cmds.setAttr(f"{tip_guide}.rz", lock=True, keyable=False)
        distance = cmds.createNode("distanceBetween")
        cmds.connectAttr(f"{base_guide}.worldMatrix[0]", f"{distance}.inMatrix1")
        cmds.connectAttr(f"{tip_guide}.worldMatrix[0]", f"{distance}.inMatrix2")
        cmds.connectAttr(f"{distance}.distance", f"{self.guide_root}.length")

        pick_m = cmds.createNode("pickMatrix")
        cmds.connectAttr(f"{base_guide}.worldMatrix[0]", f"{pick_m}.inputMatrix")
        cmds.setAttr(f"{pick_m}.useScale", 0)
        cmds.connectAttr(f"{pick_m}.outputMatrix", f"{self.guide_root}.npo_matrix[0]")
        cmds.connectAttr(
            f"{pick_m}.outputMatrix", f"{self.guide_root}.initialize_output_matrix[0]"
        )

        inv_m = cmds.createNode("inverseMatrix")
        cmds.connectAttr(f"{pick_m}.outputMatrix", f"{inv_m}.inputMatrix")
        cmds.connectAttr(
            f"{inv_m}.outputMatrix",
            f"{self.guide_root}.initialize_output_inverse_matrix[0]",
        )

        pick_m = cmds.createNode("pickMatrix")
        cmds.connectAttr(f"{tip_guide}.worldMatrix[0]", f"{pick_m}.inputMatrix")
        cmds.setAttr(f"{pick_m}.useScale", 0)
        cmds.connectAttr(f"{pick_m}.outputMatrix", f"{self.guide_root}.npo_matrix[1]")
        cmds.connectAttr(
            f"{pick_m}.outputMatrix", f"{self.guide_root}.initialize_output_matrix[1]"
        )
        cmds.connectAttr(
            f"{pick_m}.outputMatrix", f"{self.guide_root}.initialize_output_matrix[2]"
        )

        inv_m = cmds.createNode("inverseMatrix")
        cmds.connectAttr(f"{pick_m}.outputMatrix", f"{inv_m}.inputMatrix")
        cmds.connectAttr(
            f"{inv_m}.outputMatrix",
            f"{self.guide_root}.initialize_output_inverse_matrix[1]",
        )
        cmds.connectAttr(
            f"{inv_m}.outputMatrix",
            f"{self.guide_root}.initialize_output_inverse_matrix[2]",
        )

    # endregion
