# domino
from domino.component import ORIGINMATRIX, SKEL
from domino.core.utils import logger
from domino.dominoui import (
    DynamicWidget,
    UIGenerator,
    get_component,
    get_manager_ui,
    get_settings_ui,
)

# maya
from maya import cmds


class Control01(DynamicWidget):

    def __init__(self, parent=None, root=None):
        super(Control01, self).__init__(parent=parent, root=root)
        UIGenerator.add_common_component_settings(self.parent_widget, root)

        manager_ui = get_manager_ui()
        settings_ui = get_settings_ui()

        def change_controller_count():
            rig = manager_ui.rig_tree_model.rig

            current_component = get_component(rig, name, side_str, index)
            if current_component["children"]:
                logger.warning("하위 컴포넌트가 존재합니다. 확인해주세요.")
                settings_ui.refresh()
                return

            old_count = len(cmds.listAttr(f"{root}.guide_matrix", multi=True))
            count = controller_count_spin_box.value()

            if old_count == count:
                settings_ui.refresh()
                return

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
                if old_count > count:
                    current_component["guide_matrix"]["value"] = current_component[
                        "guide_matrix"
                    ]["value"][:count]
                    current_component["initialize_output_matrix"]["value"] = (
                        current_component["initialize_output_matrix"]["value"][:count]
                    )
                    current_component["initialize_output_inverse_matrix"]["value"] = (
                        current_component["initialize_output_inverse_matrix"]["value"][
                            :count
                        ]
                    )
                elif old_count < count:
                    for _ in range(old_count, count):
                        current_component["guide_matrix"]["value"].append(
                            list(ORIGINMATRIX)
                        )
                        current_component["initialize_output_matrix"]["value"].append(
                            list(ORIGINMATRIX)
                        )
                        current_component["initialize_output_inverse_matrix"][
                            "value"
                        ].append(list(ORIGINMATRIX))
                current_component["controller_count"]["value"] = count
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

                cmds.select(current_component.guide_root)
                manager_ui.refresh()
                settings_ui.refresh()
            finally:
                cmds.undoInfo(closeChunk=True)

        controller_count_spin_box = UIGenerator.add_spin_box(
            self.parent_widget,
            label="Controller Count",
            attribute=f"{root}.controller_count",
            slider=False,
            min_value=1,
            max_value=999,
        )
        name = cmds.getAttr(f"{root}.name")
        side = cmds.getAttr(f"{root}.side")
        side_str = ["C", "L", "R"][side]
        index = cmds.getAttr(f"{root}.index")
        controller_count_spin_box.editingFinished.connect(change_controller_count)
        UIGenerator.add_notes(self.parent_widget, f"{root}.notes")
