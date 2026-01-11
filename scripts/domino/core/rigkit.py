# maya
from maya import cmds

# built-ins
from pathlib import Path
import json

# domino
from domino.core.utils import logger
from domino.core import FCurve


def connect_blended_joint(source, destination, weight=0.5):
    parent = cmds.listRelatives(source, parent=True)
    if parent:
        parent = parent[0]
    orig = cmds.createNode(
        "transform", name=f"blended_{destination}_orig", parent=source
    )
    if parent:
        orig = cmds.parent(orig, parent)[0]
    else:
        orig = cmds.parent(orig, worlld=True)[0]

    cmds.addAttr(
        destination,
        longName="weight",
        attributeType="float",
        minValue=0,
        maxValue=1,
        defaultValue=weight,
        keyable=True,
    )

    blend_m = cmds.createNode("blendMatrix")
    cmds.connectAttr(f"{orig}.worldMatrix[0]", f"{blend_m}.inputMatrix")
    cmds.connectAttr(f"{source}.worldMatrix[0]", f"{blend_m}.target[0].targetMatrix")
    cmds.connectAttr(f"{destination}.weight", f"{blend_m}.target[0].weight")

    mult_m = cmds.createNode("multMatrix")
    cmds.connectAttr(f"{blend_m}.outputMatrix", f"{mult_m}.matrixIn[0]")
    cmds.connectAttr(f"{destination}.parentInverseMatrix", f"{mult_m}.matrixIn[1]")

    decom_m = cmds.createNode("decomposeMatrix")
    cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
    cmds.connectAttr(f"{decom_m}.outputRotate", f"{destination}.r")


# region IK
def ik_sc():
    pass


def ik_2jnt(
    parent,
    name,
    initial_matrix_plugs,
    initial_ik_curve,
    joints,
    ik_pos_driver,
    ik_driver,
    pole_vector,
    scale_attr,
    slide_attr,
    soft_ik_attr,
    max_stretch_attr,
    attach_pole_vector_attr,
):
    decom_m1 = cmds.createNode("decomposeMatrix")
    decom_m2 = cmds.createNode("decomposeMatrix")

    cmds.connectAttr(initial_matrix_plugs[1], f"{decom_m1}.inputMatrix")
    cmds.connectAttr(initial_matrix_plugs[2], f"{decom_m2}.inputMatrix")

    init_translate1_plug = f"{decom_m1}.outputTranslate"
    init_translate2_plug = f"{decom_m2}.outputTranslate"

    # ik scale
    md1 = cmds.createNode("multiplyDivide")
    cmds.connectAttr(init_translate1_plug, f"{md1}.input1")
    cmds.connectAttr(scale_attr, f"{md1}.input2X")
    cmds.connectAttr(scale_attr, f"{md1}.input2Y")
    cmds.connectAttr(scale_attr, f"{md1}.input2Z")

    md2 = cmds.createNode("multiplyDivide")
    cmds.connectAttr(init_translate2_plug, f"{md2}.input1")
    cmds.connectAttr(scale_attr, f"{md2}.input2X")
    cmds.connectAttr(scale_attr, f"{md2}.input2Y")
    cmds.connectAttr(scale_attr, f"{md2}.input2Z")

    length1 = cmds.createNode("length")
    cmds.connectAttr(f"{md1}.output", f"{length1}.input")
    scaled_init_distance1_plug = f"{length1}.output"

    length2 = cmds.createNode("length")
    cmds.connectAttr(f"{md2}.output", f"{length2}.input")
    scaled_init_distance2_plug = f"{length2}.output"

    pma = cmds.createNode("plusMinusAverage")
    cmds.connectAttr(scaled_init_distance1_plug, f"{pma}.input1D[0]")
    cmds.connectAttr(scaled_init_distance2_plug, f"{pma}.input1D[1]")
    slided_total_distance_plug = f"{pma}.output1D"

    # slide
    normalize_md = cmds.createNode("multiplyDivide")
    cmds.setAttr(f"{normalize_md}.operation", 2)
    cmds.connectAttr(f"{md1}.output", f"{normalize_md}.input1")
    cmds.connectAttr(scaled_init_distance1_plug, f"{normalize_md}.input2X")
    cmds.connectAttr(scaled_init_distance1_plug, f"{normalize_md}.input2Y")
    cmds.connectAttr(scaled_init_distance1_plug, f"{normalize_md}.input2Z")

    slide_max_md = cmds.createNode("multiplyDivide")
    cmds.connectAttr(f"{normalize_md}.output", f"{slide_max_md}.input1")
    cmds.connectAttr(slided_total_distance_plug, f"{slide_max_md}.input2X")
    cmds.connectAttr(slided_total_distance_plug, f"{slide_max_md}.input2Y")
    cmds.connectAttr(slided_total_distance_plug, f"{slide_max_md}.input2Z")

    minus_remap_value = cmds.createNode("remapValue")
    cmds.connectAttr(slide_attr, f"{minus_remap_value}.inputValue")
    cmds.setAttr(f"{minus_remap_value}.inputMax", -1)

    plus_remap_value = cmds.createNode("remapValue")
    cmds.connectAttr(slide_attr, f"{plus_remap_value}.inputValue")

    compose_mid_m1 = cmds.createNode("composeMatrix")
    cmds.connectAttr(f"{md1}.output", f"{compose_mid_m1}.inputTranslate")
    compose_max_m1 = cmds.createNode("composeMatrix")
    cmds.connectAttr(f"{slide_max_md}.output", f"{compose_max_m1}.inputTranslate")

    bm1 = cmds.createNode("blendMatrix")
    cmds.connectAttr(f"{compose_mid_m1}.outputMatrix", f"{bm1}.inputMatrix")
    cmds.connectAttr(f"{compose_max_m1}.outputMatrix", f"{bm1}.target[1].targetMatrix")
    cmds.connectAttr(f"{minus_remap_value}.outValue", f"{bm1}.target[0].weight")
    cmds.connectAttr(f"{plus_remap_value}.outValue", f"{bm1}.target[1].weight")

    slide_decom_m1 = cmds.createNode("decomposeMatrix")
    cmds.connectAttr(f"{bm1}.outputMatrix", f"{slide_decom_m1}.inputMatrix")
    slided_translate1_plug = f"{slide_decom_m1}.outputTranslate"

    compose_mid_m2 = cmds.createNode("composeMatrix")
    cmds.connectAttr(f"{md2}.output", f"{compose_mid_m2}.inputTranslate")
    compose_max_m2 = cmds.createNode("composeMatrix")
    cmds.connectAttr(f"{slide_max_md}.output", f"{compose_max_m2}.inputTranslate")

    bm2 = cmds.createNode("blendMatrix")
    cmds.connectAttr(f"{compose_mid_m2}.outputMatrix", f"{bm2}.inputMatrix")
    cmds.connectAttr(f"{compose_max_m2}.outputMatrix", f"{bm2}.target[1].targetMatrix")
    cmds.connectAttr(f"{plus_remap_value}.outValue", f"{bm2}.target[0].weight")
    cmds.connectAttr(f"{minus_remap_value}.outValue", f"{bm2}.target[1].weight")

    slide_decom_m2 = cmds.createNode("decomposeMatrix")
    cmds.connectAttr(f"{bm2}.outputMatrix", f"{slide_decom_m2}.inputMatrix")
    slided_translate2_plug = f"{slide_decom_m2}.outputTranslate"

    length3 = cmds.createNode("length")
    cmds.connectAttr(slided_translate1_plug, f"{length3}.input")
    length4 = cmds.createNode("length")
    cmds.connectAttr(slided_translate2_plug, f"{length4}.input")

    slided_init_distance1_plug = f"{length3}.output"
    slided_init_distance2_plug = f"{length4}.output"

    pma1 = cmds.createNode("plusMinusAverage")
    cmds.connectAttr(slided_init_distance1_plug, f"{pma1}.input1D[0]")
    cmds.connectAttr(slided_init_distance2_plug, f"{pma1}.input1D[1]")
    slided_total_distance_plug = f"{pma1}.output1D"

    # softik
    soft_ik_grp = cmds.createNode("transform", name=f"{name}_grp", parent=parent)
    ikh = cmds.ikHandle(
        startJoint=joints[0], endEffector=joints[2], solver="ikRPsolver", name=name
    )[0]
    cmds.parent(ikh, soft_ik_grp)
    cmds.poleVectorConstraint(pole_vector, ikh)
    cmds.setAttr(f"{ikh}.t", 0, 0, 0)
    cmds.setAttr(f"{ikh}.r", 0, 0, 0)
    cmds.setAttr(f"{ikh}.v", 0)

    curve_info = cmds.createNode("curveInfo")
    cmds.connectAttr(f"{initial_ik_curve}.local", f"{curve_info}.inputCurve")
    init_ik_length = f"{curve_info}.arcLength"

    curve_info = cmds.createNode("curveInfo")
    cmds.connectAttr(f"{initial_ik_curve}.worldSpace[0]", f"{curve_info}.inputCurve")
    scaled_ik_length = f"{curve_info}.arcLength"

    ik_driver_distance = cmds.createNode("distanceBetween")
    cmds.connectAttr(
        f"{ik_pos_driver}.worldMatrix[0]", f"{ik_driver_distance}.inMatrix1"
    )
    cmds.connectAttr(f"{ik_driver}.worldMatrix[0]", f"{ik_driver_distance}.inMatrix2")

    divide = cmds.createNode("divide")
    cmds.connectAttr(init_ik_length, f"{divide}.input1")
    cmds.connectAttr(scaled_ik_length, f"{divide}.input2")

    multiply = cmds.createNode("multiply")
    cmds.connectAttr(f"{divide}.output", f"{multiply}.input[0]")
    cmds.connectAttr(f"{ik_driver_distance}.distance", f"{multiply}.input[1]")

    scaled_ik_driver_distance = f"{multiply}.output"

    cmds.connectAttr(scaled_ik_driver_distance, f"{parent}.tx")
    clamp0 = cmds.createNode("clamp")
    cmds.connectAttr(scaled_ik_driver_distance, f"{clamp0}.inputR")
    cmds.connectAttr(slided_total_distance_plug, f"{clamp0}.maxR")

    divide0 = cmds.createNode("divide")
    cmds.connectAttr(f"{clamp0}.outputR", f"{divide0}.input1")
    cmds.connectAttr(slided_total_distance_plug, f"{divide0}.input2")

    multiply0 = cmds.createNode("multiply")
    cmds.connectAttr(slided_total_distance_plug, f"{multiply0}.input[0]")

    fcurve = FCurve()
    fcurve.data = [
        {
            "name": f"{name}_softIK",
            "driven": f"{multiply0}.input[1]",
            "type": "animCurveUU",
            "driver": f"{divide0}.output",
            "float_change": [0.0, 0.8, 1.0],
            "value_change": [0.0, 0.92, 1.0],
            "in_angle": [0.0, 2.743324488263113, 0.0],
            "out_angle": [2.743324488263113, 2.6984899950637997, 0.0],
            "in_weight": [8.0, 6.4073430097384705, 1.0918245871698775],
            "out_weight": [6.4073430097384705, 1.3704363225806342, 1.0918245871698775],
            "in_tangent_type": ["linear", "linear", "fixed"],
            "out_tangent_type": ["linear", "fixed", "fixed"],
            "weighted_tangents": [True],
            "lock": [True, False, True],
        }
    ]
    fcurve.create_from_data()

    subtract0 = cmds.createNode("subtract")
    cmds.connectAttr(f"{multiply0}.output", f"{subtract0}.input1")
    cmds.connectAttr(f"{clamp0}.outputR", f"{subtract0}.input2")

    bta = cmds.createNode("blendTwoAttr")
    cmds.setAttr(f"{bta}.input[0]", 0)
    cmds.connectAttr(f"{subtract0}.output", f"{bta}.input[1]")
    cmds.connectAttr(soft_ik_attr, f"{bta}.attributesBlender")

    # max stretch
    multiply1 = cmds.createNode("multiply")
    cmds.connectAttr(max_stretch_attr, f"{multiply1}.input[0]")
    cmds.connectAttr(slided_total_distance_plug, f"{multiply1}.input[1]")
    max_stretch_distance_plug = f"{multiply1}.output"

    clamp1 = cmds.createNode("clamp")
    cmds.connectAttr(scaled_ik_driver_distance, f"{clamp1}.inputR")
    cmds.connectAttr(slided_total_distance_plug, f"{clamp1}.minR")
    cmds.connectAttr(max_stretch_distance_plug, f"{clamp1}.maxR")

    stretched_total_distance_plug = f"{clamp1}.outputR"

    divide3 = cmds.createNode("divide")
    cmds.connectAttr(stretched_total_distance_plug, f"{divide3}.input1")
    cmds.connectAttr(slided_total_distance_plug, f"{divide3}.input2")

    stretch_ratio = f"{divide3}.output"

    md3 = cmds.createNode("multiplyDivide")
    cmds.connectAttr(slided_translate1_plug, f"{md3}.input1")
    cmds.connectAttr(stretch_ratio, f"{md3}.input2X")
    cmds.connectAttr(stretch_ratio, f"{md3}.input2Y")
    cmds.connectAttr(stretch_ratio, f"{md3}.input2Z")

    md4 = cmds.createNode("multiplyDivide")
    cmds.connectAttr(slided_translate2_plug, f"{md4}.input1")
    cmds.connectAttr(stretch_ratio, f"{md4}.input2X")
    cmds.connectAttr(stretch_ratio, f"{md4}.input2Y")
    cmds.connectAttr(stretch_ratio, f"{md4}.input2Z")

    # attach pole vector
    ik_pos_decom_m = cmds.createNode("decomposeMatrix")
    cmds.connectAttr(f"{ik_pos_driver}.worldMatrix[0]", f"{ik_pos_decom_m}.inputMatrix")
    pole_vector_decom_m = cmds.createNode("decomposeMatrix")
    cmds.connectAttr(
        f"{pole_vector}.worldMatrix[0]", f"{pole_vector_decom_m}.inputMatrix"
    )
    ik_driver_decom_m = cmds.createNode("decomposeMatrix")
    cmds.connectAttr(f"{ik_driver}.worldMatrix[0]", f"{ik_driver_decom_m}.inputMatrix")

    pma2 = cmds.createNode("plusMinusAverage")
    cmds.setAttr(f"{pma2}.operation", 2)
    cmds.connectAttr(f"{pole_vector_decom_m}.outputTranslate", f"{pma2}.input3D[0]")
    cmds.connectAttr(f"{ik_pos_decom_m}.outputTranslate", f"{pma2}.input3D[1]")

    length5 = cmds.createNode("length")
    cmds.connectAttr(f"{pma2}.output3D", f"{length5}.input")
    attach_pv_distance1_plug = f"{length5}.output"

    pma3 = cmds.createNode("plusMinusAverage")
    cmds.setAttr(f"{pma3}.operation", 2)
    cmds.connectAttr(f"{ik_driver_decom_m}.outputTranslate", f"{pma3}.input3D[0]")
    cmds.connectAttr(f"{pole_vector_decom_m}.outputTranslate", f"{pma3}.input3D[1]")

    length6 = cmds.createNode("length")
    cmds.connectAttr(f"{pma3}.output3D", f"{length6}.input")
    attach_pv_distance2_plug = f"{length6}.output"

    length7 = cmds.createNode("length")
    cmds.connectAttr(f"{md3}.output", f"{length7}.input")
    stretched_distance1_plug = f"{length7}.output"

    length8 = cmds.createNode("length")
    cmds.connectAttr(f"{md4}.output", f"{length8}.input")
    stretched_distance2_plug = f"{length8}.output"

    divide4 = cmds.createNode("divide")
    cmds.connectAttr(attach_pv_distance1_plug, f"{divide4}.input1")
    cmds.connectAttr(stretched_distance1_plug, f"{divide4}.input2")

    distance1_multiple = f"{divide4}.output"

    divide5 = cmds.createNode("divide")
    cmds.connectAttr(attach_pv_distance2_plug, f"{divide5}.input1")
    cmds.connectAttr(stretched_distance2_plug, f"{divide5}.input2")

    distance2_multiple = f"{divide5}.output"

    md5 = cmds.createNode("multiplyDivide")
    cmds.connectAttr(f"{md3}.output", f"{md5}.input1")
    cmds.connectAttr(distance1_multiple, f"{md5}.input2X")
    cmds.connectAttr(distance1_multiple, f"{md5}.input2Y")
    cmds.connectAttr(distance1_multiple, f"{md5}.input2Z")

    md6 = cmds.createNode("multiplyDivide")
    cmds.connectAttr(f"{md4}.output", f"{md6}.input1")
    cmds.connectAttr(distance2_multiple, f"{md6}.input2X")
    cmds.connectAttr(distance2_multiple, f"{md6}.input2Y")
    cmds.connectAttr(distance2_multiple, f"{md6}.input2Z")

    pb1 = cmds.createNode("pairBlend")
    cmds.connectAttr(attach_pole_vector_attr, f"{pb1}.weight")
    cmds.connectAttr(f"{md3}.output", f"{pb1}.inTranslate1")
    cmds.connectAttr(f"{md5}.output", f"{pb1}.inTranslate2")

    pb2 = cmds.createNode("pairBlend")
    cmds.connectAttr(attach_pole_vector_attr, f"{pb2}.weight")
    cmds.connectAttr(f"{md4}.output", f"{pb2}.inTranslate1")
    cmds.connectAttr(f"{md6}.output", f"{pb2}.inTranslate2")

    cmds.connectAttr(f"{pb1}.outTranslate", f"{joints[1]}.t")
    cmds.connectAttr(f"{pb2}.outTranslate", f"{joints[2]}.t")

    # attach pv on -> soft ik off
    bta1 = cmds.createNode("blendTwoAttr")
    cmds.connectAttr(f"{bta}.output", f"{bta1}.input[0]")
    cmds.setAttr(f"{bta1}.input[1]", 0)
    cmds.connectAttr(attach_pole_vector_attr, f"{bta1}.attributesBlender")

    cmds.connectAttr(f"{bta1}.output", f"{soft_ik_grp}.tx")


