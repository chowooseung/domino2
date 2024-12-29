# Assembly Callback -------------------------------------------------- #
def add_script(plug, scroll_list, *args) -> None:
    from maya import cmds
    from pathlib import Path

    file_path = cmds.fileDialog2(
        caption="Add Python Script",
        startingDirectory=cmds.workspace(query=True, rootDirectory=True),
        fileFilter="Python (*.py)",
        fileMode=1,
    )
    if not file_path:
        return
    file_path = Path(file_path[0])

    attrs = cmds.listAttr(plug, multi=True)
    guide_root = plug.split(".")[0]
    rig_root = cmds.connectionInfo(plug + "[0]", destinationFromSource=True)[0].split(
        "."
    )[0]
    script_paths = []
    for attr in attrs:
        data = cmds.getAttr(guide_root + "." + attr)
        if data:
            script_paths.append(data)
    script_paths.append(file_path.as_posix())

    # clear mult attribute
    for attr in attrs:
        cmds.removeMultiInstance(guide_root + "." + attr, b=True)
    cmds.textScrollList(scroll_list, edit=True, removeAll=True)

    # add
    attr = plug.split(".")[1]
    for i, script_path in enumerate(script_paths):
        cmds.setAttr(guide_root + "." + attr + f"[{i}]", script_path, type="string")
        cmds.connectAttr(
            guide_root + "." + attr + f"[{i}]", rig_root + "." + attr + f"[{i}]"
        )
        text = ""
        if script_path.startswith("*"):
            script_path = script_path[1:]
            text += "*"
        script_path = Path(script_path)
        text += script_path.name + " " + script_path.parent.as_posix()
        cmds.textScrollList(scroll_list, edit=True, append=text)


def create_script(plug, scroll_list, *args) -> None:
    from maya import cmds
    from pathlib import Path

    file_path = cmds.fileDialog2(
        caption="Create Python Script",
        startingDirectory=cmds.workspace(query=True, rootDirectory=True),
        fileFilter="Python (*.py)",
        fileMode=0,
    )
    if not file_path:
        return
    file_path = Path(file_path[0])

    content = """def run(context, *args, **kwargs):
    ..."""
    with open(file_path, "w") as f:
        f.write(content)

    attrs = cmds.listAttr(plug, multi=True)
    guide_root = plug.split(".")[0]
    rig_root = cmds.connectionInfo(plug + "[0]", destinationFromSource=True)[0].split(
        "."
    )[0]
    script_paths = []
    for attr in attrs:
        data = cmds.getAttr(guide_root + "." + attr)
        if data:
            script_paths.append(data)
    script_paths.append(file_path)

    # clear mult attribute
    for attr in attrs:
        cmds.removeMultiInstance(guide_root + "." + attr, b=True)
    cmds.textScrollList(scroll_list, edit=True, removeAll=True)

    # add
    attr = plug.split(".")[1]
    for i, script_path in enumerate(script_paths):
        cmds.setAttr(guide_root + "." + attr + f"[{i}]", script_path, type="string")
        cmds.connectAttr(
            guide_root + "." + attr + f"[{i}]", rig_root + "." + attr + f"[{i}]"
        )
        text = ""
        if script_path.startswith("*"):
            script_path = script_path[1:]
            text += "*"
        script_path = Path(script_path)
        text += script_path.name + " " + script_path.parent.as_posix()
        cmds.textScrollList(scroll_list, edit=True, append=text)


def edit_script(scroll_list, *args) -> None:
    import sys
    import os
    import subprocess
    from maya import cmds
    from pathlib import Path

    select_items = cmds.textScrollList(scroll_list, query=True, selectItem=True)

    if not select_items:
        return

    name, parent = select_items[0].split(" ")
    if select_items[0].startswith("*"):
        name = name[:1]
    path = Path(parent) / name

    if sys.platform.startswith("darwin"):
        subprocess.call(("open", path.as_posix()))
    elif os.name == "nt":
        os.startfile(path.as_posix())
    elif os.name == "posix":
        subprocess.call(("xdg-open", path.as_posix()))


