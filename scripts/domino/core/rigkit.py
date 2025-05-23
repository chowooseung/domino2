# maya
from maya import cmds
from maya.api import OpenMaya as om

# built-ins
from pathlib import Path

# domino
from domino.core.utils import logger
from domino.core import FCurve, Transform


# region IK
def ik_sc():
    pass


def ik_2jnt(
    parent,
    name,
    initial_matrix_plugs,
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
    decom_m0 = cmds.createNode("decomposeMatrix")
    decom_m1 = cmds.createNode("decomposeMatrix")
    decom_m2 = cmds.createNode("decomposeMatrix")

    init_translate1_plug = f"{decom_m1}.outputTranslate"
    init_translate2_plug = f"{decom_m2}.outputTranslate"

    cmds.connectAttr(initial_matrix_plugs[0], f"{decom_m0}.inputMatrix")
    cmds.connectAttr(initial_matrix_plugs[1], f"{decom_m1}.inputMatrix")
    cmds.connectAttr(initial_matrix_plugs[2], f"{decom_m2}.inputMatrix")

    # set initialize joint orient
    cmds.connectAttr(f"{decom_m0}.outputRotate", f"{joints[0]}.jointOrient")
    cmds.connectAttr(f"{decom_m1}.outputRotate", f"{joints[1]}.jointOrient")
    cmds.connectAttr(f"{decom_m2}.outputRotate", f"{joints[2]}.jointOrient")

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
    ikh = cmds.ikHandle(
        startJoint=joints[0], endEffector=joints[2], solver="ikRPsolver", name=name
    )[0]
    cmds.parent(ikh, parent)
    cmds.poleVectorConstraint(pole_vector, ikh)
    cmds.setAttr(f"{ikh}.t", 0, 0, 0)
    cmds.setAttr(f"{ikh}.r", 0, 0, 0)
    cmds.setAttr(f"{ikh}.v", 0)

    ik_driver_distance = cmds.createNode("distanceBetween")
    cmds.connectAttr(
        f"{ik_pos_driver}.worldMatrix[0]", f"{ik_driver_distance}.inMatrix1"
    )
    cmds.connectAttr(f"{ik_driver}.worldMatrix[0]", f"{ik_driver_distance}.inMatrix2")

    cmds.connectAttr(f"{ik_driver_distance}.distance", f"{parent}.tx")
    clamp0 = cmds.createNode("clamp")
    cmds.connectAttr(f"{ik_driver_distance}.distance", f"{clamp0}.inputR")
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
    cmds.connectAttr(f"{ik_driver_distance}.distance", f"{clamp1}.inputR")
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

    cmds.connectAttr(f"{bta1}.output", f"{ikh}.tx")


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
    volume_attr,
    volume_multiple,
    output_u_value_plugs,
    negate_plug=None,
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
    main_crv, main_offset_crv = cmds.offsetCurve(
        f"{surface}.v[1]",
        name=f"{surface}_mainIkCrv",
        constructionHistory=True,
        rn=False,
        connectBreaks=2,
        stitch=True,
        cutLoop=True,
        cutRadius=0,
        distance=0,
        tolerance=0.01,
        subdivisionDensity=5,
        useGivenNormal=False,
    )
    main_crv = cmds.parent(main_crv, parent)[0]
    curve_from_surface = cmds.listConnections(
        f"{main_offset_crv}.inputCurve", source=True, destination=False
    )[0]
    cmds.connectAttr(f"{shape}.local", f"{curve_from_surface}.inputSurface", force=1)
    up_crv, up_offset_crv = cmds.offsetCurve(
        f"{surface}.v[0]",
        name=f"{surface}_upIkCrv",
        constructionHistory=True,
        rn=False,
        connectBreaks=2,
        stitch=True,
        cutLoop=True,
        cutRadius=0,
        distance=0,
        tolerance=0.01,
        subdivisionDensity=5,
        useGivenNormal=False,
    )
    up_crv = cmds.parent(up_crv, parent)[0]
    curve_from_surface = cmds.listConnections(
        f"{up_offset_crv}.inputCurve", source=True, destination=False
    )[0]
    cmds.connectAttr(f"{shape}.local", f"{curve_from_surface}.inputSurface", force=1)

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
    main_orig_uniform_crv, main_orig_uniform_offset_crv = cmds.offsetCurve(
        f"{orig}.v[1]",
        name=f"{surface}_uniformMainCrvOrig",
        constructionHistory=True,
        rn=False,
        connectBreaks=2,
        stitch=True,
        cutLoop=True,
        cutRadius=0,
        distance=0,
        tolerance=0.01,
        subdivisionDensity=5,
        useGivenNormal=False,
    )
    main_orig_uniform_crv = cmds.parent(main_orig_uniform_crv, parent)[0]
    curve_from_surface = cmds.listConnections(
        f"{main_orig_uniform_offset_crv}.inputCurve", source=True, destination=False
    )[0]
    cmds.connectAttr(f"{orig}.local", f"{curve_from_surface}.inputSurface", force=1)
    main_orig_rebuild_curve = cmds.createNode("rebuildCurve")
    cmds.connectAttr(
        f"{curve_from_surface}.outputCurve", f"{main_orig_rebuild_curve}.inputCurve"
    )
    cmds.connectAttr(
        f"{main_orig_rebuild_curve}.outputCurve",
        f"{main_orig_uniform_crv}.create",
        force=True,
    )
    cmds.delete(main_orig_uniform_offset_crv)
    up_orig_uniform_crv, up_orig_uniform_offset_crv = cmds.offsetCurve(
        f"{orig}.v[0]",
        name=f"{surface}_uniformUpCrvOrig",
        constructionHistory=True,
        rn=False,
        connectBreaks=2,
        stitch=True,
        cutLoop=True,
        cutRadius=0,
        distance=0,
        tolerance=0.01,
        subdivisionDensity=5,
        useGivenNormal=False,
    )
    up_orig_uniform_crv = cmds.parent(up_orig_uniform_crv, parent)[0]
    curve_from_surface = cmds.listConnections(
        f"{up_orig_uniform_offset_crv}.inputCurve", source=True, destination=False
    )[0]
    cmds.connectAttr(f"{orig}.local", f"{curve_from_surface}.inputSurface", force=1)
    up_orig_rebuild_curve = cmds.createNode("rebuildCurve")
    cmds.connectAttr(
        f"{curve_from_surface}.outputCurve", f"{up_orig_rebuild_curve}.inputCurve"
    )
    cmds.connectAttr(
        f"{up_orig_rebuild_curve}.outputCurve",
        f"{up_orig_uniform_crv}.create",
        force=True,
    )
    cmds.delete(up_orig_uniform_offset_crv)

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
    plug = cmds.listConnections(
        f"{main_offset_crv}.inputCurve", source=True, destination=False, plugs=True
    )[0]
    cmds.connectAttr(plug, f"{main_rebuild_curve}.inputCurve")
    main_uniform_crv = cmds.circle(
        name=f"{surface}_uniformMainCrv", constructionHistory=False
    )
    main_uniform_crv = cmds.parent(main_uniform_crv, parent)[0]
    cmds.connectAttr(f"{main_rebuild_curve}.outputCurve", f"{main_uniform_crv}.create")

    up_rebuild_curve = cmds.createNode("rebuildCurve")
    plug = cmds.listConnections(
        f"{up_offset_crv}.inputCurve", source=True, destination=False, plugs=True
    )[0]
    cmds.connectAttr(plug, f"{up_rebuild_curve}.inputCurve")
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
    result_parent = parent
    c = 0
    last_index = len(main_ik_joints) - 1
    md = cmds.createNode("multiplyDivide")
    cmds.setAttr(f"{md}.input1", 1, 0, 0)
    cmds.connectAttr(negate_plug, f"{md}.input2X")
    cmds.connectAttr(negate_plug, f"{md}.input2Y")
    cmds.connectAttr(negate_plug, f"{md}.input2Z")
    negate_primary_vector_plug = f"{md}.output"
    md = cmds.createNode("multiplyDivide")
    cmds.setAttr(f"{md}.input1", -1, 0, 0)
    cmds.connectAttr(negate_plug, f"{md}.input2X")
    cmds.connectAttr(negate_plug, f"{md}.input2Y")
    cmds.connectAttr(negate_plug, f"{md}.input2Z")
    negate_primary_last_vector_plug = f"{md}.output"
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
        cmds.setAttr(f"{aim_m}.secondaryInputAxis", 0, 1, 0)
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
        cmds.setAttr(f"{aim_m}.secondaryInputAxis", 0, 1, 0)
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
        cmds.setAttr(f"{aim_m}.secondaryInputAxis", 0, 1, 0)
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

    # volume
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

    for multiple, output in zip(volume_multiple, outputs):
        cmds.addAttr(
            output, longName="volume_multiple", attributeType="float", keyable=True
        )
        cmds.setAttr(f"{output}.volume_multiple", multiple)
        multiply = cmds.createNode("multiply")
        cmds.connectAttr(f"{output}.volume_multiple", f"{multiply}.input[0]")
        cmds.connectAttr(volume_ratio_attr, f"{multiply}.input[1]")
        cmds.connectAttr(volume_attr, f"{multiply}.input[2]")
        cmds.connectAttr(stretch_squash_attr, f"{multiply}.input[3]")

        pma = cmds.createNode("plusMinusAverage")
        cmds.setAttr(f"{pma}.operation", 2)
        cmds.setAttr(f"{pma}.input1D[0]", 1)
        cmds.connectAttr(f"{multiply}.output", f"{pma}.input1D[1]")

        cmds.connectAttr(f"{pma}.output1D", f"{output}.sx")
        cmds.connectAttr(f"{pma}.output1D", f"{output}.sy")
        cmds.connectAttr(f"{pma}.output1D", f"{output}.sz")

    return surface, outputs


# endregion


# region bezier - nurbs layer
# endregion


# region bezier - nurbs layer
# endregion


# region blendshape transfer / import / export
def transfer_blendshape(source, destination, bs, smooth=0):
    check = False
    if not cmds.objExists(source):
        cmds.warning(f"{source} 가 존재하지 않습니다.")
        check = True
    if not cmds.objExists(destination):
        cmds.warning(f"{destination} 가 존재하지 않습니다.")
        check = True
    if not cmds.objExists(bs):
        cmds.warning(f"{bs} 가 존재하지 않습니다.")
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

    # rename
    transferred_bs = cmds.blendShape(destination)[0]
    cmds.rename(bs, "TEMPBLENDSHAPE")
    transferred_bs = cmds.rename(transferred_bs, bs)
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
            transferred_bs,
            edit=True,
            target=(destination, i, interface_mesh, 1),
            weight=(i, 0),
        )
        cmds.aliasAttr(attr, f"{transferred_bs}.w[{i}]")
        connections = cmds.listConnections(
            f"{interface_mesh}Shape.worldMesh[0]", connections=True, plugs=True
        )
        cmds.disconnectAttr(connections[0], connections[1])
        for inbetween_attr in inbetween_attrs[i]:
            value = int(inbetween_attr[-4:-1]) / 1000
            cmds.setAttr(f"{bs}.{attr}", value)
            cmds.blendShape(
                transferred_bs,
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
                        f"{transferred_bs}.{source_attr}",
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
                    f"{transferred_bs}.{destination_attr}",
                )
            else:
                plug = cmds.listConnections(
                    f"{bs}.{attr}", source=True, destination=False, plugs=True
                )[0]
                cmds.connectAttr(plug, f"{transferred_bs}.{attr}")

    # remove
    cmds.proximityWrap(p_wrap, edit=True, removeDrivers=source)
    cmds.delete(interface_mesh)