def ik_3jnt(
    parent,
    name,
    joints,
    pole_vector,
    scale_attr,
    slide_attr,
    soft_ik_attr,
    max_stretch_attr,
):
    pass


# endregion


# region ribbon
def ribbon_spline_ik(
    parent,
    driver_joints,
    driver_inverse_plugs,
    surface,
    main_ik_joints,
    up_ik_joints,
    stretch_squash_attr,
    uniform_attr,
    auto_volume_attr,
    auto_volume_multiple,
    volume_attr,
    volume_position_attr,
    volume_low_bound_attr,
    volume_high_bound_attr,
    output_u_value_plugs,
    negate_plug=None,
    primary_axis=(1, 0, 0),
    secondary_axis=(0, 0, 1),
):
    surface = cmds.parent(surface, parent)[0]

    # initialize skincluster
    temp = cmds.duplicate(surface, name="copyskindummy")[0]

    temp_sc = cmds.skinCluster(
        driver_joints + [temp],
        normalizeWeights=True,
        obeyMaxInfluences=False,
        weightDistribution=1,
        multi=True,
    )[0]

    sc = cmds.deformer(
        surface, type="skinCluster", deformerTools=True, name=f"{surface}0_sc"
    )[0]
    cmds.setAttr(f"{sc}.relativeSpaceMode", 1)
    cmds.setAttr(f"{sc}.weightDistribution", 1)

    c = 0
    for driver_jnt, inverse_plug in zip(driver_joints, driver_inverse_plugs):
        cmds.connectAttr(f"{driver_jnt}.worldMatrix", f"{sc}.matrix[{c}]", force=1)
        cmds.connectAttr(inverse_plug, f"{sc}.bindPreMatrix[{c}]", force=1)
        c += 1
    cmds.copySkinWeights(
        sourceSkin=temp_sc,
        destinationSkin=sc,
        noMirror=True,
        surfaceAssociation="closestPoint",
        influenceAssociation="closestJoint",
    )
    cmds.delete(temp)

    shape, orig = cmds.listRelatives(surface, shapes=True)

    # spline ik curve
    main_crv, main_crv_iso = cmds.duplicateCurve(
        f"{surface}.v[0.5]",
        name=f"{surface}_mainIkCrv",
        constructionHistory=True,
        rn=False,
        local=True,
    )
    main_crv = cmds.parent(main_crv, parent)[0]
    up_crv, up_crv_iso = cmds.duplicateCurve(
        f"{surface}.v[0]",
        name=f"{surface}_upIkCrv",
        constructionHistory=True,
        rn=False,
        local=True,
    )
    up_crv = cmds.parent(up_crv, parent)[0]

    # initialize spline ik distance
    uvpin = cmds.createNode("uvPin")
    cmds.setAttr(f"{uvpin}.relativeSpaceMode", 1)
    cmds.connectAttr(f"{orig}.local", f"{uvpin}.deformedGeometry")

    main_orig_output_plugs = []
    c = 0
    for plug in output_u_value_plugs:
        cmds.connectAttr(plug, f"{uvpin}.coordinate[{c}].coordinateU")
        cmds.setAttr(f"{uvpin}.coordinate[{c}].coordinateV", 0.5)
        main_orig_output_plugs.append(f"{uvpin}.outputMatrix[{c}]")
        c += 1

    up_orig_output_plugs = []
    for plug in output_u_value_plugs:
        cmds.connectAttr(plug, f"{uvpin}.coordinate[{c}].coordinateU")
        up_orig_output_plugs.append(f"{uvpin}.outputMatrix[{c}]")
        c += 1

    for c in range(len(main_orig_output_plugs)):
        if c == len(main_orig_output_plugs) - 1:
            break
        db = cmds.createNode("distanceBetween")
        cmds.connectAttr(main_orig_output_plugs[c], f"{db}.inMatrix1")
        cmds.connectAttr(main_orig_output_plugs[c + 1], f"{db}.inMatrix2")
        cmds.connectAttr(f"{db}.distance", f"{main_ik_joints[c + 1]}.tx")
        db = cmds.createNode("distanceBetween")
        cmds.connectAttr(up_orig_output_plugs[c], f"{db}.inMatrix1")
        cmds.connectAttr(up_orig_output_plugs[c + 1], f"{db}.inMatrix2")
        cmds.connectAttr(f"{db}.distance", f"{up_ik_joints[c + 1]}.tx")

    main_ikh, effector = cmds.ikHandle(
        startJoint=main_ik_joints[0],
        endEffector=main_ik_joints[-1],
        solver="ikSplineSolver",
        name=f"{surface}_mainIkh",
        curve=main_crv,
        createCurve=False,
    )
    main_ikh = cmds.parent(main_ikh, parent)[0]
    up_ikh, effector = cmds.ikHandle(
        startJoint=up_ik_joints[0],
        endEffector=up_ik_joints[-1],
        solver="ikSplineSolver",
        name=f"{surface}_upIkh",
        curve=up_crv,
        createCurve=False,
    )
    up_ikh = cmds.parent(up_ikh, parent)[0]

    # deformed uvpin
    uvpin = cmds.createNode("uvPin")
    cmds.connectAttr(f"{orig}.local", f"{uvpin}.originalGeometry")
    cmds.connectAttr(f"{shape}.worldSpace[0]", f"{uvpin}.deformedGeometry")

    main_output_plugs = []
    c = 0
    for plug in output_u_value_plugs:
        cmds.connectAttr(plug, f"{uvpin}.coordinate[{c}].coordinateU")
        cmds.setAttr(f"{uvpin}.coordinate[{c}].coordinateV", 0.5)
        main_output_plugs.append(f"{uvpin}.outputMatrix[{c}]")
        c += 1

    up_output_plugs = []
    for plug in output_u_value_plugs:
        cmds.connectAttr(plug, f"{uvpin}.coordinate[{c}].coordinateU")
        up_output_plugs.append(f"{uvpin}.outputMatrix[{c}]")
        c += 1

    # initialize uniform curve uvalue
    main_orig_uniform_crv, main_orig_uniform_crv_iso = cmds.duplicateCurve(
        f"{orig}.v[0.5]",
        name=f"{surface}_uniformMainCrvOrig",
        constructionHistory=True,
        rn=False,
        local=True,
    )
    main_orig_uniform_crv = cmds.parent(main_orig_uniform_crv, parent)[0]
    main_orig_rebuild_curve = cmds.createNode("rebuildCurve")
    cmds.connectAttr(
        f"{main_orig_uniform_crv_iso}.outputCurve",
        f"{main_orig_rebuild_curve}.inputCurve",
    )
    cmds.connectAttr(
        f"{main_orig_rebuild_curve}.outputCurve",
        f"{main_orig_uniform_crv}.create",
        force=True,
    )
    up_orig_uniform_crv, up_orig_uniform_crv_iso = cmds.duplicateCurve(
        f"{orig}.v[0]",
        name=f"{surface}_uniformUpCrvOrig",
        constructionHistory=True,
        rn=False,
        local=True,
    )
    up_orig_uniform_crv = cmds.parent(up_orig_uniform_crv, parent)[0]
    up_orig_rebuild_curve = cmds.createNode("rebuildCurve")
    cmds.connectAttr(
        f"{up_orig_uniform_crv_iso}.outputCurve", f"{up_orig_rebuild_curve}.inputCurve"
    )
    cmds.connectAttr(
        f"{up_orig_rebuild_curve}.outputCurve",
        f"{up_orig_uniform_crv}.create",
        force=True,
    )

    main_orig_uniform_parameter_plugs = []
    for orig_output in main_orig_output_plugs:
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(orig_output, f"{decom_m}.inputMatrix")
        npoc = cmds.createNode("nearestPointOnCurve")
        cmds.connectAttr(f"{main_orig_uniform_crv}.local", f"{npoc}.inputCurve")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{npoc}.inPosition")
        main_orig_uniform_parameter_plugs.append(f"{npoc}.parameter")

    up_orig_uniform_parameter_plugs = []
    for orig_output in up_orig_output_plugs:
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(orig_output, f"{decom_m}.inputMatrix")
        npoc = cmds.createNode("nearestPointOnCurve")
        cmds.connectAttr(f"{up_orig_uniform_crv}.local", f"{npoc}.inputCurve")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{npoc}.inPosition")
        up_orig_uniform_parameter_plugs.append(f"{npoc}.parameter")

    # uniform curve
    main_rebuild_curve = cmds.createNode("rebuildCurve")
    cmds.connectAttr(f"{main_crv_iso}.outputCurve", f"{main_rebuild_curve}.inputCurve")
    main_uniform_crv = cmds.circle(
        name=f"{surface}_uniformMainCrv", constructionHistory=False
    )
    main_uniform_crv = cmds.parent(main_uniform_crv, parent)[0]
    cmds.connectAttr(f"{main_rebuild_curve}.outputCurve", f"{main_uniform_crv}.create")

    up_rebuild_curve = cmds.createNode("rebuildCurve")
    cmds.connectAttr(f"{up_crv_iso}.outputCurve", f"{up_rebuild_curve}.inputCurve")
    up_uniform_crv = cmds.circle(
        name=f"{surface}_uniformUpCrv", constructionHistory=False
    )
    up_uniform_crv = cmds.parent(up_uniform_crv, parent)[0]
    cmds.connectAttr(f"{up_rebuild_curve}.outputCurve", f"{up_uniform_crv}.create")

    main_uniform_output_plugs = []
    for plug in main_orig_uniform_parameter_plugs:
        poci = cmds.createNode("pointOnCurveInfo")
        cmds.connectAttr(plug, f"{poci}.parameter")
        cmds.connectAttr(f"{main_uniform_crv}.worldSpace[0]", f"{poci}.inputCurve")
        com_m = cmds.createNode("composeMatrix")
        cmds.connectAttr(f"{poci}.position", f"{com_m}.inputTranslate")
        main_uniform_output_plugs.append(f"{com_m}.outputMatrix")
    up_uniform_output_plugs = []
    for plug in up_orig_uniform_parameter_plugs:
        poci = cmds.createNode("pointOnCurveInfo")
        cmds.connectAttr(plug, f"{poci}.parameter")
        cmds.connectAttr(f"{up_uniform_crv}.worldSpace[0]", f"{poci}.inputCurve")
        com_m = cmds.createNode("composeMatrix")
        cmds.connectAttr(f"{poci}.position", f"{com_m}.inputTranslate")
        up_uniform_output_plugs.append(f"{com_m}.outputMatrix")

    # splineIK - ribbon - uniform curve
    main_ik_joints  # splineik
    up_ik_joints  # splineik
    main_output_plugs  # ribbon
    up_output_plugs  # ribbon
    main_uniform_output_plugs  # uniform
    up_uniform_output_plugs  # uniform

    spline_ik_outs = []
    uv_outs = []
    uniform_outs = []

    last_index = len(main_ik_joints) - 1
    md = cmds.createNode("multiplyDivide")
    cmds.setAttr(f"{md}.input1", *primary_axis)
    cmds.connectAttr(negate_plug, f"{md}.input2X")
    cmds.connectAttr(negate_plug, f"{md}.input2Y")
    cmds.connectAttr(negate_plug, f"{md}.input2Z")
    negate_primary_vector_plug = f"{md}.output"
    md = cmds.createNode("multiplyDivide")
    cmds.setAttr(f"{md}.input1", *[x * -1 for x in primary_axis])
    cmds.connectAttr(negate_plug, f"{md}.input2X")
    cmds.connectAttr(negate_plug, f"{md}.input2Y")
    cmds.connectAttr(negate_plug, f"{md}.input2Z")
    negate_primary_last_vector_plug = f"{md}.output"
    md = cmds.createNode("multiplyDivide")
    cmds.setAttr(f"{md}.input1", *secondary_axis)
    cmds.connectAttr(negate_plug, f"{md}.input2X")
    cmds.connectAttr(negate_plug, f"{md}.input2Y")
    cmds.connectAttr(negate_plug, f"{md}.input2Z")
    secondary_vector_plug = f"{md}.output"

    c = 0
    result_parent = parent
    for main_j, up_j in zip(main_ik_joints, up_ik_joints):
        if c == last_index:
            next_index = last_index - 1
            primary_vector_plug = negate_primary_last_vector_plug
        else:
            next_index = c + 1
            primary_vector_plug = negate_primary_vector_plug

        t = cmds.createNode(
            "transform", parent=result_parent, name=f"{surface}_splineIKOut{c}"
        )
        aim_m = cmds.createNode("aimMatrix")
        cmds.connectAttr(primary_vector_plug, f"{aim_m}.primaryInputAxis")
        cmds.connectAttr(secondary_vector_plug, f"{aim_m}.secondaryInputAxis")
        cmds.setAttr(f"{aim_m}.primaryMode", 1)
        cmds.setAttr(f"{aim_m}.secondaryMode", 1)
        cmds.connectAttr(f"{main_j}.worldMatrix[0]", f"{aim_m}.inputMatrix")
        cmds.connectAttr(
            f"{main_ik_joints[next_index]}.worldMatrix[0]",
            f"{aim_m}.primaryTargetMatrix",
        )
        cmds.connectAttr(f"{up_j}.worldMatrix[0]", f"{aim_m}.secondaryTargetMatrix")

        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{aim_m}.outputMatrix", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{result_parent}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{t}.t")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{t}.r")
        c += 1
        result_parent = t
        spline_ik_outs.append(t)

    c = 0
    result_parent = parent
    for main_ribbon_output, up_ribbon_output in zip(main_output_plugs, up_output_plugs):
        if c == last_index:
            next_index = last_index - 1
            primary_vector_plug = negate_primary_last_vector_plug
        else:
            next_index = c + 1
            primary_vector_plug = negate_primary_vector_plug

        t = cmds.createNode(
            "transform", parent=result_parent, name=f"{surface}_uvOut{c}"
        )
        aim_m = cmds.createNode("aimMatrix")
        cmds.connectAttr(primary_vector_plug, f"{aim_m}.primaryInputAxis")
        cmds.connectAttr(secondary_vector_plug, f"{aim_m}.secondaryInputAxis")
        cmds.setAttr(f"{aim_m}.primaryMode", 1)
        cmds.setAttr(f"{aim_m}.secondaryMode", 1)
        cmds.connectAttr(main_ribbon_output, f"{aim_m}.inputMatrix")
        cmds.connectAttr(
            main_output_plugs[next_index],
            f"{aim_m}.primaryTargetMatrix",
        )
        cmds.connectAttr(up_ribbon_output, f"{aim_m}.secondaryTargetMatrix")

        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{aim_m}.outputMatrix", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{result_parent}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{t}.t")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{t}.r")
        c += 1
        result_parent = t
        uv_outs.append(t)

    c = 0
    result_parent = parent
    for main_uniform_output, up_uniform_output in zip(
        main_uniform_output_plugs, up_uniform_output_plugs
    ):
        if c == last_index:
            next_index = last_index - 1
            primary_vector_plug = negate_primary_last_vector_plug
        else:
            next_index = c + 1
            primary_vector_plug = negate_primary_vector_plug

        t = cmds.createNode(
            "transform", parent=result_parent, name=f"{surface}_uniformOut{c}"
        )
        aim_m = cmds.createNode("aimMatrix")
        cmds.connectAttr(primary_vector_plug, f"{aim_m}.primaryInputAxis")
        cmds.connectAttr(secondary_vector_plug, f"{aim_m}.secondaryInputAxis")
        cmds.setAttr(f"{aim_m}.primaryMode", 1)
        cmds.setAttr(f"{aim_m}.secondaryMode", 1)
        cmds.connectAttr(main_uniform_output, f"{aim_m}.inputMatrix")
        cmds.connectAttr(
            main_uniform_output_plugs[next_index],
            f"{aim_m}.primaryTargetMatrix",
        )
        cmds.connectAttr(up_uniform_output, f"{aim_m}.secondaryTargetMatrix")

        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{aim_m}.outputMatrix", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{result_parent}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{t}.t")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{t}.r")
        c += 1
        result_parent = t
        uniform_outs.append(t)

    uv_uniform_pbs = []
    for uv_out, uniform_out in zip(uv_outs, uniform_outs):
        pb = cmds.createNode("pairBlend")
        cmds.setAttr(f"{pb}.rotInterpolation", 1)
        cmds.connectAttr(f"{uv_out}.t", f"{pb}.inTranslate1")
        cmds.connectAttr(f"{uv_out}.r", f"{pb}.inRotate1")
        cmds.connectAttr(f"{uniform_out}.t", f"{pb}.inTranslate2")
        cmds.connectAttr(f"{uniform_out}.r", f"{pb}.inRotate2")
        cmds.connectAttr(uniform_attr, f"{pb}.weight")
        uv_uniform_pbs.append(pb)

    pos_parent = parent
    pos_list = []
    c = 0
    for ik_out, uv_uniform_pb in zip(spline_ik_outs, uv_uniform_pbs):
        pb = cmds.createNode("pairBlend")
        cmds.setAttr(f"{pb}.rotInterpolation", 1)
        cmds.connectAttr(f"{ik_out}.t", f"{pb}.inTranslate1")
        cmds.connectAttr(f"{ik_out}.r", f"{pb}.inRotate1")
        cmds.connectAttr(f"{uv_uniform_pb}.outTranslate", f"{pb}.inTranslate2")
        cmds.connectAttr(f"{uv_uniform_pb}.outRotate", f"{pb}.inRotate2")
        cmds.connectAttr(stretch_squash_attr, f"{pb}.weight")

        pos = cmds.createNode("transform", name=f"{surface}_pos{c}", parent=pos_parent)
        cmds.connectAttr(f"{pb}.outTranslate", f"{pos}.t")
        cmds.connectAttr(f"{pb}.outRotate", f"{pos}.r")

        c += 1
        pos_parent = pos
        pos_list.append(pos)

    outputs = []
    for i in range(len(output_u_value_plugs)):
        output = cmds.createNode(
            "transform", name=f"{surface}_output{i}", parent=parent
        )
        cmds.parentConstraint(pos_list[i], output)
        outputs.append(output)

    # auto volume
    curve_info = cmds.createNode("curveInfo")
    cmds.connectAttr(f"{main_orig_uniform_crv}.local", f"{curve_info}.inputCurve")
    original_length_attr = f"{curve_info}.arcLength"
    curve_info = cmds.createNode("curveInfo")
    cmds.connectAttr(f"{main_uniform_crv}.local", f"{curve_info}.inputCurve")
    deformed_length_attr = f"{curve_info}.arcLength"

    divide = cmds.createNode("divide")
    cmds.connectAttr(original_length_attr, f"{divide}.input1")
    cmds.connectAttr(deformed_length_attr, f"{divide}.input2")

    pma = cmds.createNode("plusMinusAverage")
    cmds.setAttr(f"{pma}.operation", 2)
    cmds.setAttr(f"{pma}.input1D[0]", 1)
    cmds.connectAttr(f"{divide}.output", f"{pma}.input1D[1]")
    volume_ratio_attr = f"{pma}.output1D"

    auto_volume_pma = []
    for multiple, output in zip(auto_volume_multiple, outputs):
        cmds.addAttr(
            output, longName="volume_multiple", attributeType="float", keyable=True
        )
        cmds.setAttr(f"{output}.volume_multiple", multiple)
        multiply = cmds.createNode("multiply")
        cmds.connectAttr(f"{output}.volume_multiple", f"{multiply}.input[0]")
        cmds.connectAttr(volume_ratio_attr, f"{multiply}.input[1]")
        cmds.connectAttr(auto_volume_attr, f"{multiply}.input[2]")
        cmds.connectAttr(stretch_squash_attr, f"{multiply}.input[3]")

        pma = cmds.createNode("plusMinusAverage")
        cmds.setAttr(f"{pma}.operation", 2)
        cmds.setAttr(f"{pma}.input1D[0]", 1)
        cmds.connectAttr(f"{multiply}.output", f"{pma}.input1D[1]")
        auto_volume_pma.append(pma)

    # volume
    master_remap_value = cmds.createNode("remapValue")
    cmds.setAttr(f"{master_remap_value}.value[0].value_Interp", 3)
    cmds.setAttr(f"{master_remap_value}.value[1].value_Interp", 3)
    cmds.setAttr(f"{master_remap_value}.value[2].value_Interp", 3)
    cmds.connectAttr(volume_attr, f"{master_remap_value}.value[1].value_FloatValue")
    cmds.connectAttr(
        volume_position_attr, f"{master_remap_value}.value[1].value_Position"
    )
    cmds.connectAttr(
        volume_high_bound_attr, f"{master_remap_value}.value[2].value_Position"
    )
    cmds.connectAttr(
        volume_low_bound_attr, f"{master_remap_value}.value[0].value_Position"
    )

    for i, output in enumerate(outputs):
        rv = cmds.createNode("remapValue")
        cmds.connectAttr(f"{master_remap_value}.value[0]", f"{rv}.value[0]")
        cmds.connectAttr(f"{master_remap_value}.value[1]", f"{rv}.value[1]")
        cmds.connectAttr(f"{master_remap_value}.value[2]", f"{rv}.value[2]")
        cmds.connectAttr(f"{output_u_value_plugs[i]}", f"{rv}.inputValue")

        pma = cmds.createNode("plusMinusAverage")
        cmds.connectAttr(f"{auto_volume_pma[i]}.output1D", f"{pma}.input1D[0]")
        cmds.connectAttr(f"{rv}.outValue", f"{pma}.input1D[1]")
        cmds.connectAttr(f"{pma}.output1D", f"{output}.sx")
        cmds.connectAttr(f"{pma}.output1D", f"{output}.sy")
        cmds.connectAttr(f"{pma}.output1D", f"{output}.sz")
    return surface, outputs


