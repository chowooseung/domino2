# maya
from maya import cmds
from maya.api import OpenMaya as om  # type: ignore

# domino
from domino.core import nurbscurve, matrix

## matrix
ORIGINMATRIX = om.MMatrix()

## name
joint_name_convention = "{name}_{side}{index}_{description}_{extension}"
controller_name_convention = "{name}_{side}{index}_{description}_{extension}"

center = "C"
left = "L"
right = "R"

joint_extension = "jnt"
controller_extension = "ctl"
group_extension = "grp"
npo_extension = "npo"
loc_extension = "loc"
curve_extension = "crv"
polygon_extension = "poly"
ikh_extension = "ikh"


class Name:
    """rig 에 필요한 이름 생성.

    convention 을 사용해 controller, joint 등에 쓰일 이름을 생성합니다.

    convention 의 side 는 sideStrList 의 문자열로 적용됩니다

    Examples:
        create case1:
        >>> Name.create(
                convention=controllerNameConvention,
                name="arm",
                side="L",
                index=0,
                description="ik",
                extension=controllerExtension,
            )
        >>> # return : arm_l0_ik_ctl
        create case2:
        >>> # sideStrList 바꾸기.
        >>> Name.sideStrList = ["c", "lf", "rt"]
        >>> Name.create(
                convention=controllerNameConvention,
                name="arm",
                side="L",
                index=0,
                description="ik",
                extension=controllerExtension,
            )
        >>> # return : arm_lf0_ik_ctl

        createJointLabel case1:
        >>> Name.createJointLabel(
                name="arm",
                side="L",
                index=0,
                description="ik",
            )
        >>> # return : arm_S0_ik_jnt
    """

    controller_name_convention = controller_name_convention
    joint_name_convention = joint_name_convention
    side_str_list = side_list = [center, left, right]
    controller_extension = controller_extension
    joint_extension = joint_extension

    @classmethod
    def create(
        cls,
        convention: str,
        name: str = "null",
        side: str = "C",
        index: str | int = 0,
        description: str = "",
        extension: str = "",
    ) -> str:
        """
        Args:
            convention (str): jointNameConvention, controllerNameConvention
            name (str): rig parts 이름입니다.
            side (str): C, L, R
            index (str | int): parts 의 index 입니다.
            description (str, optional): 해당 이름의 설명. Defaults to "".
            extension (str, optional): 이름의 역할. npo, ctl, loc 등. Defaults to "".

        Returns:
            str: name
        """
        side_str = cls.side_str_list[cls.side_list.index(side)] if side else ""
        name = convention.format(
            name=name,
            side=side_str,
            index=index,
            description=description,
            extension=extension,
        )
        return "_".join([x for x in name.split("_") if x])

    @classmethod
    def create_joint_label(
        cls, name: str, side: str, index: str, description: str
    ) -> str:
        """create joint label
        Args:
            name (str): rig parts
            side (str): "C", "L", "R"
            index (str): parts 의 index 입니다.
            description (str): 설명.

        Returns:
            str: joint label
        """
        if side:
            side = "C" if cls.side_list.index(side) < 1 else "S"
        else:
            side = "C"
        name = cls.controller_name_convention.format(
            name=name,
            side=side,
            index=index,
            description=description,
            extension=cls.joint_extension,
        )
        return "_".join([x for x in name.split("_") if x])


