# maya
from maya import cmds
from maya import mel
from maya.api import OpenMaya as om

# Qt
from PySide6 import QtWidgets, QtCore, QtGui

# built-ins
from pathlib import Path
import copy
import json
import math
import re

# domino
from domino.core import Transform, left, right
from domino.core.utils import logger

PSD_MANAGER = "psd_manager"
PSD_SETS = "psd_sets"
L_MIRROR_TOKEN = f"_{left}"
R_MIRROR_TOKEN = f"_{right}"

## TODO : maya 2026.2 에서 parallel 에서 blendshape 을 수정중이었다면
## undo 시 maya 가 crash 나는 문제가 있음.
## 이것이 maya 의 버그인지 코드의 문제인지 모르겠지만 maya 의 버그일 가능성이 높음.
## DG 에서는 문제가 없기 때문.
## 해결방법을 찾으면 수정한다.


def initialize():
    if not cmds.objExists(PSD_MANAGER):
        cmds.createNode("transform", name=PSD_MANAGER)
        cmds.addAttr(PSD_MANAGER, longName="_data", dataType="string")
        cmds.setAttr(f"{PSD_MANAGER}._data", json.dumps({}), type="string")


def get_data():
    data = json.loads(cmds.getAttr(f"{PSD_MANAGER}._data"))

    for intp, intp_data in copy.deepcopy(data).items():
        data[intp]["regularization"] = cmds.getAttr(f"{intp}.regularization")
        data[intp]["output_smoothing"] = cmds.getAttr(f"{intp}.outputSmoothing")
        data[intp]["interpolation"] = cmds.getAttr(f"{intp}.interpolation")
        data[intp]["allow_negative_weights"] = cmds.getAttr(
            f"{intp}.allowNegativeWeights"
        )
        data[intp]["enable_rotation"] = cmds.getAttr(f"{intp}.enableRotation")
        data[intp]["enable_translation"] = cmds.getAttr(f"{intp}.enableTranslation")
        data[intp]["driver_twist_axis"] = cmds.getAttr(
            f"{intp}.driver[0].driverTwistAxis"
        )
        data[intp]["driver_euler_twist"] = cmds.getAttr(
            f"{intp}.driver[0].driverEulerTwist"
        )

        for pose in intp_data["pose"].keys():
            names = cmds.poseInterpolator(intp, query=True, poseNames=True)
            indexes = cmds.poseInterpolator(intp, query=True, index=True)
            index = indexes[names.index(pose)]

            data[intp]["pose"][pose]["is_independent"] = cmds.getAttr(
                f"{intp}.pose[{index}].isIndependent"
            )
            data[intp]["pose"][pose]["pose_rotation_falloff"] = cmds.getAttr(
                f"{intp}.pose[{index}].poseRotationFalloff"
            )
            data[intp]["pose"][pose]["pose_translation_falloff"] = cmds.getAttr(
                f"{intp}.pose[{index}].poseTranslationFalloff"
            )
            data[intp]["pose"][pose]["pose_type"] = cmds.getAttr(
                f"{intp}.pose[{index}].poseType"
            )
            data[intp]["pose"][pose]["pose_falloff"] = cmds.getAttr(
                f"{intp}.pose[{index}].poseFalloff"
            )
            data[intp]["pose"][pose]["is_enabled"] = cmds.getAttr(
                f"{intp}.pose[{index}].isEnabled"
            )
    return data


def set_data(data):
    cmds.setAttr(f"{PSD_MANAGER}._data", json.dumps(data), type="string")


def add_intp(driver, controller, description="", swing=True, blendshape=""):
    if not cmds.objExists(driver):
        return logger.warning(f"`{driver}` 존재하지 않습니다.")
    if not cmds.objExists(controller):
        return logger.warning(f"`{controller}` 존재하지 않습니다.")
    if blendshape and not cmds.objExists(blendshape):
        return logger.warning(f"`{blendshape}` 존재하지 않습니다.")
    intp_name = "_".join([x for x in [driver, description, "intp"] if x])
    if cmds.objExists(intp_name):
        return logger.warning(f"{intp_name} 이미 존재합니다.")

    initialize()

    # new interpolator
    cmds.select(driver)
    interpolator = f"|{cmds.poseInterpolator(name=intp_name)[0]}"
    interpolator = cmds.parent(interpolator, PSD_MANAGER)[0]
    interpolator = cmds.listRelatives(interpolator, shapes=True, fullPath=True)[0]
    cmds.setAttr(f"{interpolator}.interpolation", 1)
    cmds.addAttr(intp_name, longName="description", dataType="string")
    cmds.setAttr(f"{intp_name}.description", description, type="string")

    if swing:  # swing
        index = cmds.poseInterpolator(interpolator, edit=True, addPose="neutralSwing")
        cmds.setAttr(f"{interpolator}.pose[{index}].poseType", 1)
    else:  # twist
        index = cmds.poseInterpolator(interpolator, edit=True, addPose="neutralTwist")
        cmds.setAttr(f"{interpolator}.pose[{index}].poseType", 2)

    # add data
    neutral_str = "neutralSwing" if swing else "neutralTwist"
    pose_type = 1 if swing else 2
    intp_data = {
        "is_blendshape": True if blendshape else False,
        "description": description,
        "controller": controller,
        "driver": driver,
        "driven": blendshape if blendshape else [],
        "pose": {
            neutral_str: {
                "is_independent": False,
                "pose_rotation_falloff": 180.0,
                "pose_translation_falloff": 0.0,
                "pose_type": pose_type,
                "pose_falloff": 1.0,
                "is_enabled": True,
                "t": [0, 0, 0],
                "r": [0, 0, 0],
            }
        },
        "swing": swing,
        "regularization": cmds.getAttr(f"{intp_name}.regularization"),
        "output_smoothing": cmds.getAttr(f"{intp_name}.outputSmoothing"),
        "interpolation": cmds.getAttr(f"{intp_name}.interpolation"),
        "allow_negative_weights": cmds.getAttr(f"{intp_name}.allowNegativeWeights"),
        "enable_rotation": cmds.getAttr(f"{intp_name}.enableRotation"),
        "enable_translation": cmds.getAttr(f"{intp_name}.enableTranslation"),
        "driver_twist_axis": cmds.getAttr(f"{intp_name}.driver[0].driverTwistAxis"),
        "driver_euler_twist": cmds.getAttr(f"{intp_name}.driver[0].driverEulerTwist"),
    }
    data = get_data()
    data[intp_name] = intp_data

    set_data(data)

    return intp_name


