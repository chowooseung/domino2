# maya
from maya import cmds
from maya.api import OpenMaya as om  # type: ignore

ORIGINMATRIX = om.MMatrix()


def replace_shape(source: str, destination: str) -> None:
    source_shapes = cmds.listRelatives(source, shapes=True, fullPath=True) or []
    destination_shapes = (
        cmds.listRelatives(destination, shapes=True, fullPath=True) or []
    )
    if destination_shapes:
        cmds.delete(destination_shapes)
    shapes = cmds.parent(source_shapes, destination, relative=True, shape=True)
    for shape in shapes:
        shape = cmds.rename(shape, destination + "Shape")
        cmds.setAttr(shape + ".isHistoricallyInteresting", 0)


def translate_shape(node: str, t: list) -> None:
    shapes = cmds.listRelatives(node, shapes=True) or []
    for shape in shapes:
        cmds.move(
            *t,
            shape + ".cv[*]",
            relative=True,
            objectSpace=True,
            worldSpaceDistance=True,
        )


def rotate_shape(node: str, r: list) -> None:
    shapes = cmds.listRelatives(node, shapes=True) or []
    t = cmds.xform(node, query=True, translation=True, worldSpace=True)
    for shape in shapes:
        cmds.rotate(
            *r,
            shape + ".cv[*]",
            relative=True,
            pivot=t,
            objectSpace=True,
            forceOrderXYZ=True,
        )


def scale_shape(node: str, s: list) -> None:
    shapes = cmds.listRelatives(node, shapes=True) or []
    t = cmds.xform(node, query=True, translation=True, worldSpace=True)
    for shape in shapes:
        cmds.scale(*s, shape + ".cv[*]", pivot=t)


def mirror_shape(node: str, left_str: str = "_L", right_str: str = "_R") -> None:
    source = node
    if left_str in source:
        destination = source.replace(left_str, right_str)
    elif right_str in source:
        destination = source.replace(right_str, left_str)
    if not destination:
        return

    shapes = cmds.listRelatives(source, shapes=True) or []
    cmds.delete(cmds.listRelatives(destination, shapes=True) or [])
    delete_list = []
    for shape in shapes:
        dup_curve = cmds.duplicateCurve(shape, constructionHistory=False)[0]
        cmds.scale(-1, 1, 1, dup_curve + ".cv[*]", relative=True)
        shapes = cmds.parent(
            cmds.listRelatives(dup_curve, shapes=True),
            destination,
            relative=True,
            shape=True,
        )
        for shape in shapes:
            cmds.rename(shape, destination + "Shape")
            cmds.setAttr(shape + ".isHistoricallyInteresting", 0)
        delete_list.append(dup_curve)
    cmds.delete(delete_list)


def create(shape: str, color: om.MColor | int, m: om.MMatrix = ORIGINMATRIX) -> str:
    func = globals().get(shape)
    if func and callable(func):
        return func(color=color, m=m)


def generate(
    destination: str,
    points: list,
    degree: int,
    color: om.MColor | int,
    close: bool = False,
) -> None:
    if close:
        points.extend(points[:degree])
        knots = range(len(points) + degree - 1)
        curve = cmds.curve(point=points, degree=degree, per=close, k=knots)
    else:
        curve = cmds.curve(point=points, degree=degree)
    shape = cmds.listRelatives(curve, shapes=True)[0]
    shape = cmds.rename(shape, destination + "Shape")
    shape = cmds.parent(shape, destination, relative=True, shape=True)[0]
    cmds.delete(curve)

    if color:
        cmds.setAttr(shape + ".overrideEnabled", True)

    if isinstance(color, int):
        cmds.setAttr(shape + ".overrideRGBColors", 0)
        cmds.setAttr(shape + ".overrideColor", color)
    elif isinstance(color, om.MColor):
        cmds.setAttr(shape + ".overrideRGBColors", 1)
        cmds.setAttr(shape + ".overrideColorRGB", *color)
    cmds.setAttr(shape + ".isHistoricallyInteresting", 0)