def delete_script(plug, scroll_list, *args):
    from maya import cmds
    from pathlib import Path

    select_indexes = [
        x - 1
        for x in cmds.textScrollList(scroll_list, query=True, selectIndexedItem=True)
    ]
    if not select_indexes:
        return
    all_items = cmds.textScrollList(scroll_list, query=True, allItems=True)

    attrs = cmds.listAttr(plug, multi=True)
    guide_root = plug.split(".")[0]
    rig_root = cmds.connectionInfo(plug + "[0]", destinationFromSource=True)[0].split(
        "."
    )[0]

    # clear mult attribute
    for attr in attrs:
        cmds.removeMultiInstance(guide_root + "." + attr, b=True)
    cmds.textScrollList(scroll_list, edit=True, removeAll=True)

    count = 0
    attr = plug.split(".")[1]
    for i, item in enumerate(all_items):
        if i in select_indexes:
            continue
        name, parent = item.split(" ")
        path = ""
        if name.startswith("*"):
            name = name[1:]
            path += "*"
        path += (Path(parent) / name).as_posix()
        cmds.setAttr(guide_root + "." + attr + f"[{count}]", path, type="string")
        cmds.connectAttr(
            guide_root + "." + attr + f"[{count}]", rig_root + "." + attr + f"[{count}]"
        )
        cmds.textScrollList(scroll_list, edit=True, append=item)
        count += 1

    if not cmds.listAttr(plug, multi=True):
        cmds.connectAttr(guide_root + "." + attr + "[0]", rig_root + "." + attr + "[0]")


