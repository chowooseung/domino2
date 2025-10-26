# domino
from domino import component
from domino.core import (
    attribute,
    Name,
    Surface,
    Joint,
    Transform,
    rigkit,
)
from domino.core.utils import build_log

# maya
from maya.api import OpenMaya as om
from maya import cmds

# built-ins
import logging

# gui
from PySide6 import QtWidgets


ORIGINMATRIX = om.MMatrix()
matrices = []
m = om.MMatrix()
upper_body_m = om.MTransformationMatrix(m)
upper_body_m.setTranslation(
    om.MVector((0.0, 9.53984260559082, 0.11921143531799316)), om.MSpace.kWorld
)
matrices.append(list(upper_body_m.asMatrix()))

hip_m = om.MTransformationMatrix(m)
hip_m.setTranslation(
    om.MVector((0.0, 10.8296775483839, 0.1447981369158308)), om.MSpace.kWorld
)
matrices.append(list(hip_m.asMatrix()))

fk0_m = om.MTransformationMatrix(m)
fk0_m.setTranslation(
    om.MVector((0.0, 10.149886407942963, 0.11921143531799316)), om.MSpace.kWorld
)
matrices.append(list(fk0_m.asMatrix()))

fk1_m = om.MTransformationMatrix(m)
fk1_m.setTranslation(
    om.MVector((0.0, 11.547268988596459, 0.11921143531799316)), om.MSpace.kWorld
)
matrices.append(list(fk1_m.asMatrix()))

ik_m = om.MTransformationMatrix(m)
ik_m.setTranslation(
    om.MVector((0.0, 12.765792369084298, -0.2692372427896797)), om.MSpace.kWorld
)
matrices.append(list(ik_m.asMatrix()))

tip_m = om.MTransformationMatrix(m)
tip_m.setTranslation(
    om.MVector((0.0, 13.870291709899902, -0.5028788447380066)), om.MSpace.kWorld
)
matrices.append(list(tip_m.asMatrix()))

driver0_m = om.MTransformationMatrix(m)
driver0_m.setTranslation(
    om.MVector((0.0, 9.53984260559082, 0.11921143531799316)), om.MSpace.kWorld
)
matrices.append(list(driver0_m.asMatrix()))

driver1_m = om.MTransformationMatrix(m)
driver1_m.setTranslation(
    om.MVector((0.0, 10.69349728010567, 0.11921144276857376)), om.MSpace.kWorld
)
matrices.append(list(driver1_m.asMatrix()))

driver2_m = om.MTransformationMatrix(m)
driver2_m.setTranslation(
    om.MVector((0.0, 12.50360438331311, -0.2777713934556867)), om.MSpace.kWorld
)
matrices.append(list(driver2_m.asMatrix()))

driver3_m = om.MTransformationMatrix(m)
driver3_m.setTranslation(
    om.MVector((0.0, 13.870291487161905, -0.5028788575941494)), om.MSpace.kWorld
)
matrices.append(list(driver3_m.asMatrix()))