def add_pose(intp_name, pose):
    if not cmds.objExists(intp_name):
        return logger.warning(f"`{intp_name}` 존재하지 않습니다.")
    interpolator = cmds.listRelatives(intp_name, shapes=True)[0]

    data = get_data()

    if data[intp_name]["is_blendshape"] and not cmds.objExists(
        data[intp_name]["driven"]
    ):
        return logger.warning(f"`{data[intp_name]['driven']}` 존재하지 않습니다.")

    if pose in data[intp_name]["pose"] or pose in (
        cmds.poseInterpolator(interpolator, query=True, poseNames=True) or []
    ):
        return logger.warning(f"{pose} 이미 존재합니다.")

    data[intp_name]["pose"][pose] = {
        "t": cmds.getAttr(f"{data[intp_name]['controller']}.t")[0],
        "r": cmds.getAttr(f"{data[intp_name]['controller']}.r")[0],
    }

    pose_type = 1 if data[intp_name]["swing"] else 2
    index = cmds.poseInterpolator(interpolator, edit=True, addPose=pose)
    cmds.setAttr(f"{interpolator}.pose[{index}].poseType", pose_type)
    data[intp_name]["pose"][pose]["is_independent"] = cmds.getAttr(
        f"{intp_name}.pose[{index}].isIndependent"
    )
    data[intp_name]["pose"][pose]["pose_rotation_falloff"] = cmds.getAttr(
        f"{intp_name}.pose[{index}].poseRotationFalloff"
    )
    data[intp_name]["pose"][pose]["pose_translation_falloff"] = cmds.getAttr(
        f"{intp_name}.pose[{index}].poseTranslationFalloff"
    )
    data[intp_name]["pose"][pose]["pose_type"] = cmds.getAttr(
        f"{intp_name}.pose[{index}].poseType"
    )
    data[intp_name]["pose"][pose]["pose_falloff"] = cmds.getAttr(
        f"{intp_name}.pose[{index}].poseFalloff"
    )
    data[intp_name]["pose"][pose]["is_enabled"] = cmds.getAttr(
        f"{intp_name}.pose[{index}].isEnabled"
    )
    cmds.setAttr(f"{interpolator}.pose[{index}].isEnabled", 0)

    if data[intp_name]["is_blendshape"]:
        # blendshape logic
        blendshape = data[intp_name]["driven"]
        name = f"{intp_name}__{pose}"
        alias = cmds.aliasAttr(blendshape, query=True) or []
        if name in alias:
            cmds.connectAttr(
                f"{interpolator}.output[{index}]", f"{blendshape}.{name}", force=True
            )
        elif not name in alias:
            geometry = cmds.blendShape(blendshape, query=True, geometry=True)[0]
            next_index = cmds.blendShape(blendshape, query=True, weightCount=True)

            temp_geo = cmds.duplicate(geometry)[0]
            cmds.blendShape(
                blendshape,
                edit=True,
                target=(geometry, next_index, temp_geo, 1),
                weight=(next_index, 0),
            )
            cmds.delete(temp_geo)
            cmds.blendShape(blendshape, edit=True, resetTargetDelta=(0, next_index))
            mel.eval(f"blendShapeRenameTargetAlias {blendshape} {next_index} {name};")

            cmds.connectAttr(
                f"{interpolator}.output[{index}]", f"{blendshape}.{name}", force=True
            )
    else:
        # controller logic
        blend_matrices = [f"{k}_bm" for k in data[intp_name]["driven"]]
        driven_m = {}
        for driven, blend_m in zip(data[intp_name]["driven"], blend_matrices):
            driven_world_m = om.MMatrix(
                cmds.xform(driven, query=True, matrix=True, worldSpace=True)
            )
            psd = cmds.listRelatives(driven, parent=True)[0]
            parent = cmds.listRelatives(psd, parent=True)
            parent_inverse_m = om.MMatrix()
            if parent:
                parent_m = om.MMatrix(
                    cmds.xform(parent[0], query=True, matrix=True, worldSpace=True)
                )
                parent_inverse_m = parent_m.inverse()
            driven_local_m = driven_world_m * parent_inverse_m
            cmds.setAttr(f"{driven}.t", 0, 0, 0)
            cmds.setAttr(f"{driven}.r", 0, 0, 0)
            cmds.setAttr(f"{driven}.s", 1, 1, 1)

            driven_m[driven] = list(driven_local_m)
        data[intp_name]["pose"][pose].update({"driven": driven_m})

        for driven in data[intp_name]["driven"]:
            blend_m = f"{driven}_bm"
            cmds.connectAttr(
                f"{interpolator}.output[{index}]",
                f"{blend_m}.target[{index}].weight",
            )
            cmds.setAttr(
                f"{blend_m}.target[{index}].targetMatrix",
                driven_m[driven],
                type="matrix",
            )
    cmds.setAttr(f"{interpolator}.pose[{index}].isEnabled", 1)
    set_data(data)


def add_driven(intp_name, driven):
    if not cmds.objExists(intp_name):
        return logger.warning(f"`{intp_name}` 존재하지 않습니다.")
    interpolator = cmds.listRelatives(intp_name, shapes=True)[0]

    data = get_data()

    grp = f"{driven}_grp"
    blend_m = f"{driven}_bm"

    if driven in data[intp_name]["driven"]:
        return logger.warning(f"'{driven}' 이미 존재합니다.")

    data[intp_name]["driven"].append(driven)

    blend_m = (
        cmds.createNode("blendMatrix", name=blend_m)
        if not cmds.objExists(blend_m)
        else blend_m
    )

    if not cmds.objExists(grp):
        parent = cmds.listRelatives(driven, parent=True)
        grp = cmds.createNode(
            "transform", name=grp, parent=parent[0] if parent else None
        )
        cmds.parent(driven, grp)

        decom_m = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{blend_m}.outputMatrix", f"{decom_m}.inputMatrix")
        cmds.connectAttr(f"{decom_m}.outputTranslate", f"{grp}.t")
        cmds.connectAttr(f"{decom_m}.outputRotate", f"{grp}.r")

    for pose in data[intp_name]["pose"].keys():
        if pose in ["neutralSwing", "neutralTwist"]:
            continue
        names = cmds.poseInterpolator(interpolator, query=True, poseNames=True)
        indexes = cmds.poseInterpolator(interpolator, query=True, index=True)
        index = indexes[names.index(pose)]

        data[intp_name]["pose"][pose]["driven"][driven] = list(om.MMatrix())
        cmds.connectAttr(
            f"{interpolator}.output[{index}]", f"{blend_m}.target[{index}].weight"
        )
        m = [x for x in om.MMatrix()]
        cmds.setAttr(f"{blend_m}.target[{index}].targetMatrix", m, type="matrix")
    set_data(data)


