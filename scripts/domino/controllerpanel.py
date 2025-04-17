# maya
from maya import cmds

# built-ins
import math


ID = "domino_controller_panel_ui"


def show(*args) -> None:
    if cmds.workspaceControl(ID, query=True, exists=True):
        if not cmds.workspaceControl(ID, query=True, floating=True):
            cmds.workspaceControl(ID, edit=True, restore=True)
            return
        cmds.deleteUI(ID)
    cmds.workspaceControl(
        ID,
        floating=True,
        label="Controller Panel",
        uiScript="from domino import controllerpanel;controllerpanel.ui()",
    )


replace_shape_command = """from maya import cmds
from domino.core import nurbscurve

selected = cmds.ls(selection=True)
if selected:
    destination_shapes = cmds.listRelatives(selected[-1], shapes=True)
    delete_list = []
    for ctl in selected[:-1]:
        dup_curves = [
            cmds.duplicateCurve(shape, constructionHistory=False)[0]
            for shape in destination_shapes
        ]
        temp_transform = cmds.createNode("transform", name="temp1122")
        cmds.parent(
            [cmds.listRelatives(c, shapes=True)[0] for c in dup_curves],
            temp_transform,
            relative=True,
            shape=True,
        )
        nurbscurve.replace_shape(temp_transform, ctl)
        delete_list.extend([temp_transform] + dup_curves)
    cmds.delete(delete_list)
    cmds.select(selected)"""

mirror_shape_command = """from maya import cmds
from domino.core import nurbscurve

selected = cmds.ls(selection=True)
left_str = cmds.textField("domino_left_mirror_string", query=True, text=True)
right_str = cmds.textField("domino_right_mirror_string", query=True, text=True)
for sel in selected:
    nurbscurve.mirror_shape(sel, left_str, right_str)"""

color_command = """from maya import cmds

shapes = [
    y for x in cmds.ls(selection=True) for y in cmds.listRelatives(x, shapes=True) or []
]
for shape in shapes:
    cmds.setAttr(shape + ".overrideEnabled", 1)
    cmds.setAttr(shape + ".overrideColor", {0})"""

rotate_x_command = """from maya import cmds

selected = [x + ".cv[*]" for x in cmds.ls(selection=True)]
rotate_value = cmds.intField("controller_rotate_int_field", query=True, value=True)
cmds.rotate(rotate_value, 0, 0, selected, relative=True)"""

rotate_y_command = """from maya import cmds

selected = [x + ".cv[*]" for x in cmds.ls(selection=True)]
rotate_value = cmds.intField("controller_rotate_int_field", query=True, value=True)
cmds.rotate(0, rotate_value, 0, selected, relative=True)"""

rotate_z_command = """from maya import cmds

selected = [x + ".cv[*]" for x in cmds.ls(selection=True)]
rotate_value = cmds.intField("controller_rotate_int_field", query=True, value=True)
cmds.rotate(0, 0, rotate_value, selected, relative=True)"""

scale_command = """from maya import cmds

selected = [x + ".cv[*]" for x in cmds.ls(selection=True)]
scale_value = cmds.floatField("controller_scale_float_field", query=True, value=True)
cmds.scale(scale_value, scale_value, scale_value, selected, relative=True)"""

scale_x_command = """from maya import cmds

selected = [x + ".cv[*]" for x in cmds.ls(selection=True)]
scale_value = cmds.floatField("controller_scale_float_field", query=True, value=True)
cmds.scale(scale_value, 1, 1, selected, relative=True)"""

scale_y_command = """from maya import cmds

selected = [x + ".cv[*]" for x in cmds.ls(selection=True)]
scale_value = cmds.floatField("controller_scale_float_field", query=True, value=True)
cmds.scale(1, scale_value, 1, selected, relative=True)"""

scale_z_command = """from maya import cmds

selected = [x + ".cv[*]" for x in cmds.ls(selection=True)]
scale_value = cmds.floatField("controller_scale_float_field", query=True, value=True)
cmds.scale(1, 1, scale_value, selected, relative=True)"""