DATA = [
    attribute.String(longName="component", value="humanspine01"),
    attribute.String(longName="name", value="humanSpine"),
    attribute.Enum(longName="side", enumName=Name.side_list, value=0),
    attribute.Integer(longName="index", minValue=0),
    attribute.Matrix(longName="guide_matrix", multi=True, value=matrices),
    attribute.Matrix(longName="npo_matrix", multi=True, value=matrices[:-4]),
    attribute.Matrix(
        longName="initialize_output_matrix",
        multi=True,
        value=[list(ORIGINMATRIX) for _ in range(6)],
    ),
    attribute.Matrix(
        longName="initialize_output_inverse_matrix",
        multi=True,
        value=[list(ORIGINMATRIX) for _ in range(6)],
    ),
    attribute.Integer(
        longName="guide_mirror_type",
        multi=True,
        value=[
            2,  # upperBody
            2,  # hip
            2,  # fk0
            2,  # fk1
            2,  # ik
            2,  # tip
            1,  # driver0
            1,  # driver1
            1,  # driver2
            1,  # driver3
        ],
    ),
    attribute.Integer(
        longName="parent_output_index", minValue=-1, defaultValue=-1, value=-1
    ),
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
    attribute.Integer(longName="output_count", value=5),
    attribute.Float(
        longName="output_v_values", multi=True, value=[0, 0.25, 0.5, 0.75, 1]
    ),
    attribute.Matrix(longName="driver_matrix", multi=True, value=matrices[-4:]),
    attribute.Matrix(longName="driver_inverse_matrix", multi=True, value=matrices[-4:]),
    attribute.Matrix(longName="tip_matrix", value=list(ORIGINMATRIX)),
    attribute.NurbsSurface(
        longName="ribbon_surface",
        value={
            "parent_name": "",
            "surface_name": "tempRibbonSurface",
            "surface_matrix": [
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
            ],
            "visibility": True,
            "surface": {
                "form_u": 0,
                "form_v": 0,
                "knot_u": [0.0, 1.0],
                "knot_v": [0.0, 0.0, 0.0, 0.5, 1.0, 1.0, 1.0],
                "degree_u": 1,
                "degree_v": 3,
                "cvs": [
                    (0.3239349977974598, 9.539842605590822, 0.11921144276857373, 1.0),
                    (0.3239349977974598, 10.573100090026857, 0.18489342927932736, 1.0),
                    (0.3239349977974598, 11.719689369201657, 0.26006561517715476, 1.0),
                    (0.3239349977974598, 12.829869270324705, -0.5030749440193175, 1.0),
                    (0.3239349977974598, 13.863416671752928, -0.5030738115310668, 1.0),
                    (-0.3239349977974598, 9.539842605590822, 0.11921144276857373, 1.0),
                    (-0.3239349977974598, 10.573100090026857, 0.18489342927932736, 1.0),
                    (-0.3239349977974598, 11.719689369201657, 0.26006561517715476, 1.0),
                    (-0.3239349977974598, 12.829869270324705, -0.5030749440193175, 1.0),
                    (-0.3239349977974598, 13.863416671752928, -0.5030738115310668, 1.0),
                ],
            },
        },
    ),
]


description = """humanspine01 component.

"""