def ribbon_uv(
    parent,
    driver_joints,
    driver_inverse_plugs,
    surface,
    stretch_attr,
    squash_attr,
    uniform_attr,
    auto_volume_attr,
    auto_volume_multiple,
    volume_attr,
    volume_position_attr,
    volume_low_bound_attr,
    volume_high_bound_attr,
    output_u_value_plugs,
    negate_plug=None,
    primary_axis=(1, 0, 0),
    secondary_axis=(0, 0, 1),
):
    surface = cmds.parent(surface, parent)[0]

    # initialize skincluster
    temp = cmds.duplicate(surface, name="copyskindummy")[0]

    temp_sc = cmds.skinCluster(
        driver_joints + [temp],
        normalizeWeights=True,
        obeyMaxInfluences=False,
        weightDistribution=1,
        multi=True,
    )[0]

    sc = cmds.deformer(
        surface, type="skinCluster", deformerTools=True, name=f"{surface}0_sc"
    )[0]
    cmds.setAttr(f"{sc}.relativeSpaceMode", 1)
    cmds.setAttr(f"{sc}.weightDistribution", 1)

    c = 0
    for driver_jnt, inverse_plug in zip(driver_joints, driver_inverse_plugs):
        cmds.connectAttr(f"{driver_jnt}.worldMatrix", f"{sc}.matrix[{c}]", force=1)
        cmds.connectAttr(inverse_plug, f"{sc}.bindPreMatrix[{c}]", force=1)
        c += 1
    cmds.copySkinWeights(
        sourceSkin=temp_sc,
        destinationSkin=sc,
        noMirror=True,
        surfaceAssociation="closestPoint",
        influenceAssociation="closestJoint",
    )
    cmds.delete(temp)

    shape, orig = cmds.listRelatives(surface, shapes=True)

    # initialize uniform curve, squash, stretch
    uniform_main_orig_crv, uniform_main_orig_crv_iso = cmds.duplicateCurve(
        f"{orig}.v[0.5]",
        name=f"{surface}_uniformMainCrvOrig",
        constructionHistory=True,
        rn=False,
        local=True,
    )
    uniform_main_orig_crv = cmds.parent(uniform_main_orig_crv, parent)[0]
    plug = cmds.listConnections(
        f"{uniform_main_orig_crv_iso}.outputCurve",
        source=False,
        destination=True,
        plugs=True,
    )[0]
    rebuild_curve = cmds.createNode("rebuildCurve")
    cmds.setAttr(f"{rebuild_curve}.keepRange", 0)
    cmds.connectAttr(
        f"{uniform_main_orig_crv_iso}.outputCurve", f"{rebuild_curve}.inputCurve"
    )
    curve_info = cmds.createNode("curveInfo")
    cmds.connectAttr(f"{rebuild_curve}.outputCurve", f"{curve_info}.inputCurve")
    main_orig_length_plug = f"{curve_info}.arcLength"
    detach_curve = cmds.createNode("detachCurve")
    cmds.connectAttr(f"{rebuild_curve}.outputCurve", f"{detach_curve}.inputCurve")
    cmds.connectAttr(squash_attr, f"{detach_curve}.parameter[0]")
    cmds.connectAttr(f"{detach_curve}.outputCurve[0]", plug, force=1)
    uniform_up_orig_crv, uniform_up_orig_crv_iso = cmds.duplicateCurve(
        f"{orig}.v[0]",
        name=f"{surface}_uniformUpCrvOrig",
        constructionHistory=True,
        rn=False,
        local=True,
    )
    uniform_up_orig_crv = cmds.parent(uniform_up_orig_crv, parent)[0]
    plug = cmds.listConnections(
        f"{uniform_up_orig_crv_iso}.outputCurve",
        source=False,
        destination=True,
        plugs=True,
    )[0]
    rebuild_curve = cmds.createNode("rebuildCurve")
    cmds.setAttr(f"{rebuild_curve}.keepRange", 0)
    cmds.connectAttr(
        f"{uniform_up_orig_crv_iso}.outputCurve", f"{rebuild_curve}.inputCurve"
    )
    curve_info = cmds.createNode("curveInfo")
    cmds.connectAttr(f"{rebuild_curve}.outputCurve", f"{curve_info}.inputCurve")
    up_orig_length_plug = f"{curve_info}.arcLength"
    detach_curve = cmds.createNode("detachCurve")
    cmds.connectAttr(f"{rebuild_curve}.outputCurve", f"{detach_curve}.inputCurve")
    cmds.connectAttr(squash_attr, f"{detach_curve}.parameter[0]")
    cmds.connectAttr(f"{detach_curve}.outputCurve[0]", plug, force=1)
    uniform_main_crv, uniform_main_crv_iso = cmds.duplicateCurve(
        f"{surface}.v[0.5]",
        name=f"{surface}_uniformMainCrv",
        constructionHistory=True,
        rn=False,
        local=True,
    )
    uniform_main_crv = cmds.parent(uniform_main_crv, parent)[0]
    plug = cmds.listConnections(
        f"{uniform_main_crv_iso}.outputCurve",
        source=False,
        destination=True,
        plugs=True,
    )[0]
    rebuild_curve = cmds.createNode("rebuildCurve")
    cmds.connectAttr(f"{surface}.degreeU", f"{rebuild_curve}.degree")
    cmds.connectAttr(f"{surface}.spansU", f"{rebuild_curve}.spans")
    cmds.setAttr(f"{rebuild_curve}.keepRange", 0)
    cmds.connectAttr(
        f"{uniform_main_crv_iso}.outputCurve", f"{rebuild_curve}.inputCurve"
    )
    curve_info = cmds.createNode("curveInfo")
    cmds.connectAttr(f"{rebuild_curve}.outputCurve", f"{curve_info}.inputCurve")
    main_length_plug = f"{curve_info}.arcLength"
    divide = cmds.createNode("divide")
    cmds.connectAttr(main_orig_length_plug, f"{divide}.input1")
    cmds.connectAttr(main_length_plug, f"{divide}.input2")
    clamp = cmds.createNode("clamp")
    cmds.setAttr(f"{clamp}.maxR", 1)
    cmds.connectAttr(f"{divide}.output", f"{clamp}.inputR")
    blend_color = cmds.createNode("blendColors")
    cmds.connectAttr(f"{clamp}.outputR", f"{blend_color}.color2R")
    cmds.setAttr(f"{blend_color}.color1R", 1)
    cmds.connectAttr(stretch_attr, f"{blend_color}.blender")
    multiply = cmds.createNode("multiply")
    cmds.connectAttr(f"{blend_color}.outputR", f"{multiply}.input[0]")
    cmds.connectAttr(squash_attr, f"{multiply}.input[1]")
    detach_curve = cmds.createNode("detachCurve")
    cmds.connectAttr(f"{rebuild_curve}.outputCurve", f"{detach_curve}.inputCurve")
    cmds.connectAttr(f"{multiply}.output", f"{detach_curve}.parameter[0]")
    cmds.connectAttr(f"{detach_curve}.outputCurve[0]", plug, force=1)
    uniform_up_crv, uniform_up_crv_iso = cmds.duplicateCurve(
        f"{surface}.v[0]",
        name=f"{surface}_uniformUpCrv",
        constructionHistory=True,
        rn=False,
        local=True,
    )
    uniform_up_crv = cmds.parent(uniform_up_crv, parent)[0]
    plug = cmds.listConnections(
        f"{uniform_up_crv_iso}.outputCurve",
        source=False,
        destination=True,
        plugs=True,
    )[0]
    rebuild_curve = cmds.createNode("rebuildCurve")
    cmds.connectAttr(f"{surface}.degreeU", f"{rebuild_curve}.degree")
    cmds.connectAttr(f"{surface}.spansU", f"{rebuild_curve}.spans")
    cmds.setAttr(f"{rebuild_curve}.keepRange", 0)
    cmds.connectAttr(f"{uniform_up_crv_iso}.outputCurve", f"{rebuild_curve}.inputCurve")
    curve_info = cmds.createNode("curveInfo")
    cmds.connectAttr(f"{rebuild_curve}.outputCurve", f"{curve_info}.inputCurve")
    up_length_plug = f"{curve_info}.arcLength"
    divide = cmds.createNode("divide")
    cmds.connectAttr(up_orig_length_plug, f"{divide}.input1")
    cmds.connectAttr(up_length_plug, f"{divide}.input2")
    clamp = cmds.createNode("clamp")
    cmds.setAttr(f"{clamp}.maxR", 1)
    cmds.connectAttr(f"{divide}.output", f"{clamp}.inputR")
    blend_color = cmds.createNode("blendColors")
    cmds.connectAttr(f"{clamp}.outputR", f"{blend_color}.color2R")
    cmds.setAttr(f"{blend_color}.color1R", 1)
    cmds.connectAttr(stretch_attr, f"{blend_color}.blender")
    multiply = cmds.createNode("multiply")
    cmds.connectAttr(f"{blend_color}.outputR", f"{multiply}.input[0]")
    cmds.connectAttr(squash_attr, f"{multiply}.input[1]")
    detach_curve = cmds.createNode("detachCurve")
    cmds.connectAttr(f"{rebuild_curve}.outputCurve", f"{detach_curve}.inputCurve")
    cmds.connectAttr(f"{multiply}.output", f"{detach_curve}.parameter[0]")
    cmds.connectAttr(f"{detach_curve}.outputCurve[0]", plug, force=1)

    uniform_main_output_plugs = []
    uniform_up_output_plugs = []
    main_orig_parameter_plugs = []
    up_orig_parameter_plugs = []
    for plug in output_u_value_plugs:
        poci = cmds.createNode("pointOnCurveInfo")
        cmds.setAttr(f"{poci}.turnOnPercentage", 1)
        cmds.connectAttr(plug, f"{poci}.parameter")
        cmds.connectAttr(f"{uniform_main_orig_crv}.worldSpace[0]", f"{poci}.inputCurve")
        closest_surface = cmds.createNode("closestPointOnSurface")
        cmds.connectAttr(f"{poci}.result.position", f"{closest_surface}.inPosition")
        cmds.connectAttr(f"{orig}.local", f"{closest_surface}.inputSurface")
        main_orig_parameter_plugs.append(f"{closest_surface}.result.parameterU")

        poci = cmds.createNode("pointOnCurveInfo")
        cmds.setAttr(f"{poci}.turnOnPercentage", 1)
        cmds.connectAttr(plug, f"{poci}.parameter")
        cmds.connectAttr(f"{uniform_up_orig_crv}.worldSpace[0]", f"{poci}.inputCurve")
        closest_surface = cmds.createNode("closestPointOnSurface")
        cmds.connectAttr(f"{poci}.result.position", f"{closest_surface}.inPosition")
        cmds.connectAttr(f"{orig}.local", f"{closest_surface}.inputSurface")
        up_orig_parameter_plugs.append(f"{closest_surface}.result.parameterU")

        poci = cmds.createNode("pointOnCurveInfo")
        cmds.setAttr(f"{poci}.turnOnPercentage", 1)
        cmds.connectAttr(f"{uniform_main_crv}.worldSpace[0]", f"{poci}.inputCurve")
        cmds.connectAttr(plug, f"{poci}.parameter")
        com_m = cmds.createNode("composeMatrix")
        cmds.connectAttr(f"{poci}.position", f"{com_m}.inputTranslate")
        uniform_main_output_plugs.append(f"{com_m}.outputMatrix")

        poci = cmds.createNode("pointOnCurveInfo")
        cmds.setAttr(f"{poci}.turnOnPercentage", 1)
        cmds.connectAttr(f"{uniform_up_crv}.worldSpace[0]", f"{poci}.inputCurve")
        cmds.connectAttr(plug, f"{poci}.parameter")
        com_m = cmds.createNode("composeMatrix")
        cmds.connectAttr(f"{poci}.position", f"{com_m}.inputTranslate")
        uniform_up_output_plugs.append(f"{com_m}.outputMatrix")

    main_output_plugs = []
    up_output_plugs = []
    uvpin = cmds.createNode("uvPin")
    cmds.connectAttr(f"{shape}.local", f"{uvpin}.deformedGeometry")
    c = 0
    for plug in main_orig_parameter_plugs:
        cmds.setAttr(f"{uvpin}.coordinate[{c}].coordinateV", 0.5)
        cmds.connectAttr(plug, f"{uvpin}.coordinate[{c}].coordinateU")
        main_output_plugs.append(f"{uvpin}.outputMatrix[{c}]")
        c += 1
    for plug in up_orig_parameter_plugs:
        cmds.connectAttr(plug, f"{uvpin}.coordinate[{c}].coordinateU")
        up_output_plugs.append(f"{uvpin}.outputMatrix[{c}]")
        c += 1

    main_output_plugs  # ribbon
    up_output_plugs  # ribbon
    uniform_main_output_plugs  # uniform
    uniform_up_output_plugs  # uniform

    uv_outs = []
    uniform_outs = []

    last_index = len(output_u_value_plugs) - 1
    md = cmds.createNode("multiplyDivide")
    cmds.setAttr(f"{md}.input1", *primary_axis)
    cmds.connectAttr(negate_plug, f"{md}.input2X")
    cmds.connectAttr(negate_plug, f"{md}.input2Y")
    cmds.connectAttr(negate_plug, f"{md}.input2Z")
    negate_primary_vector_plug = f"{md}.output"
    md = cmds.createNode("multiplyDivide")
    cmds.setAttr(f"{md}.input1", *[x * -1 for x in primary_axis])
    cmds.connectAttr(negate_plug, f"{md}.input2X")
    cmds.connectAttr(negate_plug, f"{md}.input2Y")
    cmds.connectAttr(negate_plug, f"{md}.input2Z")
    negate_primary_last_vector_plug = f"{md}.output"
    md = cmds.createNode("multiplyDivide")
    cmds.setAttr(f"{md}.input1", *secondary_axis)
    cmds.connectAttr(negate_plug, f"{md}.input2X")
    cmds.connectAttr(negate_plug, f"{md}.input2Y")
    cmds.connectAttr(negate_plug, f"{md}.input2Z")
    secondary_vector_plug = f"{md}.output"

    c = 0
    result_parent = parent
    for main_ribbon_output, up_ribbon_output in zip(main_output_plugs, up_output_plugs):
        if c == last_index:
            next_index = last_index - 1
            primary_vector_plug = negate_primary_last_vector_plug
        else:
            next_index = c + 1
            primary_vector_plug = negate_primary_vector_plug

        t = cmds.createNode(
            "transform", parent=result_parent, name=f"{surface}_uvOut{c}"
        )
        aim_m = cmds.createNode("aimMatrix")
        cmds.connectAttr(primary_vector_plug, f"{aim_m}.primaryInputAxis")
        cmds.connectAttr(secondary_vector_plug, f"{aim_m}.secondaryInputAxis")
        cmds.setAttr(f"{aim_m}.primaryMode", 1)
        cmds.setAttr(f"{aim_m}.secondaryMode", 1)
        cmds.connectAttr(main_ribbon_output, f"{aim_m}.inputMatrix")
        cmds.connectAttr(
            main_output_plugs[next_index],
            f"{aim_m}.primaryTargetMatrix",
        )
        cmds.connectAttr(up_ribbon_output, f"{aim_m}.secondaryTargetMatrix")

        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{aim_m}.outputMatrix", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{result_parent}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{t}.t")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{t}.r")
        c += 1
        result_parent = t
        uv_outs.append(t)

    c = 0
    result_parent = parent
    for uniform_main_output, uniform_up_output in zip(
        uniform_main_output_plugs, uniform_up_output_plugs
    ):
        if c == last_index:
            next_index = last_index - 1
            primary_vector_plug = negate_primary_last_vector_plug
        else:
            next_index = c + 1
            primary_vector_plug = negate_primary_vector_plug

        t = cmds.createNode(
            "transform", parent=result_parent, name=f"{surface}_uniformOut{c}"
        )
        aim_m = cmds.createNode("aimMatrix")
        cmds.connectAttr(primary_vector_plug, f"{aim_m}.primaryInputAxis")
        cmds.connectAttr(secondary_vector_plug, f"{aim_m}.secondaryInputAxis")
        cmds.setAttr(f"{aim_m}.primaryMode", 1)
        cmds.setAttr(f"{aim_m}.secondaryMode", 1)
        cmds.connectAttr(uniform_main_output, f"{aim_m}.inputMatrix")
        cmds.connectAttr(
            uniform_main_output_plugs[next_index],
            f"{aim_m}.primaryTargetMatrix",
        )
        cmds.connectAttr(uniform_up_output, f"{aim_m}.secondaryTargetMatrix")

        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{aim_m}.outputMatrix", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{result_parent}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{t}.t")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{t}.r")
        c += 1
        result_parent = t
        uniform_outs.append(t)

    uv_uniform_pbs = []
    pos_parent = parent
    pos_list = []
    c = 0
    for uv_out, uniform_out in zip(uv_outs, uniform_outs):
        pb = cmds.createNode("pairBlend")
        cmds.setAttr(f"{pb}.rotInterpolation", 1)
        cmds.connectAttr(f"{uv_out}.t", f"{pb}.inTranslate1")
        cmds.connectAttr(f"{uv_out}.r", f"{pb}.inRotate1")
        cmds.connectAttr(f"{uniform_out}.t", f"{pb}.inTranslate2")
        cmds.connectAttr(f"{uniform_out}.r", f"{pb}.inRotate2")
        cmds.connectAttr(uniform_attr, f"{pb}.weight")
        uv_uniform_pbs.append(pb)

        pos = cmds.createNode("transform", name=f"{surface}_pos{c}", parent=pos_parent)
        cmds.connectAttr(f"{pb}.outTranslate", f"{pos}.t")
        cmds.connectAttr(f"{pb}.outRotate", f"{pos}.r")

        c += 1
        pos_parent = pos
        pos_list.append(pos)

    outputs = []
    for i in range(len(output_u_value_plugs)):
        output = cmds.createNode(
            "transform", name=f"{surface}_output{i}", parent=parent
        )
        cmds.parentConstraint(pos_list[i], output)
        outputs.append(output)

    # auto volume
    curve_info = cmds.createNode("curveInfo")
    cmds.connectAttr(f"{uniform_main_orig_crv}.local", f"{curve_info}.inputCurve")
    original_length_attr = f"{curve_info}.arcLength"
    curve_info = cmds.createNode("curveInfo")
    cmds.connectAttr(f"{uniform_main_crv}.local", f"{curve_info}.inputCurve")
    deformed_length_attr = f"{curve_info}.arcLength"

    divide = cmds.createNode("divide")
    cmds.connectAttr(original_length_attr, f"{divide}.input1")
    cmds.connectAttr(deformed_length_attr, f"{divide}.input2")

    pma = cmds.createNode("plusMinusAverage")
    cmds.setAttr(f"{pma}.operation", 2)
    cmds.setAttr(f"{pma}.input1D[0]", 1)
    cmds.connectAttr(f"{divide}.output", f"{pma}.input1D[1]")
    volume_ratio_attr = f"{pma}.output1D"

    auto_volume_pma = []
    for multiple, output in zip(auto_volume_multiple, outputs):
        cmds.addAttr(
            output, longName="volume_multiple", attributeType="float", keyable=True
        )
        cmds.setAttr(f"{output}.volume_multiple", multiple)
        multiply = cmds.createNode("multiply")
        cmds.connectAttr(f"{output}.volume_multiple", f"{multiply}.input[0]")
        cmds.connectAttr(volume_ratio_attr, f"{multiply}.input[1]")
        cmds.connectAttr(auto_volume_attr, f"{multiply}.input[2]")

        pma = cmds.createNode("plusMinusAverage")
        cmds.setAttr(f"{pma}.operation", 2)
        cmds.setAttr(f"{pma}.input1D[0]", 1)
        cmds.connectAttr(f"{multiply}.output", f"{pma}.input1D[1]")
        auto_volume_pma.append(pma)

    # volume
    master_remap_value = cmds.createNode("remapValue")
    cmds.setAttr(f"{master_remap_value}.value[0].value_Interp", 3)
    cmds.setAttr(f"{master_remap_value}.value[1].value_Interp", 3)
    cmds.setAttr(f"{master_remap_value}.value[2].value_Interp", 3)
    cmds.connectAttr(volume_attr, f"{master_remap_value}.value[1].value_FloatValue")
    cmds.connectAttr(
        volume_position_attr, f"{master_remap_value}.value[1].value_Position"
    )
    cmds.connectAttr(
        volume_high_bound_attr, f"{master_remap_value}.value[2].value_Position"
    )
    cmds.connectAttr(
        volume_low_bound_attr, f"{master_remap_value}.value[0].value_Position"
    )

    for i, output in enumerate(outputs):
        rv = cmds.createNode("remapValue")
        cmds.connectAttr(f"{master_remap_value}.value[0]", f"{rv}.value[0]")
        cmds.connectAttr(f"{master_remap_value}.value[1]", f"{rv}.value[1]")
        cmds.connectAttr(f"{master_remap_value}.value[2]", f"{rv}.value[2]")
        cmds.connectAttr(f"{output_u_value_plugs[i]}", f"{rv}.inputValue")

        pma = cmds.createNode("plusMinusAverage")
        cmds.connectAttr(f"{auto_volume_pma[i]}.output1D", f"{pma}.input1D[0]")
        cmds.connectAttr(f"{rv}.outValue", f"{pma}.input1D[1]")
        cmds.connectAttr(f"{pma}.output1D", f"{output}.sx")
        cmds.connectAttr(f"{pma}.output1D", f"{output}.sy")
        cmds.connectAttr(f"{pma}.output1D", f"{output}.sz")

    return surface, outputs