def origin(color: om.MColor | int, m: om.MMatrix) -> str:
    dlen = 0.5
    # circle
    v0 = om.MVector(0, 0, -dlen * 1.108)
    v1 = om.MVector(dlen * 0.78, 0, -dlen * 0.78)
    v2 = om.MVector(dlen * 1.108, 0, 0)
    v3 = om.MVector(dlen * 0.78, 0, dlen * 0.78)
    v4 = om.MVector(0, 0, dlen * 1.108)
    v5 = om.MVector(-dlen * 0.78, 0, dlen * 0.78)
    v6 = om.MVector(-dlen * 1.108, 0, 0)
    v7 = om.MVector(-dlen * 0.78, 0, -dlen * 0.78)

    # x
    v8 = om.MVector(dlen - 0.01, 0, 0)
    v9 = om.MVector(dlen + 0.01, 0, 0)

    # z
    v10 = om.MVector(0, 0, dlen - 0.01)
    v11 = om.MVector(0, 0, dlen + 0.01)

    node = cmds.createNode("transform", name="origin")
    cmds.setAttr(node + ".displayRotatePivot", True)
    cmds.setAttr(node + ".overrideEnabled", True)
    cmds.setAttr(node + ".overrideRGBColors", 0)
    cmds.setAttr(node + ".overrideColor", 16)

    points = [v0, v1, v2, v3, v4, v5, v6, v7]
    generate(destination=node, points=points, degree=3, color=color, close=True)
    generate(destination=node, points=[v8, v9], degree=1, color=om.MColor((1, 0, 0)))
    generate(destination=node, points=[v10, v11], degree=1, color=om.MColor((0, 0, 1)))
    cmds.xform(node, matrix=m)
    return node


def arrow(color: om.MColor | int, m: om.MMatrix) -> str:
    points = [
        (-0.0, 0.0, -0.5),
        (0.5, 0.0, 0.0),
        (-0.0, 0.0, 0.5),
        (0.0, 0.0, 0.211),
        (-0.5, 0.0, 0.211),
        (-0.5, 0.0, -0.211),
        (0.0, 0.0, -0.211),
        (-0.0, 0.0, -0.5),
    ]
    points = [om.MVector(x) for x in points]

    node = cmds.createNode("transform", name="arrow")
    generate(
        destination=node,
        points=points,
        degree=1,
        close=True,
        color=color,
    )
    cmds.xform(node, matrix=m)
    return node


def arrow4(color: om.MColor | int, m: om.MMatrix) -> str:
    points = [
        [-0.1, 0.0, -0.3],
        [-0.2, 0.0, -0.3],
        [0.0, 0.0, -0.5],
        [0.2, 0.0, -0.3],
        [0.1, 0.0, -0.3],
        [0.1, 0.0, -0.1],
        [0.3, 0.0, -0.1],
        [0.3, 0.0, -0.2],
        [0.5, 0.0, 0.0],
        [0.3, 0.0, 0.2],
        [0.3, 0.0, 0.1],
        [0.1, 0.0, 0.1],
        [0.1, 0.0, 0.3],
        [0.2, 0.0, 0.3],
        [0.0, 0.0, 0.5],
        [-0.2, 0.0, 0.3],
        [-0.1, 0.0, 0.3],
        [-0.1, 0.0, 0.1],
        [-0.3, 0.0, 0.1],
        [-0.3, 0.0, 0.2],
        [-0.5, 0.0, 0.0],
        [-0.3, 0.0, -0.2],
        [-0.3, 0.0, -0.1],
        [-0.1, 0.0, -0.1],
        [-0.1, 0.0, -0.3],
    ]
    points = [om.MVector(x) for x in points]

    node = cmds.createNode("transform", name="arrow4")
    generate(
        destination=node,
        points=points,
        degree=1,
        close=True,
        color=color,
    )
    cmds.xform(node, matrix=m)
    return node


def square(color: om.MColor | int, m: om.MMatrix) -> str:
    dlen = 0.5
    v0 = om.MVector(dlen, 0, 0)
    v1 = om.MVector(-dlen, 0, 0)
    v2 = om.MVector(0, 0, dlen)
    v3 = om.MVector(0, 0, -dlen)
    points = [(v1 + v2), (v0 + v2), (v0 + v3), (v1 + v3)]

    node = cmds.createNode("transform", name="square")
    generate(
        destination=node,
        points=points,
        degree=1,
        close=True,
        color=color,
    )
    cmds.xform(node, matrix=m)
    return node


