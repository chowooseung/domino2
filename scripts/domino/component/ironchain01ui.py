# domino
from domino.dominoui import DynamicWidget, UIGenerator


class IronChain01(DynamicWidget):

    def __init__(self, parent=None, root=None):
        super(IronChain01, self).__init__(parent=parent, root=root)
        UIGenerator.add_common_component_settings(self.parent_widget, root)

        UIGenerator.add_double_spin_box(
            self.parent_widget,
            label=f"Chain Radius",
            attribute=f"{root}.radius",
            slider=True,
            min_value=0.1,
            max_value=1,
        )
        UIGenerator.add_double_spin_box(
            self.parent_widget,
            label=f"Chain Width",
            attribute=f"{root}.width",
            slider=True,
            min_value=0.01,
            max_value=10,
        )
        UIGenerator.add_double_spin_box(
            self.parent_widget,
            label=f"Chain Height",
            attribute=f"{root}.height",
            slider=True,
            min_value=0.01,
            max_value=10,
        )
        UIGenerator.add_double_spin_box(
            self.parent_widget,
            label=f"Chain Bevel",
            attribute=f"{root}.bevel",
            slider=True,
            min_value=0.1,
            max_value=1,
        )
        UIGenerator.add_double_spin_box(
            self.parent_widget,
            label=f"Next Chain Offset",
            attribute=f"{root}.next_chain_offset",
            slider=True,
            min_value=0.0,
            max_value=2,
        )
        UIGenerator.add_double_spin_box(
            self.parent_widget,
            label=f"Guide Surface Width",
            attribute=f"{root}.surface_width",
            slider=True,
            min_value=0.01,
            max_value=3,
        )

        UIGenerator.add_notes(self.parent_widget, f"{root}.notes")
