# domino
from domino import component
from domino.core import Transform, attribute, Name, Joint
from domino.core.utils import build_log

# maya
from maya.api import OpenMaya as om
from maya import cmds

# built-ins
import logging


# region Initialize Settings
ORIGINMATRIX = om.MMatrix()
matrices = [list(ORIGINMATRIX), list(ORIGINMATRIX), list(ORIGINMATRIX)]
DATA = [
    attribute.String(longName="component", value="eye01"),
    attribute.String(longName="name", value="eye"),
    attribute.Enum(longName="side", enumName=Name.side_list, value=0),
    attribute.Integer(longName="index", minValue=0),
    attribute.Matrix(longName="guide_matrix", multi=True, value=matrices),
    attribute.Matrix(longName="npo_matrix", multi=True, value=matrices),
    attribute.Matrix(
        longName="initialize_output_matrix",
        multi=True,
        value=matrices[:-1],
    ),
    attribute.Matrix(
        longName="initialize_output_inverse_matrix",
        multi=True,
        value=matrices[:-1],
    ),
    attribute.Integer(longName="guide_mirror_type", multi=True, value=[2, 2, 1]),
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
    attribute.Matrix(longName="aim_npo_matrix", value=matrices[0]),
]

description = """## eye01
---

eye component

### controllers
> eye 전체 컨트롤러  
> eye aim 컨트롤러  
> eye ball 컨트롤러  
"""

# endregion