generate_curve_command = """from domino.core import nurbscurve
nurbscurve.create("{0}", 17)"""


def ui(*args, **kwargs) -> None:
    width = 180
    height = 22

    column_layout = cmds.columnLayout(
        parent=ID,
        width=width,
        rowSpacing=2,
        numberOfChildren=3,
    )

    cmds.button(
        label="Replace",
        width=width,
        height=height,
        recomputeSize=False,
        command=replace_shape_command,
        annotation="선택해주세요.\n1. controllers\n2. 바꿀 shape",
    )
    w = width / 5
    cmds.rowLayout(
        parent=column_layout,
        numberOfColumns=3,
        columnWidth3=(w - 2, w - 2, w * 3 - 2),
        margins=1,
    )
    cmds.textField("domino_left_mirror_string", text="_L")
    cmds.textField("domino_right_mirror_string", text="_R")
    cmds.button(
        label="Mirror",
        width=w * 3 - 2,
        height=height,
        command=mirror_shape_command,
    )
    cmds.setParent(column_layout)

    w = width / 6 - 2
    indexes = [13, 20, 17, 21, 6, 29]
    annotations = [
        "Right Fk",
        "Right IK",
        "Center FK",
        "Center Ik",
        "Left FK",
        "Left IK",
    ]
    cmds.rowLayout(
        parent=column_layout,
        numberOfColumns=6,
        columnWidth6=(w, w, w, w, w, w),
        margins=1,
    )
    for annotation, index in zip(annotations, indexes):
        color = cmds.colorIndex(index, query=True)
        cmds.button(
            label="",
            width=w,
            height=height,
            command=color_command.format(index),
            backgroundColor=color,
            annotation=annotation,
        )
    cmds.setParent(column_layout)

    cmds.intField(
        "controller_rotate_int_field",
        width=width,
        value=45,
        step=15,
        maxValue=360,
        minValue=-360,
    )
    w = width / 3 - 2
    cmds.rowLayout(numberOfColumns=3, columnWidth3=(w, w, w), margins=1)
    cmds.button(label="rX", width=w, height=height, command=rotate_x_command)
    cmds.button(label="rY", width=w, height=height, command=rotate_y_command)
    cmds.button(label="rZ", width=w, height=height, command=rotate_z_command)
    cmds.setParent(column_layout)

    cmds.floatField(
        "controller_scale_float_field",
        width=width,
        value=0.9,
        precision=1,
        step=0.1,
    )
    w = width / 4 - 2
    cmds.rowLayout(numberOfColumns=4, columnWidth4=(w, w, w, w), margins=1)
    cmds.button(label="S", width=w, height=height, command=scale_command)
    cmds.button(label="sX", width=w, height=height, command=scale_x_command)
    cmds.button(label="sY", width=w, height=height, command=scale_y_command)
    cmds.button(label="sZ", width=w, height=height, command=scale_z_command)

    w = width / 6 - 2
    shapes = [
        "origin",
        "arrow",
        "arrow4",
        "square",
        "wave",
        "halfmoon",
        "halfcircle",
        "circle",
        "sphere",
        "locator",
        "cube",
        "cylinder",
        "x",
        "angle",
        "dodecahedron",
        "axis",
        "bracket",
        "line",
    ]
    count = math.ceil(len(shapes) / 6)
    for i in range(count):
        cmds.rowLayout(
            parent=column_layout,
            numberOfColumns=6,
            columnWidth6=(w, w, w, w, w, w),
            margins=1,
        )
        for x in range(6):
            if len(shapes) > (i * 6 + x):
                color = cmds.colorIndex(index, query=True)
                cmds.symbolButton(
                    width=w,
                    height=height,
                    image=shapes[i * 6 + x] + "_shape",
                    command=generate_curve_command.format(shapes[i * 6 + x]),
                )
        cmds.setParent(column_layout)