class Transform:
    """
    name convention 을 입력받아 새로운 transform 을 생성하거나,
    기존 node 를 입력받아 사용할수있습니다.

    Examples:
        case 1:
        >>> transform = Transform(parent=None,
                                  name="null1",
                                  side="C",
                                  index=0,
                                  extension="ctl")
        >>> transform.create()

        case 2:
        >>> null1 = Transform(node="null1")
        >>> null1.setMatrix(om.MMatrix())
    """

    def __init__(
        self,
        parent: str = "",
        name: str = "null",
        side: str = "C",
        index: str | int = 0,
        description: str = "",
        extension: str = "",
        node: str = "",
        m: om.MMatrix | list = ORIGINMATRIX,
    ) -> None:
        """
        Args:
            parent (str, optional): parent node. Defaults to "".
            name (str, optional): name convention name. Defaults to "null".
            side (str, optional): Name.sideList 중 하나. Defaults to "C".
            index (str | int, optional): name convention index. Defaults to 0.
            description (str, optional): name convention description. Defaults to "".
            extension (str, optional): name convention extension. Defaults to "".
            node (str, optional): 이미 존재하는 node. Defaults to "".
            m (om.MMatrix | list, optional): matrix. Defaults to om.MMatrix().
        """
        self._parent = parent
        self._m = list(m)
        self._description = description
        self._extension = extension

        self._node = Name.create(
            Name.controller_name_convention,
            name=name,
            side=side,
            index=index,
            description=description,
            extension=extension,
        )
        if node:
            assert cmds.objExists(node), f"{node} 가 존재하지 않습니다."
            self._node = node

    def __str__(self) -> str:
        return self._node

    def create(self) -> str:
        """create Transform

        Returns:
            str: node
        """
        if not cmds.objExists(self._node):
            self._node = cmds.createNode(
                "transform", parent=self._parent, name=self._node
            )
            cmds.addAttr(self._node, longName="description", dataType="string")
            cmds.setAttr(self._node + ".description", self._description, type="string")
            cmds.addAttr(self._node, longName="extension", dataType="string")
            cmds.setAttr(self._node + ".extension", self._extension, type="string")
        self.set_matrix(self._m)
        return self._node

    def get_parent(self) -> str:
        """get parent node

        Returns:
            str: parent node
        """
        p = cmds.listRelatives(self._node, parent=True)
        self._parent = p[0] if p else ""
        return self._parent

    def set_parent(self, parent: str) -> None:
        """set parent node

        Args:
            parent (str): parent node
        """
        (
            cmds.parent(self._node, parent)
            if parent
            else cmds.parent(self._node, world=True)
        )
        self._parent = parent

    def get_matrix(self) -> om.MMatrix:
        """get worldMatrix

        Returns:
            worldMatrix
        """
        self._m = cmds.xform(self._node, query=True, matrix=True, worldSpace=True)
        return om.MMatrix(self._m)

    def set_matrix(self, m: om.MMatrix | list) -> None:
        """set Matrix

        Args:
            m (om.MMatrix | list): worldMatrix
        """
        self._m = list(m)
        cmds.xform(self._node, matrix=m, worldSpace=True)


