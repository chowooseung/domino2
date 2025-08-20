# domino
from domino.dominoui import (
    DynamicWidget,
    UIGenerator,
    get_component,
    get_manager_ui,
    get_settings_ui,
)
from domino.component import ORIGINMATRIX, SKEL, Name
from domino.core.utils import logger

# gui
from PySide6 import QtWidgets

# maya
from maya import cmds

# built-ins
import uuid
from functools import partial


class UIContainer01(DynamicWidget):

    def __init__(self, parent=None, root=None):
        super(UIContainer01, self).__init__(parent=parent, root=root)

        settings_ui = get_settings_ui()
        manager_ui = get_manager_ui()

        def edit_name():

            new_name = name_line_edit.text()
            for s in new_name:
                if not s.isalpha() and not s.isalnum():
                    logger.warning(f"{new_name} `{s}`는 유효하지 않습니다.")
                    settings_ui.refresh()
                    return

            old_name = cmds.getAttr(f"{root}.name")
            if old_name == new_name:
                settings_ui.refresh()
                return

            try:
                cmds.undoInfo(openChunk=True)

                nodes = [
                    x for x in cmds.ls(type="transform") if x.startswith(f"{old_name}_")
                ]
                cmds.setAttr(f"{root}.name", new_name, type="string")
                for node in nodes:
                    cmds.rename(node, node.replace(f"{old_name}_", f"{new_name}_"))

                manager_ui.refresh()
                settings_ui.refresh()
            finally:
                cmds.undoInfo(closeChunk=True)

        def edit_text():
            old_text = cmds.getAttr(f"{root}.container_text")
            new_text = text_line_edit.text()
            for s in new_text:
                if not s.isalpha() and not s.isalnum():
                    logger.warning(f"{new_text} `{s}`는 유효하지 않습니다.")
                    settings_ui.refresh()
                    return
            if old_text == new_text:
                settings_ui.refresh()
                return

            try:
                cmds.undoInfo(openChunk=True)

                parent = cmds.listRelatives("uicontainer_textShape", parent=True)[0]
                cmds.delete("uicontainer_textShape")
                grp, temp = cmds.textCurves(name="uicontainer_text", text=new_text)
                cmds.setAttr(f"{grp}.t", lock=True, keyable=False)
                cmds.setAttr(f"{grp}.r", lock=True, keyable=False)
                cmds.setAttr(f"{grp}.s", lock=True, keyable=False)
                cmds.parent(grp, parent)
                cmds.setAttr(f"{grp}.overrideEnabled", 1)
                cmds.setAttr(f"{grp}.overrideDisplayType", 2)
                cmds.delete(temp)
                manager_ui.refresh()
                settings_ui.refresh()
            finally:
                cmds.undoInfo(closeChunk=True)

        def edit_slider_count():
            rig = manager_ui.rig_tree_model.rig

            old_count = cmds.getAttr(f"{root}.slider_count")
            new_count = slider_count_spin_box.value()
            if old_count == new_count:
                settings_ui.refresh()
                return

            current_component = get_component(rig, cmds.getAttr(f"{root}.name"), "", "")

            try:
                cmds.undoInfo(openChunk=True)
                current_component.detach_guide()
                output_joints = cmds.listConnections(
                    f"{current_component.rig_root}.output_joint",
                    source=True,
                    destination=False,
                )
                joint_children = []
                for j in output_joints:
                    children = cmds.listRelatives(j, children=True)
                    if children:
                        joint_children.extend(list(set(children) - set(output_joints)))
                if joint_children:
                    cmds.parent(joint_children, SKEL)
                cmds.delete([current_component.rig_root] + output_joints)

                if old_count > new_count:
                    current_component["slider_count"]["value"] = new_count
                elif old_count < new_count:
                    current_component["slider_count"]["value"] = new_count
                    for c in range(old_count, new_count):
                        uuid_string = uuid.uuid4().hex
                        for u in range(len(uuid_string)):
                            if uuid_string[u].isalpha():
                                break
                        current_component["guide_matrix"]["value"].append(
                            list(ORIGINMATRIX)
                        )
                        current_component["initialize_output_matrix"]["value"].append(
                            list(ORIGINMATRIX)
                        )
                        current_component["initialize_output_inverse_matrix"][
                            "value"
                        ].append(list(ORIGINMATRIX))
                        current_component["slider_side"]["value"].append(0)
                        current_component["slider_description"]["value"].append(
                            uuid_string[u : u + 8]
                        )
                        current_component["slider_keyable_attribute"]["value"].append(
                            "1,1,1,1"
                        )
                        current_component["slider_keyable_attribute_name"][
                            "value"
                        ].append(",,,")

                current_component["controller"] = []
                current_component["output"] = []
                current_component["output_joint"] = []
                current_component.populate()
                current_component.rig()
                current_component.attach_guide()
                output_joints = cmds.listConnections(
                    f"{current_component.rig_root}.output_joint",
                    source=True,
                    destination=False,
                )
                current_component.setup_skel(output_joints)
                cmds.select(f"{root}")
                manager_ui.refresh()
                settings_ui.refresh()
            finally:
                cmds.undoInfo(closeChunk=True)

        def change_slider_side(slider_index, index, *args):
            side_list = ["", "L", "R"]
            slider_side_list = cmds.getAttr(f"{root}.slider_side")[0]
            old_side_index = slider_side_list[slider_index]
            old_side = side_list[int(old_side_index)]

            new_side_index = side_combo_boxes[index].currentIndex()
            if old_side_index == new_side_index:
                settings_ui.refresh()
                return
            new_side = side_list[int(new_side_index)]

            name = cmds.getAttr(f"{root}.name")
            description = cmds.getAttr(f"{root}.slider_description[{slider_index}]")
            if cmds.ls(
                f"{name}_{description}{new_side}_*",
                type="transform",
            ):
                logger.warning(f"{description}{new_side} 는 이미 존재합니다.")
                settings_ui.refresh()
                return

            rig_root = cmds.listConnections(
                f"{root}.component", source=False, destination=True
            )[0]
            output_joint = cmds.listConnections(
                f"{rig_root}.output_joint", source=True, destination=False
            )[0]

            tx_ty_attrs = ["tx", "tx", "ty", "ty"]
            name_attrs = [
                x
                for x in cmds.getAttr(
                    f"{root}.slider_keyable_attribute_name[{slider_index}]"
                ).split(",")
            ]
            if name_attrs[0] or name_attrs[1] or name_attrs[2] or name_attrs[3]:
                logger.warning("attribute name 을 초기화 후 변경해주세요.")
                settings_ui.refresh()
                return

            try:
                cmds.undoInfo(openChunk=True)
                nodes = cmds.ls(
                    f"{name}_{description}{old_side}_*",
                    type="transform",
                )
                for node in nodes:
                    cmds.rename(
                        node,
                        node.replace(
                            f"{name}_{description}{old_side}_",
                            f"{name}_{description}{new_side}_",
                        ),
                    )
                cmds.setAttr(f"{root}.slider_side[{slider_index}]", new_side_index)
                c = 0
                for txy, name in zip(tx_ty_attrs, name_attrs):
                    if name:
                        old_name = f"{name}{old_side}"
                        new_name = f"{name}{new_side}"
                    else:
                        old_name = f"{description}{old_side}_{txy}_{'plus' if c % 2 == 0 else 'minus'}"
                        new_name = f"{description}{new_side}_{txy}_{'plus' if c % 2 == 0 else 'minus'}"

                    if cmds.objExists(f"{output_joint}.{old_name}"):
                        cmds.renameAttr(f"{output_joint}.{old_name}", new_name)
                    c += 1
                manager_ui.refresh()
                settings_ui.refresh()
            finally:
                cmds.undoInfo(closeChunk=True)

        def edit_slider_description(slider_index, index):
            new_description = description_line_edits[index].text()
            for s in new_description:
                if not s.isalpha() and not s.isalnum():
                    logger.warning(f"{new_description} `{s}`는 유효하지 않습니다.")
                    settings_ui.refresh()
                    return

            old_description = cmds.getAttr(f"{root}.slider_description[{slider_index}]")
            if old_description == new_description:
                settings_ui.refresh()
                return

            side_list = ["", "L", "R"]
            slider_side_list = cmds.getAttr(f"{root}.slider_side")[0]
            side_index = slider_side_list[slider_index]
            side_str = side_list[int(side_index)]
            name = cmds.getAttr(f"{root}.name")
            if cmds.ls(f"{name}_{new_description}{side_str}_*", type="transform"):
                logger.warning(f"{new_description}{side_str} 는 이미 존재합니다.")
                settings_ui.refresh()
                return

            rig_root = cmds.listConnections(
                f"{root}.component", source=False, destination=True
            )[0]
            output_joint = cmds.listConnections(
                f"{rig_root}.output_joint", source=True, destination=False
            )[0]
            ptx_attr, mtx_attr, pty_attr, mty_attr = [
                x
                for x in cmds.getAttr(
                    f"{root}.slider_keyable_attribute_name[{slider_index}]"
                ).split(",")
            ]
            if ptx_attr or mtx_attr or pty_attr or mty_attr:
                logger.warning("attribute name 을 초기화 후 변경해주세요.")
                settings_ui.refresh()
                return

            try:
                cmds.undoInfo(openChunk=True)
                nodes = cmds.ls(
                    f"{name}_{old_description}{side_str}_*", type="transform"
                )
                for node in nodes:
                    cmds.rename(
                        node,
                        node.replace(
                            f"{name}_{old_description}{side_str}_",
                            f"{name}_{new_description}{side_str}_",
                        ),
                    )
                cmds.setAttr(
                    f"{root}.slider_description[{slider_index}]",
                    new_description,
                    type="string",
                )
                if not ptx_attr:
                    old_ptx_attr = f"{old_description}{side_str}_tx_plus"
                    new_ptx_attr = f"{new_description}{side_str}_tx_plus"
                    if cmds.objExists(f"{output_joint}.{old_ptx_attr}"):
                        cmds.renameAttr(f"{output_joint}.{old_ptx_attr}", new_ptx_attr)
                if not mtx_attr:
                    old_mtx_attr = f"{old_description}{side_str}_tx_minus"
                    new_mtx_attr = f"{new_description}{side_str}_tx_minus"
                    if cmds.objExists(f"{output_joint}.{old_mtx_attr}"):
                        cmds.renameAttr(f"{output_joint}.{old_mtx_attr}", new_mtx_attr)
                if not pty_attr:
                    old_pty_attr = f"{old_description}{side_str}_ty_plus"
                    new_pty_attr = f"{new_description}{side_str}_ty_plus"
                    if cmds.objExists(f"{output_joint}.{old_pty_attr}"):
                        cmds.renameAttr(f"{output_joint}.{old_pty_attr}", new_pty_attr)
                if not mty_attr:
                    old_mty_attr = f"{old_description}{side_str}_ty_minus"
                    new_mty_attr = f"{new_description}{side_str}_ty_minus"
                    if cmds.objExists(f"{output_joint}.{old_mty_attr}"):
                        cmds.renameAttr(f"{output_joint}.{old_mty_attr}", new_mty_attr)
                manager_ui.refresh()
                settings_ui.refresh()
            finally:
                cmds.undoInfo(closeChunk=True)

        def toggle_keyable_attrs(slider_index, index, *args):
            _ptx_check_box, _mtx_check_box, _pty_check_box, _mty_check_box = (
                keyable_attr_check_boxes[index]
            )

            new_ptx_value = _ptx_check_box.isChecked()
            new_mtx_value = _mtx_check_box.isChecked()
            new_pty_value = _pty_check_box.isChecked()
            new_mty_value = _mty_check_box.isChecked()

            old_ptx_value, old_mtx_value, old_pty_value, old_mty_value = [
                bool(int(x))
                for x in cmds.getAttr(
                    f"{root}.slider_keyable_attribute[{slider_index}]"
                ).split(",")
            ]

            if (new_ptx_value, new_mtx_value, new_pty_value, new_mty_value) == (
                old_ptx_value,
                old_mtx_value,
                old_pty_value,
                old_mty_value,
            ):
                settings_ui.refresh()
                return

            name = cmds.getAttr(f"{root}.name")
            description = cmds.getAttr(f"{root}.slider_description[{slider_index}]")
            side_list = ["", "L", "R"]
            slider_side_list = cmds.getAttr(f"{root}.slider_side")[0]
            side_index = slider_side_list[slider_index]
            side_str = side_list[int(side_index)]
            frame_node = f"{name}_{description}{side_str}_frame"
            ctl_node = f"{name}_{description}{side_str}_{Name.controller_extension}"

            new_str = ",".join(
                [
                    str(int(new_ptx_value)),
                    str(int(new_mtx_value)),
                    str(int(new_pty_value)),
                    str(int(new_mty_value)),
                ]
            )

            rig_root = cmds.listConnections(
                f"{root}.component", source=False, destination=True
            )[0]
            output_joint = cmds.listConnections(
                f"{rig_root}.output_joint", source=True, destination=False
            )[0]
            ptx_attr, mtx_attr, pty_attr, mty_attr = [
                x
                for x in cmds.getAttr(
                    f"{root}.slider_keyable_attribute_name[{slider_index}]"
                ).split(",")
            ]

            side_list = ["", "L", "R"]
            slider_side_list = cmds.getAttr(f"{root}.slider_side")[0]
            side_index = slider_side_list[slider_index]
            side = side_list[int(side_index)]

            if ptx_attr:
                ptx_attr += side
            elif not ptx_attr:
                ptx_attr = f"{description}{side}_tx_plus"
            if mtx_attr:
                mtx_attr += side
            elif not mtx_attr:
                mtx_attr = f"{description}{side}_tx_minus"
            if pty_attr:
                pty_attr += side
            elif not pty_attr:
                pty_attr = f"{description}{side}_ty_plus"
            if mty_attr:
                mty_attr += side
            elif not mty_attr:
                mty_attr = f"{description}{side}_ty_minus"

            try:
                cmds.undoInfo(openChunk=True)
                selected = cmds.ls(selection=True)
                if old_ptx_value != new_ptx_value:
                    if new_ptx_value:
                        cmds.move(
                            1,
                            0,
                            0,
                            [
                                f"{frame_node}.cv[1]",
                                f"{frame_node}.cv[2]",
                            ],
                            objectSpace=True,
                            relative=True,
                        )
                        cmds.addAttr(
                            output_joint,
                            longName=ptx_attr,
                            attributeType="float",
                            keyable=True,
                        )
                        rv = cmds.createNode("remapValue")
                        cmds.setAttr(f"{rv}.inputMax", 1)
                        cmds.connectAttr(f"{ctl_node}.tx", f"{rv}.inputValue")
                        cmds.connectAttr(f"{rv}.outValue", f"{output_joint}.{ptx_attr}")
                        cmds.setAttr(f"{frame_node.replace('frame', 'ptxline')}.v", 1)
                    elif not new_ptx_value:
                        cmds.move(
                            -1,
                            0,
                            0,
                            [
                                f"{frame_node}.cv[1]",
                                f"{frame_node}.cv[2]",
                            ],
                            objectSpace=True,
                            relative=True,
                        )
                        cmds.delete(
                            cmds.listConnections(
                                f"{output_joint}.{ptx_attr}", source=True
                            )
                        )
                        cmds.deleteAttr(output_joint, attribute=ptx_attr)
                        cmds.setAttr(f"{frame_node.replace('frame', 'ptxline')}.v", 0)
                    cmds.transformLimits(
                        ctl_node,
                        translationX=(-1 * int(new_mtx_value), int(new_ptx_value)),
                        enableTranslationX=(1, 1),
                    )
                if old_mtx_value != new_mtx_value:
                    if new_mtx_value:
                        cmds.move(
                            -1,
                            0,
                            0,
                            [
                                f"{frame_node}.cv[0]",
                                f"{frame_node}.cv[4]",
                                f"{frame_node}.cv[3]",
                            ],
                            objectSpace=True,
                            relative=True,
                        )
                        cmds.addAttr(
                            output_joint,
                            longName=mtx_attr,
                            attributeType="float",
                            keyable=True,
                        )
                        rv = cmds.createNode("remapValue")
                        cmds.setAttr(f"{rv}.inputMax", -1)
                        cmds.connectAttr(f"{ctl_node}.tx", f"{rv}.inputValue")
                        cmds.connectAttr(f"{rv}.outValue", f"{output_joint}.{mtx_attr}")
                        cmds.setAttr(f"{frame_node.replace('frame', 'mtxline')}.v", 1)
                    elif not new_mtx_value:
                        cmds.move(
                            1,
                            0,
                            0,
                            [
                                f"{frame_node}.cv[0]",
                                f"{frame_node}.cv[4]",
                                f"{frame_node}.cv[3]",
                            ],
                            objectSpace=True,
                            relative=True,
                        )
                        cmds.delete(
                            cmds.listConnections(
                                f"{output_joint}.{mtx_attr}", source=True
                            )
                        )
                        cmds.deleteAttr(output_joint, attribute=mtx_attr)
                        cmds.setAttr(f"{frame_node.replace('frame', 'mtxline')}.v", 0)
                    cmds.transformLimits(
                        ctl_node,
                        translationX=(-1 * int(new_mtx_value), int(new_ptx_value)),
                        enableTranslationX=(1, 1),
                    )
                if old_pty_value != new_pty_value:
                    if new_pty_value:
                        cmds.move(
                            0,
                            1,
                            0,
                            [
                                f"{frame_node}.cv[0]",
                                f"{frame_node}.cv[1]",
                                f"{frame_node}.cv[4]",
                            ],
                            objectSpace=True,
                            relative=True,
                        )
                        cmds.addAttr(
                            output_joint,
                            longName=pty_attr,
                            attributeType="float",
                            keyable=True,
                        )
                        rv = cmds.createNode("remapValue")
                        cmds.setAttr(f"{rv}.inputMax", 1)
                        cmds.connectAttr(f"{ctl_node}.ty", f"{rv}.inputValue")
                        cmds.connectAttr(f"{rv}.outValue", f"{output_joint}.{pty_attr}")
                        cmds.setAttr(f"{frame_node.replace('frame', 'ptyline')}.v", 1)
                    elif not new_pty_value:
                        cmds.move(
                            0,
                            -1,
                            0,
                            [
                                f"{frame_node}.cv[0]",
                                f"{frame_node}.cv[1]",
                                f"{frame_node}.cv[4]",
                            ],
                            objectSpace=True,
                            relative=True,
                        )
                        cmds.delete(
                            cmds.listConnections(
                                f"{output_joint}.{pty_attr}", source=True
                            )
                        )
                        cmds.deleteAttr(output_joint, attribute=pty_attr)
                        cmds.setAttr(f"{frame_node.replace('frame', 'ptyline')}.v", 0)
                    cmds.transformLimits(
                        ctl_node,
                        translationY=(-1 * int(new_mty_value), int(new_pty_value)),
                        enableTranslationY=(1, 1),
                    )
                if old_mty_value != new_mty_value:
                    if new_mty_value:
                        cmds.move(
                            0,
                            -1,
                            0,
                            [f"{frame_node}.cv[2]", f"{frame_node}.cv[3]"],
                            objectSpace=True,
                            relative=True,
                        )
                        cmds.addAttr(
                            output_joint,
                            longName=mty_attr,
                            attributeType="float",
                            keyable=True,
                        )
                        rv = cmds.createNode("remapValue")
                        cmds.setAttr(f"{rv}.inputMax", -1)
                        cmds.connectAttr(f"{ctl_node}.ty", f"{rv}.inputValue")
                        cmds.connectAttr(f"{rv}.outValue", f"{output_joint}.{mty_attr}")
                        cmds.setAttr(f"{frame_node.replace('frame', 'mtyline')}.v", 1)
                    elif not new_mty_value:
                        cmds.move(
                            0,
                            1,
                            0,
                            [f"{frame_node}.cv[2]", f"{frame_node}.cv[3]"],
                            objectSpace=True,
                            relative=True,
                        )
                        cmds.delete(
                            cmds.listConnections(
                                f"{output_joint}.{mty_attr}", source=True
                            )
                        )
                        cmds.deleteAttr(output_joint, attribute=mty_attr)
                        cmds.setAttr(f"{frame_node.replace('frame', 'mtyline')}.v", 0)
                    cmds.transformLimits(
                        ctl_node,
                        translationY=(-1 * int(new_mty_value), int(new_pty_value)),
                        enableTranslationY=(1, 1),
                    )
                cmds.setAttr(
                    f"{root}.slider_keyable_attribute[{slider_index}]",
                    new_str,
                    type="string",
                )
                cmds.select(selected)
                manager_ui.refresh()
                settings_ui.refresh()
            finally:
                cmds.undoInfo(closeChunk=True)

        def edit_keyable_attr_name(slider_index, index):
            _ptx_line_edit, _mtx_line_edit, _pty_line_edit, _mty_line_edit = (
                keyable_attr_description_line_edits[index]
            )
            new_ptx_attr = _ptx_line_edit.text()
            if new_ptx_attr:
                if not new_ptx_attr[0].isalpha():
                    logger.warning(f"{new_ptx_attr} 알파벳으로 시작해야 합니다.")
                    settings_ui.refresh()
                    return
                for s in new_ptx_attr:
                    if not s.isalpha() and not s.isalnum():
                        logger.warning(f"{new_ptx_attr} `{s}`는 유효하지 않습니다.")
                        settings_ui.refresh()
                        return
            new_mtx_attr = _mtx_line_edit.text()
            if new_mtx_attr:
                if not new_mtx_attr[0].isalpha():
                    logger.warning(f"{new_mtx_attr} 알파벳으로 시작해야 합니다.")
                    settings_ui.refresh()
                    return
                for s in new_mtx_attr:
                    if not s.isalpha() and not s.isalnum():
                        logger.warning(f"{new_mtx_attr} `{s}`는 유효하지 않습니다.")
                        settings_ui.refresh()
                        return
            new_pty_attr = _pty_line_edit.text()
            if new_pty_attr:
                if not new_pty_attr[0].isalpha():
                    logger.warning(f"{new_pty_attr} 알파벳으로 시작해야 합니다.")
                    settings_ui.refresh()
                    return
                for s in new_pty_attr:
                    if not s.isalpha() and not s.isalnum():
                        logger.warning(f"{new_pty_attr} `{s}`는 유효하지 않습니다.")
                        settings_ui.refresh()
                        return
            new_mty_attr = _mty_line_edit.text()
            if new_mty_attr:
                if not new_mty_attr[0].isalpha():
                    logger.warning(f"{new_mty_attr} 알파벳으로 시작해야 합니다.")
                    settings_ui.refresh()
                    return
                for s in new_mty_attr:
                    if not s.isalpha() and not s.isalnum():
                        logger.warning(f"{new_mty_attr} `{s}`는 유효하지 않습니다.")
                        settings_ui.refresh()
                        return

            old_ptx_attr, old_mtx_attr, old_pty_attr, old_mty_attr = [
                x
                for x in cmds.getAttr(
                    f"{root}.slider_keyable_attribute_name[{slider_index}]"
                ).split(",")
            ]
            if (old_ptx_attr, old_mtx_attr, old_pty_attr, old_mty_attr) == (
                new_ptx_attr,
                new_mtx_attr,
                new_pty_attr,
                new_mty_attr,
            ):
                settings_ui.refresh()
                return

            rig_root = cmds.listConnections(
                f"{root}.component", source=False, destination=True
            )[0]
            output_joint = cmds.listConnections(
                f"{rig_root}.output_joint", source=True, destination=False
            )[0]
            description = cmds.getAttr(f"{root}.slider_description[{slider_index}]")

            side_list = ["", "L", "R"]
            slider_side_list = cmds.getAttr(f"{root}.slider_side")[0]
            side_index = slider_side_list[slider_index]
            side = side_list[int(side_index)]

            new_str = ",".join([new_ptx_attr, new_mtx_attr, new_pty_attr, new_mty_attr])
            if new_ptx_attr:
                new_ptx_attr += side
            if old_ptx_attr:
                old_ptx_attr += side
            if not new_ptx_attr:
                new_ptx_attr = f"{description}{side}_tx_plus"
            if not old_ptx_attr:
                old_ptx_attr = f"{description}{side}_tx_plus"
            if new_mtx_attr:
                new_mtx_attr += side
            if old_mtx_attr:
                old_mtx_attr += side
            if not new_mtx_attr:
                new_mtx_attr = f"{description}{side}_tx_minus"
            if not old_mtx_attr:
                old_mtx_attr = f"{description}{side}_tx_minus"
            if new_pty_attr:
                new_pty_attr += side
            if old_pty_attr:
                old_pty_attr += side
            if not new_pty_attr:
                new_pty_attr = f"{description}{side}_ty_plus"
            if not old_pty_attr:
                old_pty_attr = f"{description}{side}_ty_plus"
            if new_mty_attr:
                new_mty_attr += side
            if old_mty_attr:
                old_mty_attr += side
            if not new_mty_attr:
                new_mty_attr = f"{description}{side}_ty_minus"
            if not old_mty_attr:
                old_mty_attr = f"{description}{side}_ty_minus"

            if old_ptx_attr != new_ptx_attr and cmds.objExists(
                f"{output_joint}.{new_ptx_attr}"
            ):
                logger.warning(f"{output_joint}.{new_ptx_attr} 이미 존재합니다.")
                settings_ui.refresh()
                return
            if old_mtx_attr != new_mtx_attr and cmds.objExists(
                f"{output_joint}.{new_mtx_attr}"
            ):
                logger.warning(f"{output_joint}.{new_mtx_attr} 이미 존재합니다.")
                settings_ui.refresh()
                return
            if old_pty_attr != new_pty_attr and cmds.objExists(
                f"{output_joint}.{new_pty_attr}"
            ):
                logger.warning(f"{output_joint}.{new_pty_attr} 이미 존재합니다.")
                settings_ui.refresh()
                return
            if old_mty_attr != new_mty_attr and cmds.objExists(
                f"{output_joint}.{new_mty_attr}"
            ):
                logger.warning(f"{output_joint}.{new_mty_attr} 이미 존재합니다.")
                settings_ui.refresh()
                return

            try:
                cmds.undoInfo(openChunk=True)
                if old_ptx_attr != new_ptx_attr:
                    if cmds.objExists(f"{output_joint}.{old_ptx_attr}"):
                        cmds.renameAttr(f"{output_joint}.{old_ptx_attr}", new_ptx_attr)
                if old_mtx_attr != new_mtx_attr:
                    if cmds.objExists(f"{output_joint}.{old_mtx_attr}"):
                        cmds.renameAttr(f"{output_joint}.{old_mtx_attr}", new_mtx_attr)
                if old_pty_attr != new_pty_attr:
                    if cmds.objExists(f"{output_joint}.{old_pty_attr}"):
                        cmds.renameAttr(f"{output_joint}.{old_pty_attr}", new_pty_attr)
                if old_mty_attr != new_mty_attr:
                    if cmds.objExists(f"{output_joint}.{old_mty_attr}"):
                        cmds.renameAttr(f"{output_joint}.{old_mty_attr}", new_mty_attr)
                cmds.setAttr(
                    f"{root}.slider_keyable_attribute_name[{slider_index}]",
                    new_str,
                    type="string",
                )
                manager_ui.refresh()
                settings_ui.refresh()
            finally:
                cmds.undoInfo(closeChunk=True)

        name_line_edit = UIGenerator.add_line_edit(
            self.parent_widget, label="Name", attribute=f"{root}.name"
        )
        name_line_edit.editingFinished.disconnect()
        name_line_edit.editingFinished.connect(partial(edit_name))

        text_line_edit = UIGenerator.add_line_edit(
            self.parent_widget, label="Text", attribute=f"{root}.container_text"
        )
        text_line_edit.editingFinished.disconnect()
        text_line_edit.editingFinished.connect(partial(edit_text))

        slider_count_spin_box = UIGenerator.add_spin_box(
            self.parent_widget,
            label="Slider Count",
            attribute=f"{root}.slider_count",
            slider=False,
            min_value=1,
            max_value=999,
        )
        slider_count_spin_box.editingFinished.disconnect()
        slider_count_spin_box.editingFinished.connect(edit_slider_count)

        selected = cmds.ls(selection=True)
        selected_indexes = []
        for sel in selected:
            if not cmds.objExists(f"{sel}.is_domino_guide"):
                continue
            plug = cmds.listConnections(
                f"{sel}.worldMatrix[0]", source=False, destination=True, plugs=True
            )[0]
            r = plug.split(".")[0]
            if not cmds.objExists(f"{r}.is_domino_guide_root"):
                continue
            elif cmds.getAttr(f"{r}.component") != "uicontainer01":
                continue
            selected_index = int(plug.split("[")[1][:-1])
            if selected_index < 2:
                continue
            selected_indexes.append(selected_index - 2)

        loop_list = (
            selected_indexes
            if selected_indexes
            else range(cmds.getAttr(f"{root}.slider_count"))
        )

        side_combo_boxes = []
        description_line_edits = []
        keyable_attr_check_boxes = []
        keyable_attr_description_line_edits = []
        for n, i in enumerate(loop_list):
            frame = QtWidgets.QFrame()
            frame.setFrameShape(QtWidgets.QFrame.Shape.Box)

            layout = QtWidgets.QFormLayout(frame)

            combo_box = QtWidgets.QComboBox()
            side_index = cmds.getAttr(f"{root}.slider_side")[0][i]
            combo_box.addItems(["C", "L", "R"])
            combo_box.setCurrentIndex(side_index)
            combo_box.setSizePolicy(
                QtWidgets.QSizePolicy.Policy.Expanding,
                QtWidgets.QSizePolicy.Policy.Fixed,
            )
            side_combo_boxes.append(combo_box)
            layout.addRow("Slider Side", combo_box)
            description_line_edit = QtWidgets.QLineEdit()
            d = cmds.getAttr(f"{root}.slider_description[{i}]")
            description_line_edit.setText(d)
            layout.addRow("Slider Description", description_line_edit)
            description_line_edits.append(description_line_edit)

            keyable_attrs_layout = QtWidgets.QHBoxLayout()
            ptx, mtx, pty, mty = cmds.getAttr(
                f"{root}.slider_keyable_attribute[{i}]"
            ).split(",")
            ptx_check_box = QtWidgets.QCheckBox("+tx")
            ptx_check_box.setChecked(int(ptx))
            mtx_check_box = QtWidgets.QCheckBox("-tx")
            mtx_check_box.setChecked(int(mtx))
            pty_check_box = QtWidgets.QCheckBox("+ty")
            pty_check_box.setChecked(int(pty))
            mty_check_box = QtWidgets.QCheckBox("-ty")
            mty_check_box.setChecked(int(mty))
            keyable_attr_check_boxes.append(
                [ptx_check_box, mtx_check_box, pty_check_box, mty_check_box]
            )
            keyable_attrs_layout.addWidget(ptx_check_box)
            keyable_attrs_layout.addWidget(mtx_check_box)
            keyable_attrs_layout.addWidget(pty_check_box)
            keyable_attrs_layout.addWidget(mty_check_box)
            layout.addRow("Slider Attrs", keyable_attrs_layout)

            tx_description_layout = QtWidgets.QHBoxLayout()
            ptx, mtx, pty, mty = cmds.getAttr(
                f"{root}.slider_keyable_attribute_name[{i}]"
            ).split(",")
            ptx_line_edit = QtWidgets.QLineEdit()
            ptx_line_edit.setText(ptx)
            ptx_line_edit.setPlaceholderText("+tx attribute name")
            tx_description_layout.addWidget(ptx_line_edit)
            mtx_line_edit = QtWidgets.QLineEdit()
            mtx_line_edit.setText(mtx)
            mtx_line_edit.setPlaceholderText("-tx attribute name")
            tx_description_layout.addWidget(mtx_line_edit)
            ty_description_layout = QtWidgets.QHBoxLayout()
            pty_line_edit = QtWidgets.QLineEdit()
            pty_line_edit.setText(pty)
            pty_line_edit.setPlaceholderText("+ty attribute name")
            ty_description_layout.addWidget(pty_line_edit)
            mty_line_edit = QtWidgets.QLineEdit()
            mty_line_edit.setText(mty)
            mty_line_edit.setPlaceholderText("-ty attribute name")
            ty_description_layout.addWidget(mty_line_edit)
            keyable_attr_description_line_edits.append(
                [ptx_line_edit, mtx_line_edit, pty_line_edit, mty_line_edit]
            )

            combo_box.currentIndexChanged.connect(partial(change_slider_side, i, n))
            description_line_edit.editingFinished.connect(
                partial(edit_slider_description, i, n)
            )
            ptx_check_box.toggled.connect(partial(toggle_keyable_attrs, i, n))
            mtx_check_box.toggled.connect(partial(toggle_keyable_attrs, i, n))
            pty_check_box.toggled.connect(partial(toggle_keyable_attrs, i, n))
            mty_check_box.toggled.connect(partial(toggle_keyable_attrs, i, n))

            ptx_line_edit.editingFinished.connect(partial(edit_keyable_attr_name, i, n))
            mtx_line_edit.editingFinished.connect(partial(edit_keyable_attr_name, i, n))
            pty_line_edit.editingFinished.connect(partial(edit_keyable_attr_name, i, n))
            mty_line_edit.editingFinished.connect(partial(edit_keyable_attr_name, i, n))

            layout.addRow(tx_description_layout)
            layout.addRow(ty_description_layout)

            self.parent_widget.layout().addRow(frame)

        UIGenerator.add_notes(self.parent_widget, f"{root}.notes")
