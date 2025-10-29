# maya
from maya import cmds
from maya.api import OpenMaya as om

# domino
from domino import core


ORIGINMATRIX = om.MMatrix()


class Integer(dict):

    default_value = 0
    default_min_value = None
    default_max_value = None
    default_keyable = False
    default_lock = False
    default_channelbox = False
    default_multi = False
    attribute_type = "long"

    @property
    def data(self):
        return self[self._long_name]

    @data.setter
    def data(self, d):
        self[self._long_name] = d

    @property
    def long_name(self):
        return self._long_name

    @long_name.setter
    def long_name(self, n):
        self._long_name = n

    @property
    def node(self):
        return self.data["node"]

    @node.setter
    def node(self, n):
        self.data["node"] = n

    @property
    def attribute(self):
        return f"{self.node}.{self.long_name}"

    def __init__(self, longName, **kwargs):
        self.long_name = longName
        self.data = {
            "minValue": (
                kwargs["minValue"] if "minValue" in kwargs else self.default_min_value
            ),
            "maxValue": (
                kwargs["minValue"] if "minValue" in kwargs else self.default_min_value
            ),
            "keyable": (
                kwargs["keyable"] if "keyable" in kwargs else self.default_keyable
            ),
            "lock": kwargs["lock"] if "lock" in kwargs else self.default_lock,
            "channelBox": (
                kwargs["channelBox"]
                if "channelBox" in kwargs
                else self.default_channelbox
            ),
            "multi": kwargs["multi"] if "multi" in kwargs else self.default_multi,
            "attributeType": self.attribute_type,
        }
        if self.data["multi"]:
            self.data.update(
                {
                    "value": (
                        kwargs["value"] if "value" in kwargs else [self.default_value]
                    )
                }
            )
        else:
            self.data.update(
                {"value": kwargs["value"] if "value" in kwargs else self.default_value}
            )

    def create(self):
        data = self.data

        if "node" not in data:
            return ""

        try:
            cmds.addAttr(
                self.node,
                longName=self.long_name,
                shortName=self.long_name,
                attributeType=self.attribute_type,
                multi=data["multi"],
            )
        except:
            ...

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

    attribute_type = "float"


class DoubleAngle(Integer):

    attribute_type = "doubleAngle"


