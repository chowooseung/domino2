# maya
from maya import cmds
from maya.api import OpenMaya as om  # type: ignore

# domino
from domino.core import nurbscurve, matrix

## matrix
originMatrix = om.MMatrix()

## name
jointNameConvention = "{name}_{side}{index}_{description}_{extension}"
controllerNameConvention = "{name}_{side}{index}_{description}_{extension}"

center = "C"
left = "L"
right = "R"

jointExtension = "jnt"
controllerExtension = "ctl"
groupExtension = "grp"
npoExtension = "npo"
locExtension = "loc"
curveExtension = "crv"
polygonExtension = "poly"
ikhExtension = "ikh"


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

    controllerNameConvention = controllerNameConvention
    jointNameConvention = jointNameConvention
    sideStrList = sideList = [center, left, right]
    controllerExtension = controllerExtension
    jointExtension = jointExtension

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
        sideStr = cls.sideStrList[cls.sideList.index(side)] if side else ""
        name = convention.format(
            name=name,
            side=sideStr,
            index=index,
            description=description,
            extension=extension,
        )
        return "_".join([x for x in name.split("_") if x])

    @classmethod
    def createJointLabel(
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
            side = "C" if cls.sideList.index(side) < 1 else "S"
        else:
            side = "C"
        name = cls.controllerNameConvention.format(
            name=name,
            side=side,
            index=index,
            description=description,
            extension=cls.jointExtension,
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
        m: om.MMatrix | list = originMatrix,
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
            Name.controllerNameConvention,
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
        self.setMatrix(self._m)
        return self._node

    def getParent(self) -> str:
        """get parent node

        Returns:
            str: parent node
        """
        p = cmds.listRelatives(self._node, parent=True)
        self._parent = p[0] if p else ""
        return self._parent

    def setParent(self, parent: str) -> None:
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

    def getMatrix(self) -> om.MMatrix:
        """get worldMatrix

        Returns:
            worldMatrix
        """
        self._m = cmds.xform(self._node, query=True, matrix=True, worldSpace=True)
        return om.MMatrix(self._m)

    def setMatrix(self, m: om.MMatrix | list) -> None:
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
        extension: str = jointExtension,
        node: str = "",
        m: om.MMatrix | list = originMatrix,
        useJointConvention: bool = True,
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
        self.labelArgs = (
            Name.sideList.index(side) if side else 0,
            Name.createJointLabel(name, side, index, description),
        )
        self._description = description
        self._extension = extension

        self._node = Name.create(
            (
                Name.jointNameConvention
                if useJointConvention
                else Name.controllerNameConvention
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
        self.setInitializeMatrix(self._m)
        cmds.setAttr(self._node + ".segmentScaleCompensate", 0)
        self.setLabel(*self.labelArgs)
        return self._node

    def setInitializeMatrix(self, m: om.MMatrix | list) -> None:
        """set matrix, set jointOrient

        Args:
            m (om.MMatrix): worldMatrix
        """
        self.setMatrix(m)
        cmds.makeIdentity(
            self._node, apply=True, translate=True, rotate=True, scale=True
        )

    def setLabel(self, side: int, label: str) -> None:
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

    dagmenu 에서 구분을 위해 isDominoController attribute 가 추가됩니다.

    mirror 기능으로 mirrorType attribute 가 추가됩니다.
    mirrorType 은 orientation, behavior, inverseScale 가 있습니다
    orientation, behavior 는 joint mirror option 과 같습니다.
    inverseScale 은 상위 group scaleX 에 -1 한 matrix 입니다.

    controller tag 는 적용 되지만 tag node 의 parent child 기능이 부족해서
    parent child 는 tag node 와 별개로 구현됩니다.

    Examples:
        case 1:
        >>> controller = Controller(
                parent=None,
                parentControllers=[],
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
        parentControllers: list = "",
        name: str = "null",
        side: str = "C",
        index: str | int = 0,
        description: str = "",
        extension: str = "",
        node: str = "",
        m: om.MMatrix | list = originMatrix,
        shape: str = "",
        color: om.MColor | int = 0,
    ) -> None:
        """
        Args:
            parent (str, optional): npo 의 parent node. Defaults to "".
            parentControllers (list, optional): dagmenu 에서 사용할 parent controllers. Defaults to "".
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
        self._parentControllers = parentControllers
        self._m = list(m)
        self._shape = shape
        self._color = color
        self._name = name
        self._side = side
        self._index = index
        self._description = description
        self._extension = extension

        self._npo = Name.create(
            Name.controllerNameConvention,
            name=name,
            side=side,
            index=index,
            description=description,
            extension=npoExtension,
        )
        self._node = Name.create(
            Name.controllerNameConvention,
            name=name,
            side=side,
            index=index,
            description=description,
            extension=extension,
        )
        if side:
            mirrorSide = side
            if Name.sideList.index(side) == 1:
                mirrorSide = Name.sideList[2]
            elif Name.sideList.index(side) == 2:
                mirrorSide = Name.sideList[1]
        else:
            mirrorSide = ""
        self._mirrorController = Name.create(
            Name.controllerNameConvention,
            name=name,
            side=mirrorSide,
            index=index,
            description=description,
            extension=extension,
        )
        if node:
            assert cmds.objExists(node), f"{node} 가 존재하지 않습니다."
            self._node = node

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
                extension=npoExtension,
                m=originMatrix,
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
                m=originMatrix,
            )
            self._node = ins.create()
            cmds.setAttr(self._node + ".v", keyable=False)
            self.replaceShape(shape=self._shape, color=self._color)
            cmds.addAttr(
                self._node,
                longName="isDominoController",
                attributeType="bool",
                keyable=False,
            )
            cmds.addAttr(
                self._node,
                longName="mirrorControllerName",
                dataType="string",
            )
            cmds.setAttr(
                self._node + ".mirrorControllerName",
                self._mirrorController,
                type="string",
            )
            cmds.addAttr(
                self._node,
                longName="mirrorType",
                attributeType="enum",
                enumName="orientation:behavior:inverseScale",
                keyable=False,
                defaultValue=1,
            )
            cmds.addAttr(self._node, longName="npo", attributeType="message")

        self.setMatrix(self._m)

        if not cmds.listConnections(
            self._node + ".npo", source=True, destination=False
        ):
            cmds.connectAttr(self._npo + ".message", self._node + ".npo")

        if not cmds.objExists(self._node + ".parentControllers"):
            cmds.addAttr(
                self._node,
                longName="parentControllers",
                attributeType="message",
                multi=True,
            )
        if not cmds.objExists(self._node + ".childControllers"):
            cmds.addAttr(
                self._node, longName="childControllers", attributeType="message"
            )
        cmds.controller(self._node)
        [self.addParentController(c) for c in self._parentControllers]
        return self._npo, self._node

    def getParent(self) -> str:
        """get npo parent

        Returns:
            str: parent node
        """
        p = cmds.listRelatives(self.npo, parent=True)
        return p[0] if p else ""

    def replaceShape(self, shape: str, color: om.MColor | int) -> None:
        """replace controller shape

        Args:
            shape (str): nurbscurve.create shape name
            color (om.MColor | int): controller color
        """
        node = nurbscurve.create(shape, color)
        nurbscurve.replaceShape(node, self._node)
        cmds.delete(node)

    def translateShape(self, t: list) -> None:
        """move controller shape

        Args:
            t (list): translate
        """
        nurbscurve.translateShape(self._node, t)

    def rotateShape(self, r: list) -> None:
        """rotate controller shape

        Args:
            r (list): rotate
        """
        nurbscurve.rotateShape(self._node, r)

    def scaleShape(self, s: list) -> None:
        """scale controller shape

        Args:
            s (list): scale
        """
        nurbscurve.scaleShape(self._node, s)

    def mirrorShape(self) -> None:
        """mirror controller shape"""
        nurbscurve.mirrorShape(self._node)

    def addParentController(self, parentController: str) -> None:
        """dagmenu 에서 사용하기위해 parent controller 를 추가합니다.

        Args:
            parentController (str): domino controller node
        """
        assert cmds.objExists(
            parentController + ".isDominoController"
        ), f"{parentController} 는 domino controller 가 아닙니다."
        plugs = (
            cmds.listConnections(
                self._node + ".parentControllers", source=True, destination=False
            )
            or []
        )

        if parentController not in plugs:
            next_number = len(plugs)
            cmds.connectAttr(
                parentController + ".childControllers",
                self._node + f".parentControllers[{next_number}]",
            )

    def setMatrix(self, m: om.MMatrix) -> None:
        """set matrix npo

        Args:
            m (om.MMatrix): worldMatrix
        """
        self._m = m
        cmds.xform(self._npo, matrix=m, worldSpace=True)

    @staticmethod
    def getChildController(node: str) -> list:
        """get child controller list

        dagmenu 에서 사용합니다.

        Args:
            node (str): domino controller

        Returns:
            list: child controller list
        """
        children = []

        def getChild(_node):
            childrenNode = (
                cmds.listConnections(
                    _node + ".childControllers", source=False, destination=True
                )
                or []
            )

            [children.append(c) for c in childrenNode]
            for child in childrenNode:
                getChild(child)

        getChild(node)
        return children

    @staticmethod
    def getMirrorRT(node: str) -> tuple:
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
        if cmds.getAttr(node + ".mirrorType") == ORIENTATION:
            return (t[0] * -1, t[1], t[2]), (r[0] * -1, r[1] * -1, r[2] * -1)
        elif cmds.getAttr(node + ".mirrorType") == BEHAVIOR:
            return (t[0] * -1, t[1] * -1, t[2] * -1), (r[0], r[1], r[2])
        return t, r

    @staticmethod
    def getMirrorMatrix(
        node: str, planeMatrix: om.MMatrix = originMatrix
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
        if cmds.getAttr(node + ".mirrorType") == ORIENTATION:
            return matrix.getMirrorMatrix(m, planeMatrix=planeMatrix)
        elif cmds.getAttr(node + ".mirrorType") == BEHAVIOR:
            return matrix.getMirrorMatrix(m, behavior=True, planeMatrix=planeMatrix)
        return matrix.getMirrorMatrix(m, inverseScale=True, planeMatrix=planeMatrix)

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
            defaultValue = cmds.addAttr(node + attr, query=True, defaultValue=True)
            cmds.setAttr(node + attr, defaultValue)


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
    def getFnCurve(shape: str) -> om.MFnNurbsCurve:
        """get openmaya MFnNurbsCurve

        Args:
            shape (str): curve shape

        Returns:
            om.MFnNurbsCurve: fncurve
        """
        selectionList = om.MSelectionList()
        selectionList.add(shape)
        return om.MFnNurbsCurve(selectionList.getDagPath(0))

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
            "parentName": parent[0] if parent else "",
            "curveName": n,
            "curveMatrix": cmds.xform(n, query=True, matrix=True, worldSpace=True),
            "shapes": {},
        }

        for shape in cmds.listRelatives(n, shapes=True, fullPath=True) or []:
            fn_curve = self.getFnCurve(shape)
            self._data["shapes"][shape.split("|")[-1]] = {
                "form": fn_curve.form,
                "knots": list(fn_curve.knots()),
                "degree": fn_curve.degree,
                "point": [
                    list(x)[:-1] for x in fn_curve.cvPositions(om.MSpace.kObject)
                ],
                "override": cmds.getAttr(shape + ".overrideEnabled"),
                "useRgb": cmds.getAttr(shape + ".overrideRGBColors"),
                "colorRgb": cmds.getAttr(shape + ".overrideColorRGB")[0],
                "colorIndex": cmds.getAttr(shape + ".overrideColor"),
            }
        self._node = n

    def createFromData(self) -> str:
        """create curve from data

        Returns:
            str: new node
        """
        transform = cmds.createNode("transform", name=self._data["curveName"])

        for data in self._data["shapes"].values():
            shapeTransform = cmds.curve(
                name="TEMPSHAPENAME",
                point=data["point"],
                periodic=False if data["form"] == 1 else True,
                degree=data["degree"],
                knot=data["knots"],
            )
            shape = cmds.listRelatives(shapeTransform, shapes=True, fullPath=True)[0]
            cmds.setAttr(shape + ".overrideEnabled", data["override"])
            cmds.setAttr(shape + ".overrideRGBColors", data["useRgb"])
            cmds.setAttr(shape + ".overrideColorRGB", *data["colorRgb"])
            cmds.setAttr(shape + ".overrideColor", data["colorIndex"])
            shape = cmds.rename(shape, transform.split("|")[-1] + "Shape")
            cmds.parent(shape, transform, relative=True, shape=True)
            cmds.delete(shapeTransform)
        cmds.xform(transform, matrix=[float(x) for x in self._data["curveMatrix"]])
        if self._data["parentName"] and cmds.objExists(self._data["parentName"]):
            transform = cmds.parent(transform, self._data["parentName"])[0]
        return transform

    def create(
        self,
        parent: str,
        name: str,
        degree: int,
        point: list,
        m: om.MMatrix | list = originMatrix,
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

    timeInput = ["animCurveTL", "animCurveTA", "animCurveTT", "animCurveTU"]
    doubleInput = ["animCurveUL", "animCurveUA", "animCurveUT", "animCurveUU"]

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
            if cmds.nodeType(src) in self.timeInput:
                _data["time"] = cmds.keyframe(src, query=True)
            elif cmds.nodeType(src) in self.doubleInput:
                _data["driver"] = None
                _data["floatChange"] = cmds.keyframe(src, query=True, floatChange=True)
            _data["valueChange"] = cmds.keyframe(src, query=True, valueChange=True)
            _data["inAngle"] = cmds.keyframe(src, query=True, inAngle=True)
            _data["outAngle"] = cmds.keyframe(src, query=True, outAngle=True)
            _data["inWeight"] = cmds.keyframe(src, query=True, inWeight=True)
            _data["outWeight"] = cmds.keyframe(src, query=True, outWeight=True)
            _data["inTangentType"] = cmds.keyframe(src, query=True, inTangentType=True)
            _data["outTangentType"] = cmds.keyframe(
                src, query=True, outTangentType=True
            )
            _data["weightedTangents"] = cmds.keyframe(
                src, query=True, weightedTangents=True
            )
            _data["lock"] = cmds.keyframe(src, query=True, lock=True)
        self._data = data
        self._nodes = source

    def createFromData(self) -> list:
        keyframes = []
        for name, data in self._data.items():
            keyframe = cmds.createNode(data["type"], name=name)
            if data["type"] in self.timeInput:
                for time, value in zip(data["time"], data["valueChange"]):
                    cmds.setKeyframe(keyframe, edit=True, float=time, value=value)
            elif data["type"] in self.doubleInput:
                for driverValue, value in zip(data["floatChange"], data["valueChange"]):
                    cmds.setDrivenKeyframe(
                        keyframe,
                        edit=True,
                        driver=data["driver"],
                        driven=self._data["driven"],
                        driverValue=driverValue,
                        value=value,
                    )
            cmds.keyTangent(keyframe, edit=True, weightedTangents=True)
            for i in range(len(data["valueChange"])):
                cmds.keyTangent(keyframe, edit=True, index=(i, i), lock=False)
                cmds.keyTangent(
                    keyframe, edit=True, index=(i, i), itt=data["inTangentType"][i]
                )
                cmds.keyTangent(
                    keyframe, edit=True, index=(i, i), ott=data["outTangentType"][i]
                )
                cmds.keyTangent(
                    keyframe, edit=True, index=(i, i), ia=data["inAngle"][i]
                )
                cmds.keyTangent(
                    keyframe, edit=True, index=(i, i), oa=data["outAngle"][i]
                )
                cmds.keyTangent(
                    keyframe, edit=True, index=(i, i), iw=data["inWeight"][i]
                )
                cmds.keyTangent(
                    keyframe, edit=True, index=(i, i), ow=data["outWeight"][i]
                )
                cmds.keyTangent(keyframe, edit=True, index=(i, i), lock=data["lock"][i])
            cmds.keyTangent(
                keyframe, edit=True, weightedTangents=data["weightedTangents"][0]
            )
            keyframes.append(keyframe)
        return keyframes