class Joint(Transform):
    """
    Joint 를 생성합니다.
    Transform class 의 기능을 상속받고 joint에 필요한 기능이 추가되었습니다.

    jointConvention 이 True 라면 nameConvention이 jointNameConvention으로 이름이 생성됩니다.
    False 라면 controllerNameConvention으로 적용됩니다.

    Examples:
        case 1:
        >>> joint = Joint(parent=None,
                          name="null1",
                          side="C",
                          index=0,
                          extension="ctl")
        >>> joint.create()

        case 2:
        >>> null1 = Joint(node="null1")
        >>> null1.setMatrix(om.MMatrix())
    """

    def __init__(
        self,
        parent: str = "",
        name: str = "null",
        side: str = "C",
        index: str | int = 0,
        description: str = "",
        extension: str = joint_extension,
        node: str = "",
        m: om.MMatrix | list = ORIGINMATRIX,
        use_joint_convention: bool = True,
    ) -> None:
        """
        Args:
            parent (str, optional): parent node. Defaults to "".
            name (str, optional): name convention name. Defaults to "null".
            side (str, optional): Name.sideList 중 하나. Defaults to "C".
            index (str | int, optional): name convention index. Defaults to 0.
            description (str, optional): name convention description. Defaults to "".
            extension (str, optional): name convention extension. Defaults to "".
            node (str, optional): 이미 존재하는 node. Defaults to "".
            m (om.MMatrix | list, optional): matrix. Defaults to om.MMatrix().
            useJointConvention (bool, optional): use joint name convention. Defaults to True.
        """
        self._parent = parent
        self._m = list(m)
        self.label_args = (
            Name.side_list.index(side) if side else 0,
            Name.create_joint_label(name, side, index, description),
        )
        self._description = description
        self._extension = extension

        self._node = Name.create(
            (
                Name.joint_name_convention
                if use_joint_convention
                else Name.controller_name_convention
            ),
            name=name,
            side=side,
            index=index,
            description=description,
            extension=extension,
        )
        if node:
            assert cmds.objExists(node), f"{node} 가 존재하지 않습니다."
            self._node = node

    def create(self) -> str:
        """create joint

        Returns:
            str: node
        """
        if not cmds.objExists(self._node):
            self._node = cmds.createNode("joint", parent=self._parent, name=self._node)
            cmds.addAttr(self._node, longName="description", dataType="string")
            cmds.setAttr(self._node + ".description", self._description, type="string")
            cmds.addAttr(self._node, longName="extension", dataType="string")
            cmds.setAttr(self._node + ".extension", self._extension, type="string")
        self.set_initialize_matrix(self._m)
        cmds.setAttr(self._node + ".segmentScaleCompensate", 0)
        self.set_label(*self.label_args)
        return self._node

    def set_initialize_matrix(self, m: om.MMatrix | list) -> None:
        """set matrix, set jointOrient

        Args:
            m (om.MMatrix): worldMatrix
        """
        self.set_matrix(m)
        cmds.makeIdentity(
            self._node, apply=True, translate=True, rotate=True, scale=True
        )

    def set_label(self, side: int, label: str) -> None:
        """set joint label

        Args:
            side (str): ["Center", "Left", "Right", "None"] 의 index
            label (str): label

        Examples:
            case 1:
            >>> joint.setLabel(1, "arm_S0_0_jnt") # S is side

            case 2:
            >>> joint.setLabel(0, "arm_C0_0_jnt")
        """
        cmds.setAttr(self._node + ".type", 18)
        cmds.setAttr(self._node + ".side", side)
        cmds.setAttr(self._node + ".otherType", label, type="string")


