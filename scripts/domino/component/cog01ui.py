# domino
from domino.dominoui import DynamicWidget, UIGenerator


class COG01(DynamicWidget):

    def __init__(self, parent=None, root=None):
        super(COG01, self).__init__(parent=parent, root=root)
        UIGenerator.add_common_component_settings(self.parent_widget, root)

        UIGenerator.add_notes(self.parent_widget, f"{root}.notes")
