# maya
from maya import cmds
from maya.api import OpenMaya as om  # type: ignore

originMatrix = om.MMatrix()


def getLookAtMatrix(
    pos: om.MVector,
    lookAt: om.MVector,
    up: om.MVector,
    axis: str = "xy",
    negate: bool = False,
) -> om.MMatrix:
    """set lookAt(aim) Matrix

    Args:
        pos (om.MVector): position vector
        lookAt (om.MVector): target vector
        up (om.MVector): up vector
        axis (str, optional): primary, secondary axis. Defaults to "xy".
        negate (bool, optional): primary 축 뒤집기. Defaults to False.

    Returns:
        om.MMatrix: aim matrix
    """
    if negate:
        primary = (pos - lookAt).normalize()
    else:
        primary = (lookAt - pos).normalize()

    third = (primary ^ up.normalize()).normalize()
    secondary = (third ^ primary).normalize()

    if axis == "xy":
        X = primary
        Y = secondary
        Z = third
    elif axis == "xz":
        X = primary
        Z = secondary
        Y = -1 * third
    elif axis == "x-z":
        X = primary
        Z = -1 * secondary
        Y = third
    elif axis == "yx":
        Y = primary
        X = secondary
        Z = -1 * third
    elif axis == "yz":
        Y = primary
        Z = secondary
        X = third
    elif axis == "zx":
        Z = primary
        X = secondary
        Y = third
    elif axis == "z-x":
        Z = primary
        X = -1 * secondary
        Y = -1 * third
    elif axis == "zy":
        Z = primary
        Y = secondary
        X = -1 * third
    elif axis == "x-y":
        X = primary
        Y = -1 * secondary
        Z = -1 * third
    elif axis == "-xz":
        X = -1 * primary
        Z = secondary
        Y = third
    elif axis == "-xy":
        X = -1 * primary
        Y = secondary
        Z = third
    elif axis == "-yx":
        Y = -1 * primary
        X = secondary
        Z = third

    m = []
    m.extend([X[0], X[1], X[2], 0.0])
    m.extend([Y[0], Y[1], Y[2], 0.0])
    m.extend([Z[0], Z[1], Z[2], 0.0])
    m.extend([pos[0], pos[1], pos[2], 1.0])
    return om.MMatrix(m)


def getMirrorMatrix(
    worldM: om.MMatrix,
    behavior: bool = False,
    inverseScale: bool = False,
    planeMatrix: om.MMatrix = originMatrix,
) -> om.MMatrix:
    """get mirror matrix

    Args:
        worldM (om.MMatrix): source matrix
        behavior (bool, optional): behavior 로 mirror 합니다. Defaults to False.
        inverseScale (bool, optional): worldspace scaleX -1 로 mirror합니다. Defaults to False.
        planeMatrix (om.MMatrix, optional): custom mirror plane matrix 입니다. Defaults to om.MMatrix().

    Returns:
        om.MMatrix: mirror matrix
    """
    localM = worldM * planeMatrix.inverse()
    x = localM[12]
    y = localM[13]
    z = localM[14]

    if behavior:
        mirrorM = om.MMatrix(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, -1.0, 0.0, 0.0],
                [0.0, 0.0, -1.0, 0.0],
                [-2.0 * x, 2.0 * y, 2.0 * z, 1.0],
            ]
        )
        return localM * mirrorM * planeMatrix
    elif inverseScale:
        localM[0] = localM[0] * -1.0
        localM[4] = localM[4] * -1.0
        localM[8] = localM[8] * -1.0
        localM[12] = localM[12] * -1.0
        return localM * planeMatrix
    else:
        mirrorM = om.MMatrix(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0],
                [-2.0 * x, 0.0, 0.0, 1.0],
            ]
        )
        return localM * mirrorM * planeMatrix


def behaviorToInverseScale(m: om.MMatrix) -> om.MMatrix:
    """negate behavior matrix 를 inverse scale mirror matrix 로 제자리에서 변환합니다.

    Args:
        m (om.MMatrix): negate behavior matrix

    Returns:
        om.MMatrix: inverse scale matrix
    """
    x = m[12]
    y = m[13]
    z = m[14]
    return m * om.MMatrix(
        (-1.0, 0.0, 0.0, 0.0),
        (0.0, -1.0, 0.0, 0.0),
        (0.0, 0.0, -1.0, 0.0),
        (2.0 * x, 2.0 * y, 2.0 * z, 1.0),
    )