class Controller(Transform):
    """
    Controller 를 생성합니다.
    Transform class 의 기능을 상속받고 controller에 필요한 기능이 추가되었습니다.

    controller 는 아래의 hierarchy 구조를 가집니다.

    [hierarchy]
    - npo(보통 zero out 이라고 하는 neutral pose group)
        - ctl(animation controller)

    dagmenu 에서 구분을 위해 is_domino_controller attribute 가 추가됩니다.

    mirror 기능으로 mirror_type attribute 가 추가됩니다.
    mirror_type 은 orientation, behavior, inverseScale 가 있습니다
    orientation, behavior 는 joint mirror option 과 같습니다.
    inverseScale 은 상위 group scaleX 에 -1 한 matrix 입니다.

    controller tag 는 적용 되지만 tag node 의 parent child 기능이 부족해서
    parent child 는 tag node 와 별개로 구현됩니다.

    Examples:
        case 1:
        >>> controller = Controller(
                parent=None,
                parent_controllers=[],
                name="null1",
                side="C",
                index=0,
                description="ik",
                extension="ctl",
                shape="cube",
                color=17
            )
        >>> controller.create()

        case 2:
        >>> null1 = Joint(node="null1")
        >>> null1.setMatrix(om.MMatrix())
    """

    def __init__(
        self,
        parent: str = "",
        parent_controllers: list = "",
        name: str = "null",
        side: str = "C",
        index: str | int = 0,
        description: str = "",
        extension: str = "",
        node: str = "",
        m: om.MMatrix | list = ORIGINMATRIX,
        shape: str | dict = "",
        color: om.MColor | int = 0,
    ) -> None:
        """
        Args:
            parent (str, optional): npo 의 parent node. Defaults to "".
            parent_controllers (list, optional): dagmenu 에서 사용할 parent controllers. Defaults to "".
            name (str, optional): name convention name. Defaults to "null".
            side (str, optional): Name.sideList 중 하나. Defaults to "C".
            index (str | int, optional): name convention index. Defaults to 0.
            description (str, optional): name convention description. Defaults to "".
            extension (str, optional): name convention extension. Defaults to "".
            node (str, optional): 이미 존재하는 node. Defaults to "".
            m (om.MMatrix | list, optional): matrix. Defaults to om.MMatrix().
            shape (str, optional): controller shape name. Defaults to "".
            color (om.MColor | int, optional): controller shape color. Defaults to 0.
        """
        self._parent = parent
        self._parent_controllers = parent_controllers
        self._m = list(m)
        self._shape = shape
        self._color = color
        self._name = name
        self._side = side
        self._index = index
        self._description = description
        self._extension = extension

        self._npo = Name.create(
            Name.controller_name_convention,
            name=name,
            side=side,
            index=index,
            description=description,
            extension=npo_extension,
        )
        self._node = Name.create(
            Name.controller_name_convention,
            name=name,
            side=side,
            index=index,
            description=description,
            extension=extension,
        )
        if side:
            mirror_side = side
            if Name.side_list.index(side) == 1:
                mirror_side = Name.side_list[2]
            elif Name.side_list.index(side) == 2:
                mirror_side = Name.side_list[1]
        else:
            mirror_side = ""
        self._mirror_controller = Name.create(
            Name.controller_name_convention,
            name=name,
            side=mirror_side,
            index=index,
            description=description,
            extension=extension,
        )
        if node:
            assert cmds.objExists(node), f"{node} 가 존재하지 않습니다."
            self._node = node

    @property
    def root(self) -> str:
        return cmds.listConnections(
            self._node + ".message", source=False, destination=True, type="transform"
        )[0]

    @property
    def npo(self) -> str:
        """get npo

        Returns:
            str: npo node
        """
        plugs = cmds.listConnections(
            self._node + ".npo", source=True, destination=False
        )
        if plugs:
            self._npo = plugs[0]
        return self._npo

    def create(self) -> tuple:
        """create npo, ctl, loc

        Returns:
            tuple: npo node, ctl node, loc node
        """
        if not cmds.objExists(self._npo):
            ins = Transform(
                parent=self._parent,
                name=self._name,
                side=self._side,
                index=self._index,
                description=self._description,
                extension=npo_extension,
                m=ORIGINMATRIX,
            )
            self._npo = ins.create()
        if not cmds.objExists(self._node):
            ins = Transform(
                parent=self._npo,
                name=self._name,
                side=self._side,
                index=self._index,
                description=self._description,
                extension=self._extension,
                m=ORIGINMATRIX,
            )
            self._node = ins.create()
            cmds.setAttr(self._node + ".v", keyable=False)
            self.replace_shape(shape=self._shape, color=self._color)
            cmds.addAttr(
                self._node,
                longName="is_domino_controller",
                attributeType="bool",
                keyable=False,
            )
            cmds.addAttr(
                self._node,
                longName="mirror_controller_name",
                dataType="string",
            )
            cmds.setAttr(
                self._node + ".mirror_controller_name",
                self._mirror_controller,
                type="string",
            )
            cmds.addAttr(
                self._node,
                longName="mirror_type",
                attributeType="enum",
                enumName="orientation:behavior:inverseScale",
                keyable=False,
                defaultValue=1,
            )
            cmds.addAttr(self._node, longName="npo", attributeType="message")

        self.set_matrix(self._m)

        if not cmds.listConnections(
            self._node + ".npo", source=True, destination=False
        ):
            cmds.connectAttr(self._npo + ".message", self._node + ".npo")

        if not cmds.objExists(self._node + ".parent_controllers"):
            cmds.addAttr(
                self._node,
                longName="parent_controllers",
                attributeType="message",
                multi=True,
            )
        if not cmds.objExists(self._node + ".child_controllers"):
            cmds.addAttr(
                self._node, longName="child_controllers", attributeType="message"
            )
        cmds.controller(self._node)
        [self.add_parent_controller(c) for c in self._parent_controllers]
        return self._npo, self._node

    def get_parent(self) -> str:
        """get npo parent

        Returns:
            str: parent node
        """
        p = cmds.listRelatives(self.npo, parent=True)
        return p[0] if p else ""

    def replace_shape(self, shape: str | dict, color: om.MColor | int) -> None:
        """replace controller shape

        Args:
            shape (str): nurbscurve.create shape name
            color (om.MColor | int): controller color
        """
        if isinstance(shape, str):
            node = nurbscurve.create(shape, color)
            nurbscurve.replace_shape(node, self._node)
            cmds.delete(node)
        elif isinstance(shape, dict):
            shape["curve_name"] = "TEMPCRV1"
            crv = Curve()
            crv.data = shape
            crv = crv.create_from_data()
            nurbscurve.replace_shape(crv, self._node)
            cmds.delete(crv)

    def translate_shape(self, t: list) -> None:
        """move controller shape

        Args:
            t (list): translate
        """
        nurbscurve.translate_shape(self._node, t)

    def rotate_shape(self, r: list) -> None:
        """rotate controller shape

        Args:
            r (list): rotate
        """
        nurbscurve.rotate_shape(self._node, r)

    def scale_shape(self, s: list) -> None:
        """scale controller shape

        Args:
            s (list): scale
        """
        nurbscurve.scale_shape(self._node, s)

    def mirror_shape(self) -> None:
        """mirror controller shape"""
        nurbscurve.mirror_shape(self._node)

    def add_parent_controller(self, parent_controller: str) -> None:
        """dagmenu 에서 사용하기위해 parent controller 를 추가합니다.

        Args:
            parentController (str): domino controller node
        """
        assert cmds.objExists(
            parent_controller + ".is_domino_controller"
        ), f"{parent_controller} 는 domino controller 가 아닙니다."
        plugs = (
            cmds.listConnections(
                self._node + ".parent_controllers", source=True, destination=False
            )
            or []
        )

        if parent_controller not in plugs:
            next_number = len(plugs)
            cmds.connectAttr(
                parent_controller + ".child_controllers",
                self._node + f".parent_controllers[{next_number}]",
            )

    def set_matrix(self, m: om.MMatrix) -> None:
        """set matrix npo

        Args:
            m (om.MMatrix): worldMatrix
        """
        self._m = m
        cmds.xform(self._npo, matrix=m, worldSpace=True)

    @staticmethod
    def get_child_controller(node: str) -> list:
        """get child controller list

        dagmenu 에서 사용합니다.

        Args:
            node (str): domino controller

        Returns:
            list: child controller list
        """
        children = []

        def get_child(_node):
            children_node = (
                cmds.listConnections(
                    _node + ".child_controllers", source=False, destination=True
                )
                or []
            )

            [children.append(c) for c in children_node]
            for child in children_node:
                get_child(child)

        get_child(node)
        return children

    @staticmethod
    def get_mirror_RT(node: str) -> tuple:
        """get mirror translate, rotate value

        dagmenu 에서 사용합니다.

        Args:
            node (str): domino controller

        Returns:
            tuple: translate, rotate
        """
        ORIENTATION = 0
        BEHAVIOR = 1
        t = cmds.getAttr(node + ".t")[0]
        r = cmds.getAttr(node + ".r")[0]
        if cmds.getAttr(node + ".mirror_type") == ORIENTATION:
            return (t[0] * -1, t[1], t[2]), (r[0] * -1, r[1] * -1, r[2] * -1)
        elif cmds.getAttr(node + ".mirror_type") == BEHAVIOR:
            return (t[0] * -1, t[1] * -1, t[2] * -1), (r[0], r[1], r[2])
        return t, r

    @staticmethod
    def get_mirror_matrix(
        node: str, plane_matrix: om.MMatrix = ORIGINMATRIX
    ) -> om.MMatrix:
        """get mirror matrix

        mirror type 으로 mirror matrix 를 구합니다.
        dagmenu 에서 사용합니다.

        Args:
            node (str): domino controller
            planeMatrix (om.MMatrix, optional): custom plane matrix. Defaults to originMatrix.

        Returns:
            om.MMatrix: mirror matrix
        """
        ORIENTATION = 0
        BEHAVIOR = 1
        m = cmds.xform(node, query=True, matrix=True, worldSpace=True)
        if cmds.getAttr(node + ".mirror_type") == ORIENTATION:
            return matrix.get_mirror_matrix(m, plane_m=plane_matrix)
        elif cmds.getAttr(node + ".mirror_type") == BEHAVIOR:
            return matrix.get_mirror_matrix(m, behavior=True, plane_m=plane_matrix)
        return matrix.get_mirror_matrix(m, inverse_scale=True, plane_m=plane_matrix)

    @staticmethod
    def reset(node: str) -> None:
        attrs = [".tx", ".ty", ".tz", ".rx", ".ry", ".rz"]
        for attr in attrs:
            if cmds.getAttr(node + attr, lock=True):
                continue
            cmds.setAttr(node + attr, 0)
        attrs = [".sx", ".sy", ".sz"]
        for attr in attrs:
            if cmds.getAttr(node + attr, lock=True):
                continue
            cmds.setAttr(node + attr, 1)
        attrs = ["." + x for x in cmds.listAttr(node, userDefined=True, keyable=True)]
        for attr in attrs:
            default_value = cmds.addAttr(node + attr, query=True, defaultValue=True)
            cmds.setAttr(node + attr, default_value)