def ribbon_chain_spline_ik(
    parent,
    driver_joints,
    driver_inverse_plugs,
    surface,
    main_ik_joints,
    up_ik_joints,
    dyn_ik_joints,
    stretch_attr,
    squash_attr,
    squash_pin_method_attr,
    scale_attr,
    initial_chain_distance_attr,
    volume_high_position_attr,
    volume_high_value_attr,
    volume_mid_position_attr,
    volume_mid_value_attr,
    volume_low_position_attr,
    volume_low_value_attr,
    dynamic_enable_attr,
    negate_plug=None,
    primary_axis=(1, 0, 0),
    secondary_axis=(0, 0, 1),
):
    surface = cmds.parent(surface, parent)[0]

    # initialize skincluster
    temp = cmds.duplicate(surface, name="copyskindummy")[0]

    temp_sc = cmds.skinCluster(
        driver_joints + [temp],
        normalizeWeights=True,
        obeyMaxInfluences=False,
        weightDistribution=1,
        multi=True,
    )[0]

    sc = cmds.deformer(
        surface, type="skinCluster", deformerTools=True, name=f"{surface}0_sc"
    )[0]
    cmds.setAttr(f"{sc}.relativeSpaceMode", 1)
    cmds.setAttr(f"{sc}.weightDistribution", 1)

    c = 0
    for driver_jnt, inverse_plug in zip(driver_joints, driver_inverse_plugs):
        cmds.connectAttr(f"{driver_jnt}.worldMatrix", f"{sc}.matrix[{c}]", force=1)
        cmds.connectAttr(inverse_plug, f"{sc}.bindPreMatrix[{c}]", force=1)
        c += 1
    cmds.copySkinWeights(
        sourceSkin=temp_sc,
        destinationSkin=sc,
        noMirror=True,
        surfaceAssociation="closestPoint",
        influenceAssociation="closestJoint",
    )
    cmds.delete(temp)

    shape, orig = cmds.listRelatives(surface, shapes=True)

    # initialize curve
    main_orig_crv, main_orig_crv_iso = cmds.duplicateCurve(
        f"{orig}.v[0.5]",
        name=f"{surface}_mainCrvOrig",
        constructionHistory=True,
        rn=False,
        local=True,
    )
    main_orig_crv = cmds.parent(main_orig_crv, parent)[0]
    up_orig_crv, up_orig_crv_iso = cmds.duplicateCurve(
        f"{orig}.v[0]",
        name=f"{surface}_upCrvOrig",
        constructionHistory=True,
        rn=False,
        local=True,
    )
    up_orig_crv = cmds.parent(up_orig_crv, parent)[0]
    main_crv, main_crv_iso = cmds.duplicateCurve(
        f"{shape}.v[0.5]",
        name=f"{surface}_mainCrv",
        constructionHistory=True,
        rn=False,
        local=True,
    )
    main_crv = cmds.parent(main_crv, parent)[0]
    up_crv, up_crv_iso = cmds.duplicateCurve(
        f"{shape}.v[0]",
        name=f"{surface}_upCrv",
        constructionHistory=True,
        rn=False,
        local=True,
    )
    up_crv = cmds.parent(up_crv, parent)[0]

    nucleus = create_nucleus(name=f"{surface}_nucleus")
    cmds.hide(nucleus)
    dyn_crv = cmds.duplicate(main_orig_crv, name=f"{surface}_dynCrv")[0]
    cmds.rebuildCurve(
        dyn_crv,
        fitRebuild=False,
        keepControlPoints=True,
        keepRange=1,
        degree=1,
        constructionHistory=False,
        replaceOriginal=True,
    )
    hair_system, follicles, input_curves = assign_nhair(
        parent=parent,
        name=f"{surface}_nhair",
        nucleus=nucleus,
        curves=[dyn_crv],
        degree=3,
    )
    for crv in input_curves:
        cmds.connectAttr(f"{main_crv_iso}.outputCurve", f"{crv}.create")

    main_ikh, effector = cmds.ikHandle(
        startJoint=main_ik_joints[0],
        endEffector=main_ik_joints[-1],
        solver="ikSplineSolver",
        name=f"{surface}_mainIkh",
        curve=main_crv,
        createCurve=False,
    )
    main_ikh = cmds.parent(main_ikh, parent)[0]
    up_ikh, effector = cmds.ikHandle(
        startJoint=up_ik_joints[0],
        endEffector=up_ik_joints[-1],
        solver="ikSplineSolver",
        name=f"{surface}_upIkh",
        curve=up_crv,
        createCurve=False,
    )
    up_ikh = cmds.parent(up_ikh, parent)[0]
    dyn_ikh, effector = cmds.ikHandle(
        startJoint=dyn_ik_joints[0],
        endEffector=dyn_ik_joints[-1],
        solver="ikSplineSolver",
        name=f"{surface}_dynIkh",
        curve=dyn_crv,
        createCurve=False,
    )
    dyn_ikh = cmds.parent(dyn_ikh, parent)[0]

    curve_info = cmds.createNode("curveInfo")
    cmds.connectAttr(f"{main_crv}.local", f"{curve_info}.inputCurve")
    main_curve_length = f"{curve_info}.arcLength"
    curve_info = cmds.createNode("curveInfo")
    cmds.connectAttr(f"{main_orig_crv}.local", f"{curve_info}.inputCurve")
    main_orig_curve_length = f"{curve_info}.arcLength"

    divide = cmds.createNode("divide")
    cmds.connectAttr(main_curve_length, f"{divide}.input1")
    cmds.connectAttr(main_orig_curve_length, f"{divide}.input2")
    ratio = f"{divide}.output"

    multiply = cmds.createNode("multiply")
    cmds.connectAttr(initial_chain_distance_attr, f"{multiply}.input[0]")
    cmds.connectAttr(ratio, f"{multiply}.input[1]")

    rvs = []
    choices = []
    multiplies = []
    multiply = cmds.createNode("multiply")
    cmds.setAttr(f"{multiply}.input[0]", 0.00000001)
    cmds.connectAttr(negate_plug, f"{multiply}.input[1]")
    negate_min_translate_plug = f"{multiply}.output"
    is_negate = True if cmds.getAttr(negate_plug) < 0 else False
    for i in range(len(main_ik_joints[1:])):
        choice = cmds.createNode("choice")
        cmds.connectAttr(squash_pin_method_attr, f"{choice}.selector")
        # uniform squash
        cmds.connectAttr(f"{multiply}.output", f"{choice}.input[0]")

        rv = cmds.createNode("remapValue")
        cmds.connectAttr(main_curve_length, f"{rv}.inputValue")
        cmds.connectAttr(initial_chain_distance_attr, f"{rv}.outputMin")
        cmds.setAttr(f"{rv}.outputMax", 0)

        m = cmds.createNode("multiply")
        cmds.setAttr(f"{m}.input[0]", i + 1)
        cmds.connectAttr(initial_chain_distance_attr, f"{m}.input[1]")
        cmds.connectAttr(f"{m}.output", f"{rv}.inputMin")
        try:
            previous_m = multiplies[i - 1]
            cmds.connectAttr(f"{previous_m}.output", f"{rv}.inputMax")
        except:
            pass
        multiplies.append(m)
        # end stack
        cmds.connectAttr(f"{rv}.outValue", f"{choice}.input[2]")
        rvs.append(rv)
        choices.append(choice)

        if is_negate:
            cmds.transformLimits(
                main_ik_joints[i + 1],
                translationX=(-1, -0.00000001),
                enableTranslationX=(0, 1),
            )
            cmds.transformLimits(
                up_ik_joints[i + 1],
                translationX=(-1, -0.00000001),
                enableTranslationX=(0, 1),
            )
            cmds.connectAttr(
                negate_min_translate_plug, f"{main_ik_joints[i + 1]}.maxTransXLimit"
            )
            cmds.connectAttr(
                negate_min_translate_plug, f"{up_ik_joints[i + 1]}.maxTransXLimit"
            )
        else:
            cmds.transformLimits(
                main_ik_joints[i + 1],
                translationX=(0.00000001, 1),
                enableTranslationX=(1, 0),
            )
            cmds.transformLimits(
                up_ik_joints[i + 1],
                translationX=(0.00000001, 1),
                enableTranslationX=(1, 0),
            )
            cmds.connectAttr(
                negate_min_translate_plug, f"{main_ik_joints[i + 1]}.minTransXLimit"
            )
            cmds.connectAttr(
                negate_min_translate_plug, f"{up_ik_joints[i + 1]}.minTransXLimit"
            )

    i = 0
    stretch_squash_results = []
    for rv, choice in zip(reversed(rvs), choices):
        # start stack
        cmds.connectAttr(f"{rv}.outValue", f"{choice}.input[1]")

        squash_bta = cmds.createNode("blendTwoAttr")
        cmds.connectAttr(squash_attr, f"{squash_bta}.attributesBlender")
        cmds.connectAttr(initial_chain_distance_attr, f"{squash_bta}.input[0]")
        cmds.connectAttr(f"{choice}.output", f"{squash_bta}.input[1]")

        stretch_bta = cmds.createNode("blendTwoAttr")
        cmds.connectAttr(stretch_attr, f"{stretch_bta}.attributesBlender")
        cmds.connectAttr(initial_chain_distance_attr, f"{stretch_bta}.input[0]")
        cmds.connectAttr(f"{multiply}.output", f"{stretch_bta}.input[1]")

        condition = cmds.createNode("condition")
        cmds.connectAttr(ratio, f"{condition}.firstTerm")
        cmds.setAttr(f"{condition}.secondTerm", 1)
        cmds.setAttr(f"{condition}.operation", 2)
        cmds.connectAttr(f"{squash_bta}.output", f"{condition}.colorIfFalseR")
        cmds.connectAttr(f"{stretch_bta}.output", f"{condition}.colorIfTrueR")

        stretch_squash_results.append(f"{condition}.outColorR")
        i += 1

    # volume
    master_remap_value = cmds.createNode("remapValue")
    cmds.setAttr(f"{master_remap_value}.value[0].value_Interp", 3)
    cmds.setAttr(f"{master_remap_value}.value[1].value_Interp", 3)
    cmds.setAttr(f"{master_remap_value}.value[2].value_Interp", 3)
    cmds.connectAttr(
        volume_mid_value_attr, f"{master_remap_value}.value[1].value_FloatValue"
    )
    cmds.connectAttr(
        volume_mid_position_attr, f"{master_remap_value}.value[1].value_Position"
    )
    cmds.connectAttr(
        volume_high_position_attr, f"{master_remap_value}.value[2].value_Position"
    )
    cmds.connectAttr(
        volume_high_value_attr, f"{master_remap_value}.value[2].value_FloatValue"
    )
    cmds.connectAttr(
        volume_low_position_attr, f"{master_remap_value}.value[0].value_Position"
    )
    cmds.connectAttr(
        volume_low_value_attr, f"{master_remap_value}.value[0].value_FloatValue"
    )

    for i, result in enumerate(stretch_squash_results):
        rv = cmds.createNode("remapValue")
        cmds.connectAttr(f"{master_remap_value}.value[0]", f"{rv}.value[0]")
        cmds.connectAttr(f"{master_remap_value}.value[1]", f"{rv}.value[1]")
        cmds.connectAttr(f"{master_remap_value}.value[2]", f"{rv}.value[2]")
        cmds.setAttr(f"{rv}.inputValue", i / (len(main_ik_joints) - 1))

        pma = cmds.createNode("plusMinusAverage")
        cmds.setAttr(f"{pma}.input1D[0]", 1)
        cmds.connectAttr(f"{rv}.outValue", f"{pma}.input1D[1]")

        multiply = cmds.createNode("multiply")
        cmds.connectAttr(result, f"{multiply}.input[0]")
        cmds.connectAttr(f"{pma}.output1D", f"{multiply}.input[1]")

        negate_multiply = cmds.createNode("multiply")
        cmds.connectAttr(f"{multiply}.output", f"{negate_multiply}.input[0]")
        cmds.connectAttr(negate_plug, f"{negate_multiply}.input[1]")
        cmds.connectAttr(f"{negate_multiply}.output", f"{main_ik_joints[i + 1]}.tx")
        cmds.connectAttr(f"{negate_multiply}.output", f"{up_ik_joints[i + 1]}.tx")

    for i in range(len(main_ik_joints)):
        cmds.connectAttr(f"{main_ik_joints[i]}.tx", f"{dyn_ik_joints[i]}.tx")

    # splineIk
    main_ik_joints  # splineik
    up_ik_joints  # splineik

    spline_ik_outs = []

    md = cmds.createNode("multiplyDivide")
    cmds.setAttr(f"{md}.input1", *primary_axis)
    cmds.connectAttr(negate_plug, f"{md}.input2X")
    cmds.connectAttr(negate_plug, f"{md}.input2Y")
    cmds.connectAttr(negate_plug, f"{md}.input2Z")
    primary_vector_plug = f"{md}.output"
    md = cmds.createNode("multiplyDivide")
    cmds.setAttr(f"{md}.input1", *secondary_axis)
    cmds.connectAttr(negate_plug, f"{md}.input2X")
    cmds.connectAttr(negate_plug, f"{md}.input2Y")
    cmds.connectAttr(negate_plug, f"{md}.input2Z")
    secondary_vector_plug = f"{md}.output"

    result_parent = parent
    for i in range(len(main_ik_joints) - 1):
        t = cmds.createNode(
            "transform", parent=result_parent, name=f"{surface}_splineIKOut{i}"
        )
        aim_m = cmds.createNode("aimMatrix")
        cmds.connectAttr(primary_vector_plug, f"{aim_m}.primaryInputAxis")
        cmds.connectAttr(secondary_vector_plug, f"{aim_m}.secondaryInputAxis")
        cmds.setAttr(f"{aim_m}.primaryMode", 1)
        cmds.setAttr(f"{aim_m}.secondaryMode", 1)
        cmds.connectAttr(f"{main_ik_joints[i]}.worldMatrix[0]", f"{aim_m}.inputMatrix")
        cmds.connectAttr(
            f"{main_ik_joints[i + 1]}.worldMatrix[0]",
            f"{aim_m}.primaryTargetMatrix",
        )
        cmds.connectAttr(
            f"{up_ik_joints[i]}.worldMatrix[0]", f"{aim_m}.secondaryTargetMatrix"
        )

        mult_m = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{aim_m}.outputMatrix", f"{mult_m}.matrixIn[0]")
        cmds.connectAttr(
            f"{result_parent}.worldInverseMatrix[0]", f"{mult_m}.matrixIn[1]"
        )
        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{mult_m}.matrixSum", f"{decom_m}.inputMatrix")

        pair_b = cmds.createNode("pairBlend")
        cmds.setAttr(f"{pair_b}.rotInterpolation", 1)
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{pair_b}.inTranslate1")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{pair_b}.inRotate1")

        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{dyn_ik_joints[i]}.dagLocalMatrix", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{pair_b}.inTranslate2")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{pair_b}.inRotate2")
        cmds.connectAttr(dynamic_enable_attr, f"{pair_b}.weight")
        cmds.connectAttr(f"{pair_b}.outTranslate", f"{t}.t")
        cmds.connectAttr(f"{pair_b}.outRotate", f"{t}.r")

        result_parent = t
        spline_ik_outs.append(t)

    outputs = []
    for i in range(len(spline_ik_outs)):
        output = cmds.createNode(
            "transform", name=f"{surface}_output{i}", parent=parent
        )
        cmds.parentConstraint(spline_ik_outs[i], output)

        # scale
        divide = cmds.createNode("divide")
        cmds.connectAttr(f"{main_ik_joints[i + 1]}.tx", f"{divide}.input1")
        cmds.connectAttr(initial_chain_distance_attr, f"{divide}.input2")

        absolute = cmds.createNode("absolute")
        cmds.connectAttr(f"{divide}.output", f"{absolute}.input")

        bta = cmds.createNode("blendTwoAttr")
        cmds.setAttr(f"{bta}.input[0]", 1)
        cmds.connectAttr(f"{absolute}.output", f"{bta}.input[1]")
        cmds.connectAttr(scale_attr, f"{bta}.attributesBlender")
        cmds.connectAttr(f"{bta}.output", f"{output}.sx")
        cmds.connectAttr(f"{bta}.output", f"{output}.sy")
        cmds.connectAttr(f"{bta}.output", f"{output}.sz")
        outputs.append(output)

    return surface, outputs, nucleus, hair_system, follicles


