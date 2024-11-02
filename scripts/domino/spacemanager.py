# maya
from maya import cmds

# built-ins
import json
from functools import partial


ERROR = -11111


root_node_name = "space_manager"


def initialize() -> None:
    selected = cmds.ls(selection=True)
    if not cmds.objExists(root_node_name):
        cmds.createNode("transform", name=root_node_name)
    if not cmds.objExists(root_node_name + "._data"):
        cmds.addAttr(root_node_name, longName="_data", dataType="string")
        cmds.setAttr(root_node_name + "._data", json.dumps({}), type="string")
    if selected:
        cmds.select(selected)


def get_data() -> dict:
    if not cmds.objExists(root_node_name):
        return ERROR

    return json.loads(cmds.getAttr(root_node_name + "._data"))


def set_data(data) -> None:
    if cmds.objExists(root_node_name):
        cmds.setAttr(root_node_name + "._data", json.dumps(data), type="string")


def add_attr(target: str, attr_name: str, constraint_type: str = "parent") -> None:
    data = get_data()
    if target not in data:
        data[target] = {}

    if attr_name not in data[target]:
        data[target][attr_name] = {
            "source": [],
            "enum_name": [],
            "constraint": constraint_type,
        }

    set_data(data)


def add_source(target: str, attr_name: str, source: str, enum_name: str) -> None:
    data = get_data()
    if target not in data:
        return ERROR
    if attr_name not in data[target]:
        return ERROR

    data[target][attr_name]["source"].append(source)
    data[target][attr_name]["enum_name"].append(enum_name)

    set_data(data)


def delete_attr(target: str, attr_name: str) -> None:
    data = get_data()
    if target in data:
        if attr_name in data[target]:
            del data[target][attr_name]

    set_data(data)


def delete_source(target: str, attr_name: str, source: str, enum_name: str) -> None:
    data = get_data()
    if target in data:
        if attr_name in data[target]:
            if (
                source in data[target][attr_name]["source"]
                and enum_name in data[target][attr_name]["enum_name"]
            ):
                data[target][attr_name]["source"].remove(source)
                data[target][attr_name]["enum_name"].remove(enum_name)

    set_data(data)


def build(*args: tuple) -> None:
    cmds.undoInfo(openChunk=True)
    data = get_data()

    constraint_table = {
        "parent": cmds.parentConstraint,
        "point": cmds.pointConstraint,
        "orient": cmds.orientConstraint,
    }

    for target in data:
        m = cmds.xform(target, query=True, matrix=True, worldSpace=True)
        for attr_name in data[target]:
            parent_name = target + "_" + attr_name + "_spaceGrp"
            if not cmds.objExists(parent_name):
                cmds.createNode(
                    "transform",
                    parent=root_node_name,
                    name=parent_name,
                )

            source_nodes = []
            for source, enum_name in zip(
                data[target][attr_name]["source"], data[target][attr_name]["enum_name"]
            ):
                source_node_name = (
                    target + "_" + attr_name + "_" + source + "_" + enum_name
                )
                cmds.createNode("transform", name=source_node_name, parent=parent_name)
                cmds.connectAttr(
                    source + ".worldMatrix[0]",
                    source_node_name + ".offsetParentMatrix",
                )
                cmds.xform(source_node_name, matrix=m, worldSpace=True)
                source_nodes.append(source_node_name)

            constraint_func = constraint_table[data[target][attr_name]["constraint"]]
            target_parent = cmds.listRelatives(target, parent=True)
            cons = constraint_func(
                source_nodes,
                target_parent[0] if target_parent else target,
                maintainOffset=True,
            )[0]
            enum_name = ["default"] + data[target][attr_name]["enum_name"]
            if cmds.objExists(target + "." + attr_name):
                cmds.deleteAttr(target + "." + attr_name)
            cmds.addAttr(
                target,
                longName=attr_name,
                attributeType="enum",
                enumName=":".join(enum_name),
                keyable=True,
            )

            enum_count = len(data[target][attr_name]["enum_name"])
            alias_list = constraint_func(cons, query=True, weightAliasList=True)
            for i in range(enum_count):
                choice = cmds.createNode("choice")
                cmds.setAttr(choice + ".input[0]", 0)
                for _i in range(enum_count):
                    if i == _i:
                        cmds.setAttr(choice + ".input[{0}]".format(_i + 1), 1)
                    else:
                        cmds.setAttr(choice + ".input[{0}]".format(_i + 1), 0)

                cmds.connectAttr(target + "." + attr_name, choice + ".selector")
                cmds.connectAttr(choice + ".output", cons + "." + alias_list[i])
    cmds.undoInfo(closeChunk=True)


ID = "space_manager_ui"


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


def insert_row(table_view: str, *args: tuple) -> None:
    index = cmds.scriptTable(table_view, query=True, selectedRow=True)
    cmds.scriptTable(table_view, edit=True, insertRow=index + 1)


def delete_row(table_view: str, *args: tuple) -> None:
    cells = cmds.scriptTable(table_view, query=True, selectedCells=True) or []
    rows = list(set(cells[::2]))

    count = 0
    for row in sorted(rows):
        cmds.scriptTable(table_view, edit=True, deleteRow=row - count)
        count += 1


