# Assembly Callback -------------------------------------------------- #


def add_script(*args):
    pass


def new_script(*args):
    pass


def delete_script(*args):
    pass


def up_script(*args):
    pass


def down_script(*args):
    pass


def run_script(*args):
    pass


def localize_script(*args):
    pass


def refresh_script_list(*args):
    pass


def callback_pre_custom_scripts(plug, label, annotation):
    from maya import cmds

    row_layout = cmds.rowLayout(numberOfColumns=2, adjustableColumn=2)
    cmds.text(label="Pre Custom Scripts")
    form_layout = cmds.formLayout()
    li = cmds.textScrollList()
    column_layout = cmds.columnLayout(generalSpacing=2)
    cmds.button(label="Add", height=24, command=add_script)
    cmds.button(label="New", height=24, command=new_script)
    cmds.button(label="Delete", height=24, command=delete_script)
    cmds.button(label="Up", height=24, command=up_script)
    cmds.button(label="Down", height=24, command=down_script)
    cmds.button(label="Run Sel", height=24, command=run_script)
    cmds.button(label="Localize", height=24, command=localize_script)
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


def callback_post_custom_scripts(plug, label, annotation):
    from maya import cmds

    row_layout = cmds.rowLayout(numberOfColumns=2, adjustableColumn=2)
    cmds.text(label="Post Custom Scripts")
    form_layout = cmds.formLayout()
    li = cmds.textScrollList()
    column_layout = cmds.columnLayout(generalSpacing=2)
    cmds.button(label="Add", height=24, command=add_script)
    cmds.button(label="New", height=24, command=new_script)
    cmds.button(label="Delete", height=24, command=delete_script)
    cmds.button(label="Up", height=24, command=up_script)
    cmds.button(label="Down", height=24, command=down_script)
    cmds.button(label="Run Sel", height=24, command=run_script)
    cmds.button(label="Localize", height=24, command=localize_script)
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


# -------------------------------------------------------------------- #


# Common Callback ---------------------------------------------------- #
def callback_edit_name(plug, label, annotation):
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


def callback_edit_side(plug, label, annotation):
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


def callback_edit_index(plug, label, annotation):
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


def callback_toggle_create_output_joint(plug, label, annotation):
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


def callback_edit_parent_output_index(plug, label, annotation):
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


# -------------------------------------------------------------------- #


# Control01 Callback ------------------------------------------------- #
def callback_edit_mirror_type(plug, label, annotation):
    from maya import cmds

    cmds.rowLayout(numberOfColumns=2, adjustableColumn=2)
    _type = cmds.getAttr(plug)
    cmds.text(label="Mirror Type")
    menu = cmds.optionMenu()
    cmds.menuItem(label="Orientation")
    cmds.menuItem(label="Behavior")
    cmds.menuItem(label="Inverse Scale")
    cmds.optionMenu(menu, edit=True, select=_type + 1)

    def edit_mirror_type(*args):
        li = ["Orientation", "Behavior", "Inverse Scale"]
        new_type = li.index(args[0])
        cmds.setAttr(plug, new_type)

    cmds.optionMenu(menu, edit=True, changeCommand=edit_mirror_type)
    cmds.setParent(upLevel=1)


def callback_edit_controller_count(plug, label, annotation):
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