def spline_ik():
    pass


# endregion


# region dynamic
def create_nucleus(name=""):
    if cmds.objExists(name if name else "nucleus0"):
        return name if name else "nucleus0"
    nucleus = cmds.createNode(
        "nucleus", name=name if name else "nucleus0", parent="origin_ctl"
    )
    cmds.expression(
        name=f"{name}_startFrame_expr" if name else "nucleus0_startFrame_expr",
        string=f"{nucleus}.startFrame = `playbackOptions -query -minTime` * `getAttr {nucleus}.enable`;",
        alwaysEvaluate=False,
        timeDependent=False,
        safe=True,
        unitConversion="all",
    )
    cmds.connectAttr("time1.outTime", f"{nucleus}.currentTime")

    cmds.addAttr(
        nucleus, longName="is_domino_nucleus", attributeType="bool", keyable=False
    )
    cmds.addAttr(nucleus, longName="host_controller", attributeType="message")
    cmds.addAttr(
        nucleus, longName="bake_controllers", attributeType="message", multi=True
    )
    return nucleus


def assign_nhair(parent, name, nucleus, curves, degree=3):
    hair_system_t = cmds.createNode("transform", name=name, parent=parent)
    hair_system = cmds.createNode(
        "hairSystem", name=f"{name}Shape", parent=hair_system_t
    )
    cmds.connectAttr("time1.outTime", f"{hair_system}.currentTime")
    cmds.connectAttr(f"{nucleus}.startFrame", f"{hair_system}.startFrame")

    index = len(cmds.listConnections(f"{nucleus}.inputActive", source=True) or [])
    cmds.connectAttr(f"{hair_system}.currentState", f"{nucleus}.inputActive[{index}]")
    cmds.connectAttr(
        f"{hair_system}.startState", f"{nucleus}.inputActiveStart[{index}]"
    )
    cmds.connectAttr(f"{nucleus}.outputObjects[{index}]", f"{hair_system}.nextState")

    intermediates = []
    follicles = []
    inputs = []
    for i, curve in enumerate(curves):
        curve_shape = cmds.listRelatives(curve, shapes=True, noIntermediate=True)[0]
        input_curve = cmds.duplicateCurve(
            curve_shape, constructionHistory=False, name=f"{curve}_input"
        )[0]
        rebuild = cmds.createNode("rebuildCurve")
        cmds.setAttr(f"{rebuild}.rebuildType", 0)
        cmds.setAttr(f"{rebuild}.degree", 1)
        cmds.setAttr(f"{rebuild}.endKnots", 1)
        cmds.setAttr(f"{rebuild}.keepRange", 0)
        cmds.setAttr(f"{rebuild}.keepEndPoints", 1)
        cmds.setAttr(f"{rebuild}.keepTangents", 0)
        cmds.setAttr(f"{rebuild}.keepControlPoints", 1)
        cmds.connectAttr(f"{input_curve}.local", f"{rebuild}.inputCurve")

        intermediate = cmds.duplicateCurve(
            curve_shape, constructionHistory=False, name=f"{curve}_intermediate"
        )[0]
        intermediates.append(intermediate)
        intermediate_shape = cmds.listRelatives(intermediate, shapes=True)[0]
        cmds.setAttr(f"{intermediate_shape}.intermediateObject", 1)
        cmds.parent(intermediate_shape, input_curve, shape=True, relative=True)
        cmds.connectAttr(f"{rebuild}.outputCurve", f"{intermediate_shape}.create")

        follicle_t = cmds.createNode(
            "transform", name=f"{curve}_follicle", parent=parent
        )
        follicle = cmds.createNode(
            "follicle", name=f"{curve}_follicleShape", parent=follicle_t
        )
        follicles.append(follicle)
        cmds.setAttr(f"{follicle}.restPose", 1)
        cmds.setAttr(f"{follicle}.degree", 3)
        cmds.setAttr(f"{follicle}.simulationMethod", 2)
        cmds.setAttr(f"{follicle}.startDirection", 1)
        cmds.connectAttr(
            f"{hair_system}.outputHair[{i}]", f"{follicle}.currentPosition"
        )
        input_curve = cmds.parent(input_curve, follicle_t)[0]
        inputs.append(input_curve)

        cmds.connectAttr(f"{follicle}.outHair", f"{hair_system}.inputHair[{i}]")
        cmds.connectAttr(
            f"{input_curve}.worldMatrix[0]", f"{follicle}.startPositionMatrix"
        )
        cmds.connectAttr(f"{intermediate_shape}.local", f"{follicle}.startPosition")

        rebuild = cmds.createNode("rebuildCurve")
        cmds.setAttr(f"{rebuild}.rebuildType", 0)
        cmds.setAttr(f"{rebuild}.degree", degree)
        cmds.setAttr(f"{rebuild}.endKnots", 1)
        cmds.setAttr(f"{rebuild}.keepRange", 0)
        cmds.setAttr(f"{rebuild}.keepEndPoints", 0)
        cmds.setAttr(f"{rebuild}.keepTangents", 0)
        cmds.setAttr(f"{rebuild}.keepControlPoints", 1)
        cmds.setAttr(f"{rebuild}.fitRebuild", 0)
        cmds.connectAttr(f"{follicle}.outCurve", f"{rebuild}.inputCurve")

        tg = cmds.createNode("transformGeometry")
        cmds.connectAttr(f"{rebuild}.outputCurve", f"{tg}.inputGeometry")
        cmds.connectAttr(f"{input_curve}.worldInverseMatrix[0]", f"{tg}.transform")
        cmds.connectAttr(f"{tg}.outputGeometry", f"{curve_shape}.create")

    cmds.delete(intermediates)
    cmds.setAttr(f"{hair_system}.active", 1)
    cmds.setAttr(f"{hair_system}.clumpWidth", 0)
    cmds.setAttr(f"{hair_system}.clumpWidthScale[1].clumpWidthScale_FloatValue", 1)
    cmds.setAttr(f"{hair_system}.hairWidthScale[1].hairWidthScale_FloatValue", 1)
    cmds.setAttr(f"{hair_system}.mass", 10)
    cmds.setAttr(f"{hair_system}.damp", 0.1)
    cmds.setAttr(f"{hair_system}.simulationMethod", 3)
    cmds.setAttr(f"{hair_system}.selfCollide", 1)
    cmds.setAttr(f"{hair_system}.stretchResistance", 10)
    cmds.setAttr(f"{hair_system}.compressionResistance", 5)
    cmds.setAttr(f"{hair_system}.bendResistance", 0)
    return hair_system_t, follicles, inputs