class Enum(dict):

    default_value = 0
    default_keyable = False
    default_lock = False
    default_channelbox = False
    attribute_type = "enum"

    @property
    def data(self):
        return self[self._long_name]

    @data.setter
    def data(self, d):
        self[self._long_name] = d

    @property
    def long_name(self):
        return self._long_name

    @long_name.setter
    def long_name(self, n):
        self._long_name = n

    @property
    def node(self):
        return self.data["node"]

    @node.setter
    def node(self, n):
        self.data["node"] = n

    @property
    def attribute(self):
        return f"{self.node}.{self.long_name}"

    def __init__(self, longName, enumName, **kwargs):
        self.long_name = longName
        self.data = {
            "enumName": enumName,
            "value": kwargs["value"] if "value" in kwargs else self.default_value,
            "keyable": (
                kwargs["keyable"] if "keyable" in kwargs else self.default_keyable
            ),
            "lock": kwargs["lock"] if "lock" in kwargs else self.default_lock,
            "channelBox": (
                kwargs["channelBox"]
                if "channelBox" in kwargs
                else self.default_channelbox
            ),
            "attributeType": self.attribute_type,
            "multi": False,
        }

    def create(self):
        data = self.data

        if "node" not in data:
            return ""

        try:
            cmds.addAttr(
                data["node"],
                longName=self.long_name,
                shortName=self.long_name,
                attributeType=self.attribute_type,
                enumName="TEMP:TEMP",  # 넣어주지 않으면 enumName을 수정할 때 작동하지 않음.
            )
        except:
            ...

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

    default_value = 0
    default_keyable = False
    default_lock = False
    default_channelbox = False
    default_multi = False
    attribute_type = "bool"

    @property
    def data(self):
        return self[self._long_name]

    @data.setter
    def data(self, d):
        self[self._long_name] = d

    @property
    def long_name(self):
        return self._long_name

    @long_name.setter
    def long_name(self, n):
        self._long_name = n

    @property
    def node(self):
        return self.data["node"]

    @node.setter
    def node(self, n):
        self.data["node"] = n

    @property
    def attribute(self):
        return f"{self.node}.{self.long_name}"

    def __init__(self, longName, **kwargs):
        self.long_name = longName
        self.data = {
            "keyable": (
                kwargs["keyable"] if "keyable" in kwargs else self.default_keyable
            ),
            "lock": kwargs["lock"] if "lock" in kwargs else self.default_lock,
            "channelBox": (
                kwargs["channelBox"]
                if "channelBox" in kwargs
                else self.default_channelbox
            ),
            "multi": kwargs["multi"] if "multi" in kwargs else self.default_multi,
            "attributeType": self.attribute_type,
        }
        if self.data["multi"]:
            self.data.update(
                {
                    "value": (
                        kwargs["value"] if "value" in kwargs else [self.default_value]
                    )
                }
            )
        else:
            self.data.update(
                {"value": kwargs["value"] if "value" in kwargs else self.default_value}
            )

    def create(self):
        data = self.data

        if "node" not in data:
            return ""

        try:
            cmds.addAttr(
                self.node,
                longName=self.long_name,
                shortName=self.long_name,
                attributeType=self.attribute_type,
                multi=data["multi"],
            )
        except:
            ...

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

    default_value = ""
    default_lock = False
    default_multi = False
    data_type = "string"

    @property
    def data(self):
        return self[self._long_name]

    @data.setter
    def data(self, d):
        self[self._long_name] = d

    @property
    def long_name(self):
        return self._long_name

    @long_name.setter
    def long_name(self, n):
        self._long_name = n

    @property
    def node(self):
        return self.data["node"]

    @node.setter
    def node(self, n):
        self.data["node"] = n

    @property
    def attribute(self):
        return f"{self.node}.{self.long_name}"

    def __init__(self, longName, **kwargs):
        self.long_name = longName
        self.data = {
            "lock": kwargs["lock"] if "lock" in kwargs else self.default_lock,
            "multi": kwargs["multi"] if "multi" in kwargs else self.default_multi,
            "dataType": self.data_type,
        }
        if self.data["multi"]:
            self.data.update(
                {
                    "value": (
                        kwargs["value"] if "value" in kwargs else [self.default_value]
                    )
                }
            )
        else:
            self.data.update(
                {"value": kwargs["value"] if "value" in kwargs else self.default_value}
            )

    def create(self):
        data = self.data

        if "node" not in data:
            return ""

        try:
            cmds.addAttr(
                self.node,
                longName=self.long_name,
                shortName=self.long_name,
                dataType=self.data_type,
                multi=data["multi"],
            )
        except:
            ...

        cmds.setAttr(self.attribute, lock=data["lock"])
        if data["multi"]:
            for i, v in enumerate(data["value"]):
                cmds.setAttr(f"{self.attribute}[{i}]", v, type="string")
        else:
            cmds.setAttr(self.attribute, data["value"], type="string")
        return self.attribute


class Matrix(dict):

    data_type = "matrix"
    default_value = list(ORIGINMATRIX)
    default_multi = False

    @property
    def data(self):
        return self[self._long_name]

    @data.setter
    def data(self, d):
        self[self._long_name] = d

    @property
    def long_name(self):
        return self._long_name

    @long_name.setter
    def long_name(self, n):
        self._long_name = n

    @property
    def node(self):
        return self.data["node"]

    @node.setter
    def node(self, n):
        self.data["node"] = n

    @property
    def attribute(self):
        return f"{self.node}.{self.long_name}"

    def __init__(self, longName, **kwargs):
        self.long_name = longName
        self.data = {
            "multi": kwargs["multi"] if "multi" in kwargs else self.default_multi,
            "dataType": self.data_type,
        }
        if self.data["multi"]:
            value = []
            for v in kwargs["value"] if "value" in kwargs else [self.default_value]:
                value.append([float(_v) for _v in v])
            self.data.update({"value": value})
        else:
            value = kwargs.get("value", self.default_value)
            if not isinstance(value, list):
                value = [value]
            self.data.update({"value": [float(v) for v in value]})

    def create(self):
        data = self.data

        if "node" not in data:
            return ""

        try:
            cmds.addAttr(
                self.node,
                longName=self.long_name,
                shortName=self.long_name,
                dataType=self.data_type,
                multi=data["multi"],
            )
        except:
            ...

        if data["multi"]:
            for i, v in enumerate(data["value"]):
                cmds.setAttr(f"{self.attribute}[{i}]", v, type="matrix")
        else:
            cmds.setAttr(self.attribute, data["value"], type="matrix")
        return self.attribute


