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


class Fk01(DynamicWidget):

    def __init__(self, parent=None, root=None):
        super(Fk01, self).__init__(parent=parent, root=root)
        UIGenerator.add_common_component_settings(self.parent_widget, root)

        manager_ui = get_manager_ui()
        settings_ui = get_settings_ui()

        def change_count():
            rig = manager_ui.rig_tree_model.rig

            current_component = get_component(rig, name, side_str, index)
            if current_component["children"]:
                logger.warning("하위 컴포넌트가 존재합니다. 확인해주세요.")
                settings_ui.refresh()
                return

            root_count = root_count_spin_box.value()
            chain_counts = [s_box.value() for s_box in chain_count_spin_boxes]

            if (old_root_count == root_count) and (old_chain_counts == chain_counts):
                settings_ui.refresh()
                return

            matrices = [list(ORIGINMATRIX) for _ in range(2)]
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
                if old_root_count > root_count:
                    delete_count = sum(old_chain_counts[old_root_count - root_count :])
                    current_component["guide_matrix"]["value"] = current_component[
                        "guide_matrix"
                    ]["value"][:delete_count]
                    current_component["initialize_output_matrix"]["value"] = (
                        current_component["initialize_output_matrix"]["value"][
                            :delete_count
                        ]
                    )
                    current_component["initialize_output_inverse_matrix"]["value"] = (
                        current_component["initialize_output_inverse_matrix"]["value"][
                            :delete_count
                        ]
                    )
                    chain_counts = chain_counts[:delete_count]
                elif old_root_count < root_count:
                    for _ in range(old_root_count, root_count):
                        current_component["guide_matrix"]["value"].extend(matrices)
                        current_component["initialize_output_matrix"]["value"].extend(
                            matrices
                        )
                        current_component["initialize_output_inverse_matrix"][
                            "value"
                        ].extend(matrices)
                        chain_counts.append(2)
                elif old_chain_counts != chain_counts:
                    chain_guide_matrices = []
                    chain_output_matrices = []
                    chain_output_inverse_matrices = []
                    i = 0
                    for count in old_chain_counts:
                        chain_guide_matrices.append(
                            current_component["guide_matrix"]["value"][i : i + count]
                        )
                        chain_output_matrices.append(
                            current_component["initialize_output_matrix"]["value"][
                                i : i + count
                            ]
                        )
                        chain_output_inverse_matrices.append(
                            current_component["initialize_output_inverse_matrix"][
                                "value"
                            ][i : i + count]
                        )
                        i += count
                    c = 0
                    for new_count, old_count in zip(chain_counts, old_chain_counts):
                        if old_count > new_count:
                            chain_guide_matrices[c] = chain_guide_matrices[c][
                                :new_count
                            ]
                            chain_output_matrices[c] = chain_output_matrices[c][
                                :new_count
                            ]
                            chain_output_inverse_matrices[c] = (
                                chain_output_inverse_matrices[c][:new_count]
                            )
                        elif old_count < new_count:
                            chain_guide_matrices[c].append(list(ORIGINMATRIX))
                            chain_output_matrices[c].append(list(ORIGINMATRIX))
                            chain_output_inverse_matrices[c].append(list(ORIGINMATRIX))
                        c += 1
                    current_component["guide_matrix"]["value"].extend(
                        [y for x in chain_guide_matrices for y in x]
                    )
                    current_component["initialize_output_matrix"]["value"].extend(
                        [y for x in chain_output_inverse_matrices for y in x]
                    )
                    current_component["initialize_output_inverse_matrix"][
                        "value"
                    ].extend([y for x in chain_output_inverse_matrices for y in x])
                current_component["root_count"]["value"] = root_count
                current_component["chain_count"]["value"] = chain_counts
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

        name = cmds.getAttr(f"{root}.name")
        side = cmds.getAttr(f"{root}.side")
        side_str = ["C", "L", "R"][side]
        index = cmds.getAttr(f"{root}.index")

        old_root_count = cmds.getAttr(f"{root}.root_count")
        old_chain_counts = []
        for i in range(old_root_count):
            old_chain_counts.append(cmds.getAttr(f"{root}.chain_count[{i}]"))

        root_count = cmds.getAttr(f"{root}.root_count")
        root_count_spin_box = UIGenerator.add_spin_box(
            self.parent_widget,
            label="Root Count",
            attribute=f"{root}.root_count",
            slider=False,
            min_value=1,
            max_value=999,
        )
        root_count_spin_box.editingFinished.connect(change_count)
        chain_count_spin_boxes = []
        for i in range(root_count):
            chain_count_spin_box = UIGenerator.add_spin_box(
                self.parent_widget,
                label=f"Root {i + 1} Chain Count",
                attribute=f"{root}.chain_count[{i}]",
                slider=False,
                min_value=1,
                max_value=999,
            )
            chain_count_spin_box.editingFinished.connect(change_count)
            chain_count_spin_boxes.append(chain_count_spin_box)
        UIGenerator.add_notes(self.parent_widget, f"{root}.notes")