class Rig(component.Rig):

    def input_data(self):
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Ribbon u value Count")
        label = QtWidgets.QLabel("u Value Count : ")
        line_edit = QtWidgets.QLineEdit()
        ok_btn = QtWidgets.QPushButton("Ok")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)

        layout0 = QtWidgets.QVBoxLayout(dialog)
        layout1 = QtWidgets.QHBoxLayout()
        layout1.addWidget(label)
        layout1.addWidget(line_edit)
        layout2 = QtWidgets.QHBoxLayout()
        layout2.addWidget(ok_btn)
        layout2.addWidget(cancel_btn)
        layout0.addLayout(layout1)
        layout0.addLayout(layout2)

        result = dialog.exec()
        try:
            value = int(line_edit.text())
            if value < 3:
                return False
            self["output_count"]["value"] = value
            self["output_v_values"]["value"] = [v / (value - 1) for v in range(value)]
            self["initialize_output_matrix"]["value"] = [
                list(ORIGINMATRIX) for _ in range(value + 1)
            ]
            self["initialize_output_inverse_matrix"]["value"] = [
                list(ORIGINMATRIX) for _ in range(value + 1)
            ]
        except:
            return False
        return result

    def __init__(self):
        super().__init__(DATA)

    def populate_controller(self):
        if not self["controller"]:
            self.add_controller(description="host", parent_controllers=[])
            self.add_controller(
                description="upperBody",
                parent_controllers=[(self.identifier, "host")],
            )
            self.add_controller(
                description="hip",
                parent_controllers=[(self.identifier, "upperBody")],
            )
            fk_descriptions = ["fk0", "fk1"]
            parent_controllers = [(self.identifier, "hip")]
            for description in fk_descriptions:
                self.add_controller(
                    description=description,
                    parent_controllers=parent_controllers,
                )
                parent_controllers = [(self.identifier, description)]
            self.add_controller(
                description="ik",
                parent_controllers=[(self.identifier, "fk1")],
            )
            self.add_controller(
                description="tip", parent_controllers=[(self.identifier, "ik")]
            )
            parent_controllers = [(self.identifier, "tip")]
            for i in range(self["output_count"]["value"]):
                self.add_controller(
                    description=f"tweak{i}", parent_controllers=parent_controllers
                )
                parent_controllers = [(self.identifier, f"tweak{i}")]

    def populate_output(self):
        if not self["output"]:
            self.add_output(description="hip", extension=Name.output_extension)
            for i in range(self["output_count"]["value"]):
                self.add_output(description=i, extension=Name.output_extension)

    def populate_output_joint(self):
        if not self["output_joint"]:
            self.add_output_joint(parent_description=None, description="hip")
            parent_description = "hip"
            for i in range(self["output_count"]["value"]):
                self.add_output_joint(
                    parent_description=parent_description, description=i
                )
                parent_description = i

    # region RIG
    @build_log(logging.INFO)
    def rig(self):
        super().rig(description=description)

        name, side, index = self.identifier

        # controller
        host_npo, host_ctl = self["controller"][0].create(
            parent=self.rig_root,
            shape=(
                self["controller"][0]["shape"]
                if "shape" in self["controller"][0]
                else "host"
            ),
            color=12,
            host=True,
        )
        cmds.setAttr(f"{host_ctl}.tx", lock=True, keyable=False)
        cmds.setAttr(f"{host_ctl}.ty", lock=True, keyable=False)
        cmds.setAttr(f"{host_ctl}.tz", lock=True, keyable=False)
        cmds.setAttr(f"{host_ctl}.rx", lock=True, keyable=False)
        cmds.setAttr(f"{host_ctl}.ry", lock=True, keyable=False)
        cmds.setAttr(f"{host_ctl}.rz", lock=True, keyable=False)
        cmds.setAttr(f"{host_ctl}.rotateOrder", channelBox=False)
        cmds.addAttr(
            host_ctl,
            longName="enable_stretch_squash",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=0,
            keyable=True,
        )
        cmds.addAttr(
            host_ctl,
            longName="uniform",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=1,
            keyable=True,
        )
        cmds.addAttr(
            host_ctl,
            longName="auto_volume",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=0,
            keyable=True,
        )
        cmds.addAttr(
            host_ctl,
            longName="volume",
            attributeType="float",
            minValue=-1,
            maxValue=10,
            defaultValue=0,
            keyable=True,
        )
        cmds.addAttr(
            host_ctl,
            longName="volume_high_bound",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=1,
            keyable=True,
        )
        cmds.addAttr(
            host_ctl,
            longName="volume_position",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=0.5,
            keyable=True,
        )
        cmds.addAttr(
            host_ctl,
            longName="volume_low_bound",
            attributeType="float",
            minValue=0,
            maxValue=1,
            defaultValue=0,
            keyable=True,
        )
        cmds.addAttr(
            host_ctl,
            longName="tweak_ctls_visibility",
            attributeType="enum",
            enumName="off:on",
            defaultValue=0,
            keyable=True,
        )
        upper_body_npo, upper_body_ctl = self["controller"][1].create(
            parent=self.rig_root,
            shape=(
                self["controller"][1]["shape"]
                if "shape" in self["controller"][1]
                else "cube"
            ),
            color=12,
            npo_matrix_index=0,
        )
        hip_npo, hip_ctl = self["controller"][2].create(
            parent=upper_body_ctl,
            shape=(
                self["controller"][2]["shape"]
                if "shape" in self["controller"][2]
                else "cube"
            ),
            color=12,
            npo_matrix_index=1,
        )
        hip_loc = cmds.createNode(
            "transform",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="hip",
                extension=Name.loc_extension,
            ),
            parent=hip_ctl,
        )
        cmds.setAttr(f"{hip_loc}.rz", 90)
        fk0_npo, fk0_ctl = self["controller"][3].create(
            parent=upper_body_ctl,
            shape=(
                self["controller"][3]["shape"]
                if "shape" in self["controller"][3]
                else "cube"
            ),
            color=12,
            npo_matrix_index=2,
        )
        fk1_npo, fk1_ctl = self["controller"][4].create(
            parent=fk0_ctl,
            shape=(
                self["controller"][4]["shape"]
                if "shape" in self["controller"][4]
                else "cube"
            ),
            color=12,
            npo_matrix_index=3,
        )
        ik_npo, ik_ctl = self["controller"][5].create(
            parent=fk1_ctl,
            shape=(
                self["controller"][5]["shape"]
                if "shape" in self["controller"][5]
                else "cube"
            ),
            color=12,
            npo_matrix_index=4,
        )
        tip_npo, tip_ctl = self["controller"][6].create(
            parent=ik_ctl,
            shape=(
                self["controller"][6]["shape"]
                if "shape" in self["controller"][6]
                else "cube"
            ),
            color=12,
            npo_matrix_index=5,
        )
        ins = Transform(
            tip_ctl,
            name=name,
            side=side,
            index=index,
            description="tip",
            extension="rot",
            m=cmds.xform(tip_ctl, query=True, matrix=True, worldSpace=True),
        )
        tip_rot = ins.create()
        cmds.connectAttr(f"{self.rig_root}.tip_matrix", f"{tip_rot}.offsetParentMatrix")

        ins = Transform(
            parent=self.rig_root,
            name=name,
            side=side,
            index=index,
            description="ribbon",
            extension="grp",
            m=ORIGINMATRIX,
        )
        ribbon_grp = ins.create()

        ins = Joint(
            parent=upper_body_ctl,
            name=name,
            side=side,
            index=index,
            description="ribbonDriver0",
            extension=Name.joint_extension,
            m=cmds.xform(upper_body_ctl, query=True, matrix=True, worldSpace=True),
            use_joint_convention=False,
        )
        ribbon0_jnt = ins.create()
        cmds.connectAttr(
            f"{self.rig_root}.driver_matrix[0]", f"{ribbon0_jnt}.offsetParentMatrix"
        )

        ins = Joint(
            parent=fk1_ctl,
            name=name,
            side=side,
            index=index,
            description="ribbonDriver1",
            extension=Name.joint_extension,
            m=cmds.xform(fk1_ctl, query=True, matrix=True, worldSpace=True),
            use_joint_convention=False,
        )
        ribbon1_jnt = ins.create()
        cmds.connectAttr(
            f"{self.rig_root}.driver_matrix[1]", f"{ribbon1_jnt}.offsetParentMatrix"
        )

        ins = Joint(
            parent=ik_ctl,
            name=name,
            side=side,
            index=index,
            description="ribbonDriver2",
            extension=Name.joint_extension,
            m=cmds.xform(ik_ctl, query=True, matrix=True, worldSpace=True),
            use_joint_convention=False,
        )
        ribbon2_jnt = ins.create()
        cmds.connectAttr(
            f"{self.rig_root}.driver_matrix[2]", f"{ribbon2_jnt}.offsetParentMatrix"
        )

        ins = Joint(
            parent=tip_ctl,
            name=name,
            side=side,
            index=index,
            description="ribbonDriver3",
            extension=Name.joint_extension,
            m=cmds.xform(tip_ctl, query=True, matrix=True, worldSpace=True),
            use_joint_convention=False,
        )
        ribbon3_jnt = ins.create()
        cmds.connectAttr(
            f"{self.rig_root}.driver_matrix[3]", f"{ribbon3_jnt}.offsetParentMatrix"
        )

        ins = Surface(data=self["ribbon_surface"]["value"])
        ribbon_surface = ins.create_from_data()
        ribbon_surface = cmds.rename(
            ribbon_surface,
            Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="ribbonSurface",
            ),
        )
        main_ik_joints = []
        parent = ribbon_grp
        for i in range(len(self["output_v_values"]["value"])):
            ins = Joint(
                parent=parent,
                name=name,
                side=side,
                index=index,
                description=f"mainIk{i}",
                extension=Name.joint_extension,
            )
            main_ik_joints.append(ins.create())
            parent = main_ik_joints[i]
        up_ik_joints = []
        parent = ribbon_grp
        for i in range(len(self["output_v_values"]["value"])):
            ins = Joint(
                parent=parent,
                name=name,
                side=side,
                index=index,
                description=f"upIk{i}",
                extension=Name.joint_extension,
            )
            up_ik_joints.append(ins.create())
            parent = up_ik_joints[i]

        output_v_values = self["output_v_values"]["value"]
        half_list = output_v_values[: int(len(output_v_values) / 2)]
        if len(output_v_values) % 2 == 1:
            value = 1 / (len(half_list))
            half_list = [x * value for x in range(len(half_list))]
            auto_volume_multiple = half_list + [1] + list(reversed(half_list))
        else:
            value = 1 / (len(half_list) - 1)
            half_list = [x * value for x in range(len(half_list))]
            auto_volume_multiple = half_list + list(reversed(half_list))

        condition = cmds.createNode("condition")
        cmds.connectAttr(f"{self.rig_root}.side", f"{condition}.firstTerm")
        cmds.setAttr(f"{condition}.secondTerm", 2)
        cmds.setAttr(f"{condition}.colorIfTrueR", -1)
        cmds.setAttr(f"{condition}.colorIfFalseR", 1)

        ribbon_surface, ribbon_outputs = rigkit.ribbon_spline_ik(
            ribbon_grp,
            driver_joints=[ribbon0_jnt, ribbon1_jnt, ribbon2_jnt, ribbon3_jnt],
            driver_inverse_plugs=[
                f"{self.rig_root}.driver_inverse_matrix[0]",
                f"{self.rig_root}.driver_inverse_matrix[1]",
                f"{self.rig_root}.driver_inverse_matrix[2]",
                f"{self.rig_root}.driver_inverse_matrix[3]",
            ],
            surface=ribbon_surface,
            main_ik_joints=main_ik_joints,
            up_ik_joints=up_ik_joints,
            stretch_squash_attr=f"{host_ctl}.enable_stretch_squash",
            uniform_attr=f"{host_ctl}.uniform",
            auto_volume_attr=f"{host_ctl}.auto_volume",
            auto_volume_multiple=auto_volume_multiple,
            volume_attr=f"{host_ctl}.volume",
            volume_position_attr=f"{host_ctl}.volume_position",
            volume_high_bound_attr=f"{host_ctl}.volume_high_bound",
            volume_low_bound_attr=f"{host_ctl}.volume_low_bound",
            output_v_value_plugs=[
                f"{self.rig_root}.output_v_values[{i}]"
                for i in range(self["output_count"]["value"])
            ],
            negate_plug=f"{condition}.outColorR",
            secondary_axis=(0, -1, 0),
        )
        cmds.connectAttr(
            f"{self.rig_root}.ribbon_surface", f"{ribbon_surface}ShapeOrig.create"
        )
        sc = cmds.findDeformers(ribbon_surface)[0]
        cmds.sets(sc, edit=True, addElement=component.DEFORMER_WEIGHTS_SETS)

        cmds.hide(ribbon_grp, ribbon0_jnt, ribbon1_jnt, ribbon2_jnt, ribbon3_jnt)
        cmds.skinPercent(
            sc, f"{ribbon_surface}.cv[*][0]", transformValue=[ribbon0_jnt, 1]
        )
        cmds.skinPercent(
            sc,
            f"{ribbon_surface}.cv[*][1]",
            transformValue=[(ribbon0_jnt, 0.65), (ribbon1_jnt, 0.35)],
        )
        cmds.skinPercent(
            sc,
            f"{ribbon_surface}.cv[*][2]",
            transformValue=[
                (ribbon0_jnt, 0.25),
                (ribbon1_jnt, 0.55),
                (ribbon2_jnt, 0.2),
            ],
        )
        cmds.skinPercent(
            sc, f"{ribbon_surface}.cv[*][3]", transformValue=[ribbon2_jnt, 1]
        )
        cmds.skinPercent(
            sc, f"{ribbon_surface}.cv[*][4]", transformValue=[ribbon3_jnt, 1]
        )
        ins = Transform(
            ribbon_outputs[-1],
            name=name,
            side=side,
            index=index,
            description="tip",
            extension="output",
            m=cmds.xform(ribbon_outputs[-1], query=True, matrix=True, worldSpace=True),
        )
        tip_output = ins.create()
        cmds.orientConstraint(tip_rot, tip_output)

        ins = Joint(
            self.rig_root,
            name=name,
            side=side,
            index=index,
            description="hip",
            extension=Name.output_extension,
            m=ORIGINMATRIX,
        )
        hip_output = ins.create()
        cmds.setAttr(f"{hip_output}.drawStyle", 2)
        self["output"][0].connect(hip_loc)

        output_sources = ribbon_outputs[:-1] + [tip_output]
        for i in range(self["output_count"]["value"]):
            output_npo, output_ctl = self["controller"][7 + i].create(
                parent=self.rig_root,
                shape=(
                    self["controller"][7 + i]["shape"]
                    if "shape" in self["controller"][7 + i]
                    else "sphere"
                ),
                color=12,
            )
            mult_m = cmds.createNode("multMatrix")
            cmds.connectAttr(
                f"{output_sources[i]}.worldMatrix[0]", f"{mult_m}.matrixIn[0]"
            )
            cmds.connectAttr(
                f"{self.rig_root}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
            )
            cmds.connectAttr(f"{mult_m}.matrixSum", f"{output_npo}.offsetParentMatrix")
            cmds.connectAttr(f"{host_ctl}.tweak_ctls_visibility", f"{output_npo}.v")
            cmds.setAttr(f"{output_npo}.t", 0, 0, 0)
            cmds.setAttr(f"{output_npo}.r", 0, 0, 0)
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
            cmds.setAttr(f"{output}.drawStyle", 2)
            self["output"][i + 1].connect(output_ctl)

        # output joint
        for i in range(self["output_count"]["value"] + 1):
            if self["create_output_joint"]["value"]:
                self["output_joint"][i].create()

    # endregion

    # region GUIDE
    @build_log(logging.INFO)
    def guide(self):
        super().guide(description=description)
        graph, guide_compound = self.add_guide_graph()

        cmds.vnnNode(
            graph,
            "/input",
            createOutputPort=("main_transforms", "array<Math::float4x4>"),
        )
        cmds.vnnNode(
            graph,
            "/input",
            createOutputPort=("up_transforms", "array<Math::float4x4>"),
        )
        cmds.vnnNode(
            graph,
            "/input",
            createOutputPort=("negate", "bool"),
        )
        cmds.vnnNode(
            graph,
            "/output",
            createInputPort=("driver_matrix", "array<Math::float4x4>"),
        )
        cmds.vnnNode(
            graph,
            "/output",
            createInputPort=("driver_inverse_matrix", "array<Math::float4x4>"),
        )
        cmds.vnnNode(
            graph,
            "/output",
            createInputPort=("tip_matrix", "Math::double4x4"),
        )
        cmds.vnnConnect(
            graph,
            "/input.main_transforms",
            f"/{guide_compound}.main_transforms",
        )
        cmds.vnnConnect(
            graph,
            "/input.up_transforms",
            f"/{guide_compound}.up_transforms",
        )
        cmds.vnnConnect(
            graph,
            "/input.negate",
            f"/{guide_compound}.negate",
        )
        cmds.vnnConnect(
            graph,
            f"/{guide_compound}.driver_matrix",
            f"/output.driver_matrix",
        )
        cmds.vnnConnect(
            graph,
            f"/{guide_compound}.driver_inverse_matrix",
            f"/output.driver_inverse_matrix",
        )
        cmds.vnnConnect(
            graph,
            f"/{guide_compound}.tip_matrix",
            f"/output.tip_matrix",
        )

        condition = cmds.createNode("condition")
        cmds.connectAttr(f"{self.rig_root}.side", f"{condition}.firstTerm")
        cmds.setAttr(f"{condition}.secondTerm", 2)
        cmds.setAttr(f"{condition}.colorIfTrueR", 1)
        cmds.setAttr(f"{condition}.colorIfFalseR", 0)
        cmds.connectAttr(f"{condition}.outColorR", f"{self.guide_graph}.negate")

        # guide
        upper_body_guide = self.add_guide(
            parent=self.guide_root,
            description="upperBody",
            m=self["guide_matrix"]["value"][0],
            mirror_type=self["guide_mirror_type"]["value"][0],
        )
        hip_guide = self.add_guide(
            parent=upper_body_guide,
            description="hip",
            m=self["guide_matrix"]["value"][1],
            mirror_type=self["guide_mirror_type"]["value"][1],
        )
        fk0_guide = self.add_guide(
            parent=upper_body_guide,
            description="fk0",
            m=self["guide_matrix"]["value"][2],
            mirror_type=self["guide_mirror_type"]["value"][2],
        )
        fk1_guide = self.add_guide(
            parent=fk0_guide,
            description="fk1",
            m=self["guide_matrix"]["value"][3],
            mirror_type=self["guide_mirror_type"]["value"][3],
        )
        ik_guide = self.add_guide(
            parent=fk1_guide,
            description="ik",
            m=self["guide_matrix"]["value"][4],
            mirror_type=self["guide_mirror_type"]["value"][4],
        )
        tip_guide = self.add_guide(
            parent=ik_guide,
            description="tip",
            m=self["guide_matrix"]["value"][5],
            mirror_type=self["guide_mirror_type"]["value"][5],
        )
        driver0_guide = self.add_guide(
            parent=upper_body_guide,
            description="driver0",
            m=self["guide_matrix"]["value"][6],
            mirror_type=self["guide_mirror_type"]["value"][6],
        )
        driver1_guide = self.add_guide(
            parent=upper_body_guide,
            description="driver1",
            m=self["guide_matrix"]["value"][7],
            mirror_type=self["guide_mirror_type"]["value"][7],
        )
        driver2_guide = self.add_guide(
            parent=upper_body_guide,
            description="driver2",
            m=self["guide_matrix"]["value"][8],
            mirror_type=self["guide_mirror_type"]["value"][8],
        )
        driver3_guide = self.add_guide(
            parent=upper_body_guide,
            description="driver3",
            m=self["guide_matrix"]["value"][9],
            mirror_type=self["guide_mirror_type"]["value"][9],
        )

        ins = Surface(data=self["ribbon_surface"]["value"])
        surface = ins.create_from_data()
        surface = cmds.parent(surface, upper_body_guide)[0]
        surface = cmds.rename(surface, tip_guide.replace("tip", "surface"))
        cmds.setAttr(f"{surface}.t", lock=True)
        cmds.setAttr(f"{surface}.r", lock=True)
        tg = cmds.createNode("transformGeometry")
        cmds.connectAttr(f"{surface}.worldMatrix[0]", f"{tg}.transform")
        cmds.connectAttr(f"{surface}.worldSpace[0]", f"{tg}.inputGeometry")
        cmds.connectAttr(f"{tg}.outputGeometry", f"{self.guide_root}.ribbon_surface")

        uvpin = cmds.createNode("uvPin")
        cmds.connectAttr(f"{surface}.worldSpace[0]", f"{uvpin}.deformedGeometry")

        c = 0
        for i in range(len(self["output_v_values"]["value"])):
            cmds.connectAttr(
                f"{self.guide_root}.output_v_values[{i}]",
                f"{uvpin}.coordinate[{c}].coordinateV",
            )
            cmds.setAttr(f"{uvpin}.coordinate[{c}].coordinateU", 0.5)
            cmds.connectAttr(
                f"{uvpin}.outputMatrix[{c}]", f"{graph}.main_transforms[{i}]"
            )
            c += 1
        for i in range(len(self["output_v_values"]["value"])):
            cmds.connectAttr(
                f"{self.guide_root}.output_v_values[{i}]",
                f"{uvpin}.coordinate[{c}].coordinateV",
            )
            cmds.connectAttr(
                f"{uvpin}.outputMatrix[{c}]", f"{graph}.up_transforms[{i}]"
            )
            c += 1

        for i in range(6):
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

        for i in range(self["output_count"]["value"] + 1):
            cmds.connectAttr(
                f"{self.guide_graph}.initialize_output_matrix[{i}]",
                f"{self.guide_root}.initialize_output_matrix[{i}]",
            )
            cmds.connectAttr(
                f"{self.guide_graph}.initialize_output_inverse_matrix[{i}]",
                f"{self.guide_root}.initialize_output_inverse_matrix[{i}]",
            )

        for i in range(4):
            cmds.connectAttr(
                f"{self.guide_graph}.driver_matrix[{i}]",
                f"{self.guide_root}.driver_matrix[{i}]",
            )
            cmds.connectAttr(
                f"{self.guide_graph}.driver_inverse_matrix[{i}]",
                f"{self.guide_root}.driver_inverse_matrix[{i}]",
            )
        cmds.connectAttr(
            f"{self.guide_graph}.tip_matrix", f"{self.guide_root}.tip_matrix"
        )

    # endregion
