# domino
from domino.dominoui import DynamicWidget, UIGenerator


class Foot01(DynamicWidget):

    def __init__(self, parent=None, root=None):
        super(Foot01, self).__init__(parent=parent, root=root)
        UIGenerator.add_common_component_settings(self.parent_widget, root)

        UIGenerator.add_combo_box(
            self.parent_widget,
            "Roll axis",
            f"{root}.roll_axis",
        )

        UIGenerator.add_notes(self.parent_widget, f"{root}.notes")