class Rig(component.Rig):

    def __init__(self):
        super().__init__(DATA)

    def populate_controller(self):
        if not self["controller"]:
            self.add_controller(description="", parent_controllers=[])
            self.add_controller(
                description="aim", parent_controllers=[(self.identifier, "")]
            )
            self.add_controller(
                description="ball", parent_controllers=[(self.identifier, "")]
            )

    def populate_output(self):
        if not self["output"]:
            self.add_output(description="", extension=Name.output_extension)
            self.add_output(description="ball", extension=Name.output_extension)

    def populate_output_joint(self):
        if not self["output_joint"]:
            self.add_output_joint(parent_description=None, description="")
            self.add_output_joint(parent_description="", description="ball")

    # region RIG
    @build_log(logging.INFO)
    def rig(self):
        super().rig(description=description)

        name, side, index = self.identifier

        condition = cmds.createNode("condition")
        cmds.setAttr(f"{condition}.operation", 0)
        cmds.connectAttr(f"{self.rig_root}.side", f"{condition}.firstTerm")
        cmds.setAttr(f"{condition}.secondTerm", 2)
        cmds.setAttr(f"{condition}.colorIfTrueR", -1)
        cmds.setAttr(f"{condition}.colorIfFalseR", 1)

        # controller
        npo, ctl = self["controller"][0].create(
            parent=self.rig_root,
            shape=(
                self["controller"][0]["shape"]
                if "shape" in self["controller"][0]
                else "circle"
            ),
            color=12,
            npo_matrix_index=0,
        )
        cmds.setAttr(f"{ctl}.sx", lock=False, keyable=True)
        cmds.setAttr(f"{ctl}.sy", lock=False, keyable=True)
        cmds.setAttr(f"{ctl}.sz", lock=False, keyable=True)
        cmds.addAttr(
            ctl,
            longName="eye_ball_visibility",
            attributeType="enum",
            enumName="off:on",
            keyable=True,
        )
        loc = cmds.createNode(
            "transform",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                extension=Name.loc_extension,
            ),
            parent=ctl,
        )
        cmds.connectAttr(f"{condition}.outColorR", f"{loc}.sz")
        aim_npo, aim_ctl = self["controller"][1].create(
            parent=ctl,
            shape=(
                self["controller"][1]["shape"]
                if "shape" in self["controller"][1]
                else "circle"
            ),
            color=12,
            npo_matrix_index=1,
        )
        cmds.connectAttr(f"{condition}.outColorR", f"{aim_npo}.sy")
        aim_space = cmds.createNode(
            "transform",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="aim",
                extension="space",
            ),
            parent=ctl,
        )
        cmds.connectAttr(
            f"{self.rig_root}.aim_npo_matrix", f"{aim_space}.offsetParentMatrix"
        )
        cons = cmds.aimConstraint(
            aim_ctl,
            aim_space,
            aimVector=(1, 0, 0),
            upVector=(0, 1, 0),
            worldUpType="scene",
        )[0]
        cmds.connectAttr(f"{condition}.outColorR", f"{cons}.aimVectorX")
        cmds.connectAttr(f"{condition}.outColorR", f"{cons}.upVectorY")

        ball_npo, ball_ctl = self["controller"][2].create(
            parent=aim_space,
            shape=(
                self["controller"][2]["shape"]
                if "shape" in self["controller"][2]
                else "circle"
            ),
            color=12,
            npo_matrix_index=2,
        )
        cmds.connectAttr(f"{ctl}.eye_ball_visibility", f"{ball_npo}.visibility")
        ball_loc = cmds.createNode(
            "transform",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="ball",
                extension=Name.loc_extension,
            ),
            parent=ball_ctl,
        )
        cmds.connectAttr(f"{condition}.outColorR", f"{ball_loc}.sz")

        # output
        ins = Joint(
            self.rig_root,
            name=name,
            side=side,
            index=index,
            description="",
            extension=Name.output_extension,
            m=ORIGINMATRIX,
        )
        output = ins.create()
        self["output"][0].connect(loc)
        cmds.setAttr(f"{output}.drawStyle", 2)

        ins = Joint(
            self.rig_root,
            name=name,
            side=side,
            index=index,
            description="ball",
            extension=Name.output_extension,
            m=ORIGINMATRIX,
        )
        output = ins.create()
        self["output"][1].connect(ball_loc)
        cmds.setAttr(f"{output}.drawStyle", 2)

        # output joint
        if self["create_output_joint"]["value"]:
            self["output_joint"][0].create()
            self["output_joint"][1].create()

    # endregion

    # region GUIDE
    @build_log(logging.INFO)
    def guide(self):
        super().guide(description=description)

        name, side, index = self.identifier

        # guide
        root_guide = self.add_guide(
            parent=self.guide_root,
            description="",
            m=self["guide_matrix"]["value"][0],
            mirror_type=self["guide_mirror_type"]["value"][0],
        )
        eye_guide = self.add_guide(
            parent=root_guide,
            description="eye",
            m=self["guide_matrix"]["value"][1],
            mirror_type=self["guide_mirror_type"]["value"][1],
        )
        aim_guide = self.add_guide(
            parent=eye_guide,
            description="aim",
            m=self["guide_matrix"]["value"][2],
            mirror_type=self["guide_mirror_type"]["value"][2],
        )
        if cmds.getAttr(f"{aim_guide}.t")[0] == (0.0, 0.0, 0.0):
            cmds.setAttr(f"{aim_guide}.tz", 3)

        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{root_guide}.worldMatrix[0]", f"{decom_m}.inputMatrix")

        condition = cmds.createNode("condition")
        cmds.setAttr(f"{condition}.operation", 4)
        cmds.connectAttr(f"{decom_m}.outputScaleZ", f"{condition}.firstTerm")
        cmds.setAttr(f"{condition}.secondTerm", 0)
        cmds.setAttr(f"{condition}.colorIfTrue", 1, 1, -1)
        cmds.setAttr(f"{condition}.colorIfFalse", 1, 1, 1)

        compose_m = cmds.createNode("composeMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{compose_m}.inputTranslate")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{compose_m}.inputRotate")
        cmds.connectAttr(f"{condition}.outColor", f"{compose_m}.inputScale")
        cmds.connectAttr(
            f"{compose_m}.outputMatrix", f"{self.guide_root}.npo_matrix[0]"
        )
        npo_matrix0_plug = f"{compose_m}.outputMatrix"
        aim_space_guide = cmds.createNode(
            "transform",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="aimSpace",
                extension="guide",
            ),
            parent=root_guide,
        )
        cmds.pointConstraint(eye_guide, aim_space_guide)
        cons = cmds.aimConstraint(
            aim_guide,
            aim_space_guide,
            aimVector=(1, 0, 0),
            upVector=(0, 1, 0),
            worldUpType="scene",
        )[0]
        cmds.connectAttr(f"{condition}.outColorB", f"{cons}.aimVectorX")
        cmds.connectAttr(f"{condition}.outColorB", f"{cons}.upVectorY")

        pick_m = cmds.createNode("pickMatrix")
        cmds.setAttr(f"{pick_m}.useScale", 0)
        cmds.connectAttr(f"{aim_space_guide}.worldMatrix[0]", f"{pick_m}.inputMatrix")
        inverse_m = cmds.createNode("inverseMatrix")
        cmds.connectAttr(npo_matrix0_plug, f"{inverse_m}.inputMatrix")
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{pick_m}.outputMatrix", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(f"{inverse_m}.outputMatrix", f"{mult_m}.matrixIn[1]")

        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        compose_m = cmds.createNode("composeMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{compose_m}.inputTranslate")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{compose_m}.inputRotate")
        cmds.connectAttr(f"{condition}.outColor", f"{compose_m}.inputScale")
        cmds.connectAttr(
            f"{compose_m}.outputMatrix", f"{self.guide_root}.aim_npo_matrix"
        )

        offset_rotate_compose_m = cmds.createNode("composeMatrix")
        cmds.connectAttr(
            f"{self.guide_root}.offset_output_rotate_x",
            f"{offset_rotate_compose_m}.inputRotateX",
        )
        cmds.connectAttr(
            f"{self.guide_root}.offset_output_rotate_y",
            f"{offset_rotate_compose_m}.inputRotateY",
        )
        cmds.connectAttr(
            f"{self.guide_root}.offset_output_rotate_z",
            f"{offset_rotate_compose_m}.inputRotateZ",
        )

        pick_m = cmds.createNode("pickMatrix")
        cmds.setAttr(f"{pick_m}.useScale", 0)
        cmds.setAttr(f"{pick_m}.useShear", 0)
        cmds.connectAttr(f"{root_guide}.worldMatrix[0]", f"{pick_m}.inputMatrix")
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(
            f"{offset_rotate_compose_m}.outputMatrix", f"{mult_m}.matrixIn[0]"
        )
        cmds.connectAttr(f"{pick_m}.outputMatrix", f"{mult_m}.matrixIn[1]")
        cmds.connectAttr(
            f"{mult_m}.matrixSum",
            f"{self.guide_root}.initialize_output_matrix[0]",
        )

        inv_m = cmds.createNode("inverseMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{inv_m}.inputMatrix")
        cmds.connectAttr(
            f"{inv_m}.outputMatrix",
            f"{self.guide_root}.initialize_output_inverse_matrix[0]",
        )

        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{aim_guide}.worldMatrix[0]", f"{decom_m}.inputMatrix")
        compose_m = cmds.createNode("composeMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{compose_m}.inputTranslate")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{compose_m}.inputRotate")
        cmds.connectAttr(f"{condition}.outColor", f"{compose_m}.inputScale")
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{compose_m}.outputMatrix", f"{mult_m}.matrixIn[0]")
        inverse_m = cmds.createNode("inverseMatrix")
        cmds.connectAttr(npo_matrix0_plug, f"{inverse_m}.inputMatrix")
        cmds.connectAttr(f"{inverse_m}.outputMatrix", f"{mult_m}.matrixIn[1]")

        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        compose_m = cmds.createNode("composeMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{compose_m}.inputTranslate")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{compose_m}.inputRotate")
        cmds.connectAttr(f"{condition}.outColor", f"{compose_m}.inputScale")
        cmds.connectAttr(
            f"{compose_m}.outputMatrix", f"{self.guide_root}.npo_matrix[1]"
        )

        pick_m = cmds.createNode("pickMatrix")
        cmds.setAttr(f"{pick_m}.useScale", 0)
        cmds.connectAttr(f"{eye_guide}.worldMatrix[0]", f"{pick_m}.inputMatrix")

        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{pick_m}.outputMatrix", f"{mult_m}.matrixIn[0]")

        pick_m = cmds.createNode("pickMatrix")
        cmds.setAttr(f"{pick_m}.useScale", 0)
        cmds.connectAttr(f"{aim_space_guide}.worldMatrix[0]", f"{pick_m}.inputMatrix")
        inverse_m = cmds.createNode("inverseMatrix")
        cmds.connectAttr(f"{pick_m}.outputMatrix", f"{inverse_m}.inputMatrix")

        cmds.connectAttr(f"{inverse_m}.outputMatrix", f"{mult_m}.matrixIn[1]")
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        compose_m = cmds.createNode("composeMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{compose_m}.inputTranslate")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{compose_m}.inputRotate")
        cmds.connectAttr(f"{condition}.outColorB", f"{compose_m}.inputScaleZ")
        cmds.connectAttr(
            f"{compose_m}.outputMatrix", f"{self.guide_root}.npo_matrix[2]"
        )

        pick_m = cmds.createNode("pickMatrix")
        cmds.setAttr(f"{pick_m}.useScale", 0)
        cmds.setAttr(f"{pick_m}.useShear", 0)
        cmds.connectAttr(f"{eye_guide}.worldMatrix[0]", f"{pick_m}.inputMatrix")
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(
            f"{offset_rotate_compose_m}.outputMatrix", f"{mult_m}.matrixIn[0]"
        )
        cmds.connectAttr(f"{pick_m}.outputMatrix", f"{mult_m}.matrixIn[1]")
        cmds.connectAttr(
            f"{mult_m}.matrixSum",
            f"{self.guide_root}.initialize_output_matrix[1]",
        )

        inv_m = cmds.createNode("inverseMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{inv_m}.inputMatrix")
        cmds.connectAttr(
            f"{inv_m}.outputMatrix",
            f"{self.guide_root}.initialize_output_inverse_matrix[1]",
        )

    # endregion
