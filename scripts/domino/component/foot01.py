# maya
from domino import component
from domino.core import attribute, Name, NurbsCurve, Joint
from domino.core.utils import build_log

# maya
from maya.api import OpenMaya as om
from maya import cmds

# built-ins
import logging

# gui
from PySide6 import QtWidgets


# region Initialize Settings
ORIGINMATRIX = om.MMatrix()
matrices = [list(ORIGINMATRIX)]
DATA = [
    attribute.String(longName="component", value="foot01"),
    attribute.String(longName="name", value="foot"),
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
    attribute.Float(longName="radius", minValue=0, value=0.5),
    attribute.Float(longName="scaled_radius", minValue=0, value=0.5),
    attribute.Enum(
        longName="roll_axis", enumName=["x", "y", "z", "-x", "-y", "-z"], value=1
    ),
    attribute.Float(longName="default_inverse_angle", multi=True),
    attribute.NurbsCurve(
        longName="foot_shape_curve",
        value={
            "parent_name": "",
            "curve_name": "footShapeCurve",
            "curve_matrix": [
                1,
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
            "shapes": {
                "footShapeCurveShape": {
                    "form": 3,
                    "knots": [
                        -2.0,
                        -1.0,
                        0.0,
                        1.0,
                        2.0,
                        3.0,
                        4.0,
                        5.0,
                        6.0,
                        7.0,
                        8.0,
                        9.0,
                        10.0,
                        11.0,
                        12.0,
                    ],
                    "degree": 3,
                    "point": [
                        [
                            0.30881453179753815,
                            4.257038687343693e-17,
                            -3.3181128145471717,
                        ],
                        [
                            0.01503351067311031,
                            5.261989200403277e-17,
                            -3.590273873743019,
                        ],
                        [
                            -0.3684783356992707,
                            4.2570386873436926e-17,
                            -3.3181128145471708,
                        ],
                        [
                            -0.31004058784399907,
                            1.6260440871420544e-17,
                            -2.710572716585927,
                        ],
                        [
                            -0.4371801483172836,
                            -1.6260440871420532e-17,
                            -1.7233459681889678,
                        ],
                        [
                            -0.4213744709213093,
                            -4.2570386873436945e-17,
                            -0.9490712806160652,
                        ],
                        [
                            0.010059244903375623,
                            -5.261989200403276e-17,
                            -0.6884728626713134,
                        ],
                        [
                            0.5843524449253141,
                            -4.2570386873436945e-17,
                            -1.1588916092326786,
                        ],
                        [
                            0.5974423943663967,
                            -1.626044087142054e-17,
                            -1.7233459681889676,
                        ],
                        [
                            0.34989705767478446,
                            1.6260440871420532e-17,
                            -2.710572716585927,
                        ],
                        [
                            0.30881453179753815,
                            4.257038687343693e-17,
                            -3.3181128145471717,
                        ],
                        [
                            0.01503351067311031,
                            5.261989200403277e-17,
                            -3.590273873743019,
                        ],
                        [
                            -0.3684783356992707,
                            4.2570386873436926e-17,
                            -3.3181128145471708,
                        ],
                    ],
                    "override": False,
                    "use_rgb": False,
                    "color_rgb": (0.0, 0.0, 0.0),
                    "color_index": 0,
                    "always_draw_on_top": False,
                    "visibility": True,
                }
            },
            "visibility": True,
        },
    ),
]

description = """## foot01
---

foot 컴포넌트 입니다. fk 와 reverse foot 기능이 있습니다.   

#### Input
> 관절 갯수를 입력합니다.

#### Settings
"""
# endregion


class Rig(component.Rig):

    def input_data(self):
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle("Output Count")
        label = QtWidgets.QLabel("Output Count : ")
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
            if value < 1:
                return False
            self["initialize_output_matrix"]["value"] = [
                list(ORIGINMATRIX) for _ in range(value)
            ]
            self["initialize_output_inverse_matrix"]["value"] = [
                list(ORIGINMATRIX) for _ in range(value)
            ]

            self["guide_matrix"]["value"] = []
            self["guide_mirror_type"]["value"] = []
            self["npo_matrix"]["value"] = []
            self["default_inverse_angle"]["value"] = []
            init_matrices = [
                [
                    0.9897002248149297,
                    0.0,
                    -0.14315538760828278,
                    0.0,
                    0.0,
                    1.0,
                    0.0,
                    0.0,
                    0.14315538760828278,
                    0.0,
                    0.9897002248149297,
                    0.0,
                    1.4848742485046387,
                    1.1313194036483765,
                    -0.42793452739715576,
                    1.0,
                ],
                [
                    0.9897002248149297,
                    0.0,
                    -0.14315538760828278,
                    0.0,
                    0.0,
                    1.0,
                    0.0,
                    0.0,
                    0.14315538760828278,
                    0.0,
                    0.9897002248149297,
                    0.0,
                    1.8991612928257677,
                    0.0,
                    2.436225793445786,
                    1.0,
                ],
                [
                    0.9897002248149297,
                    0.0,
                    -0.14315538760828278,
                    0.0,
                    0.0,
                    1.0,
                    0.0,
                    0.0,
                    0.14315538760828278,
                    0.0,
                    0.9897002248149297,
                    0.0,
                    1.4110682011422395,
                    0.0,
                    -0.9381902913446694,
                    1.0,
                ],
                [
                    0.9990726354059491,
                    0.0,
                    -0.043056581181180886,
                    0.0,
                    0.0,
                    1.0,
                    0.0,
                    0.0,
                    0.043056581181180886,
                    0.0,
                    0.9990726354059491,
                    0.0,
                    1.2442596988288277,
                    0.0,
                    0.2827487349919464,
                    1.0,
                ],
                [
                    0.9403312516864117,
                    0.0,
                    -0.3402603960232021,
                    0.0,
                    0.0,
                    1.0,
                    0.0,
                    0.0,
                    0.3402603960232021,
                    0.0,
                    0.9403312516864117,
                    0.0,
                    2.097143040911047,
                    0.0,
                    0.2628767868826061,
                    1.0,
                ],
                [
                    0.9897002248149298,
                    0.0,
                    -0.14315538760828272,
                    0.0,
                    0.0,
                    1.0,
                    0.0,
                    0.0,
                    0.14315538760828272,
                    0.0,
                    0.9897002248149298,
                    0.0,
                    1.7769843402348195,
                    0.0,
                    1.5915593127308985,
                    1.0,
                ],
                [
                    0.14315538760828278,
                    0.0,
                    0.9897002248149297,
                    0.0,
                    0.9897002248149297,
                    0.0,
                    -0.14315538760828278,
                    0.0,
                    0.0,
                    1.0,
                    0.0,
                    0.0,
                    1.7175422274917784,
                    0.14633208492886185,
                    1.1806081544954916,
                    1.0,
                ],
            ]
            # root
            self["guide_matrix"]["value"].append(init_matrices[0])
            self["guide_mirror_type"]["value"].append(1)
            # roll-bank
            self["guide_matrix"]["value"].append(init_matrices[1])
            self["guide_mirror_type"]["value"].append(1)
            self["npo_matrix"]["value"].append(list(ORIGINMATRIX))
            # heel
            self["guide_matrix"]["value"].append(init_matrices[2])
            self["guide_mirror_type"]["value"].append(2)
            self["npo_matrix"]["value"].append(list(ORIGINMATRIX))
            # in
            self["guide_matrix"]["value"].append(init_matrices[3])
            self["guide_mirror_type"]["value"].append(2)
            self["npo_matrix"]["value"].append(list(ORIGINMATRIX))
            # out
            self["guide_matrix"]["value"].append(init_matrices[4])
            self["guide_mirror_type"]["value"].append(2)
            self["npo_matrix"]["value"].append(list(ORIGINMATRIX))
            # toeEnd
            self["guide_matrix"]["value"].append(init_matrices[5])
            self["guide_mirror_type"]["value"].append(2)
            self["npo_matrix"]["value"].append(list(ORIGINMATRIX))
            # fk
            c = 1
            m = init_matrices[6].copy()
            for _ in range(value):
                self["guide_matrix"]["value"].append(m.copy())
                self["guide_mirror_type"]["value"].append(1)
                c += 1
                # forward
                self["npo_matrix"]["value"].append(list(ORIGINMATRIX))
                # inverse
                self["npo_matrix"]["value"].append(list(ORIGINMATRIX))
                m[12] += 0.14315538760828316889
                m[14] += 0.98970022481492980759
                self["default_inverse_angle"]["value"].append(20)
        except:
            return False
        return result

    def __init__(self):
        super().__init__(DATA)

    def populate_controller(self):
        if not self["controller"]:
            self.add_controller(description="host", parent_controllers=[])
            self.add_controller(
                description="rollBank", parent_controllers=[(self.identifier, "host")]
            )
            self.add_controller(
                description="heel", parent_controllers=[(self.identifier, "host")]
            )
            self.add_controller(
                description="in", parent_controllers=[(self.identifier, "heel")]
            )
            self.add_controller(
                description="out", parent_controllers=[(self.identifier, "in")]
            )
            self.add_controller(
                description="toeEnd", parent_controllers=[(self.identifier, "out")]
            )
            fk_count = len(self["guide_matrix"]["value"]) - 6
            parent_controllers = [
                (self.identifier, "toeEnd"),
                (self.identifier, "rollBank"),
            ]
            for i in reversed(range(fk_count)):
                self.add_controller(
                    description=f"inv{i}", parent_controllers=parent_controllers
                )
                parent_controllers = [(self.identifier, f"inv{i}")]
            for i in range(fk_count):
                self.add_controller(
                    description=i, parent_controllers=parent_controllers
                )
                parent_controllers = [(self.identifier, i)]

    def populate_output(self):
        if not self["output"]:
            fk_count = len(self["guide_matrix"]["value"]) - 6
            for i in range(fk_count):
                self.add_output(description=i, extension=Name.output_extension)

    def populate_output_joint(self):
        if not self["output_joint"]:
            fk_count = len(self["guide_matrix"]["value"]) - 6
            parent = None
            for i in range(fk_count):
                self.add_output_joint(parent_description=parent, description=i)
                parent = i

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
            longName="legacy",
            attributeType="bool",
            defaultValue=0,
            keyable=True,
        )
        roll_bank_npo, roll_bank_ctl = self["controller"][1].create(
            parent=self.rig_root,
            shape=(
                self["controller"][1]["shape"]
                if "shape" in self["controller"][1]
                else "line"
            ),
            color=12,
            npo_matrix_index=0,
        )
        for i, angle in enumerate(self["default_inverse_angle"]["value"]):
            cmds.addAttr(
                roll_bank_ctl,
                longName=f"angle{i}",
                attributeType="float",
                defaultValue=angle,
                keyable=True,
            )
        rev = cmds.createNode("reverse")
        cmds.connectAttr(f"{host_ctl}.legacy", f"{rev}.inputX")
        cmds.connectAttr(f"{rev}.outputX", f"{roll_bank_npo}.v")
        cmds.setAttr(f"{roll_bank_ctl}.tx", lock=True, keyable=False)
        cmds.setAttr(f"{roll_bank_ctl}.ty", lock=True, keyable=False)
        cmds.setAttr(f"{roll_bank_ctl}.tz", lock=True, keyable=False)
        roll_bank_offset = cmds.createNode(
            "transform",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="rollBank",
                extension="offset",
            ),
            parent=roll_bank_ctl,
        )
        cmds.connectAttr(f"{self.rig_root}.scaled_radius", f"{roll_bank_offset}.ty")
        circle, make_circle = cmds.circle(
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="nearest",
                extension=Name.curve_extension,
            ),
            degree=3,
            sections=10,
            normal=(0, 1, 0),
        )
        circle = cmds.parent(circle, roll_bank_npo)[0]
        cmds.connectAttr(f"{self.rig_root}.scaled_radius", f"{make_circle}.radius")
        ins = NurbsCurve(data=self["foot_shape_curve"]["value"])
        foot_shape_curve = ins.create_from_data()
        foot_shape_curve = cmds.rename(
            foot_shape_curve,
            Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="footShape",
                extension=Name.curve_extension,
            ),
        )
        foot_shape_curve = cmds.parent(foot_shape_curve, roll_bank_npo)[0]
        cmds.connectAttr(
            f"{self.rig_root}.foot_shape_curve", f"{foot_shape_curve}.create"
        )
        for attr in [".tx", ".ty", ".tz", ".rx", ".ry", ".rz"]:
            cmds.setAttr(f"{circle}{attr}", 0)
            cmds.setAttr(f"{foot_shape_curve}{attr}", 0)
            cmds.setAttr(f"{circle}{attr}", lock=True, keyable=False)
            cmds.setAttr(f"{foot_shape_curve}{attr}", lock=True, keyable=False)
        for attr in [".sx", ".sy", ".sz"]:
            cmds.setAttr(f"{circle}{attr}", 1)
            cmds.setAttr(f"{foot_shape_curve}{attr}", 1)
            cmds.setAttr(f"{circle}{attr}", lock=True, keyable=False)
        cmds.setAttr(f"{circle}.overrideEnabled", 1)
        cmds.setAttr(f"{circle}.overrideDisplayType", 2)
        cmds.setAttr(f"{foot_shape_curve}.overrideEnabled", 1)
        cmds.setAttr(f"{foot_shape_curve}.overrideDisplayType", 2)

        pivot = cmds.createNode(
            "transform",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="rollBank",
                extension="pivot",
            ),
            parent=roll_bank_npo,
        )
        pivot_inverse = cmds.createNode(
            "transform",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="rollBank",
                extension="pivotInverse",
            ),
            parent=pivot,
        )
        inverse_m = cmds.createNode("inverseMatrix")
        cmds.connectAttr(f"{self.rig_root}.npo_matrix[0]", f"{inverse_m}.inputMatrix")
        cmds.connectAttr(
            f"{inverse_m}.outputMatrix", f"{pivot_inverse}.offsetParentMatrix"
        )
        cmds.connectAttr(f"{roll_bank_ctl}.rz", f"{pivot}.rz")
        pma = cmds.createNode("plusMinusAverage")
        for i in range(len(self["default_inverse_angle"]["value"])):
            cmds.connectAttr(f"{roll_bank_ctl}.angle{i}", f"{pma}.input1D[{i}]")
        pma1 = cmds.createNode("plusMinusAverage")
        cmds.setAttr(f"{pma1}.operation", 2)
        cmds.connectAttr(f"{roll_bank_ctl}.rx", f"{pma1}.input1D[0]")
        cmds.connectAttr(f"{pma}.output1D", f"{pma1}.input1D[1]")
        cr = cmds.createNode("clampRange")
        cmds.connectAttr(f"{pma1}.output1D", f"{cr}.input")
        cmds.setAttr(f"{cr}.maximum", 99999999)
        condition = cmds.createNode("condition")
        cmds.setAttr(f"{condition}.secondTerm", 0)
        cmds.setAttr(f"{condition}.operation", 2)
        cmds.connectAttr(f"{roll_bank_ctl}.rx", f"{condition}.firstTerm")
        cmds.connectAttr(f"{cr}.output", f"{condition}.colorIfTrueR")
        cmds.connectAttr(f"{roll_bank_ctl}.rx", f"{condition}.colorIfFalseR")
        cmds.connectAttr(f"{condition}.outColorR", f"{pivot}.rx")

        heel_npo, heel_ctl = self["controller"][2].create(
            parent=self.rig_root,
            shape=(
                self["controller"][2]["shape"]
                if "shape" in self["controller"][2]
                else "cube"
            ),
            color=12,
            npo_matrix_index=1,
        )
        cmds.connectAttr(f"{host_ctl}.legacy", f"{heel_npo}.v")
        cmds.setAttr(f"{heel_ctl}.tx", lock=True, keyable=False)
        cmds.setAttr(f"{heel_ctl}.ty", lock=True, keyable=False)
        cmds.setAttr(f"{heel_ctl}.tz", lock=True, keyable=False)
        in_npo, in_ctl = self["controller"][3].create(
            parent=heel_ctl,
            shape=(
                self["controller"][3]["shape"]
                if "shape" in self["controller"][3]
                else "cube"
            ),
            color=12,
            npo_matrix_index=2,
        )
        cmds.setAttr(f"{in_ctl}.tx", lock=True, keyable=False)
        cmds.setAttr(f"{in_ctl}.ty", lock=True, keyable=False)
        cmds.setAttr(f"{in_ctl}.tz", lock=True, keyable=False)
        out_npo, out_ctl = self["controller"][4].create(
            parent=in_ctl,
            shape=(
                self["controller"][4]["shape"]
                if "shape" in self["controller"][4]
                else "cube"
            ),
            color=12,
            npo_matrix_index=3,
        )
        cmds.setAttr(f"{out_ctl}.tx", lock=True, keyable=False)
        cmds.setAttr(f"{out_ctl}.ty", lock=True, keyable=False)
        cmds.setAttr(f"{out_ctl}.tz", lock=True, keyable=False)
        toe_end_npo, toe_end_ctl = self["controller"][5].create(
            parent=out_ctl,
            shape=(
                self["controller"][5]["shape"]
                if "shape" in self["controller"][5]
                else "cube"
            ),
            color=12,
            npo_matrix_index=4,
        )
        cmds.setAttr(f"{toe_end_ctl}.tx", lock=True, keyable=False)
        cmds.setAttr(f"{toe_end_ctl}.ty", lock=True, keyable=False)
        cmds.setAttr(f"{toe_end_ctl}.tz", lock=True, keyable=False)
        legacy_inverse = cmds.createNode(
            "transform",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="legacy",
                extension="inverse",
            ),
            parent=toe_end_ctl,
        )
        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{self.rig_root}.npo_matrix[4]", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(f"{self.rig_root}.npo_matrix[3]", f"{mult_m}.matrixIn[1]")
        cmds.connectAttr(f"{self.rig_root}.npo_matrix[2]", f"{mult_m}.matrixIn[2]")
        cmds.connectAttr(f"{self.rig_root}.npo_matrix[1]", f"{mult_m}.matrixIn[3]")
        inverse_m = cmds.createNode("inverseMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{inverse_m}.inputMatrix")
        cmds.connectAttr(
            f"{inverse_m}.outputMatrix", f"{legacy_inverse}.offsetParentMatrix"
        )

        inverse_grp = cmds.createNode(
            "transform",
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="inv",
                extension=Name.group_extension,
            ),
            parent=self.rig_root,
        )
        cons = cmds.parentConstraint(pivot_inverse, legacy_inverse, inverse_grp)[0]
        rev = cmds.createNode("reverse")
        cmds.connectAttr(f"{host_ctl}.legacy", f"{rev}.inputX")
        attrs = cmds.parentConstraint(cons, query=True, weightAliasList=True)
        cmds.connectAttr(f"{host_ctl}.legacy", f"{cons}.{attrs[1]}")
        cmds.connectAttr(f"{rev}.outputX", f"{cons}.{attrs[0]}")

        fk_count = len(self["guide_matrix"]["value"]) - 6
        c = 6
        parent = inverse_grp
        reverse_ctls = []
        fix_objs = []
        for i in range(fk_count):
            npo, ctl = self["controller"][c].create(
                parent=parent,
                shape=(
                    self["controller"][c]["shape"]
                    if "shape" in self["controller"][c]
                    else "cube"
                ),
                color=12,
                npo_matrix_index=c - 1,
            )
            cmds.setAttr(f"{ctl}.tx", lock=True, keyable=False)
            cmds.setAttr(f"{ctl}.ty", lock=True, keyable=False)
            cmds.setAttr(f"{ctl}.tz", lock=True, keyable=False)
            fix_obj = cmds.createNode(
                "transform",
                name=Name.create(
                    Name.controller_name_convention,
                    name=name,
                    side=side,
                    index=index,
                    description=f"fix{i}",
                    extension="source",
                ),
                parent=cmds.listRelatives(npo, parent=True)[0],
            )
            plug = cmds.listConnections(
                f"{npo}.offsetParentMatrix", source=True, destination=False, plugs=True
            )[0]
            cmds.connectAttr(plug, f"{fix_obj}.offsetParentMatrix")
            parent = ctl
            reverse_ctls.append(ctl)
            fix_objs.append(fix_obj)
            c += 1

        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{roll_bank_offset}.worldMatrix[0]", f"{decom_m}.inputMatrix")
        nearest_point = cmds.createNode("nearestPointOnCurve")
        cmds.connectAttr(f"{circle}.worldSpace[0]", f"{nearest_point}.inputCurve")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{nearest_point}.inPosition")
        poci = cmds.createNode("pointOnCurveInfo")
        cmds.connectAttr(f"{foot_shape_curve}.local", f"{poci}.inputCurve")
        cmds.connectAttr(f"{nearest_point}.parameter", f"{poci}.parameter")
        cmds.connectAttr(f"{poci}.position", f"{pivot}.rotatePivot")

        reverse_npos = [
            cmds.listRelatives(x, parent=True)[0] for x in list(reversed(reverse_ctls))
        ]
        axis = ((1, 0, 0), (0, 1, 0), (0, 0, 1), (-1, 0, 0), (0, -1, 0), (0, 0, -1))
        axis_md = []
        for a in axis:
            md = cmds.createNode("multiplyDivide")
            cmds.setAttr(f"{md}.input1", *a)
            cmds.setAttr(f"{md}.input2", 1, 1, 1)
            axis_md.append(md)
        roll_axis_choide = cmds.createNode("choice")
        for i, md in enumerate(axis_md):
            cmds.connectAttr(f"{md}.output", f"{roll_axis_choide}.input[{i}]")
        cmds.connectAttr(f"{self.rig_root}.roll_axis", f"{roll_axis_choide}.selector")

        enable_rev = cmds.createNode("reverse")
        cmds.connectAttr(f"{host_ctl}.legacy", f"{enable_rev}.inputX")
        for i in range(len(self["default_inverse_angle"]["value"])):
            min_pma = cmds.createNode("plusMinusAverage")
            max_pma = cmds.createNode("plusMinusAverage")
            cmds.setAttr(f"{min_pma}.input1D[0]", 0)
            cmds.setAttr(f"{max_pma}.input1D[0]", 0)
            if i > 0:
                for x in range(i):
                    cmds.connectAttr(
                        f"{roll_bank_ctl}.angle{x}", f"{min_pma}.input1D[{1 + x}]"
                    )
            for x in range(i + 1):
                cmds.connectAttr(
                    f"{roll_bank_ctl}.angle{x}", f"{max_pma}.input1D[{1 + x}]"
                )
            rv = cmds.createNode("remapValue")
            cmds.connectAttr(f"{min_pma}.output1D", f"{rv}.inputMin")
            cmds.connectAttr(f"{max_pma}.output1D", f"{rv}.inputMax")
            cmds.connectAttr(f"{roll_bank_ctl}.rx", f"{rv}.inputValue")
            cmds.connectAttr(f"{roll_bank_ctl}.angle{i}", f"{rv}.outputMax")
            md = cmds.createNode("multiplyDivide")
            cmds.connectAttr(f"{rv}.outValue", f"{md}.input1X")
            cmds.connectAttr(f"{rv}.outValue", f"{md}.input1Y")
            cmds.connectAttr(f"{rv}.outValue", f"{md}.input1Z")
            cmds.connectAttr(f"{roll_axis_choide}.output", f"{md}.input2")
            enable_md = cmds.createNode("multiplyDivide")
            cmds.connectAttr(f"{enable_rev}.outputX", f"{enable_md}.input1X")
            cmds.connectAttr(f"{enable_rev}.outputX", f"{enable_md}.input1Y")
            cmds.connectAttr(f"{enable_rev}.outputX", f"{enable_md}.input1Z")
            cmds.connectAttr(f"{md}.output", f"{enable_md}.input2")
            cmds.connectAttr(f"{enable_md}.output", f"{reverse_npos[i]}.r")

        fk_ctls = []
        rot_refs = []
        parent = self.rig_root
        rot_parent = inverse_grp
        for i in range(fk_count):
            rot_ref = cmds.createNode(
                "transform",
                name=Name.create(
                    Name.controller_name_convention,
                    name=name,
                    side=side,
                    index=index,
                    description=i,
                    extension="ref",
                ),
                parent=rot_parent,
            )
            npo, ctl = self["controller"][c].create(
                parent=parent,
                shape=(
                    self["controller"][c]["shape"]
                    if "shape" in self["controller"][c]
                    else "cube"
                ),
                color=12,
                npo_matrix_index=c - 1,
            )
            plug = cmds.listConnections(
                f"{npo}.offsetParentMatrix", source=True, destination=False, plugs=True
            )[0]
            cmds.connectAttr(plug, f"{rot_ref}.offsetParentMatrix")
            cmds.connectAttr(f"{rot_ref}.t", f"{npo}.t")
            cmds.connectAttr(f"{rot_ref}.r", f"{npo}.r")
            parent = ctl
            rot_parent = rot_ref
            fk_ctls.append(ctl)
            rot_refs.append(rot_ref)
            c += 1
        for ref, obj in zip(rot_refs, reversed(fix_objs)):
            cmds.parentConstraint(obj, ref)

        # output
        outputs = []
        for i, ctl in enumerate(fk_ctls):
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
            self["output"][i].connect(ctl)
            cmds.setAttr(f"{output}.drawStyle", 2)
            outputs.append(output)

        # output joint
        if self["create_output_joint"]["value"]:
            for i in range(len(fk_ctls)):
                self["output_joint"][i].create()

    # endregion

    # region GUIDE
    @build_log(logging.INFO)
    def guide(self):
        super().guide(description=description)
        graph, guide_compound = self.add_guide_graph()

        name, side, index = self.identifier

        root_guide = self.add_guide(
            parent=self.guide_root,
            description="root",
            m=self["guide_matrix"]["value"][0],
            mirror_type=self["guide_mirror_type"]["value"][0],
        )
        cmds.setAttr(f"{root_guide}.mirror_type", lock=True, keyable=False)
        roll_bank_guide = self.add_guide(
            parent=root_guide,
            description="rollBank",
            m=self["guide_matrix"]["value"][1],
            mirror_type=self["guide_mirror_type"]["value"][1],
        )
        cmds.setAttr(f"{roll_bank_guide}.mirror_type", lock=True, keyable=False)
        cmds.addAttr(
            roll_bank_guide,
            longName="mirror_foot_shape",
            attributeType="bool",
            keyable=True,
            defaultValue=0,
        )

        circle, make_circle = cmds.circle(
            name=Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="nearestGuide",
                extension=Name.curve_extension,
            ),
            degree=3,
            sections=10,
            normal=(0, 1, 0),
        )
        circle = cmds.parent(circle, roll_bank_guide)[0]
        cmds.setAttr(f"{circle}.t", 0, 0, 0)
        cmds.setAttr(f"{circle}.r", 0, 0, 0)
        cmds.setAttr(f"{circle}.s", 1, 1, 1)
        cmds.setAttr(f"{circle}.t", lock=True)
        cmds.setAttr(f"{circle}.r", lock=True)
        cmds.setAttr(f"{circle}.s", lock=True)
        cmds.setAttr(f"{circle}.v", lock=True)
        cmds.setAttr(f"{circle}.overrideEnabled", 1)
        cmds.setAttr(f"{circle}.overrideDisplayType", 2)
        if round(cmds.getAttr(f"{self.guide_root}.sx"), 3) == 1.0:
            cmds.setAttr(
                f"{self.guide_root}.radius",
                cmds.getAttr(f"{self.guide_root}.scaled_radius"),
            )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{self.guide_root}.worldMatrix[0]", f"{decom_m}.inputMatrix")

        multiply = cmds.createNode("multiply")
        cmds.connectAttr(f"{self.guide_root}.radius", f"{multiply}.input[0]")
        cmds.connectAttr(f"{decom_m}.outputScaleX", f"{multiply}.input[1]")
        cmds.connectAttr(f"{multiply}.output", f"{self.guide_root}.scaled_radius")
        cmds.connectAttr(f"{self.guide_root}.radius", f"{make_circle}.radius")

        ins = NurbsCurve(data=self["foot_shape_curve"]["value"])
        shape_curve = ins.create_from_data()
        shape_curve = cmds.rename(
            shape_curve,
            Name.create(
                Name.controller_name_convention,
                name=name,
                side=side,
                index=index,
                description="footShapeGuide",
                extension=Name.curve_extension,
            ),
        )
        shape_curve = cmds.parent(shape_curve, roll_bank_guide)[0]
        temp_bs = cmds.blendShape()
        cmds.delete(temp_bs)

        condition = cmds.createNode("condition")
        cmds.connectAttr(
            f"{roll_bank_guide}.mirror_foot_shape", f"{condition}.firstTerm"
        )
        cmds.setAttr(f"{condition}.secondTerm", 1)
        cmds.setAttr(f"{condition}.colorIfTrueR", -1)
        cmds.setAttr(f"{condition}.colorIfFalseR", 1)
        md = cmds.createNode("multiplyDivide")
        cmds.setAttr(f"{md}.operation", 2)
        cmds.setAttr(f"{md}.input1Y", 1)
        cmds.connectAttr(f"{condition}.outColorR", f"{md}.input1X")
        cmds.connectAttr(f"{condition}.outColorR", f"{md}.input1Z")
        cmds.connectAttr(f"{root_guide}.s", f"{md}.input2")

        tg = cmds.createNode("transformGeometry")
        cmds.connectAttr(f"{shape_curve}ShapeOrig.local", f"{tg}.inputGeometry")
        compose_m = cmds.createNode("composeMatrix")
        cmds.connectAttr(f"{md}.output", f"{compose_m}.inputScale")
        cmds.connectAttr(f"{compose_m}.outputMatrix", f"{tg}.transform")
        cmds.connectAttr(f"{tg}.outputGeometry", f"{shape_curve}Shape.create", force=1)

        tg = cmds.createNode("transformGeometry")
        cmds.connectAttr(f"{make_circle}.outputCurve", f"{tg}.inputGeometry")
        compose_m = cmds.createNode("composeMatrix")
        cmds.connectAttr(f"{md}.output", f"{compose_m}.inputScale")
        cmds.connectAttr(f"{compose_m}.outputMatrix", f"{tg}.transform")
        cmds.connectAttr(f"{tg}.outputGeometry", f"{circle}Shape.create", force=1)

        cmds.setAttr(f"{shape_curve}.t", 0, 0, 0)
        cmds.setAttr(f"{shape_curve}.r", 0, 0, 0)
        cmds.setAttr(f"{shape_curve}.s", 1, 1, 1)
        cmds.setAttr(f"{shape_curve}.t", lock=True)
        cmds.setAttr(f"{shape_curve}.r", lock=True)
        cmds.setAttr(f"{shape_curve}.s", lock=True)
        cmds.setAttr(f"{shape_curve}.v", lock=True)
        cmds.setAttr(f"{shape_curve}.dispHull", 1)
        pick_m = cmds.createNode("pickMatrix")
        cmds.connectAttr(f"{shape_curve}.worldMatrix[0]", f"{pick_m}.inputMatrix")
        cmds.setAttr(f"{pick_m}.useTranslate", 0)
        cmds.setAttr(f"{pick_m}.useRotate", 0)
        cmds.setAttr(f"{pick_m}.useShear", 0)
        tg = cmds.createNode("transformGeometry")
        cmds.connectAttr(f"{shape_curve}.worldSpace[0]", f"{tg}.inputGeometry")
        cmds.connectAttr(f"{pick_m}.outputMatrix", f"{tg}.transform")
        cmds.connectAttr(f"{tg}.outputGeometry", f"{self.guide_root}.foot_shape_curve")

        heel_guide = self.add_guide(
            parent=root_guide,
            description="heel",
            m=self["guide_matrix"]["value"][2],
            mirror_type=self["guide_mirror_type"]["value"][2],
        )
        cmds.setAttr(f"{heel_guide}.mirror_type", lock=True, keyable=False)
        in_guide = self.add_guide(
            parent=heel_guide,
            description="in",
            m=self["guide_matrix"]["value"][3],
            mirror_type=self["guide_mirror_type"]["value"][3],
        )
        cmds.setAttr(f"{in_guide}.mirror_type", lock=True, keyable=False)
        out_guide = self.add_guide(
            parent=in_guide,
            description="out",
            m=self["guide_matrix"]["value"][4],
            mirror_type=self["guide_mirror_type"]["value"][4],
        )
        cmds.setAttr(f"{out_guide}.mirror_type", lock=True, keyable=False)
        toe_end_guide = self.add_guide(
            parent=out_guide,
            description="toeEnd",
            m=self["guide_matrix"]["value"][5],
            mirror_type=self["guide_mirror_type"]["value"][5],
        )
        cmds.setAttr(f"{toe_end_guide}.mirror_type", lock=True, keyable=False)
        fk_count = len(self["guide_matrix"]["value"]) - 6
        parent = root_guide
        for i in range(fk_count):
            guide = self.add_guide(
                parent=parent,
                description=i,
                m=self["guide_matrix"]["value"][i + 6],
                mirror_type=self["guide_mirror_type"]["value"][i + 6],
            )
            cmds.setAttr(f"{guide}.mirror_type", lock=True, keyable=False)
            parent = guide

        for i in range(len(self["npo_matrix"]["value"])):
            cmds.connectAttr(
                f"{self.guide_graph}.npo_matrix[{i}]",
                f"{self.guide_root}.npo_matrix[{i}]",
            )
        for i in range(fk_count):
            cmds.connectAttr(
                f"{self.guide_graph}.initialize_output_matrix[{i}]",
                f"{self.guide_root}.initialize_output_matrix[{i}]",
            )
            cmds.connectAttr(
                f"{self.guide_graph}.initialize_output_inverse_matrix[{i}]",
                f"{self.guide_root}.initialize_output_inverse_matrix[{i}]",
            )

    # endregion


