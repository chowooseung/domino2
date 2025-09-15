# domino
from domino.dominoui import UIGenerator, DynamicWidget


class HumanNeck01(DynamicWidget):

    def __init__(self, parent=None, root=None):
        super(HumanNeck01, self).__init__(parent=parent, root=root)
        UIGenerator.add_common_component_settings(self.parent_widget, root)
        UIGenerator.add_ribbon_settings(self.parent_widget, f"{root}.output_u_values")
        UIGenerator.add_notes(self.parent_widget, f"{root}.notes")
