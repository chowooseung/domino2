# maya
from maya import cmds
from maya.api import OpenMaya as om  # type: ignore

ORIGINMATRIX = om.MMatrix()


class Integer(dict):

    defaultValue = 0
    defaultMinValue = None
    defaultMaxValue = None
    defaultKeyable = False
    defaultLock = False
    defaultChannelBox = False
    defaultMulti = False
    attributeType = "long"

    @property
    def data(self) -> dict:
        return self[self._longName]

    @data.setter
    def data(self, d: dict) -> None:
        self[self._longName] = d

    @property
    def longName(self) -> str:
        return self._longName

    @longName.setter
    def longName(self, n: str) -> None:
        self._longName = n

    @property
    def node(self) -> str:
        return self.data["node"]

    @node.setter
    def node(self, n: str) -> None:
        self.data["node"] = n

    @property
    def attribute(self) -> str:
        return self.node + "." + self.longName

    def __init__(self, longName: str, **kwargs: dict) -> None:
        self.longName = longName
        self.data = {
            "minValue": (
                kwargs["minValue"] if "minValue" in kwargs else self.defaultMinValue
            ),
            "maxValue": (
                kwargs["minValue"] if "minValue" in kwargs else self.defaultMinValue
            ),
            "keyable": (
                kwargs["keyable"] if "keyable" in kwargs else self.defaultKeyable
            ),
            "lock": kwargs["lock"] if "lock" in kwargs else self.defaultLock,
            "channelBox": (
                kwargs["channelBox"]
                if "channelBox" in kwargs
                else self.defaultChannelBox
            ),
            "multi": kwargs["multi"] if "multi" in kwargs else self.defaultMulti,
            "attributeType": self.attributeType,
        }
        if self.data["multi"]:
            self.data.update(
                {"value": kwargs["value"] if "value" in kwargs else [self.defaultValue]}
            )
        else:
            self.data.update(
                {"value": kwargs["value"] if "value" in kwargs else self.defaultValue}
            )

    def create(self) -> str:
        data = self.data

        if "node" not in data:
            return ""

        try:
            cmds.addAttr(
                self.node,
                longName=self.longName,
                shortName=self.longName,
                attributeType=self.attributeType,
                multi=data["multi"],
            )
        except:
            None

        cmds.setAttr(self.attribute, keyable=data["keyable"])
        cmds.setAttr(self.attribute, lock=data["lock"])
        if data["channelBox"]:
            cmds.setAttr(self.attribute, channelBox=data["channelBox"])
        if data["minValue"] is not None:
            cmds.addAttr(
                self.attribute,
                edit=True,
                minValue=data["minValue"],
            )
        if data["maxValue"] is not None:
            cmds.addAttr(
                self.attribute,
                edit=True,
                minValue=data["maxValue"],
            )
        if data["multi"]:
            for i, v in enumerate(data["value"]):
                cmds.setAttr(f"{self.attribute}[{i}]", v)
        else:
            cmds.setAttr(self.attribute, data["value"])
        return self.attribute


class Float(Integer):

    attributeType = "float"


class Enum(dict):

    defaultValue = 0
    defaultKeyable = False
    defaultLock = False
    defaultChannelBox = False
    attributeType = "enum"

    @property
    def data(self) -> dict:
        return self[self._longName]

    @data.setter
    def data(self, d: dict) -> None:
        self[self._longName] = d

    @property
    def longName(self) -> str:
        return self._longName

    @longName.setter
    def longName(self, n: str) -> None:
        self._longName = n

    @property
    def node(self) -> str:
        return self.data["node"]

    @node.setter
    def node(self, n: str) -> None:
        self.data["node"] = n

    @property
    def attribute(self) -> str:
        return self.node + "." + self.longName

    def __init__(self, longName: str, enumName: list, **kwargs: dict) -> None:
        self.longName = longName
        self.data = {
            "enumName": enumName,
            "value": kwargs["value"] if "value" in kwargs else self.defaultValue,
            "keyable": (
                kwargs["keyable"] if "keyable" in kwargs else self.defaultKeyable
            ),
            "lock": kwargs["lock"] if "lock" in kwargs else self.defaultLock,
            "channelBox": (
                kwargs["channelBox"]
                if "channelBox" in kwargs
                else self.defaultChannelBox
            ),
            "attributeType": self.attributeType,
            "multi": False,
        }

    def create(self) -> str:
        data = self.data

        if "node" not in data:
            return ""

        try:
            cmds.addAttr(
                data["node"],
                longName=self.longName,
                shortName=self.longName,
                attributeType=self.attributeType,
                enumName="TEMP:TEMP",  # 넣어주지 않으면 enumName을 수정할 때 작동하지 않음.
            )
        except:
            None

        cmds.addAttr(
            self.attribute,
            edit=True,
            enumName=":".join(data["enumName"]),
        )
        cmds.setAttr(self.attribute, data["value"])
        cmds.setAttr(self.attribute, keyable=data["keyable"])
        cmds.setAttr(self.attribute, lock=data["lock"])
        if data["channelBox"]:
            cmds.setAttr(self.attribute, channelBox=data["channelBox"])
        return self.attribute