def connect_fkik2jnt01(
    foot_name, foot_side, foot_index, fkik2jnt_name, fkik2jnt_side, fkik2jnt_index
):
    roll_bank = Name.create(
        Name.controller_name_convention,
        name=foot_name,
        side=foot_side,
        index=foot_index,
        description="rollBank",
        extension=Name.npo_extension,
    )
    heel_npo = Name.create(
        Name.controller_name_convention,
        name=foot_name,
        side=foot_side,
        index=foot_index,
        description="heel",
        extension=Name.npo_extension,
    )
    inv_grp = Name.create(
        Name.controller_name_convention,
        name=foot_name,
        side=foot_side,
        index=foot_index,
        description="inv",
        extension=Name.group_extension,
    )
    ik_local_ctl = Name.create(
        Name.controller_name_convention,
        name=fkik2jnt_name,
        side=fkik2jnt_side,
        index=fkik2jnt_index,
        description="ikLocal",
        extension=Name.controller_extension,
    )
    cmds.parent([roll_bank, heel_npo, inv_grp], ik_local_ctl)
    inv_ctls = list(
        [x for x in cmds.ls(inv_grp, dagObjects=True, type="transform") if "ctl" in x]
    )
    ik_local_loc = Name.create(
        Name.controller_name_convention,
        name=fkik2jnt_name,
        side=fkik2jnt_side,
        index=fkik2jnt_index,
        description="ikLocal",
        extension=Name.loc_extension,
    )
    cmds.parent(ik_local_loc, inv_ctls[-1])

    last_out = Name.create(
        Name.controller_name_convention,
        name=fkik2jnt_name,
        side=fkik2jnt_side,
        index=fkik2jnt_index,
        description="2",
        extension=Name.output_extension,
    )
    last_inverse = cmds.createNode(
        "transform",
        name=Name.create(
            Name.controller_name_convention,
            name=foot_name,
            side=foot_side,
            index=foot_index,
            description="2",
            extension="inverse",
        ),
    )

    last_inverse = cmds.parent(last_inverse, last_out)[0]
    fk_npo = Name.create(
        Name.controller_name_convention,
        name=foot_name,
        side=foot_side,
        index=foot_index,
        description=0,
        extension=Name.npo_extension,
    )
    cmds.parent(fk_npo, last_inverse)

    last_ctl = Name.create(
        Name.controller_name_convention,
        name=fkik2jnt_name,
        side=fkik2jnt_side,
        index=fkik2jnt_index,
        description="fk2",
        extension=Name.controller_extension,
    )
    host = Name.create(
        Name.controller_name_convention,
        name=foot_name,
        side=foot_side,
        index=foot_index,
        description="host",
        extension=Name.controller_extension,
    )
    sources = (
        cmds.listConnections(
            f"{host}.parent_controllers", source=True, destination=False
        )
        or []
    )
    if last_ctl not in sources:
        cmds.connectAttr(
            f"{last_ctl}.child_controllers",
            f"{host}.parent_controllers[{len(sources)}]",
        )
        cmds.connectAttr(
            f"{ik_local_ctl}.child_controllers",
            f"{host}.parent_controllers[{len(sources) + 1}]",
        )