def wave(color: om.MColor | int, m: om.MMatrix) -> str:
    points = [
        [0.129648, 0.0, -0.567988],
        [0.0, 0.0, -0.338736],
        [-0.129648, 0.0, -0.567988],
        [-0.14698, 0.0, -0.305169],
        [-0.363233, 0.0, -0.4555],
        [-0.264842, 0.0, -0.211169],
        [-0.524946, 0.0, -0.252767],
        [-0.330243, 0.0, -0.075397],
        [-0.577752, 0.0, 0.0],
        [-0.330243, 0.0, 0.075397],
        [-0.524946, 0.0, 0.252767],
        [-0.264842, 0.0, 0.211169],
        [-0.363233, 0.0, 0.4555],
        [-0.14698, 0.0, 0.305169],
        [-0.129648, 0.0, 0.567988],
        [0.0, 0.0, 0.338736],
        [0.129648, 0.0, 0.567988],
        [0.14698, 0.0, 0.305169],
        [0.363233, 0.0, 0.4555],
        [0.264842, 0.0, 0.211169],
        [0.524946, 0.0, 0.252767],
        [0.330243, 0.0, 0.075397],
        [0.577752, 0.0, 0.0],
        [0.330243, 0.0, -0.075397],
        [0.524946, 0.0, -0.252767],
        [0.264842, 0.0, -0.211169],
        [0.363233, 0.0, -0.4555],
        [0.14698, 0.0, -0.305169],
    ]
    points = [om.MVector(p) for p in points]
    node = cmds.createNode("transform", name="wave")

    generate(
        destination=node,
        points=points,
        degree=3,
        color=color,
        close=True,
    )
    cmds.xform(node, matrix=m)
    return node


def halfmoon(color: om.MColor | int, m: om.MMatrix) -> str:
    node = cmds.createNode("transform", name="halfmoon")

    points = [
        [0.0, 0.0, -0.5],
        [-0.065, 0.0, -0.5],
        [-0.197, 0.0, -0.474],
        [-0.363, 0.0, -0.363],
        [-0.474, 0.0, -0.196],
        [-0.513, -0.0, 0.0],
        [-0.474, -0.0, 0.196],
        [-0.363, -0.0, 0.363],
        [-0.197, -0.0, 0.474],
        [-0.065, -0.0, 0.5],
        [0.0, -0.0, 0.5],
    ]
    points = [om.MVector(p) for p in points]
    generate(
        destination=node,
        points=points,
        degree=3,
        color=color,
        close=False,
    )

    points = [[0.0, 0.0, -0.5], [0.0, -0.0, 0.5]]
    points = [om.MVector(p) for p in points]
    generate(
        destination=node,
        points=points,
        degree=1,
        color=color,
        close=False,
    )
    cmds.xform(node, matrix=m)
    return node


def halfcircle(color: om.MColor | int, m: om.MMatrix) -> str:
    points = [
        [0.0, 0.0, -0.5],
        [-0.065, 0.0, -0.5],
        [-0.197, 0.0, -0.474],
        [-0.363, 0.0, -0.363],
        [-0.474, 0.0, -0.196],
        [-0.513, -0.0, 0.0],
        [-0.474, -0.0, 0.196],
        [-0.363, -0.0, 0.363],
        [-0.197, -0.0, 0.474],
        [-0.065, -0.0, 0.5],
        [0.0, -0.0, 0.5],
    ]
    points = [om.MVector(p) for p in points]

    node = cmds.createNode("transform", name="halfcircle")
    generate(
        destination=node,
        points=points,
        degree=3,
        color=color,
        close=False,
    )
    cmds.xform(node, matrix=m)
    return node


def circle(color: om.MColor | int, m: om.MMatrix) -> str:
    dlen = 0.5
    v0 = om.MVector(0, 0, -dlen * 1.108)
    v1 = om.MVector(dlen * 0.78, 0, -dlen * 0.78)
    v2 = om.MVector(dlen * 1.108, 0, 0)
    v3 = om.MVector(dlen * 0.78, 0, dlen * 0.78)
    v4 = om.MVector(0, 0, dlen * 1.108)
    v5 = om.MVector(-dlen * 0.78, 0, dlen * 0.78)
    v6 = om.MVector(-dlen * 1.108, 0, 0)
    v7 = om.MVector(-dlen * 0.78, 0, -dlen * 0.78)

    node = cmds.createNode("transform", name="circle")
    generate(
        destination=node,
        points=[v0, v1, v2, v3, v4, v5, v6, v7],
        degree=3,
        color=color,
        close=True,
    )
    cmds.xform(node, matrix=m)
    return node