# endregion


# region blendshape transfer / import / export
def transfer_blendshape(source, destination, bs, smooth=0, delta_mush=False):
    check = False
    if not cmds.objExists(source):
        logger.warning(f"{source} 가 존재하지 않습니다.")
        check = True
    if not cmds.objExists(destination):
        logger.warning(f"{destination} 가 존재하지 않습니다.")
        check = True
    if not cmds.objExists(bs):
        logger.warning(f"{bs} 가 존재하지 않습니다.")
        check = True
    if check:
        return

    # interface mesh
    interface_mesh = cmds.duplicate(destination, name="interface_mesh")[0]
    intermediate = cmds.ls(interface_mesh, dagObjects=True, intermediateObjects=True)
    if intermediate:
        cmds.delete(intermediate)

    # wrap
    p_wrap = cmds.proximityWrap(interface_mesh)[0]
    cmds.proximityWrap(p_wrap, edit=True, addDrivers=source)
    cmds.setAttr(f"{p_wrap}.wrapMode", 0)
    cmds.setAttr(f"{p_wrap}.smoothInfluences", smooth)
    if delta_mush:
        delta_mush = cmds.deformer(interface_mesh, tool="deltaMush")[0]
        cmds.setAttr(f"{delta_mush}.displacement", 1)
        cmds.setAttr(f"{delta_mush}.pinBorderVertices", 0)

    # rename
    final_bs = cmds.blendShape(destination)[0]
    cmds.rename(bs, "TEMPBLENDSHAPE")
    final_bs = cmds.rename(final_bs, bs)
    bs = cmds.rename("TEMPBLENDSHAPE", f"{bs}_transferred")

    # inbetween attributes
    attrs = [
        x
        for x in cmds.listAttr(f"{bs}.inputTarget[0].inputTargetGroup", multi=True)
        if "inputTargetItem" in x
    ][::6]
    indexes = []
    for attr in attrs:
        if "6000" in attr:
            indexes.append(attrs.index(attr))

    inbetween_attrs = []
    previous_index = -1
    for index in indexes:
        inbetween_attrs.append(attrs[previous_index + 1 : index + 1][:-1])
        previous_index = index

    # input disconnect
    weight_attrs = cmds.listAttr(f"{bs}.weight", multi=True)
    destination_source = []
    for attr in weight_attrs:
        plugs = (
            cmds.listConnections(
                f"{bs}.{attr}",
                source=True,
                destination=False,
                plugs=True,
                connections=True,
            )
            or []
        )
        if plugs:
            cmds.disconnectAttr(plugs[1], plugs[0])
        destination_source.append(plugs)

    # transfer
    for attr in weight_attrs:
        cmds.setAttr(f"{bs}.{attr}", 0)

    cmds.select(interface_mesh)
    for i, attr in enumerate(weight_attrs):
        cmds.setAttr(f"{bs}.{attr}", 1)
        cmds.blendShape(
            final_bs,
            edit=True,
            target=(destination, i, interface_mesh, 1),
            weight=(i, 0),
        )
        cmds.aliasAttr(attr, f"{final_bs}.w[{i}]")
        connections = cmds.listConnections(
            f"{interface_mesh}Shape.worldMesh[0]", connections=True, plugs=True
        )
        cmds.disconnectAttr(connections[0], connections[1])
        for inbetween_attr in inbetween_attrs[i]:
            value = int(inbetween_attr[-4:-1]) / 1000
            cmds.setAttr(f"{bs}.{attr}", value)
            cmds.blendShape(
                final_bs,
                edit=True,
                inBetween=True,
                inBetweenType="absolute",
                target=(destination, i, interface_mesh, value),
            )
            connections = cmds.listConnections(
                f"{interface_mesh}Shape.worldMesh[0]", connections=True, plugs=True
            )
            cmds.disconnectAttr(connections[0], connections[1])
        cmds.setAttr(f"{bs}.{attr}", 0)

    # reconnect bs
    for plugs in destination_source:
        if plugs:
            cmds.connectAttr(plugs[1], plugs[0])

    # copy combinationShape / connect driver
    for attr in weight_attrs:
        driver = cmds.listConnections(f"{bs}.{attr}", source=True, destination=False)
        if driver:
            if cmds.nodeType(driver[0]) == "combinationShape":
                method = cmds.getAttr(f"{driver[0]}.combinationMethod")
                combination_shape = cmds.createNode("combinationShape")
                cmds.setAttr(f"{combination_shape}.combinationMethod", method)
                connections = cmds.listConnections(
                    f"{driver[0]}.inputWeight",
                    source=True,
                    destination=False,
                    plugs=True,
                    connections=True,
                )
                for i in range(int(len(connections) / 2)):
                    destination_attr = connections[i * 2].split(".")[1]
                    source_attr = connections[i * 2 + 1].split(".")[1]
                    cmds.connectAttr(
                        f"{final_bs}.{source_attr}",
                        f"{combination_shape}.{destination_attr}",
                    )
                connections = cmds.listConnections(
                    f"{driver[0]}.outputWeight",
                    source=False,
                    destination=True,
                    plugs=True,
                    connections=True,
                )
                destination_attr = connections[1].split(".")[1]
                source_attr = connections[0].split(".")[1]
                cmds.connectAttr(
                    f"{combination_shape}.{source_attr}",
                    f"{final_bs}.{destination_attr}",
                )
            else:
                plug = cmds.listConnections(
                    f"{bs}.{attr}", source=True, destination=False, plugs=True
                )[0]
                cmds.connectAttr(plug, f"{final_bs}.{attr}")

    # remove
    cmds.proximityWrap(p_wrap, edit=True, removeDrivers=source)
    cmds.delete(interface_mesh)