def connect_humanleg01(
    foot_name, foot_side, foot_index, humanleg_name, humanleg_side, humanleg_index
):
    roll_bank = Name.create(
        Name.controller_name_convention,
        name=foot_name,
        side=foot_side,
        index=foot_index,
        description="rollBank",
        extension=Name.npo_extension,
    )
    heel_npo = Name.create(
        Name.controller_name_convention,
        name=foot_name,
        side=foot_side,
        index=foot_index,
        description="heel",
        extension=Name.npo_extension,
    )
    inv_grp = Name.create(
        Name.controller_name_convention,
        name=foot_name,
        side=foot_side,
        index=foot_index,
        description="inv",
        extension=Name.group_extension,
    )
    ik_local_ctl = Name.create(
        Name.controller_name_convention,
        name=humanleg_name,
        side=humanleg_side,
        index=humanleg_index,
        description="ikLocal",
        extension=Name.controller_extension,
    )
    cmds.parent([roll_bank, heel_npo, inv_grp], ik_local_ctl)
    inv_ctls = list(
        [x for x in cmds.ls(inv_grp, dagObjects=True, type="transform") if "ctl" in x]
    )
    ik_local_loc = Name.create(
        Name.controller_name_convention,
        name=humanleg_name,
        side=humanleg_side,
        index=humanleg_index,
        description="ikLocal",
        extension=Name.loc_extension,
    )
    cmds.parent(ik_local_loc, inv_ctls[-1])

    ankle_out = Name.create(
        Name.controller_name_convention,
        name=humanleg_name,
        side=humanleg_side,
        index=humanleg_index,
        description="ankle",
        extension=Name.output_extension,
    )
    ankle_inverse = cmds.createNode(
        "transform",
        name=Name.create(
            Name.controller_name_convention,
            name=foot_name,
            side=foot_side,
            index=foot_index,
            description="ankle",
            extension="inverse",
        ),
    )

    ankle_inverse = cmds.parent(ankle_inverse, ankle_out)[0]
    fk_npo = Name.create(
        Name.controller_name_convention,
        name=foot_name,
        side=foot_side,
        index=foot_index,
        description=0,
        extension=Name.npo_extension,
    )
    cmds.parent(fk_npo, ankle_inverse)

    ankle_ctl = Name.create(
        Name.controller_name_convention,
        name=humanleg_name,
        side=humanleg_side,
        index=humanleg_index,
        description="ankle",
        extension=Name.controller_extension,
    )
    host = Name.create(
        Name.controller_name_convention,
        name=foot_name,
        side=foot_side,
        index=foot_index,
        description="host",
        extension=Name.controller_extension,
    )
    sources = (
        cmds.listConnections(
            f"{host}.parent_controllers", source=True, destination=False
        )
        or []
    )
    if ankle_ctl not in sources:
        cmds.connectAttr(
            f"{ankle_ctl}.child_controllers",
            f"{host}.parent_controllers[{len(sources)}]",
        )
        cmds.connectAttr(
            f"{ik_local_ctl}.child_controllers",
            f"{host}.parent_controllers[{len(sources) + 1}]",
        )