def sphere(color: om.MColor | int, m: om.MMatrix) -> str:
    c0 = circle(color, ORIGINMATRIX)
    cmds.setAttr(c0 + ".rz", 90)
    c1 = circle(color, ORIGINMATRIX)
    cmds.setAttr(c1 + ".rx", 90)
    c2 = circle(color, ORIGINMATRIX)
    cmds.makeIdentity([c0, c1], apply=True, rotate=True)

    node = cmds.createNode("transform", name="sphere")

    c0_shape = cmds.listRelatives(c0, shapes=True)[0]
    c1_shape = cmds.listRelatives(c1, shapes=True)[0]
    c2_shape = cmds.listRelatives(c2, shapes=True)[0]
    cmds.parent([c0_shape, c1_shape, c2_shape], node, relative=True, shape=True)

    cmds.rename(c0_shape, node + "Shape")
    cmds.rename(c1_shape, node + "Shape1")
    cmds.rename(c2_shape, node + "Shape2")

    cmds.delete([c0, c1, c2])
    cmds.xform(node, matrix=m)
    return node


def locator(color: om.MColor | int, m: om.MMatrix) -> str:
    node = cmds.createNode("transform", name="locator")

    dlen = 0.5
    v0 = om.MVector(dlen, 0, 0)
    v1 = om.MVector(-dlen, 0, 0)
    v2 = om.MVector(0, dlen, 0)
    v3 = om.MVector(0, -dlen, 0)
    v4 = om.MVector(0, 0, dlen)
    v5 = om.MVector(0, 0, -dlen)

    points = [v0, v1]
    generate(destination=node, points=points, degree=1, color=color)

    points = [v2, v3]
    generate(destination=node, points=points, degree=1, color=color)

    points = [v4, v5]
    generate(destination=node, points=points, degree=1, color=color)
    cmds.xform(node, matrix=m)
    return node


def cube(color: om.MColor | int, m: om.MMatrix) -> str:
    dlen = 0.5
    v0 = om.MVector(dlen, dlen, dlen)
    v1 = om.MVector(dlen, dlen, -dlen)
    v2 = om.MVector(dlen, -dlen, dlen)
    v3 = om.MVector(dlen, -dlen, -dlen)

    v4 = om.MVector(-dlen, dlen, dlen)
    v5 = om.MVector(-dlen, dlen, -dlen)
    v6 = om.MVector(-dlen, -dlen, dlen)
    v7 = om.MVector(-dlen, -dlen, -dlen)

    node = cmds.createNode("transform", name="cube")

    points = [v0, v1, v3, v2, v0, v4, v5, v7, v6, v4, v5, v1, v3, v7, v6, v2]
    generate(destination=node, points=points, degree=1, color=color)
    cmds.xform(node, matrix=m)
    return node


def cylinder(color: om.MColor | int, m: om.MMatrix) -> str:
    node = cmds.createNode("transform", name="cylinder")

    dlen = 0.5
    v0 = om.MVector(0, 0, -dlen * 1.108)
    v1 = om.MVector(dlen * 0.78, 0, -dlen * 0.78)
    v2 = om.MVector(dlen * 1.108, 0, 0)
    v3 = om.MVector(dlen * 0.78, 0, dlen * 0.78)
    v4 = om.MVector(0, 0, dlen * 1.108)
    v5 = om.MVector(-dlen * 0.78, 0, dlen * 0.78)
    v6 = om.MVector(-dlen * 1.108, 0, 0)
    v7 = om.MVector(-dlen * 0.78, 0, -dlen * 0.78)

    up_circle_points = [
        p + om.MVector(0, 0.5, 0) for p in [v0, v1, v2, v3, v4, v5, v6, v7]
    ]
    down_circle_points = [
        p + om.MVector(0, -0.5, 0) for p in [v0, v1, v2, v3, v4, v5, v6, v7]
    ]
    generate(
        destination=node, points=up_circle_points, degree=3, color=color, close=True
    )
    generate(
        destination=node, points=down_circle_points, degree=3, color=color, close=True
    )

    points = [om.MVector(0.354, 0.5, 0.354), om.MVector(0.354, -0.5, 0.354)]
    generate(destination=node, points=points, degree=1, color=color)
    generate(
        destination=node,
        points=[(p[0] * -1, p[1], p[2]) for p in points],
        degree=1,
        color=color,
    )
    generate(
        destination=node,
        points=[(p[0], p[1], p[2] * -1) for p in points],
        degree=1,
        color=color,
    )
    generate(
        destination=node,
        points=[(p[0] * -1, p[1], p[2] * -1) for p in points],
        degree=1,
        color=color,
    )
    cmds.xform(node, matrix=m)
    return node