def export_blendshape(directory, bs):
    directory_path = Path(directory)
    if not directory_path.exists():
        return logger.warning(f"{directory} 가 존재하지 않습니다.")
    mesh = cmds.deformer(bs, geometry=True, query=True)[0]

    plug = cmds.listConnections(f"{bs}.originalGeometry[0]", plugs=True)[0]
    shape = plug.split(".")[0]
    new_transform = cmds.duplicate(shape)
    shape = cmds.listRelatives(new_transform, shapes=True, noIntermediate=True)
    if shape:
        cmds.delete(shape)
    orig_shape = cmds.ls(new_transform, dagObjects=True, intermediateObjects=True)[0]
    cmds.setAttr(f"{orig_shape}.intermediateObject", 0)

    new_transform = cmds.rename(new_transform, f"{bs}_orig")
    new_shape = cmds.listRelatives(new_transform, shapes=True)[0]
    new_shape = cmds.rename(new_shape, f"{new_transform}Shape")

    original_obj_path = directory_path / f"{mesh}__{bs}.obj"
    cmds.select(new_transform)
    cmds.file(
        original_obj_path,
        typ="OBJexport",
        preserveReferences=True,
        exportSelected=True,
        options="groups=0;ptgroups=0;materials=0;smoothing=0;normals=0",
    )
    logger.info(f"Exported original mesh to `{original_obj_path}`")
    cmds.delete(new_transform)

    shp_path = directory_path / f"{bs}.shp"
    cmds.blendShape(bs, edit=True, export=shp_path)
    logger.info(f"Exported blendShape(.shp) to `{shp_path}`")