class Bool(dict):

    defaultValue = 0
    defaultKeyable = False
    defaultLock = False
    defaultChannelBox = False
    defaultMulti = False
    attributeType = "bool"

    @property
    def data(self) -> dict:
        return self[self._longName]

    @data.setter
    def data(self, d: dict) -> None:
        self[self._longName] = d

    @property
    def longName(self) -> str:
        return self._longName

    @longName.setter
    def longName(self, n: str) -> None:
        self._longName = n

    @property
    def node(self) -> str:
        return self.data["node"]

    @node.setter
    def node(self, n: str) -> None:
        self.data["node"] = n

    @property
    def attribute(self) -> str:
        return self.node + "." + self.longName

    def __init__(self, longName: str, **kwargs: dict) -> None:
        self.longName = longName
        self.data = {
            "keyable": (
                kwargs["keyable"] if "keyable" in kwargs else self.defaultKeyable
            ),
            "lock": kwargs["lock"] if "lock" in kwargs else self.defaultLock,
            "channelBox": (
                kwargs["channelBox"]
                if "channelBox" in kwargs
                else self.defaultChannelBox
            ),
            "multi": kwargs["multi"] if "multi" in kwargs else self.defaultMulti,
            "attributeType": self.attributeType,
        }
        if self.data["multi"]:
            self.data.update(
                {"value": kwargs["value"] if "value" in kwargs else [self.defaultValue]}
            )
        else:
            self.data.update(
                {"value": kwargs["value"] if "value" in kwargs else self.defaultValue}
            )

    def create(self) -> str:
        data = self.data

        if "node" not in data:
            return ""

        try:
            cmds.addAttr(
                self.node,
                longName=self.longName,
                shortName=self.longName,
                attributeType=self.attributeType,
                multi=data["multi"],
            )
        except:
            None

        cmds.setAttr(self.attribute, lock=data["lock"])
        cmds.setAttr(self.attribute, keyable=data["keyable"])
        if data["channelBox"]:
            cmds.setAttr(self.attribute, channelBox=data["channelBox"])
        if data["multi"]:
            for i, v in enumerate(data["value"]):
                cmds.setAttr(f"{self.attribute}[{i}]", v)
        else:
            cmds.setAttr(self.attribute, data["value"])
        return self.attribute


