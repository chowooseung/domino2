# maya
from maya import cmds

# built-ins
import json
from functools import partial


ERROR = -11111


rootNodeName = "spaceManager"


def initialize() -> None:
    selected = cmds.ls(selection=True)
    if not cmds.objExists(rootNodeName):
        cmds.createNode("transform", name=rootNodeName)
    if not cmds.objExists(rootNodeName + "._data"):
        cmds.addAttr(rootNodeName, longName="_data", dataType="string")
        cmds.setAttr(rootNodeName + "._data", json.dumps({}), type="string")
    if selected:
        cmds.select(selected)


def getData() -> dict:
    if not cmds.objExists(rootNodeName):
        return ERROR

    return json.loads(cmds.getAttr(rootNodeName + "._data"))


def setData(data) -> None:
    if cmds.objExists(rootNodeName):
        cmds.setAttr(rootNodeName + "._data", json.dumps(data), type="string")


def addAttr(target: str, attrName: str, constraintType: str = "parent") -> None:
    data = getData()
    if target not in data:
        data[target] = {}

    if attrName not in data[target]:
        data[target][attrName] = {
            "source": [],
            "enumName": [],
            "constraint": constraintType,
        }

    setData(data)


def addSource(target: str, attrName: str, source: str, enumName: str) -> None:
    data = getData()
    if target not in data:
        return ERROR
    if attrName not in data[target]:
        return ERROR

    data[target][attrName]["source"].append(source)
    data[target][attrName]["enumName"].append(enumName)

    setData(data)


def deleteAttr(target: str, attrName: str) -> None:
    data = getData()
    if target in data:
        if attrName in data[target]:
            del data[target][attrName]

    setData(data)


def deleteSource(target: str, attrName: str, source: str, enumName: str) -> None:
    data = getData()
    if target in data:
        if attrName in data[target]:
            if (
                source in data[target][attrName]["source"]
                and enumName in data[target][attrName]["enumName"]
            ):
                data[target][attrName]["source"].remove(source)
                data[target][attrName]["enumName"].remove(enumName)

    setData(data)


def build(*args: tuple) -> None:
    cmds.undoInfo(openChunk=True)
    data = getData()

    constraintTable = {
        "parent": cmds.parentConstraint,
        "point": cmds.pointConstraint,
        "orient": cmds.orientConstraint,
    }

    for target in data:
        m = cmds.xform(target, query=True, matrix=True, worldSpace=True)
        for attrName in data[target]:
            parentName = target + "_" + attrName + "_spaceGrp"
            if not cmds.objExists(parentName):
                cmds.createNode(
                    "transform",
                    parent=rootNodeName,
                    name=parentName,
                )

            sourceNodes = []
            for source, enumName in zip(
                data[target][attrName]["source"], data[target][attrName]["enumName"]
            ):
                sourceNodeName = target + "_" + attrName + "_" + source + "_" + enumName
                cmds.createNode("transform", name=sourceNodeName, parent=parentName)
                cmds.connectAttr(
                    source + ".worldMatrix[0]",
                    sourceNodeName + ".offsetParentMatrix",
                )
                cmds.xform(sourceNodeName, matrix=m, worldSpace=True)
                sourceNodes.append(sourceNodeName)

            constraintFunc = constraintTable[data[target][attrName]["constraint"]]
            targetParent = cmds.listRelatives(target, parent=True)
            cons = constraintFunc(
                sourceNodes,
                targetParent[0] if targetParent else target,
                maintainOffset=True,
            )[0]
            enumName = ["default"] + data[target][attrName]["enumName"]
            if cmds.objExists(target + "." + attrName):
                cmds.deleteAttr(target + "." + attrName)
            cmds.addAttr(
                target,
                longName=attrName,
                attributeType="enum",
                enumName=":".join(enumName),
                keyable=True,
            )

            enumCount = len(data[target][attrName]["enumName"])
            aliasList = constraintFunc(cons, query=True, weightAliasList=True)
            for i in range(enumCount):
                choice = cmds.createNode("choice")
                cmds.setAttr(choice + ".input[0]", 0)
                for _i in range(enumCount):
                    if i == _i:
                        cmds.setAttr(choice + ".input[{0}]".format(_i + 1), 1)
                    else:
                        cmds.setAttr(choice + ".input[{0}]".format(_i + 1), 0)

                cmds.connectAttr(target + "." + attrName, choice + ".selector")
                cmds.connectAttr(choice + ".output", cons + "." + aliasList[i])
    cmds.undoInfo(closeChunk=True)