def import_blendshape(directory):
    directory_path = Path(directory)
    if not directory_path.exists():
        return logger.warning(f"{directory} 가 존재하지 않습니다.")

    obj_files = directory_path.glob("*__*.obj")
    for obj in obj_files:
        name, _ = obj.name.split(".")
        mesh, bs = name.split("__")
        for p in directory_path.glob(f"{bs}.shp"):
            if not cmds.objExists(mesh):
                logger.warning(f"{mesh} 가 존재하지 않습니다.")
                continue
            if not cmds.objExists(bs):
                cmds.blendShape(mesh, name=bs)
            cmds.blendShape(bs, edit=True, ip=p)


# endregion


# region deformerWeight import / export
DEFORMER_TYPE_TABLE = {
    "skinCluster": [
        "skinningMethod",
        "useComponents",
        "normalizeWeights",
        "deformUserNormals",
        "relativeSpaceMode",
        "weightDistribution",
    ],
    "blendShape": ["weight", "origin"],
    "cluster": ["relative", "angleInterpolation"],
    "deltaMush": [
        "smoothingIterations",
        "smoothingStep",
        "inwardConstraint",
        "outwardConstraint",
        "distanceWeight",
        "displacement",
        "pinBorderVertices",
    ],
    "tension": [
        "smoothingIterations",
        "smoothingStep",
        "inwardConstraint",
        "outwardConstraint",
        "squashConstraint",
        "stretchConstraint",
        "relative",
        "shearStrength",
        "bendStrength",
        "pinBorderVertices",
    ],
    "proximityWrap": [
        "wrapMode",
        "coordinateFrames",
        "maxDrivers",
        "falloffScale",
        "dropoffRateScale",
        "scaleCompensation",
        "smoothInfluences",
        "smoothNormals",
        "softNormalization",
        "spanSamples",
    ],
    "shrinkWrap": [
        "targetSmoothLevel",
        "projection",
        "closestIfNoIntersection",
        "reverse",
        "bidirectional",
        "boundingBoxCenter",
        "axisReference",
        "alongX",
        "alongY",
        "alongZ",
        "offset",
        "targetInflation",
        "falloff",
        "falloffIterations",
        "shapePreservationEnable",
        "shapePreservationSteps",
        "shapePreservationReprojection",
    ],
    "wire": [
        "crossingEffect",
        "tension",
        "localInfluence",
        "rotation",
        "dropoffDistance",
        "scale",
        "freezeGeometry",
        "bindToOriginalGeometry",
    ],
    "jiggle": [
        "enable",
        "ignoreTransform",
        "forceAlongNormal",
        "forceOnTangent",
        "motionMultiplier",
        "stiffness",
        "damping",
        "jiggleWeight",
        "directionBias",
    ],
    "ffd": [
        "local",
        "localInfluenceS",
        "localInfluenceT",
        "localInfluenceU",
        "outsideLattice",
        "outsideFalloffDist",
        "usePartialResolution",
        "partialResolution",
        "bindToOriginalGeometry",
        "freezeGeometry",
    ],
}


def bind_skincluster(geometry, joints, name=""):
    sc = cmds.skinCluster(
        joints + [geometry],
        maximumInfluences=1,
        normalizeWeights=True,
        obeyMaxInfluences=False,
        weightDistribution=1,
        multi=True,
        toSelectedBones=True,
    )[0]
    cmds.setAttr(f"{sc}.relativeSpaceMode", 1)
    if name:
        sc = cmds.rename(sc, name)
    return sc


def export_weight(path, deformer):
    directory = Path(path).parent.as_posix()
    file_name = Path(path).name
    deformer_type = cmds.nodeType(deformer)
    if deformer_type not in DEFORMER_TYPE_TABLE:
        return logger.warning(f"{deformer_type} 을 지원하지 않습니다.")
    objs = cmds.deformer(deformer, geometry=True, query=True) or []
    for obj in objs:
        all_deformer = cmds.deformableShape(obj) or []
        all_deformer.remove(deformer)
        skip_objs = objs.copy()
        skip_objs.remove(obj)
        flags = {
            "export": True,
            "deformer": deformer,
            "shape": obj,
            "skip": skip_objs + all_deformer,
            "format": "JSON",
            "path": directory,
            "vertexConnections": True if cmds.nodeType(obj) == "mesh" else False,
            "weightTolerance": 0.0,
            "attribute": (
                DEFORMER_TYPE_TABLE[deformer_type]
                if deformer_type in DEFORMER_TYPE_TABLE
                else []
            ),
            "defaultValue": 0 if deformer_type == "skinCluster" else 1,
        }
        cmds.deformerWeights(file_name, **flags)
        with open(path, "r") as f:
            data = json.load(f)

        # weight 수정을 하지않는 경우 제대로 export 되지 않음. 수동으로 추가.
        if "weights" not in data["deformerWeight"]:
            data["deformerWeight"]["weights"] = [
                {
                    "deformer": deformer,
                    "source": "baseLayer",
                    "shape": obj,
                    "layer": 0,
                    "defaultValue": 1.0,
                    "size": 0,
                    "max": 0,
                }
            ]
        with open(path, "w") as f:
            json.dump(data, f, indent=2)


def export_weights_to_directory(directory, deformers):
    if not Path(directory).exists():
        logger.info(f"{directory} 가 존재하지 않습니다.")

    for deformer in deformers:
        deformer_type = cmds.nodeType(deformer)
        if deformer_type not in DEFORMER_TYPE_TABLE:
            logger.warning(f"{deformer_type} 을 지원하지 않습니다.")
            continue
        objs = cmds.deformer(deformer, geometry=True, query=True) or []
        for obj in objs:
            file_name = f"{obj}__{deformer}__{deformer_type}.json"
            export_weight((Path(directory) / file_name).as_posix(), deformer)


def import_weight(file_path):
    directory = Path(file_path).parent
    file_name = Path(file_path).name
    with open(file_path, "r") as f:
        data = json.load(f)

    deformer_name = data["deformerWeight"]["deformers"][0]["name"]
    deformer_type = data["deformerWeight"]["deformers"][0]["type"]
    shape_name = data["deformerWeight"]["shapes"][0]["name"]

    if not cmds.objExists(shape_name):
        return logger.warning(f"{shape_name} 가 존재하지 않습니다.")

    flags = {
        "im": True,
        "deformer": deformer_name,
        "format": "JSON",
        "path": directory,
        "attribute": DEFORMER_TYPE_TABLE[deformer_type],
    }
    # skincluster 의 경우 없으면 생성하는것이 작업하기 편함.
    try:
        if deformer_type == "skinCluster" and not cmds.objExists(deformer_name):
            joints = [d["source"] for d in data["deformerWeight"]["weights"]]
            deformer_name = bind_skincluster(shape_name, joints, deformer_name)
            logger.info(f"Create {deformer_name}")
    except Exception as e:
        return logger.warning(
            f"skinCluster 생성 실패: `{deformer_name}` {joints + [shape_name]}"
        )

    cmds.deformerWeights(file_name, **flags)

    # 이유를 모르겠지만 attribute flag 가 작동하지 않음. 수동으로 적용.
    for attr in data["deformerWeight"]["deformers"][0]["attributes"]:
        if "multi" in attr:
            multi_indexes = attr["multi"].split(" ")
            value_indexes = attr["value"].split(" ")
            for m_i, v_i in zip(multi_indexes, value_indexes):
                cmds.setAttr(f"{deformer_name}.{attr['name']}[{m_i}]", float(v_i))
        else:
            cmds.setAttr(f"{deformer_name}.{attr['name']}", float(attr["value"]))
    logger.info(f"Imported {deformer_name} weights")


def import_weights_from_directory(directory):
    path = Path(directory)
    if not path.exists():
        logger.info(f"{directory} 가 존재하지 않습니다.")

    for f in path.iterdir():
        if f.suffix != ".json":
            continue
        import_weight(f.as_posix())


# endregion


# region deformerChain
def get_deformer_chain(geometry):
    return cmds.deformableShape(geometry, chain=True) or []


def set_deformer_chain(geometry, chain):
    new_chain = get_deformer_chain(geometry)

    check = False
    if len(chain) != len(new_chain):
        logger.warning(f"deformer 가 서로 맞지 않습니다. {chain} {new_chain}")
        check = True

    for deformer in chain:
        if deformer not in new_chain:
            logger.warning(f"{deformer} 가 현재 {new_chain} 에 존재하지 않습니다.")
            check = True

    if check:
        return

    for i in range(len(chain)):
        if chain[i] != new_chain[i]:
            cmds.reorderDeformers(new_chain[i], chain[i], geometry)
            new_chain = get_deformer_chain(geometry)


# endregion