def connect_humanarm01(
    foot_name, foot_side, foot_index, humanarm_name, humanarm_side, humanarm_index
):
    roll_bank = Name.create(
        Name.controller_name_convention,
        name=foot_name,
        side=foot_side,
        index=foot_index,
        description="rollBank",
        extension=Name.npo_extension,
    )
    heel_npo = Name.create(
        Name.controller_name_convention,
        name=foot_name,
        side=foot_side,
        index=foot_index,
        description="heel",
        extension=Name.npo_extension,
    )
    inv_grp = Name.create(
        Name.controller_name_convention,
        name=foot_name,
        side=foot_side,
        index=foot_index,
        description="inv",
        extension=Name.group_extension,
    )
    ik_local_ctl = Name.create(
        Name.controller_name_convention,
        name=humanarm_name,
        side=humanarm_side,
        index=humanarm_index,
        description="ikLocal",
        extension=Name.controller_extension,
    )
    cmds.parent([roll_bank, heel_npo, inv_grp], ik_local_ctl)
    inv_ctls = list(
        [x for x in cmds.ls(inv_grp, dagObjects=True, type="transform") if "ctl" in x]
    )
    ik_local_loc = Name.create(
        Name.controller_name_convention,
        name=humanarm_name,
        side=humanarm_side,
        index=humanarm_index,
        description="ikLocal",
        extension=Name.loc_extension,
    )
    cmds.parent(ik_local_loc, inv_ctls[-1])

    wrist_out = Name.create(
        Name.controller_name_convention,
        name=humanarm_name,
        side=humanarm_side,
        index=humanarm_index,
        description="wrist",
        extension=Name.output_extension,
    )
    wrist_inverse = cmds.createNode(
        "transform",
        name=Name.create(
            Name.controller_name_convention,
            name=foot_name,
            side=foot_side,
            index=foot_index,
            description="wrist",
            extension="inverse",
        ),
    )

    wrist_inverse = cmds.parent(wrist_inverse, wrist_out)[0]
    fk_npo = Name.create(
        Name.controller_name_convention,
        name=foot_name,
        side=foot_side,
        index=foot_index,
        description=0,
        extension=Name.npo_extension,
    )
    cmds.parent(fk_npo, wrist_inverse)

    wrist_ctl = Name.create(
        Name.controller_name_convention,
        name=humanarm_name,
        side=humanarm_side,
        index=humanarm_index,
        description="wrist",
        extension=Name.controller_extension,
    )
    host = Name.create(
        Name.controller_name_convention,
        name=foot_name,
        side=foot_side,
        index=foot_index,
        description="host",
        extension=Name.controller_extension,
    )
    sources = (
        cmds.listConnections(
            f"{host}.parent_controllers", source=True, destination=False
        )
        or []
    )
    if wrist_ctl not in sources:
        cmds.connectAttr(
            f"{wrist_ctl}.child_controllers",
            f"{host}.parent_controllers[{len(sources)}]",
        )
        cmds.connectAttr(
            f"{ik_local_ctl}.child_controllers",
            f"{host}.parent_controllers[{len(sources) + 1}]",
        )