class String(dict):

    defaultValue = ""
    defaultLock = False
    defaultMulti = False
    dataType = "string"

    @property
    def data(self) -> dict:
        return self[self._longName]

    @data.setter
    def data(self, d: dict) -> None:
        self[self._longName] = d

    @property
    def longName(self) -> str:
        return self._longName

    @longName.setter
    def longName(self, n: str) -> None:
        self._longName = n

    @property
    def node(self) -> str:
        return self.data["node"]

    @node.setter
    def node(self, n: str) -> None:
        self.data["node"] = n

    @property
    def attribute(self) -> str:
        return self.node + "." + self.longName

    def __init__(self, longName: str, **kwargs: dict) -> None:
        self.longName = longName
        self.data = {
            "lock": kwargs["lock"] if "lock" in kwargs else self.defaultLock,
            "multi": kwargs["multi"] if "multi" in kwargs else self.defaultMulti,
            "dataType": self.dataType,
        }
        if self.data["multi"]:
            self.data.update(
                {"value": kwargs["value"] if "value" in kwargs else [self.defaultValue]}
            )
        else:
            self.data.update(
                {"value": kwargs["value"] if "value" in kwargs else self.defaultValue}
            )

    def create(self) -> str:
        data = self.data

        if "node" not in data:
            return ""

        try:
            cmds.addAttr(
                self.node,
                longName=self.longName,
                shortName=self.longName,
                dataType=self.dataType,
                multi=data["multi"],
            )
        except:
            None

        cmds.setAttr(self.attribute, lock=data["lock"])
        if data["multi"]:
            for i, v in enumerate(data["value"]):
                cmds.setAttr(f"{self.attribute}[{i}]", v, type="string")
        else:
            cmds.setAttr(self.attribute, data["value"], type="string")
        return self.attribute


class Matrix(dict):

    dataType = "matrix"
    defaultValue = list(ORIGINMATRIX)
    defaultMulti = False

    @property
    def data(self) -> dict:
        return self[self._longName]

    @data.setter
    def data(self, d: dict) -> None:
        self[self._longName] = d

    @property
    def longName(self) -> str:
        return self._longName

    @longName.setter
    def longName(self, n: str) -> None:
        self._longName = n

    @property
    def node(self) -> str:
        return self.data["node"]

    @node.setter
    def node(self, n: str) -> None:
        self.data["node"] = n

    @property
    def attribute(self) -> str:
        return self.node + "." + self.longName

    def __init__(self, longName: str, **kwargs: dict) -> None:
        self.longName = longName
        self.data = {
            "multi": kwargs["multi"] if "multi" in kwargs else self.defaultMulti,
            "dataType": self.dataType,
        }
        if self.data["multi"]:
            value = []
            for v in kwargs["value"] if "value" in kwargs else [self.defaultValue]:
                value.append([float(_v) for _v in v])
            self.data.update({"value": value})
        else:
            self.data.update(
                {
                    "value": [
                        float(v)
                        for v in (
                            kwargs["value"]
                            if "value" in kwargs
                            else [self.defaultValue]
                        )
                    ]
                }
            )

    def create(self) -> str:
        data = self.data

        if "node" not in data:
            return

        try:
            cmds.addAttr(
                self.node,
                longName=self.longName,
                shortName=self.longName,
                dataType=self.dataType,
                multi=data["multi"],
            )
        except:
            None

        if data["multi"]:
            for i, v in enumerate(data["value"]):
                cmds.setAttr(f"{self.attribute}[{i}]", v, type="matrix")
        else:
            cmds.setAttr(self.attribute, data["value"], type="matrix")
        return self.attribute


class Message(dict):

    attributeType = "message"
    defaultMulti = False

    @property
    def data(self) -> dict:
        return self[self._longName]

    @data.setter
    def data(self, d: dict) -> None:
        self[self._longName] = d

    @property
    def longName(self) -> str:
        return self._longName

    @longName.setter
    def longName(self, n: str) -> None:
        self._longName = n

    @property
    def node(self) -> str:
        return self.data["node"]

    @node.setter
    def node(self, n: str) -> None:
        self.data["node"] = n

    @property
    def attribute(self) -> str:
        return self.node + "." + self.longName

    def __init__(self, longName: str, **kwargs: dict) -> None:
        self.longName = longName
        self.data = {
            "multi": kwargs.pop("multi", self.defaultMulti),
            "attributeType": self.attributeType,
        }

    def create(self) -> str:
        data = self.data

        if "node" not in data:
            return

        try:
            cmds.addAttr(
                self.node,
                longName=self.longName,
                shortName=self.longName,
                attributeType=self.attributeType,
                multi=data["multi"],
            )
        except:
            None

        return self.attribute


TYPETABLE = {
    "long": Integer,
    "float": Float,
    "enum": Enum,
    "bool": Bool,
    "string": String,
    "matrix": Matrix,
    "message": Message,
}