class Curve:
    """nurbscurve data

    Examples:
        curve data:
        >>> curve1 = Curve(node="nurbsCurve1")
        >>> print(curve1.data)
        curve create:
        >>> circle = Curve(node="circle")
        >>> newCurve = Curve(data=circle.data)
        >>> newCurve.createFromData()
    """

    def __init__(self, node: str = None, data: dict = None) -> None:
        """

        Args:
            node (str, optional): curve node. Defaults to None.
            data (dict, optional): curve data. Defaults to None.
        """
        self._data = {}
        self._node = ""
        if node:
            self.node = node
        elif data:
            self.data = data

    @staticmethod
    def get_fn_curve(shape: str) -> om.MFnNurbsCurve:
        """get openmaya MFnNurbsCurve

        Args:
            shape (str): curve shape

        Returns:
            om.MFnNurbsCurve: fncurve
        """
        selection_list = om.MSelectionList()
        selection_list.add(shape)
        return om.MFnNurbsCurve(selection_list.getDagPath(0))

    @property
    def data(self) -> dict:
        """get curve data(dict)

        Returns:
            dict: curve data
        """
        return self._data

    @property
    def node(self) -> str:
        """get node

        Returns:
            str: node
        """
        return self._node

    @data.setter
    def data(self, d: dict) -> None:
        """set curve data

        Args:
            d (dict): curve data
        """
        self._data = d

    @node.setter
    def node(self, n: str) -> None:
        """set curve data from node

        Args:
            n (str): node
        """
        parent = cmds.listRelatives(n, parent=True)
        self._data = {
            "parent_name": parent[0] if parent else "",
            "curve_name": n,
            "curve_matrix": cmds.xform(n, query=True, matrix=True, worldSpace=True),
            "shapes": {},
        }

        for shape in cmds.listRelatives(n, shapes=True, fullPath=True) or []:
            fn_curve = self.get_fn_curve(shape)
            self._data["shapes"][shape.split("|")[-1]] = {
                "form": fn_curve.form,
                "knots": list(fn_curve.knots()),
                "degree": fn_curve.degree,
                "point": [
                    list(x)[:-1] for x in fn_curve.cvPositions(om.MSpace.kObject)
                ],
                "override": cmds.getAttr(shape + ".overrideEnabled"),
                "use_rgb": cmds.getAttr(shape + ".overrideRGBColors"),
                "color_rgb": cmds.getAttr(shape + ".overrideColorRGB")[0],
                "color_index": cmds.getAttr(shape + ".overrideColor"),
            }
        self._node = n

    def create_from_data(self) -> str:
        """create curve from data

        Returns:
            str: new node
        """
        transform = cmds.createNode("transform", name=self._data["curve_name"])

        for data in self._data["shapes"].values():
            shape_transform = cmds.curve(
                name="TEMPSHAPENAME",
                point=data["point"],
                periodic=False if data["form"] == 1 else True,
                degree=data["degree"],
                knot=data["knots"],
            )
            shape = cmds.listRelatives(shape_transform, shapes=True, fullPath=True)[0]
            cmds.setAttr(shape + ".overrideEnabled", data["override"])
            cmds.setAttr(shape + ".overrideRGBColors", data["use_rgb"])
            cmds.setAttr(shape + ".overrideColorRGB", *data["color_rgb"])
            cmds.setAttr(shape + ".overrideColor", data["color_index"])
            shape = cmds.rename(shape, transform.split("|")[-1] + "Shape")
            cmds.parent(shape, transform, relative=True, shape=True)
            cmds.delete(shape_transform)
        cmds.xform(transform, matrix=[float(x) for x in self._data["curve_matrix"]])
        if self._data["parent_name"] and cmds.objExists(self._data["parent_name"]):
            transform = cmds.parent(transform, self._data["parent_name"])[0]
        return transform

    def create(
        self,
        parent: str,
        name: str,
        degree: int,
        point: list,
        m: om.MMatrix | list = ORIGINMATRIX,
    ) -> str:
        """create curve

        Args:
            parent (str): parent node
            name (str): curve name
            degree (int): degree
            point (list): shape position
            m (om.MMtrix | list, optional): worldMatrix. Defaults to originMatrix.

        Returns:
            str: new node
        """
        args = {"name": name, "degree": degree, "point": point}

        curve = cmds.curve(**args)
        curve = cmds.rename(curve, name)
        cmds.rename(cmds.listRelatives(curve, shapes=True)[0], curve + "Shape")
        if parent:
            curve = cmds.parent(curve, parent)[0]

        cmds.xform(curve, matrix=m, worldSpace=True)
        self.node = curve
        return curve