def update_pose(intp_name, pose):
    if not cmds.objExists(intp_name):
        return logger.warning(f"`{intp_name}` 존재하지 않습니다.")
    interpolator = cmds.listRelatives(intp_name, shapes=True)[0]

    data = get_data()

    if pose not in data[intp_name]["pose"]:
        return logger.warning(f"존재하지 않습니다. '{pose}'")

    controller = data[intp_name]["controller"]
    data[intp_name]["pose"][pose]["t"] = cmds.getAttr(f"{controller}.t")[0]
    data[intp_name]["pose"][pose]["r"] = cmds.getAttr(f"{controller}.r")[0]

    indexes = [
        x.split("[")[1].split("]")[0]
        for x in cmds.listAttr(f"{interpolator}.pose", multi=True)
        if "." not in x
    ]
    names = cmds.poseInterpolator(interpolator, query=True, poseNames=True)
    index = indexes[names.index(pose)]

    if not data[intp_name]["is_blendshape"]:
        # controller logic
        driven_m = {}
        for driven in data[intp_name]["driven"]:
            blend_m = f"{driven}_bm"
            driven_world_m = om.MMatrix(
                cmds.xform(driven, query=True, matrix=True, worldSpace=True)
            )
            grp = cmds.listRelatives(driven, parent=True)[0]
            parent = cmds.listRelatives(grp, parent=True)
            parent_inverse_m = om.MMatrix()
            if parent:
                parent_m = om.MMatrix(
                    cmds.xform(parent[0], query=True, matrix=True, worldSpace=True)
                )
                parent_inverse_m = parent_m.inverse()
            driven_local_m = driven_world_m * parent_inverse_m

            driven_m[driven] = list(driven_local_m)
            cmds.setAttr(
                f"{blend_m}.target[{index}].targetMatrix", driven_local_m, type="matrix"
            )
            cmds.setAttr(f"{driven}.t", 0, 0, 0)
            cmds.setAttr(f"{driven}.r", 0, 0, 0)
            cmds.setAttr(f"{driven}.s", 1, 1, 1)
        data[intp_name]["pose"][pose].update({"driven": driven_m})
    cmds.poseInterpolator(interpolator, edit=True, updatePose=pose)
    set_data(data)


def remove_intp(intp_name):
    if not cmds.objExists(intp_name):
        return logger.warning(f"`{intp_name}` 존재하지 않습니다.")

    data = get_data()

    if data[intp_name]["is_blendshape"]:
        temp = cmds.aliasAttr(data[intp_name]["driven"], query=True)
        if temp:
            alias = temp[::2]
            for pose in data[intp_name]["pose"].keys():
                if pose in ["neutralSwing", "neutralTwist"]:
                    continue
                name = f"{intp_name}__{pose}"
                if name in alias:
                    index = alias.index(name)
                    mel.eval(
                        f"blendShapeDeleteTargetGroup {data[intp_name]['driven']} {index};"
                    )
        cmds.delete(intp_name)
    else:
        delete_list = []
        for driven in data[intp_name]["driven"]:
            grp = f"{driven}_grp"
            parent = cmds.listRelatives(grp, parent=True)
            if parent:
                cmds.parent(driven, parent[0])
            else:
                cmds.parent(driven, world=True)
            cmds.xform(driven, matrix=om.MMatrix(), worldSpace=False)

            delete_list.append(grp)

        cmds.delete(
            [intp_name] + delete_list + [f"{k}_bm" for k in data[intp_name]["driven"]]
        )

    del data[intp_name]

    set_data(data)
    if not data:
        cmds.delete(PSD_MANAGER)


def remove_pose(intp_name, pose):
    if not cmds.objExists(intp_name):
        return logger.warning(f"`{intp_name}` 존재하지 않습니다.")
    interpolator = cmds.listRelatives(intp_name, shapes=True)[0]

    data = get_data()

    if pose not in data[intp_name]["pose"]:
        return logger.warning(f"`{pose}` 존재하지 않습니다.")

    if pose not in cmds.poseInterpolator(interpolator, query=True, poseNames=True):
        return logger.warning(f"`{pose}` 존재하지 않습니다.")

    index = cmds.poseInterpolator(interpolator, edit=True, deletePose=pose)
    if data["is_blendshape"]:
        temp = cmds.aliasAttr(data[intp_name]["driven"], query=True)
        alias = temp[::2]
        name = f"{intp_name}__{pose}"
        if name in alias:
            index = alias.index(name)
            mel.eval(
                f"blendShapeDeleteTargetGroup {data[intp_name]['driven']} {index};"
            )
    else:
        for driven in data[intp_name]["driven"]:
            blend_m = f"{driven}_bm"
            cmds.removeMultiInstance(f"{blend_m}.target[{index}]")
    del data[intp_name]["pose"][pose]

    set_data(data)


def remove_driven(intp_name, driven):
    if not cmds.objExists(intp_name):
        return logger.warning(f"`{intp_name}` 존재하지 않습니다.")

    data = get_data()

    if data["is_blendshape"]:
        return

    grp = f"{driven}_grp"
    blend_m = f"{driven}_bm"

    if not cmds.objExists(blend_m):
        return logger.warning(f"Don't exists '{blend_m}'")
    if not cmds.objExists(grp):
        return logger.warning(f"Don't exists '{grp}'")
    if driven not in data[intp_name]["driven"]:
        return logger.warning(f"Don't exists '{driven}' in _data")

    parent = cmds.listRelatives(grp, parent=True)
    if parent:
        cmds.parent(driven, parent[0])
    else:
        cmds.parent(driven, world=True)

    cmds.delete([blend_m, grp])

    data[intp_name]["driven"].remove(driven)
    for v in data[intp_name]["pose"].values():
        del v["driven"][driven]
    set_data(data)