def export_blendshape(directory, bs):
    directory_path = Path(directory)
    mesh = cmds.deformer(bs, geometry=True, query=True)[0]

    plug = cmds.listConnections(f"{bs}.originalGeometry[0]", plugs=True)[0]
    shape = plug.split(".")[0]
    new_transform = cmds.duplicate(shape)
    shape = cmds.listRelatives(new_transform, shapes=True, noIntermediate=True)
    if shape:
        cmds.delete(shape)
    orig_shape = cmds.ls(new_transform, dagObjects=True, intermediateObjects=True)[0]
    cmds.setAttr(f"{orig_shape}.intermediateObject", 0)

    new_transform = cmds.rename(new_transform, f"{bs}_shp")
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
    logger.indo(f"Exported original mesh to `{original_obj_path}`")
    cmds.delete(new_transform)

    shp_path = directory_path / f"{bs}.shp"
    cmds.blendShape(bs, edit=True, export=shp_path)
    logger.indo(f"Exported blendShape(.shp) to `{shp_path}`")


def import_blendshape(directory):
    directory_path = Path(directory)

    obj_files = directory_path.glob("*__*.obj")
    for obj in obj_files:
        name, _ = obj.name.split(".")
        mesh, bs = name.split("__")
        for p in directory_path.glob(f"{bs}.shp"):
            if not cmds.objExists(mesh):
                cmds.warning(f"{mesh} 가 존재하지 않습니다.")
                continue
            if not cmds.objExists(bs):
                cmds.blendShape(mesh, name=bs)
            cmds.blendShape(bs, edit=True, ip=p)