ID = "spaceManagerUI"


def show(*args) -> None:
    if cmds.window(ID, query=True, exists=True):
        cmds.deleteUI(ID)
    cmds.workspaceControl(
        ID,
        retain=False,
        floating=True,
        label="Space Manager UI",
        uiScript="from domino import spacemanager;spacemanager.ui()",
    )


def insertRow(tableView: str, *args: tuple) -> None:
    index = cmds.scriptTable(tableView, query=True, selectedRow=True)
    cmds.scriptTable(tableView, edit=True, insertRow=index + 1)


def deleteRow(tableView: str, *args: tuple) -> None:
    cells = cmds.scriptTable(tableView, query=True, selectedCells=True) or []
    rows = list(set(cells[::2]))

    count = 0
    for row in sorted(rows):
        cmds.scriptTable(tableView, edit=True, deleteRow=row - count)
        count += 1


def pushData(tableView: str, *args: tuple) -> None:
    cmds.undoInfo(openChunk=True)
    setData({})
    rowCount = cmds.scriptTable(tableView, query=True, rows=True)
    columnCount = cmds.scriptTable(tableView, query=True, columns=True)
    tableData = []
    for _row in range(1, rowCount):
        data = []
        for _column in range(1, columnCount):
            cellValue = cmds.scriptTable(
                tableView,
                query=True,
                cellIndex=(_row, _column),
                cellValue=True,
            )[0]
            data.append(cellValue)
        tableData.append(data)

    currentTarget = ""
    currentAttribute = ""
    currentConstraintType = ""
    for rowData in tableData:
        if rowData[0]:
            currentTarget = rowData[0]
            currentAttribute = rowData[1]
            currentConstraintType = rowData[2]
            status = addAttr(currentTarget, currentAttribute, currentConstraintType)
            if status == ERROR:
                cmds.warning(
                    f"addAttr {currentTarget} {currentAttribute} {currentConstraintType}"
                )
        else:
            if currentTarget and currentAttribute and currentConstraintType:
                status = addSource(
                    currentTarget,
                    currentAttribute,
                    rowData[3],
                    rowData[4],
                )
                if status == ERROR:
                    cmds.warning(
                        f"addSource {currentTarget} {currentAttribute} {rowData[3]} {rowData[4]}"
                    )
    cmds.undoInfo(closeChunk=True)


def pullData(tableView: str, *args: tuple) -> None:
    # delete All item
    rowCount = cmds.scriptTable(tableView, query=True, rows=True)
    for _ in range(1, rowCount):
        cmds.scriptTable(tableView, edit=True, deleteRow=1)

    data = getData()
    if data == ERROR:
        return

    # populate tableView
    currentRow = 1
    for target in data:
        cmds.scriptTable(tableView, edit=True, insertRow=currentRow)
        cmds.scriptTable(
            tableView, edit=True, cellIndex=(currentRow, 1), cellValue=target
        )
        for attrName in data[target]:
            cmds.scriptTable(
                tableView, edit=True, cellIndex=(currentRow, 2), cellValue=attrName
            )
            cmds.scriptTable(
                tableView,
                edit=True,
                cellIndex=(currentRow, 3),
                cellValue=data[target][attrName]["constraint"],
            )
            currentRow += 1
            for source, enumName in zip(
                data[target][attrName]["source"], data[target][attrName]["enumName"]
            ):
                cmds.scriptTable(tableView, edit=True, insertRow=currentRow)
                cmds.scriptTable(
                    tableView, edit=True, cellIndex=(currentRow, 4), cellValue=source
                )
                cmds.scriptTable(
                    tableView, edit=True, cellIndex=(currentRow, 5), cellValue=enumName
                )
                currentRow += 1