class Message(dict):

    attribute_type = "message"
    default_multi = False

    @property
    def data(self):
        return self[self._long_name]

    @data.setter
    def data(self, d):
        self[self._long_name] = d

    @property
    def long_name(self):
        return self._long_name

    @long_name.setter
    def long_name(self, n):
        self._long_name = n

    @property
    def node(self):
        return self.data["node"]

    @node.setter
    def node(self, n):
        self.data["node"] = n

    @property
    def attribute(self):
        return f"{self.node}.{self.long_name}"

    def __init__(self, longName, **kwargs):
        self.long_name = longName
        self.data = {
            "multi": kwargs.pop("multi", self.default_multi),
            "attributeType": self.attribute_type,
        }

    def create(self):
        data = self.data

        if "node" not in data:
            return ""

        try:
            cmds.addAttr(
                self.node,
                longName=self.long_name,
                shortName=self.long_name,
                attributeType=self.attribute_type,
                multi=data["multi"],
            )
        except:
            ...

        return self.attribute


class NurbsCurve(dict):

    data_type = "nurbsCurve"

    @property
    def data(self):
        return self[self._long_name]

    @data.setter
    def data(self, d):
        self[self._long_name] = d

    @property
    def long_name(self):
        return self._long_name

    @long_name.setter
    def long_name(self, n):
        self._long_name = n

    @property
    def node(self):
        return self.data["node"]

    @node.setter
    def node(self, n):
        self.data["node"] = n

    @property
    def attribute(self):
        return f"{self.node}.{self.long_name}"

    def __init__(self, longName, **kwargs):
        self.long_name = longName
        self.data = {
            "dataType": self.data_type,
            "multi": False,
        }
        if "value" in kwargs:
            self.data["value"] = kwargs["value"]

    def create(self):
        data = self.data

        if "node" not in data:
            return ""

        try:
            cmds.addAttr(
                self.node,
                longName=self.long_name,
                shortName=self.long_name,
                dataType=self.data_type,
            )
            if "value" in self.data:
                ins = core.NurbsCurve(data=self.data["value"])
                crv = ins.create_from_data()
                cmds.connectAttr(f"{crv}.local", f"{self.node}.{self.long_name}")
                cmds.delete(crv)
        except:
            ...

        return self.attribute


class NurbsSurface(dict):

    data_type = "nurbsSurface"

    @property
    def data(self):
        return self[self._long_name]

    @data.setter
    def data(self, d):
        self[self._long_name] = d

    @property
    def long_name(self):
        return self._long_name

    @long_name.setter
    def long_name(self, n):
        self._long_name = n

    @property
    def node(self):
        return self.data["node"]

    @node.setter
    def node(self, n):
        self.data["node"] = n

    @property
    def attribute(self):
        return f"{self.node}.{self.long_name}"

    def __init__(self, longName, **kwargs):
        self.long_name = longName
        self.data = {
            "dataType": self.data_type,
            "multi": False,
        }
        if "value" in kwargs:
            self.data["value"] = kwargs["value"]

    def create(self):
        data = self.data

        if "node" not in data:
            return ""

        try:
            cmds.addAttr(
                self.node,
                longName=self.long_name,
                shortName=self.long_name,
                dataType=self.data_type,
            )
            if "value" in self.data:
                ins = core.NurbsSurface(data=self.data["value"])
                surface = ins.create_from_data()
                cmds.connectAttr(f"{surface}.local", f"{self.node}.{self.long_name}")
                cmds.delete(surface)
        except:
            ...

        return self.attribute


class Mesh(dict):

    data_type = "mesh"

    @property
    def data(self):
        return self[self._long_name]

    @data.setter
    def data(self, d):
        self[self._long_name] = d

    @property
    def long_name(self):
        return self._long_name

    @long_name.setter
    def long_name(self, n):
        self._long_name = n

    @property
    def node(self):
        return self.data["node"]

    @node.setter
    def node(self, n):
        self.data["node"] = n

    @property
    def attribute(self):
        return f"{self.node}.{self.long_name}"

    def __init__(self, longName, **kwargs):
        self.long_name = longName
        self.data = {
            "dataType": self.data_type,
            "multi": False,
        }
        if "value" in kwargs:
            self.data["value"] = kwargs["value"]

    def create(self):
        data = self.data

        if "node" not in data:
            return ""

        try:
            cmds.addAttr(
                self.node,
                longName=self.long_name,
                shortName=self.long_name,
                dataType=self.data_type,
            )
            if "value" in self.data:
                ins = core.Mesh(data=self.data["value"])
                mesh = ins.create_from_data()
                cmds.connectAttr(f"{mesh}.outMesh", f"{self.node}.{self.long_name}")
                cmds.delete(mesh)
        except:
            ...

        return self.attribute


TYPETABLE = {
    "long": Integer,
    "float": Float,
    "enum": Enum,
    "bool": Bool,
    "string": String,
    "matrix": Matrix,
    "message": Message,
    "doubleAngle": DoubleAngle,
    "nurbsCurve": NurbsCurve,
    "nurbsSurface": NurbsSurface,
    "mesh": Mesh,
}
