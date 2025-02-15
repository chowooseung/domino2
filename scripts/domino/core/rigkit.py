# maya
from maya import cmds
from maya.api import OpenMaya as om  # type: ignore

# built-ins
from pathlib import Path

# domino
from domino.core.utils import logger


# region ribbon
def create_ribbon_surf(
    parent: str,
    name: str,
    positions: list,
    width_vector: tuple = (0, 0, 1),
    width: float = 0.1,
    degree: int = 3,
    drivers: list = [],
    invserse_plugs: list = [],
) -> str:
    positions = [om.MVector(p) for p in positions]
    width_vector = om.MVector(width_vector)
    normalize_width_vector = width_vector.normalize()
    offset_vector = normalize_width_vector * width

    crv0_positions = []
    crv1_positions = []
    crv2_positions = []
    for p in positions:
        crv0_positions.append(p - (offset_vector / 2))
        crv1_positions.append(p)
        crv2_positions.append(p + (offset_vector / 2))
    crv0 = cmds.curve(point=crv0_positions, degree=degree)
    crv1 = cmds.curve(point=crv1_positions, degree=degree)
    crv2 = cmds.curve(point=crv2_positions, degree=degree)

    surf = cmds.loft(
        crv0,
        crv1,
        crv2,
        name=name,
        constructionHistory=0,
        uniform=1,
        close=0,
        reverse=0,
        degree=1,
        sectionSpans=1,
        rn=0,
        polygon=0,
        reverseSurfaceNormals=True,
    )
    cmds.delete(crv0, crv1, crv2)

    if parent:
        surf = cmds.parent(surf, parent)
    surf = cmds.rename(surf, name)

    sc = cmds.skinCluster(
        drivers + [surf],
        name=name + "_sc0",
        maximumInfluences=len(drivers),
        normalizeWeights=True,
        obeyMaxInfluences=False,
        weightDistribution=1,
        multi=True,
    )[0]
    for i, plug in enumerate(
        cmds.listConnections(sc + ".matrix", source=True, destination=False)
    ):
        cmds.connectAttr(plug + ".matrix", sc + f".matrix[{i}]", force=True)
    for i, plug in enumerate(invserse_plugs):
        cmds.connectAttr(plug, sc + f".bindPreMatrix[{i}]")
    return surf


def create_tangent_output(
    surf: str,
    name: str,
    output_u_values: list,
    primary_axis: str = "x",
    secondary_axis: str = "-z",
) -> list:
    axis = ["x", "y", "z", "-x", "-y", "-z"]
    primary_axis_index = axis.index(primary_axis)
    secondary_axis_index = axis.index(secondary_axis)

    parent = cmds.listRelatives(surf, parent=True)
    parent = parent[0] if parent else None

    uv_pin = cmds.createNode("uvPin")
    shape, orig = cmds.listRelatives(surf, shapes=True, noIntermediate=False)
    cmds.connectAttr(orig + ".local", uv_pin + ".originalGeometry")
    cmds.connectAttr(shape + ".local", uv_pin + ".deformedGeometry")
    outputs = []
    for i, u_value in enumerate(output_u_values):
        cmds.setAttr(uv_pin + f".coordinate[{i}].coordinateU", u_value)
        cmds.setAttr(uv_pin + f".coordinate[{i}].coordinateV", 0.5)
        cmds.setAttr(uv_pin + ".tangentAxis", primary_axis_index)
        cmds.setAttr(uv_pin + ".normalAxis", secondary_axis_index)

        output = cmds.createNode(
            "transform", parent=parent, name=name + f"_{i}_tangentOutput"
        )
        cmds.connectAttr(uv_pin + f".outputMatrix[{i}]", output + ".offsetParentMatrix")
        outputs.append(output)
    return outputs