def run_script(scroll_list, *args):
    from pathlib import Path
    import importlib.util
    import sys
    from maya import cmds
    from domino.core.utils import logger

    select_items = cmds.textScrollList(scroll_list, query=True, selectItem=True) or []
    if not select_items:
        return

    try:
        for item in select_items:
            if item.startswith("*"):
                item = item[1:]
            name, parent = item.split(" ")
            path = (Path(parent) / name).as_posix()
            spec = importlib.util.spec_from_file_location(name[:-3], path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[name[:-3]] = module

            module.run({})
    except ImportError as e:
        logger.error(e, exc_info=True)
    except Exception as e:
        logger.error(e, exc_info=True)


def enable_script(plug, scroll_list, *args):
    from maya import cmds
    from pathlib import Path

    select_indexes = [
        x - 1
        for x in cmds.textScrollList(scroll_list, query=True, selectIndexedItem=True)
        or []
    ]
    if not select_indexes:
        return

    attrs = cmds.listAttr(plug, multi=True)
    root = plug.split(".")[0]

    # clear mult attribute
    cmds.textScrollList(scroll_list, edit=True, removeAll=True)

    for i, attr in enumerate(attrs):
        path = cmds.getAttr(root + "." + attr)
        if i in select_indexes and path.startswith("*"):
            cmds.setAttr(root + "." + attr, path[1:], type="string")
        path = cmds.getAttr(root + "." + attr)
        item = ""
        if path.startswith("*"):
            item += "*"
            path = path[1:]
        parent = Path(path).parent
        name = Path(path).name
        item += f"{name} {parent}"
        cmds.textScrollList(scroll_list, edit=True, append=item)


def disable_script(plug, scroll_list, *args):
    from maya import cmds
    from pathlib import Path

    select_indexes = [
        x - 1
        for x in cmds.textScrollList(scroll_list, query=True, selectIndexedItem=True)
        or []
    ]
    if not select_indexes:
        return

    attrs = cmds.listAttr(plug, multi=True)
    root = plug.split(".")[0]

    # clear mult attribute
    cmds.textScrollList(scroll_list, edit=True, removeAll=True)

    for i, attr in enumerate(attrs):
        path = cmds.getAttr(root + "." + attr)
        if i in select_indexes and not path.startswith("*"):
            cmds.setAttr(root + "." + attr, "*" + path, type="string")
        path = cmds.getAttr(root + "." + attr)
        item = ""
        if path.startswith("*"):
            item += "*"
            path = path[1:]
        parent = Path(path).parent
        name = Path(path).name
        item += f"{name} {parent}"
        cmds.textScrollList(scroll_list, edit=True, append=item)


def cb_pre_custom_scripts(plug, label, annotation) -> None:
    from maya import cmds
    from functools import partial
    from pathlib import Path

    previous_index = None

    def cb_drag(*args):
        nonlocal previous_index
        previous_index = None

        select_index = [
            x - 1
            for x in cmds.textScrollList(li, query=True, selectIndexedItem=True) or []
        ]
        if not select_index:
            return

        _, _, height, _ = args
        index = int(height / 16)
        if index != select_index[0]:
            return

        previous_index = index

    def cb_drop(*args):
        nonlocal previous_index

        if previous_index is None:
            return

        _, _, _, _, height, _ = args
        index = int(height / 16)
        if ((height % 16) / 16) > 0.5:
            index += 1

        if previous_index == index:
            return

        attrs = cmds.listAttr(plug, multi=True)
        guide_root = plug.split(".")[0]
        rig_root = cmds.connectionInfo(plug + "[0]", destinationFromSource=True)[
            0
        ].split(".")[0]

        items = cmds.textScrollList(li, query=True, allItems=True)
        items.insert(index, items[previous_index])
        remove_index = previous_index
        if previous_index > index:
            remove_index = previous_index + 1
        items.pop(remove_index)

        # clear mult attribute
        for attr in attrs:
            cmds.removeMultiInstance(guide_root + "." + attr, b=True)
        cmds.textScrollList(li, edit=True, removeAll=True)

        attr = plug.split(".")[1]
        for i, item in enumerate(items):
            name, parent = item.split(" ")
            path = ""
            if name.startswith("*"):
                name = name[1:]
                path += "*"
            path += (Path(parent) / name).as_posix()
            cmds.setAttr(guide_root + "." + attr + f"[{i}]", path, type="string")
            cmds.connectAttr(
                guide_root + "." + attr + f"[{i}]", rig_root + "." + attr + f"[{i}]"
            )
            cmds.textScrollList(li, edit=True, append=item)

    row_layout = cmds.rowLayout(numberOfColumns=2, adjustableColumn=2)
    cmds.text(label="Pre Custom Scripts")
    form_layout = cmds.formLayout()
    li = cmds.textScrollList(allowMultiSelection=True)
    cmds.textScrollList(
        li,
        edit=True,
        doubleClickCommand=partial(edit_script, li),
        dragCallback=cb_drag,
        dropCallback=cb_drop,
    )
    column_layout = cmds.columnLayout(generalSpacing=2)
    cmds.button(label="Add", height=24, command=partial(add_script, plug, li))
    cmds.button(label="Create", height=24, command=partial(create_script, plug, li))
    cmds.button(label="Delete", height=24, command=partial(delete_script, plug, li))
    cmds.button(label="Run Sel", height=24, command=partial(run_script, li))
    cmds.button(label="Enable", height=24, command=partial(enable_script, plug, li))
    cmds.button(label="Disable", height=24, command=partial(disable_script, plug, li))
    cmds.formLayout(
        form_layout,
        edit=True,
        attachForm=[
            (li, "top", 2),
            (li, "left", 2),
            (li, "bottom", 2),
            (column_layout, "right", 2),
            (column_layout, "top", 2),
        ],
        attachControl=[(li, "right", 2, column_layout)],
    )
    cmds.rowLayout(row_layout, edit=True, columnAttach=[(1, "right", 2)])
    cmds.setParent(upLevel=1)
    cmds.setParent(upLevel=1)

    attrs = cmds.listAttr(plug, multi=True) or []
    guide_root = plug.split(".")[0]
    scripts = []
    for attr in attrs:
        data = cmds.getAttr(guide_root + "." + attr)
        if data:
            scripts.append(data)

    # add
    attr = plug.split(".")[1]
    for script in scripts:
        text = ""
        if script.startswith("*"):
            text += "*"
            script = script[1:]
        script = Path(script)
        text += script.name + " " + script.parent.as_posix()
        cmds.textScrollList(li, edit=True, append=text)


def cb_post_custom_scripts(plug, label, annotation) -> None:
    from maya import cmds
    from functools import partial
    from pathlib import Path

    previous_index = None

    def cb_drag(*args):
        nonlocal previous_index
        previous_index = None

        select_index = [
            x - 1
            for x in cmds.textScrollList(li, query=True, selectIndexedItem=True) or []
        ]
        if not select_index:
            return

        _, _, height, _ = args
        index = int(height / 16)
        if index != select_index[0]:
            return

        previous_index = index

    def cb_drop(*args):
        nonlocal previous_index

        if previous_index is None:
            return

        _, _, _, _, height, _ = args
        index = int(height / 16)
        if ((height % 16) / 16) > 0.5:
            index += 1

        if previous_index == index:
            return

        attrs = cmds.listAttr(plug, multi=True)
        guide_root = plug.split(".")[0]
        rig_root = cmds.connectionInfo(plug + "[0]", destinationFromSource=True)[
            0
        ].split(".")[0]

        items = cmds.textScrollList(li, query=True, allItems=True)
        items.insert(index, items[previous_index])
        remove_index = previous_index
        if previous_index > index:
            remove_index = previous_index + 1
        items.pop(remove_index)

        # clear mult attribute
        for attr in attrs:
            cmds.removeMultiInstance(guide_root + "." + attr, b=True)
        cmds.textScrollList(li, edit=True, removeAll=True)

        attr = plug.split(".")[1]
        for i, item in enumerate(items):
            name, parent = item.split(" ")
            path = ""
            if name.startswith("*"):
                name = name[1:]
                path += "*"
            path += (Path(parent) / name).as_posix()
            cmds.setAttr(guide_root + "." + attr + f"[{i}]", path, type="string")
            cmds.connectAttr(
                guide_root + "." + attr + f"[{i}]", rig_root + "." + attr + f"[{i}]"
            )
            cmds.textScrollList(li, edit=True, append=item)

    row_layout = cmds.rowLayout(numberOfColumns=2, adjustableColumn=2)
    cmds.text(label="Post Custom Scripts")
    form_layout = cmds.formLayout()
    li = cmds.textScrollList(allowMultiSelection=True)
    cmds.textScrollList(
        li,
        edit=True,
        doubleClickCommand=partial(edit_script, li),
        dragCallback=cb_drag,
        dropCallback=cb_drop,
    )
    column_layout = cmds.columnLayout(generalSpacing=2)
    cmds.button(label="Add", height=24, command=partial(add_script, plug, li))
    cmds.button(label="Create", height=24, command=partial(create_script, plug, li))
    cmds.button(label="Delete", height=24, command=partial(delete_script, plug, li))
    cmds.button(label="Run Sel", height=24, command=partial(run_script, li))
    cmds.button(label="Enable", height=24, command=partial(enable_script, li))
    cmds.button(label="Disable", height=24, command=partial(disable_script, li))
    cmds.formLayout(
        form_layout,
        edit=True,
        attachForm=[
            (li, "top", 2),
            (li, "left", 2),
            (li, "bottom", 2),
            (column_layout, "right", 2),
            (column_layout, "top", 2),
        ],
        attachControl=[(li, "right", 2, column_layout)],
    )
    cmds.rowLayout(row_layout, edit=True, columnAttach=[(1, "right", 2)])
    cmds.setParent(upLevel=1)
    cmds.setParent(upLevel=1)

    attrs = cmds.listAttr(plug, multi=True) or []
    guide_root = plug.split(".")[0]
    scripts = []
    for attr in attrs:
        data = cmds.getAttr(guide_root + "." + attr)
        if data:
            scripts.append(data)

    # add
    attr = plug.split(".")[1]
    for script in scripts:
        text = ""
        if script.startswith("*"):
            text += "*"
            script = script[1:]
        script = Path(script)
        text = script.name + " " + script.parent.as_posix()
        cmds.textScrollList(li, edit=True, append=text)


# -------------------------------------------------------------------- #


# Common Callback ---------------------------------------------------- #
def cb_edit_name(plug, label, annotation):
    from maya import cmds

    cmds.rowLayout(numberOfColumns=2, adjustableColumn=2)
    name = cmds.getAttr(plug)
    cmds.text(label="Name")
    field = cmds.textField(text=name)

    def edit_name(*args):
        new_name = args[0]
        cmds.setAttr(plug, new_name, type="string")
        # TODO

    cmds.textField(field, edit=True, changeCommand=edit_name)
    cmds.setParent(upLevel=1)


def cb_edit_side(plug, label, annotation):
    from maya import cmds

    cmds.rowLayout(numberOfColumns=2, adjustableColumn=2)
    side = cmds.getAttr(plug)
    cmds.text(label="Side")
    menu = cmds.optionMenu()
    cmds.menuItem(label="C")
    cmds.menuItem(label="L")
    cmds.menuItem(label="R")
    cmds.optionMenu(menu, edit=True, select=side + 1)

    def edit_side(*args):
        li = ["C", "L", "R"]
        new_side = li.index(args[0])
        cmds.setAttr(plug, new_side)

    cmds.optionMenu(menu, edit=True, changeCommand=edit_side)
    cmds.setParent(upLevel=1)


def cb_edit_index(plug, label, annotation):
    from maya import cmds

    cmds.columnLayout()
    index = cmds.getAttr(plug)
    slider = cmds.intSliderGrp(
        field=True,
        label="Index",
        value=index,
        step=1,
        fieldMinValue=0,
        fieldMaxValue=999,
        minValue=0,
        maxValue=99,
    )

    def edit_index(*args):
        new_index = args[0]
        cmds.setAttr(plug, new_index)

    cmds.intSliderGrp(slider, edit=True, changeCommand=edit_index)
    cmds.setParent(upLevel=1)


def cb_toggle_create_output_joint(plug, label, annotation):
    from maya import cmds

    cmds.rowLayout(numberOfColumns=2, adjustableColumn=2)
    value = cmds.getAttr(plug)
    cmds.text(label="Create Output Joint")
    checkbox = cmds.checkBox(value=value, label="")

    def toggle(*args):
        new_value = args[0]
        cmds.setAttr(plug, new_value)

    cmds.checkBox(checkbox, edit=True, changeCommand=toggle)
    cmds.setParent(upLevel=1)


def cb_edit_parent_output_index(plug, label, annotation):
    from maya import cmds

    cmds.columnLayout()
    index = cmds.getAttr(plug)
    slider = cmds.intSliderGrp(
        field=True,
        label="Parent Output Index",
        value=index,
        step=1,
        fieldMinValue=-1,
        fieldMaxValue=999,
        minValue=-1,
        maxValue=99,
    )

    def edit_parent_output_index(*args):
        new_index = args[0]
        cmds.setAttr(plug, new_index)

    cmds.intSliderGrp(slider, edit=True, changeCommand=edit_parent_output_index)
    cmds.setParent(upLevel=1)


def cb_edit_parent_controller(plug, label, annotation):
    from maya import cmds

    row_layout = cmds.rowLayout(numberOfColumns=2, adjustableColumn=2)
    cmds.text("Parent Controller")

    form_layout = cmds.formLayout()

    # component 의 controller 전체 추가.
    menu = cmds.optionMenu(height=24)
    cmds.menuItem(label="C")
    cmds.menuItem(label="L")
    cmds.menuItem(label="R")

    set_btn = cmds.button(height=24)
    unset_btn = cmds.button(height=24)

    # parent component 의 전체 추가.
    li = cmds.textScrollList()

    cmds.formLayout(
        form_layout,
        edit=True,
        attachForm=[
            (menu, "left", 2),
            (menu, "top", 2),
            (set_btn, "top", 2),
            (unset_btn, "top", 2),
            (unset_btn, "right", 2),
            (li, "bottom", 2),
            (li, "left", 2),
            (li, "right", 2),
        ],
        attachControl=[
            (menu, "right", 2, set_btn),
            (set_btn, "right", 2, unset_btn),
            (li, "top", 2, unset_btn),
        ],
    )
    cmds.setParent(upLevel=1)


# -------------------------------------------------------------------- #


# Control01 Callback ------------------------------------------------- #
def cb_edit_controller_count(plug, label, annotation):
    from maya import cmds

    cmds.columnLayout()
    index = cmds.getAttr(plug)
    slider = cmds.intSliderGrp(
        field=True,
        label="Controller Count",
        value=index,
        step=1,
        fieldMinValue=1,
        fieldMaxValue=999,
        minValue=1,
        maxValue=99,
    )

    def edit_controller_count(*args):
        new_index = args[0]
        cmds.setAttr(plug, new_index)

    cmds.intSliderGrp(slider, edit=True, changeCommand=edit_controller_count)
    cmds.setParent(upLevel=1)


# -------------------------------------------------------------------- #