# endregion


# region deformerWeight import / export
FILETYPE = {"xml": "XML", "json": "JSON"}


def export_weights(directory, objs, file_type="xml"):
    for obj in objs:
        deformers = cmds.findDeformers(obj) or []
        for deformer in deformers:
            cmds.deformerWeights(
                f"{obj}__{deformer}.{file_type}",
                export=True,
                deformer=deformer,
                format=FILETYPE[file_type],
                path=directory,
            )


def import_weights(directory):
    path = Path(directory)

    for f in path.iterdir():
        try:
            name, ext = f.name.split(".")
            _, deformer = name.split("__")
        except:
            continue
        if cmds.objExists(deformer):
            cmds.deformerWeights(
                f.name,
                im=True,
                deformer=deformer,
                format=FILETYPE[ext],
                path=directory,
            )
            logger.info(f"Imported {deformer} weights")
        else:
            cmds.warning(
                f"{deformer} 가 존재하지 않습니다. weights 를 가져오는데 실패하였습니다."
            )


# endregion


# region deformerChain
def get_deformer_chain(geometry):
    return cmds.deformableShape(geometry, chain=True) or []


def set_deformer_chain(geometry, chain):
    new_chain = get_deformer_chain(geometry)

    check = False
    if len(chain) != len(new_chain):
        cmds.warning(f"deformer 가 서로 맞지 않습니다. {chain} {new_chain}")

    for deformer in chain:
        if deformer not in new_chain:
            cmds.warning(f"{deformer} 가 현재 {new_chain} 에 존재하지 않습니다.")

    if check:
        return

    for i in range(len(chain)):
        if chain[i] != new_chain[i]:
            cmds.reorderDeformers(new_chain[i], chain[i], geometry)
            new_chain = get_deformer_chain(geometry)


# endregion