def x(color: om.MColor | int, m: om.MMatrix) -> str:
    node = cmds.createNode("transform", name="x")

    dlen = 0.25
    v0 = om.MVector(dlen, 0, 0)
    v1 = om.MVector(-dlen, 0, 0)
    v2 = om.MVector(0, dlen, 0)
    v3 = om.MVector(0, -dlen, 0)
    v4 = om.MVector(0, 0, dlen)
    v5 = om.MVector(0, 0, -dlen)

    points = [(v0 + v2 + v4), (v1 + v3 + v5)]
    generate(
        destination=node,
        points=points,
        degree=1,
        color=color,
    )

    points = [(v1 + v2 + v4), (v0 + v3 + v5)]
    generate(
        destination=node,
        points=points,
        degree=1,
        color=color,
    )

    points = [(v0 + v3 + v4), (v1 + v2 + v5)]
    generate(
        destination=node,
        points=points,
        degree=1,
        color=color,
    )

    points = [(v0 + v2 + v5), (v1 + v3 + v4)]
    generate(
        destination=node,
        points=points,
        degree=1,
        color=color,
    )
    cmds.xform(node, matrix=m)
    return node


def angle(color: om.MColor | int, m: om.MMatrix) -> str:
    dlen = 0.5
    v0 = om.MVector(dlen, 0, dlen)
    v1 = om.MVector(dlen, 0, -dlen)
    v2 = om.MVector(-dlen, 0, -dlen)
    v3 = om.MVector(dlen, 0, dlen)
    points = [v0, v1, v2, v3]

    node = cmds.createNode("transform", name="angle")
    generate(
        destination=node,
        points=points,
        degree=1,
        color=color,
    )
    cmds.xform(node, matrix=m)
    return node


def dodecahedron(color: om.MColor | int, m: om.MMatrix) -> str:
    shapes = [
        [
            [-0.19, 0.496, 0.0],
            [0.19, 0.496, 0.0],
            [0.307, 0.307, -0.307],
            [0.0, 0.19, -0.496],
            [-0.307, 0.307, -0.307],
            [-0.19, 0.496, 0.0],
        ],
        [
            [0.19, 0.496, 0.0],
            [0.307, 0.307, -0.307],
            [0.496, 0.0, -0.19],
            [0.496, 0.0, 0.19],
            [0.307, 0.307, 0.307],
            [0.19, 0.496, 0.0],
        ],
        [
            [-0.19, 0.496, 0.0],
            [0.19, 0.496, 0.0],
            [0.307, 0.307, 0.307],
            [0.0, 0.19, 0.496],
            [-0.307, 0.307, 0.307],
            [-0.19, 0.496, 0.0],
        ],
        [
            [0.496, 0.0, 0.19],
            [0.307, 0.307, 0.307],
            [0.0, 0.19, 0.496],
            [0.0, -0.19, 0.496],
            [0.307, -0.307, 0.307],
            [0.496, 0.0, 0.19],
        ],
        [
            [-0.307, 0.307, 0.307],
            [0.0, 0.19, 0.496],
            [0.0, -0.19, 0.496],
            [-0.307, -0.307, 0.307],
            [-0.496, 0.0, 0.19],
            [-0.307, 0.307, 0.307],
        ],
        [
            [-0.307, 0.307, 0.307],
            [-0.496, 0.0, 0.19],
            [-0.496, 0.0, -0.19],
            [-0.307, 0.307, -0.307],
            [-0.19, 0.496, 0.0],
        ],
        [
            [-0.496, 0.0, -0.19],
            [-0.496, 0.0, 0.19],
            [-0.307, -0.307, 0.307],
            [-0.19, -0.496, 0.0],
            [-0.307, -0.307, -0.307],
            [-0.496, 0.0, -0.19],
        ],
        [
            [-0.307, 0.307, -0.307],
            [0.0, 0.19, -0.496],
            [0.0, -0.19, -0.496],
            [-0.307, -0.307, -0.307],
            [-0.496, 0.0, -0.19],
            [-0.307, 0.307, -0.307],
        ],
        [
            [-0.19, -0.496, 0.0],
            [0.19, -0.496, 0.0],
            [0.307, -0.307, -0.307],
            [0.0, -0.19, -0.496],
            [-0.307, -0.307, -0.307],
            [-0.19, -0.496, 0.0],
        ],
        [
            [0.0, 0.19, -0.496],
            [0.307, 0.307, -0.307],
            [0.496, 0.0, -0.19],
            [0.307, -0.307, -0.307],
            [0.0, -0.19, -0.496],
            [0.0, 0.19, -0.496],
        ],
        [
            [0.496, 0.0, -0.19],
            [0.496, 0.0, 0.19],
            [0.307, -0.307, 0.307],
            [0.19, -0.496, 0.0],
            [0.307, -0.307, -0.307],
            [0.496, 0.0, -0.19],
        ],
    ]
    node = cmds.createNode("transform", name="dodecahedron")

    for shape in shapes:
        points = [(s[0], s[1], s[2]) for s in shape]
        generate(
            destination=node,
            points=points,
            degree=1,
            color=color,
        )
    cmds.xform(node, matrix=m)
    return node