def create_aim_output(
    surf: str,
    name: str,
    output_u_values: list,
    up_vector: tuple = (0, 0, 1),
    primary_vector: tuple = (1, 0, 0),
    secondary_vector: tuple = (0, 0, 1),
) -> list:
    parent = cmds.listRelatives(surf, parent=True)
    parent = parent[0] if parent else None

    uv_pin = cmds.createNode("uvPin")
    shape, orig = cmds.listRelatives(surf, shapes=True, noIntermediate=False)
    cmds.connectAttr(orig + ".local", uv_pin + ".originalGeometry")
    cmds.connectAttr(shape + ".local", uv_pin + ".deformedGeometry")
    pos_matrices = []
    up_matrices = []
    for i, u_value in enumerate(output_u_values):
        cmds.setAttr(uv_pin + f".coordinate[{i}].coordinateU", u_value)
        cmds.setAttr(uv_pin + f".coordinate[{i}].coordinateV", 0.5)
        pos_matrices.append(uv_pin + f".outputMatrix[{i}]")

        pos_m = om.MTransformationMatrix(
            om.MMatrix(cmds.getAttr(uv_pin + f".outputMatrix[{i}]"))
        )
        pos_vector = pos_m.translation(om.MSpace.kWorld)
        up_m = om.MTransformationMatrix()
        up_m.setTranslation(pos_vector + om.MVector(up_vector), om.MSpace.kWorld)

        mult_m = cmds.createNode("multMatrix")
        cmds.setAttr(mult_m + ".matrixIn[0]", up_m.asMatrix(), type="matrix")
        m = om.MMatrix(cmds.getAttr(uv_pin + f".outputMatrix[{i}]"))
        cmds.setAttr(mult_m + ".matrixIn[1]", m.inverse(), type="matrix")
        cmds.connectAttr(uv_pin + f".outputMatrix[{i}]", mult_m + ".matrixIn[2]")
        up_matrices.append(mult_m + ".matrixSum")

    outputs = []
    for i in range(len(pos_matrices) - 1):
        aim_m = cmds.createNode("aimMatrix")
        cmds.setAttr(aim_m + ".primaryInputAxis", *primary_vector)
        cmds.setAttr(aim_m + ".secondaryInputAxis", *secondary_vector)
        cmds.setAttr(aim_m + ".primaryMode", 1)
        cmds.setAttr(aim_m + ".secondaryMode", 1)

        cmds.connectAttr(pos_matrices[i], aim_m + ".inputMatrix")
        cmds.connectAttr(pos_matrices[i + 1], aim_m + ".primaryTargetMatrix")
        cmds.connectAttr(up_matrices[i], aim_m + ".secondaryTargetMatrix")

        output = cmds.createNode(
            "transform", parent=parent, name=name + f"_{i}_aimOutput"
        )
        cmds.connectAttr(aim_m + f".outputMatrix", output + ".offsetParentMatrix")
        outputs.append(output)
    return outputs


# endregion


# region bezier - nurbs layer
# endregion


# region bezier - nurbs layer
# endregion


# region blendshape transfer / import / export
def transfer_blendshape(
    source: str, destination: str, bs: str, smooth: int = 0
) -> None:
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
    cmds.setAttr(p_wrap + ".wrapMode", 0)
    cmds.setAttr(p_wrap + ".smoothInfluences", smooth)

    # rename
    transferred_bs = cmds.blendShape(destination)[0]
    cmds.rename(bs, "TEMPBLENDSHAPE")
    transferred_bs = cmds.rename(transferred_bs, bs)
    bs = cmds.rename("TEMPBLENDSHAPE", bs + "_transferred")

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
    weight_attrs = cmds.listAttr(bs + ".weight", multi=True)
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
            interface_mesh + "Shape.worldMesh[0]", connections=True, plugs=True
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
                interface_mesh + "Shape.worldMesh[0]", connections=True, plugs=True
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
                method = cmds.getAttr(driver[0] + ".combinationMethod")
                combination_shape = cmds.createNode("combinationShape")
                cmds.setAttr(combination_shape + ".combinationMethod", method)
                connections = cmds.listConnections(
                    driver[0] + ".inputWeight",
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
                    driver[0] + ".outputWeight",
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


def export_blendshape(directory: str, bs: str) -> None:
    directory_path = Path(directory)
    mesh = cmds.deformer(bs, geometry=True, query=True)[0]

    plug = cmds.listConnections(bs + ".originalGeometry[0]", plugs=True)[0]
    shape = plug.split(".")[0]
    new_transform = cmds.duplicate(shape)
    shape = cmds.listRelatives(new_transform, shapes=True, noIntermediate=True)
    if shape:
        cmds.delete(shape)
    orig_shape = cmds.ls(new_transform, dagObjects=True, intermediateObjects=True)[0]
    cmds.setAttr(orig_shape + ".intermediateObject", 0)

    new_transform = cmds.rename(new_transform, f"{bs}_shp")
    new_shape = cmds.listRelatives(new_transform, shapes=True)[0]
    new_shape = cmds.rename(new_shape, new_transform + "Shape")

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


def import_blendshape(directory: str) -> None:
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


def export_weights(directory: str, geometries: list, file_type: str = "xml") -> None:
    for geo in geometries:
        deformers = cmds.findDeformers(geo) or []
        for deformer in deformers:
            cmds.deformerWeights(
                f"{geo}__{deformer}.{file_type}",
                export=True,
                deformer=deformer,
                format=FILETYPE[file_type],
                path=directory,
            )


def import_weights(directory: str) -> None:
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
def get_deformer_chain(geometry: str) -> list:
    return cmds.deformableShape(geometry, chain=True) or []


def set_deformer_chain(geometry: str, chain: list) -> None:
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
