# domino
from domino.dominoui import UIGenerator, DynamicWidget

# maya
from maya import cmds


class HumanArm01(DynamicWidget):

    def __init__(self, parent=None, root=None):

        def toggle_unlock_last_scale():
            rig_root = cmds.listConnections(
                f"{root}.component", source=False, destination=True
            )[0]
            controllers = cmds.listConnections(
                f"{rig_root}.controller", source=True, destination=False
            )

            if check_box.isChecked():
                for i in [5, 8, 9]:
                    cmds.setAttr(f"{controllers[i]}.sx", lock=False, keyable=True)
                    cmds.setAttr(f"{controllers[i]}.sy", lock=False, keyable=True)
                    cmds.setAttr(f"{controllers[i]}.sz", lock=False, keyable=True)
            else:
                for i in [5, 8, 9]:
                    cmds.setAttr(f"{controllers[i]}.sx", 1)
                    cmds.setAttr(f"{controllers[i]}.sy", 1)
                    cmds.setAttr(f"{controllers[i]}.sz", 1)
                    cmds.setAttr(f"{controllers[i]}.sx", lock=True, keyable=False)
                    cmds.setAttr(f"{controllers[i]}.sy", lock=True, keyable=False)
                    cmds.setAttr(f"{controllers[i]}.sz", lock=True, keyable=False)

        super(HumanArm01, self).__init__(parent=parent, root=root)
        UIGenerator.add_common_component_settings(self.parent_widget, root)

        UIGenerator.add_check_box(
            self.parent_widget,
            "Align last transform to guide",
            f"{root}.align_last_transform_to_guide",
        )
        check_box = UIGenerator.add_check_box(
            self.parent_widget,
            "Unlock last scale",
            f"{root}.unlock_last_scale",
        )
        check_box.toggled.connect(toggle_unlock_last_scale)

        UIGenerator.add_notes(self.parent_widget, f"{root}.notes")