class Polygon:

    def __init__(self, node: str = None, data: dict = None) -> None:
        self._data = {}
        self._node = ""
        if node:
            self.node = node
        elif data:
            self.data = data

    @property
    def data(self) -> dict:
        return self._data

    @property
    def node(self) -> list:
        return self._node

    @data.setter
    def data(self, d: dict) -> None:
        self._data = d

    @node.setter
    def node(self, n: str) -> None:
        self._node = n


class FCurve:
    """anim curve data

    timeInput : maya time anim curve type
    doubleInput : maya double anim curve type

    Examples:
        fcurve data:
        >>> fcurve1 = FCurve(attribute="cube1.tx")
        >>> print(fcurve1.data)
        fcurve move:
        >>> fcurve1 = FCurve(attribute="cube1.tx")
        >>> fcurve1.data["driven"] = "cube2.tx"
        >>> fcurve1.createFromData()
    """

    time_input = ["animCurveTL", "animCurveTA", "animCurveTT", "animCurveTU"]
    double_input = ["animCurveUL", "animCurveUA", "animCurveUT", "animCurveUU"]

    def __init__(self, attribute: str = None, data: dict = None) -> None:
        self._data = {}
        self._nodes = []
        if attribute:
            self.attribute = attribute
        elif data:
            self.data = data

    @property
    def data(self) -> dict:
        return self._data

    @property
    def attribute(self) -> list:
        return self._nodes

    @data.setter
    def data(self, d: dict) -> None:
        self._data = d

    @attribute.setter
    def attribute(self, attribute: str) -> None:
        source = cmds.listConnections(attribute, source=True, destination=False) or []
        if not source:
            return
        if cmds.nodeType(source[0]) == "blendWeighted":
            source = (
                cmds.listConnections(source[0], source=True, destination=False) or []
            )
        data = {}
        data["driven"] = attribute
        for src in source:
            data["name"] = {}
            _data = data["name"]
            _data["type"] = cmds.nodeType(src)
            if cmds.nodeType(src) in self.time_input:
                _data["time"] = cmds.keyframe(src, query=True)
            elif cmds.nodeType(src) in self.double_input:
                _data["driver"] = None
                _data["float_change"] = cmds.keyframe(src, query=True, floatChange=True)
            _data["value_change"] = cmds.keyframe(src, query=True, valueChange=True)
            _data["in_angle"] = cmds.keyframe(src, query=True, inAngle=True)
            _data["out_angle"] = cmds.keyframe(src, query=True, outAngle=True)
            _data["in_weight"] = cmds.keyframe(src, query=True, inWeight=True)
            _data["out_weight"] = cmds.keyframe(src, query=True, outWeight=True)
            _data["in_tangent_type"] = cmds.keyframe(
                src, query=True, inTangentType=True
            )
            _data["out_tangent_type"] = cmds.keyframe(
                src, query=True, outTangentType=True
            )
            _data["weighted_tangents"] = cmds.keyframe(
                src, query=True, weightedTangents=True
            )
            _data["lock"] = cmds.keyframe(src, query=True, lock=True)
        self._data = data
        self._nodes = source

    def create_from_data(self) -> list:
        keyframes = []
        for name, data in self._data.items():
            keyframe = cmds.createNode(data["type"], name=name)
            if data["type"] in self.time_input:
                for time, value in zip(data["time"], data["value_change"]):
                    cmds.setKeyframe(keyframe, edit=True, float=time, value=value)
            elif data["type"] in self.double_input:
                for driverValue, value in zip(
                    data["float_change"], data["value_change"]
                ):
                    cmds.setDrivenKeyframe(
                        keyframe,
                        edit=True,
                        driver=data["driver"],
                        driven=self._data["driven"],
                        driverValue=driverValue,
                        value=value,
                    )
            cmds.keyTangent(keyframe, edit=True, weightedTangents=True)
            for i in range(len(data["value_change"])):
                cmds.keyTangent(keyframe, edit=True, index=(i, i), lock=False)
                cmds.keyTangent(
                    keyframe, edit=True, index=(i, i), itt=data["in_tangent_type"][i]
                )
                cmds.keyTangent(
                    keyframe, edit=True, index=(i, i), ott=data["out_tangent_type"][i]
                )
                cmds.keyTangent(
                    keyframe, edit=True, index=(i, i), ia=data["in_angle"][i]
                )
                cmds.keyTangent(
                    keyframe, edit=True, index=(i, i), oa=data["out_angle"][i]
                )
                cmds.keyTangent(
                    keyframe, edit=True, index=(i, i), iw=data["in_weight"][i]
                )
                cmds.keyTangent(
                    keyframe, edit=True, index=(i, i), ow=data["out_weight"][i]
                )
                cmds.keyTangent(keyframe, edit=True, index=(i, i), lock=data["lock"][i])
            cmds.keyTangent(
                keyframe, edit=True, weightedTangents=data["weighted_tangents"][0]
            )
            keyframes.append(keyframe)
        return keyframes
