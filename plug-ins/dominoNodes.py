# maya
from maya import OpenMaya as om  # type: ignore
from maya import OpenMayaMPx as ompx  # type: ignore

# built-ins
import sys


class DAssemblyMatrix(ompx.MPxTransformationMatrix):
    id = om.MTypeId(0x0013EBC0)

    def __init__(self):
        ompx.MPxTransformationMatrix.__init__(self)

    @staticmethod
    def creator():
        return ompx.asMPxPtr(DAssemblyMatrix())


class DAssembly(ompx.MPxTransform):
    id = om.MTypeId(0x0013EBC1)

    def __init__(self, transform=None):
        if transform:
            ompx.MPxTransform.__init__(self, transform)
        else:
            ompx.MPxTransform.__init__(self)

    def createTransformationMatrix(self):
        return ompx.asMPxPtr(DAssemblyMatrix())

    @staticmethod
    def creator():
        return ompx.asMPxPtr(DAssembly())

    @staticmethod
    def initialize():
        pass


class DControl01Matrix(ompx.MPxTransformationMatrix):
    id = om.MTypeId(0x0013EBC2)

    def __init__(self):
        ompx.MPxTransformationMatrix.__init__(self)

    @staticmethod
    def creator():
        return ompx.asMPxPtr(DControl01Matrix())


class DControl01(ompx.MPxTransform):
    id = om.MTypeId(0x0013EBC3)

    def __init__(self, transform=None):
        if transform:
            ompx.MPxTransform.__init__(self, transform)
        else:
            ompx.MPxTransform.__init__(self)

    def createTransformationMatrix(self):
        return ompx.asMPxPtr(DControl01Matrix())

    @staticmethod
    def creator():
        return ompx.asMPxPtr(DControl01())

    @staticmethod
    def initialize():
        pass


def initializePlugin(obj):
    """0x0013ebc0 - 0x0013ebff"""
    plugin = ompx.MFnPlugin(obj, "Wooseung Cho", "1.0", "Any")

    try:
        plugin.registerTransform(
            "dAssembly",
            DAssembly.id,
            DAssembly.creator,
            DAssembly.initialize,
            DAssemblyMatrix.creator,
            DAssemblyMatrix.id,
        )
    except:
        sys.stderr.write("Failed to register node\n")

    try:
        plugin.registerTransform(
            "dControl01",
            DControl01.id,
            DControl01.creator,
            DControl01.initialize,
            DControl01Matrix.creator,
            DControl01Matrix.id,
        )
    except:
        sys.stderr.write("Failed to register node\n")


def uninitializePlugin(obj):
    plugin = ompx.MFnPlugin(obj)

    try:
        plugin.deregisterNode(DAssembly.id)
    except:
        sys.stderr.write("Failed to deregister node\n")

    try:
        plugin.deregisterNode(DControl01.id)
    except:
        sys.stderr.write("Failed to deregister node\n")