def axis(color: om.MColor | int, m: om.MMatrix) -> str:
    node = cmds.createNode("transform", name="axis")

    points = [
        [0.0, 0.0, 0.0],
        [0.5, 0.0, 0.0],
        [0.45, 0.0, -0.05],
        [0.45, 0.05, 0.0],
        [0.45, 0.0, 0.05],
        [0.45, -0.05, 0.0],
        [0.45, 0.0, -0.05],
        [0.45, 0.05, 0.0],
        [0.5, 0.0, 0.0],
        [0.45, 0.0, 0.05],
        [0.45, -0.05, 0.0],
        [0.5, 0.0, 0.0],
    ]
    generate(destination=node, points=points, degree=1, color=om.MColor([1, 0, 0]))

    points = [
        [0.0, 0.0, 0.0],
        [0.0, 0.5, 0.0],
        [0.0, 0.45, -0.05],
        [-0.05, 0.45, 0.0],
        [0.0, 0.45, 0.05],
        [0.05, 0.45, 0.0],
        [0.0, 0.45, -0.05],
        [-0.05, 0.45, 0.0],
        [0.0, 0.5, 0.0],
        [0.0, 0.45, 0.05],
        [0.05, 0.45, 0.0],
        [0.0, 0.5, 0.0],
    ]
    generate(destination=node, points=points, degree=1, color=om.MColor([0, 1, 0]))

    points = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.5],
        [0.0, 0.05, 0.45],
        [-0.05, 0.0, 0.45],
        [0.0, -0.05, 0.45],
        [0.05, 0.0, 0.45],
        [0.0, 0.05, 0.45],
        [-0.05, 0.0, 0.45],
        [0.0, 0.0, 0.5],
        [0.0, -0.05, 0.45],
        [0.05, 0.0, 0.45],
        [0.0, 0.0, 0.5],
    ]
    generate(destination=node, points=points, degree=1, color=om.MColor([0, 0, 1]))
    cmds.xform(node, matrix=m)
    return node


def bracket(color: om.MColor | int, m: om.MMatrix) -> str:
    dlen = 0.5
    v0 = om.MVector(0, dlen, 0)
    v1 = om.MVector(0, 0, 0)
    v2 = om.MVector(dlen * -1, 0, 0)

    node = cmds.createNode("transform", name="bracket")

    generate(destination=node, points=[v0, v1, v2], degree=1, color=color)
    cmds.xform(node, matrix=m)
    return node


def line(color: om.MColor | int, m: om.MMatrix) -> str:
    node = cmds.createNode("transform", name="line")

    points = [om.MVector(0.5, 0, 0), om.MVector(-0.5, 0, 0)]
    generate(destination=node, points=points, degree=1, color=color)
    cmds.xform(node, matrix=m)
    return node