def mirror_intp(intp_name):
    if not cmds.objExists(intp_name):
        return logger.warning(f"`{intp_name}` 존재하지 않습니다.")

    data = get_data()

    if intp_name not in data:
        return logger.warning(f"`{intp_name}` 존재하지 않습니다.")

    driver = cmds.poseInterpolator(intp_name, query=True, drivers=True)[0]

    # target name
    source_side = L_MIRROR_TOKEN if L_MIRROR_TOKEN in intp_name else R_MIRROR_TOKEN
    target_side = R_MIRROR_TOKEN if source_side == L_MIRROR_TOKEN else L_MIRROR_TOKEN

    target_intp_name = intp_name.replace(source_side, target_side)
    target_driver = driver.replace(source_side, target_side)
    target_controller = data[intp_name]["controller"].replace(source_side, target_side)

    if driver == target_driver:
        return logger.warning(f"`{intp_name}` 는 _L, _R 이 맞나요? ")
    if not cmds.objExists(target_driver):
        return logger.warning(f"`{target_driver}` 존재하지 않습니다.")
    if not cmds.objExists(target_controller):
        return logger.warning(f"`{target_controller}` 존재하지 않습니다.")

    # target interpolator
    cmds.select(target_driver)
    for attr in [".tx", ".ty", ".tz", ".rx", ".ry", ".rz"]:
        if not cmds.getAttr(f"{target_controller}{attr}", lock=True):
            cmds.setAttr(f"{target_controller}{attr}", 0)
    interpolator = f"|{cmds.poseInterpolator(name=target_intp_name)[0]}"
    interpolator = cmds.parent(interpolator, PSD_MANAGER)[0]
    interpolator = cmds.listRelatives(interpolator, shapes=True, fullPath=True)[0]
    cmds.setAttr(f"{interpolator}.regularization", data[intp_name]["regularization"])
    cmds.setAttr(f"{interpolator}.outputSmoothing", data[intp_name]["output_smoothing"])
    cmds.setAttr(f"{interpolator}.interpolation", data[intp_name]["interpolation"])
    cmds.setAttr(
        f"{interpolator}.allowNegativeWeights",
        data[intp_name]["allow_negative_weights"],
    )
    cmds.setAttr(f"{interpolator}.enableRotation", data[intp_name]["enable_rotation"])
    cmds.setAttr(
        f"{interpolator}.enableTranslation", data[intp_name]["enable_translation"]
    )
    cmds.setAttr(
        f"{interpolator}.driver[0].driverTwistAxis",
        data[intp_name]["driver_twist_axis"],
    )
    cmds.setAttr(
        f"{interpolator}.driver[0].driverEulerTwist",
        data[intp_name]["driver_euler_twist"],
    )

    if data[intp_name]["swing"]:  # swing
        index = cmds.poseInterpolator(interpolator, edit=True, addPose="neutralSwing")
        cmds.setAttr(f"{interpolator}.pose[{index}].poseType", 1)
    else:  # twist
        index = cmds.poseInterpolator(interpolator, edit=True, addPose="neutralTwist")
        cmds.setAttr(f"{interpolator}.pose[{index}].poseType", 2)

    # target interpolator in _data
    neutral_str = "neutralSwing" if data[intp_name]["swing"] else "neutralTwist"
    pose_type = 1 if data[intp_name]["swing"] else 2
    if data[intp_name]["is_blendshape"]:
        target_driven = data[intp_name]["driven"]
    else:
        target_driven = [
            x.replace(source_side, target_side) for x in data[intp_name]["driven"]
        ]
    target_intp_data = {
        "is_blendshape": data[intp_name]["is_blendshape"],
        "description": data[intp_name]["description"],
        "controller": target_controller,
        "driver": target_driver,
        "driven": target_driven,
        "pose": {
            neutral_str: {
                "is_independent": False,
                "pose_rotation_falloff": 180.0,
                "pose_translation_falloff": 0.0,
                "pose_type": pose_type,
                "pose_falloff": 1.0,
                "is_enabled": True,
                "t": [0, 0, 0],
                "r": [0, 0, 0],
            }
        },
        "swing": data[intp_name]["swing"],
        "regularization": data[intp_name]["regularization"],
        "output_smoothing": data[intp_name]["output_smoothing"],
        "interpolation": data[intp_name]["interpolation"],
        "allow_negative_weights": data[intp_name]["allow_negative_weights"],
        "enable_rotation": data[intp_name]["enable_rotation"],
        "enable_translation": data[intp_name]["enable_translation"],
        "driver_twist_axis": data[intp_name]["driver_twist_axis"],
        "driver_euler_twist": data[intp_name]["driver_euler_twist"],
    }
    data[target_intp_name] = target_intp_data

    source_controller = data[intp_name]["controller"]
    mirror_type = cmds.getAttr(f"{source_controller}.mirror_type")

    data[target_intp_name]["pose"] = copy.deepcopy(data[intp_name]["pose"])
    for pose, pose_data in data[intp_name]["pose"].copy().items():
        # add pose
        # rule is controller attribute
        source_t = data[intp_name]["pose"][pose]["t"]
        source_r = data[intp_name]["pose"][pose]["r"]
        target_t, target_r = Transform.get_mirror_RT(source_t, source_r, mirror_type)
        orig_t = cmds.getAttr(f"{target_controller}.t")[0]
        orig_r = cmds.getAttr(f"{target_controller}.r")[0]
        cmds.setAttr(f"{target_controller}.t", *target_t)
        cmds.setAttr(f"{target_controller}.r", *target_r)
        if pose in ["neutralSwing", "neutralTwist"]:
            index = 0
        else:
            index = cmds.poseInterpolator(interpolator, edit=True, addPose=pose)
        cmds.setAttr(
            f"{interpolator}.pose[{index}].poseType",
            data[intp_name]["pose"][pose]["pose_type"],
        )
        cmds.setAttr(
            f"{interpolator}.pose[{index}].isIndependent",
            data[intp_name]["pose"][pose]["is_independent"],
        )
        cmds.setAttr(
            f"{interpolator}.pose[{index}].poseRotationFalloff",
            data[intp_name]["pose"][pose]["pose_rotation_falloff"],
        )
        if data[intp_name]["pose"][pose]["pose_translation_falloff"]:
            cmds.setAttr(
                f"{interpolator}.pose[{index}].poseTranslationFalloff",
                data[intp_name]["pose"][pose]["pose_translation_falloff"],
            )
        cmds.setAttr(
            f"{interpolator}.pose[{index}].poseFalloff",
            data[intp_name]["pose"][pose]["pose_falloff"],
        )
        cmds.setAttr(
            f"{interpolator}.pose[{index}].isEnabled",
            data[intp_name]["pose"][pose]["is_enabled"],
        )
        cmds.setAttr(f"{target_controller}.t", *orig_t)
        cmds.setAttr(f"{target_controller}.r", *orig_r)

        # add pose in _data
        if pose not in ["neutralSwing", "neutralTwist"]:
            data[target_intp_name]["pose"][pose]["t"] = target_t
            data[target_intp_name]["pose"][pose]["r"] = target_r
        if pose in ["neutralSwing", "neutralTwist"]:
            continue

        # blendshape logic
        if data[intp_name]["is_blendshape"]:
            blendshape = target_driven
            temp = cmds.aliasAttr(blendshape, query=True) or []
            name = f"{target_intp_name}__{pose}"
            if temp:
                alias = temp[::2]
                weights = temp[1::2]

                if name in temp:
                    alias_index = alias.index(f"{target_intp_name}__{pose}")
                    target_index = int(weights[alias_index].split("[")[1].split("]")[0])
                    mel.eval(
                        f"blendShapeDeleteTargetGroup {blendshape} {target_index};"
                    )

                geometry = cmds.blendShape(blendshape, query=True, geometry=True)[0]
                next_index = int(weights[-1].split("[")[1].split("]")[0]) + 1

                alias_index = alias.index(f"{intp_name}__{pose}")
                source_index = int(weights[alias_index].split("[")[1].split("]")[0])

                duplicated = cmds.sculptTarget(
                    blendshape, edit=True, regenerate=True, target=source_index
                )[0]
                temp_geo = cmds.duplicate(duplicated)[0]
                cmds.delete(duplicated)
                cmds.blendShape(
                    blendshape,
                    edit=True,
                    target=(geometry, next_index, temp_geo, 1),
                    weight=(next_index, 0),
                )
                cmds.delete(temp_geo)
                cmds.blendShape(
                    blendshape,
                    edit=True,
                    flipTarget=[(0, next_index)],
                    mirrorDirection=(
                        0 if source_side == L_MIRROR_TOKEN else 1
                    ),  # 0=negative,1=positive
                    symmetrySpace=1,  # 0=topological, 1=object, 2=UV
                    symmetryAxis="x",  # for object
                )

                mel.eval(
                    f"blendShapeRenameTargetAlias {blendshape} {next_index} {name};"
                )
                cmds.connectAttr(
                    f"{interpolator}.output[{index}]",
                    f"{blendshape}.{name}",
                    force=True,
                )
                continue

        # controller logic
        data[target_intp_name]["pose"][pose]["driven"] = {}
        for source_driven in pose_data["driven"].keys():
            # add driven
            target_driven = source_driven.replace(source_side, target_side)
            if not cmds.objExists(target_driven):
                logger.warning(f"'{target_driven}' 존재하지 않습니다.")
                continue

            # add blendMatrix
            target_blend_m = f"{target_driven}_bm"
            if not cmds.objExists(target_blend_m):
                target_blend_m = cmds.createNode("blendMatrix", name=target_blend_m)

            # rule is controller attribute
            driven_mirror_type = cmds.getAttr(f"{source_driven}.mirror_type")

            source_m = data[intp_name]["pose"][pose]["driven"][source_driven]
            m = om.MTransformationMatrix(om.MMatrix(source_m))
            source_t = m.translation(om.MSpace.kWorld)
            quat = m.rotation(om.MSpace.kWorld)
            euler = om.MQuaternion(quat).asEulerRotation()
            source_r = [math.degrees(x) for x in (euler.x, euler.y, euler.z)]
            target_t, target_r = Transform.get_mirror_RT(
                source_t, source_r, driven_mirror_type
            )

            target_m = om.MTransformationMatrix()
            target_m.setTranslation(om.MVector(target_t), om.MSpace.kWorld)
            target_m.setRotation(om.MEulerRotation([math.radians(x) for x in target_r]))

            cmds.setAttr(
                f"{target_blend_m}.target[{index}].targetMatrix",
                target_m.asMatrix(),
                type="matrix",
            )
            cmds.connectAttr(
                f"{interpolator}.output[{index}]",
                f"{target_blend_m}.target[{index}].weight",
            )

            # add driven in _data
            data[target_intp_name]["pose"][pose]["driven"][target_driven] = list(
                target_m.asMatrix()
            )

            # add driven npo
            grp = f"{target_driven}_grp"
            if not cmds.objExists(grp):
                parent = cmds.listRelatives(target_driven, parent=True)
                grp = cmds.createNode(
                    "transform",
                    name=grp,
                    parent=parent[0] if parent else None,
                )
                cmds.parent(target_driven, grp)

                decom_m = cmds.createNode("decomposeMatrix")
                cmds.connectAttr(
                    f"{target_blend_m}.outputMatrix", f"{decom_m}.inputMatrix"
                )
                cmds.connectAttr(f"{decom_m}.outputTranslate", f"{grp}.t")
                cmds.connectAttr(f"{decom_m}.outputRotate", f"{grp}.r")

    set_data(data)


