# maya
from maya import cmds


TIME_ANIM_CURVE_TYPES = [
    "animCurveTL",
    "animCurveTA",
    "animCurveTT",
    "animCurveTU",
]

FLOAT_ANIM_CURVE_TYPES = [
    "animCurveUL",
    "animCurveUA",
    "animCurveUT",
    "animCurveUU",
]


def is_static(fcurve):
    if len(cmds.keyframe(fcurve, query=True, valueChange=True) or []) > 1:
        # keyframe 이 2 이상이지만 value, tangent 가 모두 동일한 경우. static
        if (
            len(set(cmds.keyframe(fcurve, query=True, valueChange=True))) == 1
            and len(set(cmds.keyTangent(fcurve, query=True, inAngle=True) or [])) == 1
            and len(set(cmds.keyTangent(fcurve, query=True, outAngle=True) or [])) == 1
        ):
            return True
    elif len(cmds.keyframe(fcurve, query=True, valueChange=True) or []) < 2:
        # keyframe 이 1개 이하인 경우. static
        return True
    return False


def get_driver(fcurve):
    stack = [fcurve]
    driver = None
    while driver is None and stack:
        node = stack.pop().split(".")[0]
        source = cmds.listConnections(node, source=True, destination=False, plugs=True)
        if not source:
            return

        if cmds.nodeType(source[0]) == "unitConversion":
            stack.append(source[0])
            continue

        driver = source[0]
    return driver


def get_fcurve(driver):
    fcurves = []
    stack = [driver]
    while stack:
        node = stack.pop()
        if cmds.nodeType(node) in TIME_ANIM_CURVE_TYPES + FLOAT_ANIM_CURVE_TYPES:
            fcurves.append(node)
            continue
        stack.extend(cmds.listConnections(node, source=False, destination=True) or [])
    return fcurves


def get_driven(fcurve):
    stack = [fcurve]
    driven = None
    while driven is None and stack:
        node = stack.pop().split(".")[0]
        destination = cmds.listConnections(
            node, source=False, destination=True, plugs=True
        )
        if not destination:
            return

        if cmds.nodeType(destination[0]) in ["unitConversion", "blendWeighted"]:
            stack.append(destination[0])
            continue

        driven = destination[0]
    return driven


def serialize_fcurve(fcurve):
    """
    fcurve 를 dict 로 serialize 한다.
    """
    data = {}
    data["type"] = cmds.nodeType(fcurve)
    data["driver"] = get_driver(fcurve)
    data["driven"] = get_driven(fcurve)
    data["time"] = cmds.keyframe(fcurve, query=True)
    data["floatChange"] = cmds.keyframe(fcurve, query=True, floatChange=True)
    data["valueChange"] = cmds.keyframe(fcurve, query=True, valueChange=True)
    data["inAngle"] = cmds.keyTangent(fcurve, query=True, inAngle=True)
    data["outAngle"] = cmds.keyTangent(fcurve, query=True, outAngle=True)
    data["inWeight"] = cmds.keyTangent(fcurve, query=True, inWeight=True)
    data["outWeight"] = cmds.keyTangent(fcurve, query=True, outWeight=True)
    data["inTangentType"] = cmds.keyTangent(fcurve, query=True, inTangentType=True)
    data["outTangentType"] = cmds.keyTangent(fcurve, query=True, outTangentType=True)
    data["weightedTangents"] = cmds.keyTangent(
        fcurve, query=True, weightedTangents=True
    )
    data["lock"] = cmds.keyTangent(fcurve, query=True, lock=True)
    return data


def deserialize_fcurve(data, custom_driver=None, custom_driven=None):
    fcurve = cmds.createNode(data["type"])

    # keyframe
    if data["type"] in TIME_ANIM_CURVE_TYPES:
        for i, value in enumerate(data["valueChange"]):
            cmds.setKeyframe(fcurve, edit=True, time=data["time"][i], value=value)
    elif data["type"] in FLOAT_ANIM_CURVE_TYPES:
        for i, value in enumerate(data["valueChange"]):
            cmds.setKeyframe(
                fcurve, edit=True, float=data["floatChange"][i], value=value
            )

    # keytangent
    cmds.keyTangent(fcurve, edit=True, weightedTangents=True)
    for i in range(len(data["valueChange"])):
        cmds.keyTangent(fcurve, edit=True, index=(i, i), lock=False)
        cmds.keyTangent(fcurve, edit=True, index=(i, i), itt=data["inTangentType"][i])
        cmds.keyTangent(fcurve, edit=True, index=(i, i), ott=data["outTangentType"][i])
        cmds.keyTangent(fcurve, edit=True, index=(i, i), ia=data["inAngle"][i])
        cmds.keyTangent(fcurve, edit=True, index=(i, i), oa=data["outAngle"][i])
        cmds.keyTangent(fcurve, edit=True, index=(i, i), iw=data["inWeight"][i])
        cmds.keyTangent(fcurve, edit=True, index=(i, i), ow=data["outWeight"][i])
        cmds.keyTangent(fcurve, edit=True, index=(i, i), lock=data["lock"][i])
    cmds.keyTangent(fcurve, edit=True, weightedTangents=data["weightedTangents"][0])

    # driver and driven
    driver = data["driver"]
    if custom_driver:
        driver = custom_driver

    if driver:
        cmds.connectAttr(driver, f"{fcurve}.input")

    driven = data["driven"]
    if custom_driven:
        driven = custom_driven

    if not driven:
        return fcurve

    source = cmds.listConnections(driven, source=True, destination=False, plugs=True)
    if not source:
        cmds.connectAttr(f"{fcurve}.output", driven)
        return fcurve

    stack = [source[0]]
    while stack:
        node = stack.pop().split(".")[0]
        if cmds.nodeType(node) == "unitConversion":
            source = cmds.listConnections(
                node, source=True, destination=False, plugs=True
            )
            if source:
                stack.append(source[0])
                continue
            else:
                return fcurve
        elif cmds.nodeType(node) == "blendWeighted":
            index = len(cmds.listAttr(f"{node}.input", multi=True))
            cmds.connectAttr(f"{fcurve}.output", f"{node}.input[{index}]")
            return fcurve
        elif cmds.nodeType(node) in TIME_ANIM_CURVE_TYPES + FLOAT_ANIM_CURVE_TYPES:
            blend_weighted = cmds.createNode("blendWeighted")
            cmds.connectAttr(f"{node}.output", f"{blend_weighted}.input[0]")
            cmds.connectAttr(f"{fcurve}.output", f"{blend_weighted}.input[1]")
            cmds.connectAttr(f"{blend_weighted}.output", driven, force=True)
            return fcurve
        else:
            return fcurve