def saveFile(filePath: str, *args: tuple) -> None:
    data = getData()

    if not filePath:
        projectPath = cmds.workspace(query=True, rootDirectory=True)
        filePath = cmds.fileDialog2(
            fileFilter="*.dsm",
            dialogStyle=2,
            fileMode=0,
            caption="Save .dsm File",
            startingDirectory=projectPath,
        )

    if isinstance(filePath, list):
        filePath = filePath[0]

    with open(filePath, "w") as f:
        json.dump(data, f, indent=2)


def loadFile(filePath: str, tableView: str, *args: tuple) -> None:
    if not filePath:
        projectPath = cmds.workspace(query=True, rootDirectory=True)
        filePath = cmds.fileDialog2(
            fileFilter="*.dsm",
            dialogStyle=2,
            fileMode=1,
            caption="Load .dsm File",
            startingDirectory=projectPath,
        )

    if isinstance(filePath, list):
        filePath = filePath[0]

    with open(filePath, "r") as f:
        data = json.load(f)

    if cmds.objExists(rootNodeName):
        cmds.delete(rootNodeName)

    initialize()
    setData(data)
    if tableView:
        pullData(tableView=tableView)


def ui(*args, **kwargs) -> None:

    def editCell(row: int, column: int, value: str) -> int:
        return 1

    # create widget
    menuLayout = cmds.menuBarLayout(parent=ID)
    layout = cmds.formLayout(parent=ID)
    tableView = cmds.scriptTable(
        "SMScriptTable",
        parent=layout,
        multiEditEnabled=True,
        cellChangedCmd=editCell,
        columns=5,
        label=[
            (1, "Target"),
            (2, "Attribute Name"),
            (3, "Constraint Type"),
            (4, "Source"),
            (5, "Enum Name"),
        ],
        useDoubleClickEdit=True,
    )
    rowCount = cmds.scriptTable(tableView, query=True, rows=True)
    for _ in range(1, rowCount):
        cmds.scriptTable(tableView, edit=True, deleteRow=1)

    insertRowBtn = cmds.button(
        "SMinsertRowBtn",
        parent=layout,
        label="insert row",
        command=partial(insertRow, tableView),
    )
    deleteRowBtn = cmds.button(
        "SMdeleteRowBtn",
        parent=layout,
        label="delete row",
        command=partial(deleteRow, tableView),
    )

    # menu
    menu = cmds.menu(parent=menuLayout, label="Command")
    cmds.menuItem(
        parent=menu,
        label="Save File(.dsm)",
        command=partial(saveFile, ""),
    )
    cmds.menuItem(
        parent=menu,
        label="Load File(.dsm)",
        command=partial(loadFile, "", tableView),
    )
    cmds.menuItem(
        parent=menu,
        label="Push Data",
        command=partial(pushData, tableView),
    )
    cmds.menuItem(
        parent=menu,
        label="Pull Data",
        command=partial(pullData, tableView),
    )
    cmds.menuItem(parent=menu, label="Build", command=build)

    # layout
    cmds.formLayout(
        layout,
        edit=True,
        attachForm=[
            (tableView, "top", 4),
            (tableView, "left", 4),
            (tableView, "right", 4),
            (insertRowBtn, "bottom", 4),
            (deleteRowBtn, "bottom", 4),
        ],
        attachControl=[(tableView, "bottom", 4, insertRowBtn)],
        attachPosition=[
            (insertRowBtn, "left", 4, 0),
            (insertRowBtn, "right", 2, 50),
            (deleteRowBtn, "left", 2, 50),
            (deleteRowBtn, "right", 4, 100),
        ],
    )
    pullData(tableView=tableView)