def go_to_pose(intp_name, pose):
    if not cmds.objExists(intp_name):
        return logger.warning(f"`{intp_name}` 존재하지 않습니다.")

    data = get_data()

    if pose == "neutralSwing" or pose == "neutralTwist":
        cmds.setAttr(f"{data[intp_name]['controller']}.t", 0, 0, 0)
        cmds.setAttr(f"{data[intp_name]['controller']}.r", 0, 0, 0)
        return

    if pose not in data[intp_name]["pose"]:
        return logger.warning(f"'{pose}' 존재하지 않습니다.")

    cmds.setAttr(
        f"{data[intp_name]['controller']}.t", *data[intp_name]["pose"][pose]["t"]
    )
    cmds.setAttr(
        f"{data[intp_name]['controller']}.r", *data[intp_name]["pose"][pose]["r"]
    )


def import_psd(file_path):
    path = Path(file_path)
    if not path.exists():
        return logger.warning(f"{file_path} 존재하지 않습니다.")

    with open(file_path, "r") as f:
        data = json.load(f)

    if cmds.objExists(PSD_MANAGER):
        return logger.warning(f"{PSD_MANAGER} 이미 존재합니다.")

    for intp_name, intp_data in data.items():
        # interpolator setup
        add_intp(
            driver=intp_data["driver"],
            controller=intp_data["controller"],
            description=intp_data["description"],
            swing=intp_data["swing"],
            blendshape=intp_data["driven"] if intp_data["is_blendshape"] else "",
        )
        cmds.setAttr(f"{intp_name}.regularization", intp_data["regularization"])
        cmds.setAttr(f"{intp_name}.outputSmoothing", intp_data["output_smoothing"])
        cmds.setAttr(f"{intp_name}.interpolation", intp_data["interpolation"])
        cmds.setAttr(
            f"{intp_name}.allowNegativeWeights", intp_data["allow_negative_weights"]
        )
        cmds.setAttr(f"{intp_name}.enableRotation", intp_data["enable_rotation"])
        cmds.setAttr(f"{intp_name}.enableTranslation", intp_data["enable_translation"])
        cmds.setAttr(
            f"{intp_name}.driver[0].driverTwistAxis", intp_data["driver_twist_axis"]
        )
        cmds.setAttr(
            f"{intp_name}.driver[0].driverEulerTwist", intp_data["driver_euler_twist"]
        )
        # neutral pose setup
        neutral_str = "neutralSwing" if intp_data["swing"] else "neutralTwist"
        neutral_pose_data = intp_data["pose"][neutral_str]
        cmds.setAttr(f"{intp_name}.pose[0].poseType", neutral_pose_data["pose_type"])
        cmds.setAttr(
            f"{intp_name}.pose[0].isIndependent", neutral_pose_data["is_independent"]
        )
        cmds.setAttr(
            f"{intp_name}.pose[0].poseRotationFalloff",
            neutral_pose_data["pose_rotation_falloff"],
        )
        if neutral_pose_data["pose_translation_falloff"]:
            cmds.setAttr(
                f"{intp_name}.pose[0].poseTranslationFalloff",
                neutral_pose_data["pose_translation_falloff"],
            )
        cmds.setAttr(
            f"{intp_name}.pose[0].poseFalloff", neutral_pose_data["pose_falloff"]
        )
        # add driven
        if not intp_data["is_blendshape"]:
            for driven in intp_data["driven"]:
                add_driven(intp_name, driven)

        # pose
        del intp_data["pose"][neutral_str]
        i = 1
        for pose, pose_data in intp_data["pose"].items():
            if pose == "neutralSwing" or pose == "neutralTwist":
                continue
            cmds.setAttr(f"{intp_data['controller']}.t", *pose_data["t"])
            cmds.setAttr(f"{intp_data['controller']}.r", *pose_data["r"])

            # init
            add_pose(intp_name, pose)
            cmds.setAttr(f"{intp_name}.pose[{i}].isEnabled", 0)
            cmds.setAttr(f"{intp_name}.pose[{i}].poseType", pose_data["pose_type"])
            cmds.setAttr(
                f"{intp_name}.pose[{i}].isIndependent", pose_data["is_independent"]
            )
            cmds.setAttr(
                f"{intp_name}.pose[{i}].poseRotationFalloff",
                pose_data["pose_rotation_falloff"],
            )
            if pose_data["pose_translation_falloff"]:
                cmds.setAttr(
                    f"{intp_name}.pose[{i}].poseTranslationFalloff",
                    pose_data["pose_translation_falloff"],
                )
            cmds.setAttr(
                f"{intp_name}.pose[{i}].poseFalloff", pose_data["pose_falloff"]
            )

            # update
            if not intp_data["is_blendshape"]:
                for driven, m in pose_data["driven"].items():
                    cmds.xform(driven, matrix=m, worldSpace=False)
                update_pose(intp_name, pose)

            cmds.setAttr(f"{intp_data['controller']}.t", 0, 0, 0)
            cmds.setAttr(f"{intp_data['controller']}.r", 0, 0, 0)
            i += 1

        # set isEnabled
        i = 1
        for pose, pose_data in intp_data["pose"].items():
            cmds.setAttr(f"{intp_name}.pose[{i}].isEnabled", pose_data["is_enabled"])
            i += 1