def push_data(table_view: str, *args: tuple) -> None:
    cmds.undoInfo(openChunk=True)
    set_data({})
    row_count = cmds.scriptTable(table_view, query=True, rows=True)
    column_count = cmds.scriptTable(table_view, query=True, columns=True)
    table_data = []
    for _row in range(1, row_count):
        data = []
        for _column in range(1, column_count):
            cell_value = cmds.scriptTable(
                table_view,
                query=True,
                cellIndex=(_row, _column),
                cellValue=True,
            )[0]
            data.append(cell_value)
        table_data.append(data)

    current_target = ""
    current_attribute = ""
    current_constraint_type = ""
    for row_data in table_data:
        if row_data[0]:
            current_target = row_data[0]
            current_attribute = row_data[1]
            current_constraint_type = row_data[2]
            status = add_attr(
                current_target, current_attribute, current_constraint_type
            )
            if status == ERROR:
                cmds.warning(
                    f"add_attr {current_target} {current_attribute} {current_constraint_type}"
                )
        else:
            if current_target and current_attribute and current_constraint_type:
                status = add_source(
                    current_target,
                    current_attribute,
                    row_data[3],
                    row_data[4],
                )
                if status == ERROR:
                    cmds.warning(
                        f"add_source {current_target} {current_attribute} {row_data[3]} {row_data[4]}"
                    )
    cmds.undoInfo(closeChunk=True)


def pull_data(table_view: str, *args: tuple) -> None:
    # delete All item
    row_count = cmds.scriptTable(table_view, query=True, rows=True)
    for _ in range(1, row_count):
        cmds.scriptTable(table_view, edit=True, deleteRow=1)

    data = get_data()
    if data == ERROR:
        return

    # populate tableView
    current_row = 1
    for target in data:
        cmds.scriptTable(table_view, edit=True, insertRow=current_row)
        cmds.scriptTable(
            table_view, edit=True, cellIndex=(current_row, 1), cellValue=target
        )
        for attr_name in data[target]:
            cmds.scriptTable(
                table_view, edit=True, cellIndex=(current_row, 2), cellValue=attr_name
            )
            cmds.scriptTable(
                table_view,
                edit=True,
                cellIndex=(current_row, 3),
                cellValue=data[target][attr_name]["constraint"],
            )
            current_row += 1
            for source, enum_name in zip(
                data[target][attr_name]["source"], data[target][attr_name]["enum_name"]
            ):
                cmds.scriptTable(table_view, edit=True, insertRow=current_row)
                cmds.scriptTable(
                    table_view, edit=True, cellIndex=(current_row, 4), cellValue=source
                )
                cmds.scriptTable(
                    table_view,
                    edit=True,
                    cellIndex=(current_row, 5),
                    cellValue=enum_name,
                )
                current_row += 1


def save_file(file_path: str, *args: tuple) -> None:
    data = get_data()

    if not file_path:
        project_path = cmds.workspace(query=True, rootDirectory=True)
        file_path = cmds.fileDialog2(
            fileFilter="*.dsm",
            dialogStyle=2,
            fileMode=0,
            caption="Save .dsm File",
            startingDirectory=project_path,
        )

    if isinstance(file_path, list):
        file_path = file_path[0]

    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


def load_file(file_path: str, table_view: str, *args: tuple) -> None:
    if not file_path:
        project_path = cmds.workspace(query=True, rootDirectory=True)
        file_path = cmds.fileDialog2(
            fileFilter="*.dsm",
            dialogStyle=2,
            fileMode=1,
            caption="Load .dsm File",
            startingDirectory=project_path,
        )

    if isinstance(file_path, list):
        file_path = file_path[0]

    with open(file_path, "r") as f:
        data = json.load(f)

    if cmds.objExists(root_node_name):
        cmds.delete(root_node_name)

    initialize()
    set_data(data)
    if table_view:
        pull_data(table_view=table_view)


def ui(*args, **kwargs) -> None:

    def edit_cell(row: int, column: int, value: str) -> int:
        return 1

    # create widget
    menu_layout = cmds.menuBarLayout(parent=ID)
    layout = cmds.formLayout(parent=ID)
    table_view = cmds.scriptTable(
        "sm_script_table",
        parent=layout,
        multiEditEnabled=True,
        cellChangedCmd=edit_cell,
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
    row_count = cmds.scriptTable(table_view, query=True, rows=True)
    for _ in range(1, row_count):
        cmds.scriptTable(table_view, edit=True, deleteRow=1)

    insert_row_btn = cmds.button(
        "sm_insert_row_btn",
        parent=layout,
        label="insert row",
        command=partial(insert_row, table_view),
    )
    delete_row_btn = cmds.button(
        "sm_delete_row_btn",
        parent=layout,
        label="delete row",
        command=partial(delete_row, table_view),
    )

    # menu
    menu = cmds.menu(parent=menu_layout, label="Command")
    cmds.menuItem(
        parent=menu,
        label="Save File(.dsm)",
        command=partial(save_file, ""),
    )
    cmds.menuItem(
        parent=menu,
        label="Load File(.dsm)",
        command=partial(load_file, "", table_view),
    )
    cmds.menuItem(
        parent=menu,
        label="Push Data",
        command=partial(push_data, table_view),
    )
    cmds.menuItem(
        parent=menu,
        label="Pull Data",
        command=partial(pull_data, table_view),
    )
    cmds.menuItem(parent=menu, label="Build", command=build)

    # layout
    cmds.formLayout(
        layout,
        edit=True,
        attachForm=[
            (table_view, "top", 4),
            (table_view, "left", 4),
            (table_view, "right", 4),
            (insert_row_btn, "bottom", 4),
            (delete_row_btn, "bottom", 4),
        ],
        attachControl=[(table_view, "bottom", 4, insert_row_btn)],
        attachPosition=[
            (insert_row_btn, "left", 4, 0),
            (insert_row_btn, "right", 2, 50),
            (delete_row_btn, "left", 2, 50),
            (delete_row_btn, "right", 4, 100),
        ],
    )
    pull_data(table_view=table_view)
