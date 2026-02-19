# maya
from maya.api import OpenMaya as om

ORIGINMATRIX = om.MMatrix()


def get_look_at_matrix(pos, look_at, up, axis=["x", "y"]):
    """get lookAt(aim) Matrix

    Args:
        pos (om.MVector): position vector
        lookAt (om.MVector): target vector
        up (om.MVector): up vector
        axis (list, optional): primary, secondary axis. Defaults to ["x", "y"]

    Returns:
        om.MMatrix: aim matrix

    Example:
        >>> all_axis = [
        >>>     ("x", "y"),
        >>>     ("x", "-y"),
        >>>     ("-x", "y"),
        >>>     ("-x", "-y"),
        >>>     ("y", "x"),
        >>>     ("y", "-x"),
        >>>     ("-y", "x"),
        >>>     ("-y", "-x"),
        >>>     ("x", "z"),
        >>>     ("x", "-z"),
        >>>     ("-x", "z"),
        >>>     ("-x", "-z"),
        >>>     ("z", "x"),
        >>>     ("z", "-x"),
        >>>     ("-z", "x"),
        >>>     ("-z", "-x"),
        >>>     ("y", "z"),
        >>>     ("y", "-z"),
        >>>     ("-y", "z"),
        >>>     ("-y", "-z"),
        >>>     ("z", "y"),
        >>>     ("z", "-y"),
        >>>     ("-z", "y"),
        >>>     ("-z", "-y"),
        >>> ]

        >>> pos = om.MVector((0, 0, 0))
        >>> look_at = om.MVector((2, 0, 0))
        >>> up = om.MVector((0, 2, 0))

        >>> for axis in all_axis:
        >>>    axis_obj = nurbscurve.create("axis", (0, 0, 0))
        >>>    axis_obj = cmds.rename(axis_obj, (axis[0] + axis[1]).replace("-", "m"))

        >>>    m = matrix.get_look_at_matrix(pos, look_at, up, axis=axis)
        >>>    cmds.xform(axis_obj, matrix=m)
    """
    primary = (look_at - pos).normalize()
    temp = (primary ^ up.normalize()).normalize()
    secondary = (temp ^ primary).normalize()

    if "x" in axis[0]:
        X = primary
        if "-" in axis[0]:
            X *= -1
    if "y" in axis[0]:
        Y = primary
        if "-" in axis[0]:
            Y *= -1
    if "z" in axis[0]:
        Z = primary
        if "-" in axis[0]:
            Z *= -1

    if "x" in axis[1]:
        X = secondary
        if "-" in axis[1]:
            X *= -1
    if "y" in axis[1]:
        Y = secondary
        if "-" in axis[1]:
            Y *= -1
    if "z" in axis[1]:
        Z = secondary
        if "-" in axis[1]:
            Z *= -1

    all_axis = axis[0] + axis[1]
    if "x" in all_axis and "y" in all_axis:
        Z = (X ^ Y).normalize()
    if "x" in all_axis and "z" in all_axis:
        Y = (Z ^ X).normalize()
    if "y" in all_axis and "z" in all_axis:
        X = (Y ^ Z).normalize()

    m = []
    m.extend([X[0], X[1], X[2], 0.0])
    m.extend([Y[0], Y[1], Y[2], 0.0])
    m.extend([Z[0], Z[1], Z[2], 0.0])
    m.extend([pos[0], pos[1], pos[2], 1.0])
    return om.MMatrix(m)


def get_mirror_matrix(
    world_m, behavior=False, inverse_scale=False, plane_m=ORIGINMATRIX
):
    """get mirror matrix

    Args:
        worldM (om.MMatrix): source matrix
        behavior (bool, optional): behavior 로 mirror 합니다. Defaults to False.
        inverseScale (bool, optional): worldspace scaleX -1 로 mirror합니다. Defaults to False.
        planeMatrix (om.MMatrix, optional): custom mirror plane matrix 입니다. Defaults to om.MMatrix().

    Returns:
        om.MMatrix: mirror matrix
    """
    local_m = world_m * plane_m.inverse()
    x = local_m[12]
    y = local_m[13]
    z = local_m[14]

    if behavior:
        mirror_m = om.MMatrix(
            [
                [1.0, 0.0, 0.0, 0.0],
                [0.0, -1.0, 0.0, 0.0],
                [0.0, 0.0, -1.0, 0.0],
                [-2.0 * x, 2.0 * y, 2.0 * z, 1.0],
            ]
        )
        return local_m * mirror_m * plane_m
    elif inverse_scale:
        local_m[0] = local_m[0] * -1.0
        local_m[4] = local_m[4] * -1.0
        local_m[8] = local_m[8] * -1.0
        local_m[12] = local_m[12] * -1.0
        return local_m * plane_m
    else:
        # 1. 로컬 행렬 복제
        m = om.MMatrix(local_m)

        # 2. 위치(Translation) 미러: X축 반전
        m[12] = -m[12]

        # 3. 회전 및 스케일 보정 (YZ 평면 대칭)
        # YZ 평면 미러링 시, X축 벡터의 X성분, Y축 벡터의 X성분, Z축 벡터의 X성분을 반전합니다.
        # [m00, m01, m02, m03]  <- X axis
        # [m10, m11, m12, m13]  <- Y axis
        # [m20, m21, m22, m23]  <- Z axis

        # 각 축의 X 성분(Column 0)을 반전시킵니다.
        m[0] = -m[0]
        m[4] = -m[4]
        m[8] = -m[8]

        # 4. 중요: Scale 1, 1, 1을 유지하기 위한 처리
        # 위 단계까지만 하면 Determinant가 -1이 되어 스케일이 뒤집힙니다.
        # 이를 보정하기 위해 X축 벡터 전체에 -1을 곱해 방향을 정렬합니다.
        m[0] = -m[0]
        m[1] = -m[1]
        m[2] = -m[2]
        return m * plane_m


def behavior_to_inverse_scale(m):
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