def export_psd(file_path):
    if not cmds.objExists(PSD_MANAGER):
        return logger.warning(f"{PSD_MANAGER} 존재하지 않습니다.")

    data = get_data()

    path = Path(file_path)
    if not path.parent.exists():
        return logger.warning(f"{path.parent} 존재하지 않습니다.")

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


class PSDManager(QtWidgets.QDialog):

    # 싱글톤 패턴
    _instance = None

    ui_name = "domino_psd_ui"

    def __init__(self, parent=None):
        super(PSDManager, self).__init__(parent=parent)
        self.current_intp = None
        self.setObjectName(self.ui_name)
        self.setWindowTitle("PSD Manager")
        self.setWindowFlags(
            self.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint
        )

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        # menu
        self.menu_bar = QtWidgets.QMenuBar()
        layout.setMenuBar(self.menu_bar)

        self.file_menu = self.menu_bar.addMenu("File")
        self.import_psd_action = QtGui.QAction("Import PSD")
        self.import_psd_action.triggered.connect(self.import_psd)
        self.export_psd_action = QtGui.QAction("Export PSD")
        self.export_psd_action.triggered.connect(self.export_psd)
        self.file_menu.addAction(self.import_psd_action)
        self.file_menu.addAction(self.export_psd_action)

        # interpolator widget
        interpolator_layout = QtWidgets.QVBoxLayout()
        layout.addLayout(interpolator_layout)

        current_interpolator_layout = QtWidgets.QHBoxLayout()
        self.driver_line_edit = QtWidgets.QLineEdit()
        self.driver_line_edit.setReadOnly(True)
        self.driver_line_edit.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.controller_line_edit = QtWidgets.QLineEdit()
        self.controller_line_edit.setReadOnly(True)
        self.controller_line_edit.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        current_interpolator_layout.addWidget(self.driver_line_edit)
        current_interpolator_layout.addWidget(self.controller_line_edit)
        interpolator_layout.addLayout(current_interpolator_layout)

        self.interpolator_list_widget = QtWidgets.QListWidget()
        self.interpolator_list_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.interpolator_list_widget.itemDoubleClicked.connect(
            self.set_current_interpolator
        )
        self.interpolator_list_widget.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        interpolator_layout.addWidget(self.interpolator_list_widget)

        interpolator_btn_layout = QtWidgets.QHBoxLayout()
        self.add_interpolator_btn = QtWidgets.QPushButton("Add Intp")
        self.add_interpolator_btn.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.add_interpolator_btn.clicked.connect(self.add_interpolator)
        self.mirror_interpolator_btn = QtWidgets.QPushButton("Mirror Intp")
        self.mirror_interpolator_btn.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.mirror_interpolator_btn.clicked.connect(self.mirror_interpolator)
        self.remove_interpolator_btn = QtWidgets.QPushButton("Remove Intp")
        self.remove_interpolator_btn.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Minimum,
            QtWidgets.QSizePolicy.Policy.Fixed,
        )
        self.remove_interpolator_btn.clicked.connect(self.remove_interpolator)
        interpolator_btn_layout.addWidget(self.add_interpolator_btn)
        interpolator_btn_layout.addWidget(self.mirror_interpolator_btn)
        interpolator_btn_layout.addWidget(self.remove_interpolator_btn)
        interpolator_layout.addLayout(interpolator_btn_layout)

        pose_driven_layout = QtWidgets.QVBoxLayout()
        layout.addLayout(pose_driven_layout)

        pose_layout = QtWidgets.QHBoxLayout()
        pose_driven_layout.addLayout(pose_layout)

        self.pose_list_widget = QtWidgets.QListWidget()
        self.pose_list_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.pose_list_widget.setFixedSize(160, 140)
        self.pose_list_widget.itemDoubleClicked.connect(self.go_to_pose)
        pose_layout.addWidget(self.pose_list_widget)

        pose_btn_layout = QtWidgets.QVBoxLayout()
        pose_layout.addLayout(pose_btn_layout)

        self.add_pose_btn = QtWidgets.QPushButton("Add Pose")
        self.add_pose_btn.clicked.connect(self.add_pose)
        self.update_pose_btn = QtWidgets.QPushButton("Update Pose")
        self.update_pose_btn.clicked.connect(self.update_pose)
        self.remove_pose_btn = QtWidgets.QPushButton("Remove Pose")
        self.remove_pose_btn.clicked.connect(self.remove_pose)
        pose_btn_layout.addWidget(self.add_pose_btn)
        pose_btn_layout.addWidget(self.update_pose_btn)
        pose_btn_layout.addWidget(self.remove_pose_btn)
        pose_btn_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                20,
                40,
                QtWidgets.QSizePolicy.Policy.Minimum,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        )

        driven_layout = QtWidgets.QHBoxLayout()
        pose_driven_layout.addLayout(driven_layout)

        self.driven_list_widget = QtWidgets.QListWidget()
        self.driven_list_widget.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.driven_list_widget.setFixedSize(160, 140)
        self.driven_list_widget.itemSelectionChanged.connect(self.select_driven)
        driven_layout.addWidget(self.driven_list_widget)

        driven_transform_btn_layout = QtWidgets.QVBoxLayout()
        driven_layout.addLayout(driven_transform_btn_layout)

        self.add_transform_driven_btn = QtWidgets.QPushButton("Add Driven\n(transform)")
        self.add_transform_driven_btn.clicked.connect(self.add_driven_transform)
        self.remove_transform_driven_btn = QtWidgets.QPushButton(
            "Remove Driven\n(transform)"
        )
        self.remove_transform_driven_btn.clicked.connect(self.remove_driven_transform)
        driven_transform_btn_layout.addWidget(self.add_transform_driven_btn)
        driven_transform_btn_layout.addWidget(self.remove_transform_driven_btn)
        driven_transform_btn_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                20,
                40,
                QtWidgets.QSizePolicy.Policy.Minimum,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        )

        self.refresh()

    def refresh(self):
        self.driver_line_edit.clear()
        self.controller_line_edit.clear()
        self.interpolator_list_widget.clear()
        self.pose_list_widget.clear()
        self.driven_list_widget.clear()

        if not cmds.objExists(PSD_MANAGER):
            return

        data = get_data()
        for intp in data.keys():
            item = QtWidgets.QListWidgetItem(intp)
            if self.current_intp == intp:
                item.setBackground(QtGui.QColor("#707070"))
                item.setForeground(QtGui.QColor("#cccccc"))
            self.interpolator_list_widget.addItem(item)

        if self.current_intp is None:
            return

        if self.current_intp not in data.keys():
            self.current_intp = None
            return

        for pose_name in data[self.current_intp]["pose"]:
            item = QtWidgets.QListWidgetItem(pose_name)
            self.pose_list_widget.addItem(item)

        if not data[self.current_intp]["is_blendshape"]:
            for driven in data[self.current_intp]["driven"]:
                item = QtWidgets.QListWidgetItem(driven)
                self.driven_list_widget.addItem(item)
        else:
            item = QtWidgets.QListWidgetItem(data[self.current_intp]["driven"])
            self.driven_list_widget.addItem(item)

        self.driver_line_edit.setText(data[self.current_intp]["driver"])
        self.controller_line_edit.setText(data[self.current_intp]["controller"])

    def set_current_interpolator(self):
        index = self.interpolator_list_widget.currentIndex()
        item = self.interpolator_list_widget.itemFromIndex(index)

        self.current_intp = item.text()
        self.refresh()

    def select_driven(self):
        items = self.driven_list_widget.selectedItems()
        if not items:
            return
        cmds.select([x.text() for x in items])

    def add_interpolator(self):
        selected = cmds.ls(selection=True)
        if len(selected) < 2:
            return logger.warning("Driver, Controller 를 선택해주세요.")

        driver, controller = selected

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Add Driver")
        dialog.setModal(True)

        dialog_layout = QtWidgets.QVBoxLayout(dialog)

        description_layout = QtWidgets.QHBoxLayout()
        interpolator_description_label = QtWidgets.QLabel("Description")
        interpolator_description_line_edit = QtWidgets.QLineEdit()
        interpolator_description_line_edit.setPlaceholderText(
            "Fill Interpolator description"
        )
        interpolator_description_line_edit.returnPressed.connect(dialog.accept)
        description_layout.addWidget(interpolator_description_label)
        description_layout.addWidget(interpolator_description_line_edit)
        dialog_layout.addLayout(description_layout)

        swing_twist_layout = QtWidgets.QHBoxLayout()
        btn1_group = QtWidgets.QButtonGroup()
        swing_radio_btn = QtWidgets.QRadioButton("Swing")
        swing_radio_btn.setChecked(True)
        twist_radio_btn = QtWidgets.QRadioButton("Twist")
        swing_twist_layout.addWidget(swing_radio_btn)
        swing_twist_layout.addWidget(twist_radio_btn)
        swing_twist_layout.addItem(
            QtWidgets.QSpacerItem(
                0,
                0,
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Minimum,
            )
        )
        btn1_group.addButton(swing_radio_btn)
        btn1_group.addButton(twist_radio_btn)
        dialog_layout.addLayout(swing_twist_layout)

        type_layout = QtWidgets.QHBoxLayout()
        btn2_group = QtWidgets.QButtonGroup()
        transform_radio_btn = QtWidgets.QRadioButton("Transform")
        transform_radio_btn.setChecked(True)
        blendshape_radio_btn = QtWidgets.QRadioButton("Blendshape")
        type_layout.addWidget(transform_radio_btn)
        type_layout.addWidget(blendshape_radio_btn)
        type_layout.addItem(
            QtWidgets.QSpacerItem(
                0,
                0,
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Minimum,
            )
        )
        btn2_group.addButton(transform_radio_btn)
        btn2_group.addButton(blendshape_radio_btn)
        dialog_layout.addLayout(type_layout)

        blendshape_line_edit = QtWidgets.QLineEdit()
        blendshape_line_edit.setPlaceholderText("Fill Blendshape Name")
        blendshape_line_edit.setEnabled(False)

        blendshapes = cmds.ls(type="blendShape")
        completer = QtWidgets.QCompleter(blendshapes)
        completer.setFilterMode(QtCore.Qt.MatchFlag.MatchContains)
        blendshape_line_edit.setCompleter(completer)

        blendshape_radio_btn.toggled.connect(blendshape_line_edit.clear)
        blendshape_radio_btn.toggled.connect(blendshape_line_edit.setEnabled)
        dialog_layout.addWidget(blendshape_line_edit)

        ok_cancel_layout = QtWidgets.QHBoxLayout()
        ok_btn = QtWidgets.QPushButton("Ok")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        ok_cancel_layout.addItem(
            QtWidgets.QSpacerItem(
                0,
                0,
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Minimum,
            )
        )
        ok_cancel_layout.addWidget(ok_btn)
        ok_cancel_layout.addWidget(cancel_btn)
        dialog_layout.addLayout(ok_cancel_layout)

        if not dialog.exec_():
            return

        description = interpolator_description_line_edit.text()

        pattern = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")  # 영어 + 숫자

        if not bool(pattern.match(description)):
            return logger.warning("description 은 영어, 숫자 여야합니다.")

        is_blendshape = blendshape_radio_btn.isChecked()
        blendshape = blendshape_line_edit.text()

        try:
            cmds.undoInfo(openChunk=True)
            add_intp(
                driver,
                controller,
                description,
                swing_radio_btn.isChecked(),
                blendshape if is_blendshape else "",
            )
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)
        self.refresh()

    def mirror_interpolator(self):
        items = self.interpolator_list_widget.selectedItems()
        if not items:
            return
        intps = [x.text() for x in items]
        try:
            cmds.undoInfo(openChunk=True)
            for intp in intps:
                mirror_intp(intp)
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)
        self.refresh()

    def remove_interpolator(self):
        items = self.interpolator_list_widget.selectedItems()
        if not items:
            return
        intps = [x.text() for x in items]
        try:
            cmds.undoInfo(openChunk=True)
            for intp in intps:
                remove_intp(intp)
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)
        self.refresh()

    def add_pose(self):
        if self.current_intp is None:
            return

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Add Pose")
        dialog.setModal(True)

        dialog_layout = QtWidgets.QVBoxLayout(dialog)

        pose_layout = QtWidgets.QHBoxLayout()
        pose_label = QtWidgets.QLabel("Description")
        pose_line_edit = QtWidgets.QLineEdit()
        pose_line_edit.setPlaceholderText("Fill Pose description")
        pose_line_edit.returnPressed.connect(dialog.accept)
        pose_layout.addWidget(pose_label)
        pose_layout.addWidget(pose_line_edit)
        dialog_layout.addLayout(pose_layout)

        ok_cancel_layout = QtWidgets.QHBoxLayout()
        ok_btn = QtWidgets.QPushButton("Ok")
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        ok_cancel_layout.addItem(
            QtWidgets.QSpacerItem(
                0,
                0,
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Minimum,
            )
        )
        ok_cancel_layout.addWidget(ok_btn)
        ok_cancel_layout.addWidget(cancel_btn)
        dialog_layout.addLayout(ok_cancel_layout)

        if not dialog.exec_():
            return

        pose_name = pose_line_edit.text()
        pattern = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")  # 영어 + 숫자

        if not bool(pattern.match(pose_name)):
            return logger.warning("pose 는 영어, 숫자 여야합니다.")

        try:
            cmds.undoInfo(openChunk=True)
            add_pose(self.current_intp, pose_name)
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)
        self.refresh()

    def update_pose(self):
        if self.current_intp is None:
            return

        items = self.pose_list_widget.selectedItems()
        try:
            cmds.undoInfo(openChunk=True)
            update_pose(self.current_intp, items[0].text())
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)
        self.refresh()

    def remove_pose(self):
        if self.current_intp is None:
            return

        items = self.pose_list_widget.selectedItems()
        try:
            cmds.undoInfo(openChunk=True)
            for pose in [x.text() for x in items]:
                remove_pose(self.current_intp, pose)
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)
        self.refresh()

    def go_to_pose(self, item):
        if self.current_intp is None:
            return
        try:
            cmds.undoInfo(openChunk=True)
            go_to_pose(self.current_intp, item.text())
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)

    def add_driven_transform(self):
        if self.current_intp is None:
            return
        selected = cmds.ls(selection=True)
        if not selected:
            return
        try:
            cmds.undoInfo(openChunk=True)
            for sel in selected:
                add_driven(self.current_intp, sel)
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)
        self.refresh()

    def remove_driven_transform(self):
        if self.current_intp is None:
            return
        items = self.driven_list_widget.selectedItems()
        try:
            cmds.undoInfo(openChunk=True)
            for driven in [x.text() for x in items]:
                remove_driven(self.current_intp, driven)
        except Exception as e:
            logger.error(e, exc_info=True)
        finally:
            cmds.undoInfo(closeChunk=True)
        self.refresh()

    def import_psd(self):
        file_path = cmds.fileDialog2(
            caption="Load PSD(Pose Space Deformation)",
            startingDirectory=cmds.workspace(query=True, rootDirectory=True),
            fileFilter="PSD (*.psd)",
            fileMode=1,
        )
        if file_path:
            try:
                cmds.undoInfo(openChunk=True)
                import_psd(file_path)
            except Exception as e:
                logger.error(e, exc_info=True)
            finally:
                cmds.undoInfo(closeChunk=True)
            self.refresh()

    def export_psd(self):
        file_path = cmds.fileDialog2(
            caption="Save PSD(Pose Space Deformation)",
            startingDirectory=cmds.workspace(query=True, rootDirectory=True),
            fileFilter="PSD (*.psd)",
            fileMode=0,
        )
        if not file_path:
            return
        file_path = file_path[0]
        export_psd(file_path=file_path)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
