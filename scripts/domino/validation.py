# maya
from maya import cmds

# built-ins
from functools import partial
from pathlib import Path

# gui
from PySide6 import QtWidgets, QtCore, QtGui

icon_dir = Path(__file__).parent.parent.parent / "icons"

SUCCESS = 0
WARNING = 1
ERROR = 2
INITIALIZE = 3
VALIDATING = 4


def check_clashs():
    nodes = cmds.ls("clash*") + cmds.ls("*:clash*")
    return (
        ERROR if nodes else SUCCESS,
        nodes,
        "clash nodes found!",
        "clash node 를 찾습니다.",
        "clash node 는 여타 scene 을 import 할 때 중복된 이름으로 생성됩니다."
        "노드를 찾아서 삭제하거나 이름을 변경해주세요.",
    )


def check_same_name():
    nodes = []
    for node in cmds.ls():
        if "|" in node:
            nodes.append(node)
    return (
        ERROR if nodes else SUCCESS,
        nodes,
        "same name nodes found!",
        "same name node 를 찾습니다.",
        "같은 이름을 가진 노드의 이름을 변경해주세요.",
    )


def check_namespace():
    ns = cmds.namespaceInfo(":", listOnlyNamespaces=True, recurse=True) or []
    ns.remove("UI")
    ns.remove("shared")
    return (
        ERROR if ns else SUCCESS,
        ns,
        "namespace found!",
        "namespace 를 찾습니다.",
        "namespace 를 제거해주세요.",
    )


def check_display_layer():
    nodes = cmds.ls(type="displayLayer")[1:]
    return (
        ERROR if nodes else SUCCESS,
        nodes,
        "display layers found!",
        "display layer 를 찾습니다.",
        "display layer 를 제거해주세요.",
    )


def check_anim_layer():
    nodes = cmds.ls(type="animLayer")
    return (
        ERROR if nodes else SUCCESS,
        nodes,
        "anim layers found!",
        "anim layer 를 찾습니다.",
        "anim layer 를 제거해주세요.",
    )


def check_unknown_plugins():
    plugins = cmds.unknownPlugin(query=True, list=True) or []
    return (
        ERROR if plugins else SUCCESS,
        plugins,
        "unknown plugins found!",
        "unknown plug-ins 를 찾습니다.",
        "unknown plug-ins 은 현재 maya 환경에서 인식되지 않는 플러그인입니다."
        "해당 플러그인을 사용한 scene 을 import 하거나 reference 로 사용하면 발생합니다."
        "스크립트를 사용해 제거해주세요.",
    )


def check_unknown_nodes():
    nodes = (
        cmds.ls(type="unknown")
        + cmds.ls(type="unknownDag")
        + cmds.ls(type="unknownTransform")
    )
    return (
        ERROR if nodes else SUCCESS,
        nodes,
        "unknown nodes found!",
        "unknown node 를 찾습니다.",
        "unknown node 는 잘못된 node 타입으로 생성된 노드입니다. 사용하려던 노드타입을 확인하고 제거해주세요.",
    )


def check_expression():
    expression = cmds.ls(type="expression")
    return (
        WARNING if expression else SUCCESS,
        expression,
        "expression found!",
        "expression node 를 찾습니다.",
        "expression 은 잘못 사용한다면 해결하기 힘든 버그를 발생시킬수있고 리그의 속도를 저하시키는 원인이 될수있습니다."
        "주의해서 사용해주세요.",
    )


def check_script():
    nodes = [
        x
        for x in cmds.ls(type="script")
        if "sceneConfigurationScriptNode" not in x
        and "uiConfigurationScriptNode" not in x
    ]
    return (
        WARNING if nodes else SUCCESS,
        nodes,
        "script nodes found!",
        "script node 를 찾습니다.",
        "일반적인 경우 script 노드를 사용하지 않는 것이 좋습니다.",
    )


def check_default_value_controller():
    tr = (
        ".tx",
        ".ty",
        ".tz",
        ".rx",
        ".ry",
        ".rz",
        ".shearXY",
        ".shearXZ",
        ".shearYZ",
    )
    s = [".sx", ".sy", ".sz"]

    controllers = cmds.controller(query=True, allControllers=True)

    result = []
    for ctl in controllers:
        keyable = cmds.listAttr(ctl, userDefined=True, keyable=True) or []
        channelbox = cmds.listAttr(ctl, userDefined=True, channelBox=True) or []
        for attr in tr:
            if cmds.getAttr(ctl + attr) != 0.0:
                result.append(ctl + attr)
        for attr in s:
            if cmds.getAttr(ctl + attr) != 1.0:
                result.append(ctl + attr)
        attrs = keyable + channelbox
        for attr in ["." + x for x in attrs]:
            default_value = cmds.addAttr(ctl + attr, query=True, defaultValue=True)
            if default_value != cmds.getAttr(ctl + attr):
                result.append(ctl + attr)
    return (
        WARNING if result else SUCCESS,
        result,
        "default value controller found!",
        "default value 가 아닌 controller 를 찾습니다.",
        "controller 의 기본값이 아닌 값을 가지고 있습니다. 특별한 경우가 아니라면 기본값을 유지해주세요.",
    )


def check_keyframe():
    translate = cmds.ls(type="animCurveTL")
    rotate = cmds.ls(type="animCurveTA")
    scale = cmds.ls(type="animCurveTU")
    nodes = translate + rotate + scale
    return (
        ERROR if nodes else SUCCESS,
        nodes,
        "keyframes found!",
        "keyframe 를 찾습니다.",
        "keyframe 는 리그에 포함될 이유가 없습니다.",
    )


class TargetWidget(QtWidgets.QFrame):

    def __init__(self, title, scene):
        super(TargetWidget, self).__init__()

        self.scene = scene
        self.result = []
        self.setObjectName("target_widget")
        self.validating_stylesheet(False)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.frame = QtWidgets.QFrame()
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setStyleSheet("background-color: #999999; border-radius: 2px;")
        self.frame.setFixedSize(16, 16)
        layout.addWidget(self.frame, alignment=QtCore.Qt.AlignVCenter)

        self.label = QtWidgets.QLabel(title)
        layout.addWidget(self.label, alignment=QtCore.Qt.AlignVCenter)

    def mousePressEvent(self, event):
        if self.hasFocus():
            self.clearFocus()
        else:
            self.setFocus()
        return super().mousePressEvent(event)

    def validating_stylesheet(self, state):
        if state:
            self.setStyleSheet(
                """#target_widget {
border: 1px solid #00aaff; 
border-radius: 2px;
}
#target_widget:focus {
border: 1px solid #00aaff;
}"""
            )
        else:
            self.setStyleSheet(
                """#target_widget {}
#target_widget:focus {
border: 1px solid #00aaff;
}"""
            )

    def set_state(self, state):
        if state == SUCCESS:
            self.validating_stylesheet(False)
            self.frame.setStyleSheet(
                "QFrame {background-color: #00ff00; border-radius: 2px;}"
            )
        elif state == WARNING:
            self.validating_stylesheet(False)
            self.frame.setStyleSheet(
                "QFrame {background-color: #ffff00; border-radius: 2px;}"
            )
        elif state == ERROR:
            self.validating_stylesheet(False)
            self.frame.setStyleSheet(
                "QFrame {background-color: #ff0000; border-radius: 2px;}"
            )
        elif state == INITIALIZE:
            self.validating_stylesheet(False)
            self.frame.setStyleSheet(
                "QFrame {background-color: #999999; border-radius: 2px;}"
            )
        elif state == VALIDATING:
            self.validating_stylesheet(True)


class CheckListWidget(QtWidgets.QWidget):

    def __init__(self, title, f, msg, btn_events):
        super(CheckListWidget, self).__init__()

        self._func = f
        self._msg = msg

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.frame = QtWidgets.QFrame()
        self.frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.frame.setStyleSheet("background-color: #999999; border-radius: 2px;")
        self.frame.setFixedSize(16, 16)
        layout.addWidget(self.frame, alignment=QtCore.Qt.AlignVCenter)

        self.label = QtWidgets.QLabel(title)
        layout.addWidget(self.label, alignment=QtCore.Qt.AlignVCenter)

        self.btn = QtWidgets.QPushButton()
        self.btn.setIcon(QtGui.QIcon(f"{icon_dir}/chevron-right-grey.svg"))
        self.btn.setFlat(True)
        self.btn.setFixedSize(16, 16)
        if btn_events:
            for event in btn_events:
                self.btn.clicked.connect(event)
        layout.addWidget(self.btn, alignment=QtCore.Qt.AlignVCenter)

    def set_state(self, state):
        if state == SUCCESS:
            self.frame.setStyleSheet("background-color: #00ff00; border-radius: 2px;")
        elif state == WARNING:
            self.frame.setStyleSheet("background-color: #ffff00; border-radius: 2px;")
        elif state == ERROR:
            self.frame.setStyleSheet("background-color: #ff0000; border-radius: 2px;")
        elif state == INITIALIZE:
            self.frame.setStyleSheet("background-color: #999999; border-radius: 2px;")


class AnimatedStackedWidget(QtWidgets.QStackedWidget):

    def __init__(self):
        super(AnimatedStackedWidget, self).__init__()
        self._animation_duration = 300
        self._current_animation = None

    def slide_to_index(self, index):
        current_index = self.currentIndex()
        if index == current_index:
            return

        direction = 1 if index > current_index else -1
        offsetX = self.frameRect().width() * direction

        current_widget = self.currentWidget()
        next_widget = self.widget(index)

        # 두 위젯을 같은 위치에 놓고 슬라이드
        next_widget.setGeometry(
            self.geometry().x() + offsetX, 0, self.width(), self.height()
        )
        next_widget.show()

        anim_current = QtCore.QPropertyAnimation(current_widget, b"geometry")
        anim_next = QtCore.QPropertyAnimation(next_widget, b"geometry")

        anim_current.setDuration(self._animation_duration)
        anim_next.setDuration(self._animation_duration)

        anim_current.setStartValue(current_widget.geometry())
        anim_current.setEndValue(QtCore.QRect(-offsetX, 0, self.width(), self.height()))

        anim_next.setStartValue(next_widget.geometry())
        anim_next.setEndValue(QtCore.QRect(0, 0, self.width(), self.height()))

        # 부드러운 커브
        for anim in (anim_current, anim_next):
            anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)

        def on_finished():
            self.setCurrentIndex(index)
            next_widget.setGeometry(0, 0, self.width(), self.height())

        anim_current.finished.connect(on_finished)
        anim_current.start()
        anim_next.start()

        # 참조 유지를 위해 저장
        self._current_animation = (anim_current, anim_next)


class ValidateUI(QtWidgets.QDialog):

    _instance = None

    def __init__(self, parent=None):
        super(ValidateUI, self).__init__(parent)
        self.setWindowTitle("Domino Validation UI")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setMinimumSize(400, 500)
        self.setBaseSize(400, 500)

        self._targets = []
        self._check_list = []
        self._targets_queue = []
        self._check_list_queue = []
        self._current_target = None
        self._current_target_state = 0

        self.validation_widget = QtWidgets.QWidget()
        self.validation_widget.setLayout(QtWidgets.QVBoxLayout())
        self.validation_layout = self.validation_widget.layout()
        self.validation_layout.setContentsMargins(0, 0, 0, 0)
        self.validation_layout.setSpacing(0)

        self.target_and_list_widget = QtWidgets.QWidget()
        self.target_and_list_widget.setObjectName("target_and_list_widget")
        self.target_and_list_widget.setLayout(QtWidgets.QHBoxLayout())
        self.target_and_list_widget.setStyleSheet(
            """#target_and_list_widget {
border: 4px solid #555555;
border-bottom: none;
background-color: #353535;
}"""
        )
        self.validation_layout.addWidget(self.target_and_list_widget)

        self.target_and_list_layout = self.target_and_list_widget.layout()
        self.target_and_list_layout.setContentsMargins(12, 12, 12, 12)

        self.validation_target_layout = QtWidgets.QVBoxLayout()
        self.validation_target_layout.setContentsMargins(0, 0, 10, 0)
        self.validation_target_label = QtWidgets.QLabel(
            "Validation Target", alignment=QtCore.Qt.AlignCenter
        )
        self.validation_target_label.setStyleSheet("font-size: 16px;")
        self.validation_target_layout.addWidget(self.validation_target_label)
        self.target_and_list_layout.addLayout(self.validation_target_layout)

        self.validation_target_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
            )
        )

        self.validation_list_layout = QtWidgets.QVBoxLayout()
        self.validation_list_layout.setContentsMargins(10, 0, 0, 0)
        self.validation_list_label = QtWidgets.QLabel(
            "Validation List", alignment=QtCore.Qt.AlignCenter
        )
        self.validation_list_label.setStyleSheet("font-size: 16px;")
        self.validation_list_layout.addWidget(self.validation_list_label)

        self.target_and_list_layout.addLayout(self.validation_list_layout)

        self.tool_button_widget = QtWidgets.QWidget()
        self.tool_button_widget.setObjectName("tool_button_widget")
        self.tool_button_widget.setLayout(QtWidgets.QHBoxLayout())
        self.tool_button_widget.setStyleSheet(
            """#tool_button_widget {
border: 4px solid #555555;
border-top: none;
background-color: #353535;
}"""
        )
        self.btn_layout = self.tool_button_widget.layout()
        self.btn_layout.setContentsMargins(12, 0, 12, 4)
        self.btn_layout.setSpacing(6)
        self.btn_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                20, 40, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
            )
        )

        self.validate_btn = QtWidgets.QPushButton()
        self.validate_btn.setIcon(QtGui.QIcon(f"{icon_dir}/refresh.svg"))
        self.validate_btn.setIconSize(QtCore.QSize(22, 22))
        self.validate_btn.setFixedSize(28, 28)
        self.validate_btn.clicked.connect(self.validate)
        self.btn_layout.addWidget(self.validate_btn)

        self.validation_layout.addWidget(self.tool_button_widget)

        self.validation_list_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
            )
        )

        self.validation_list_description_widget = QtWidgets.QWidget()
        self.validation_list_description_widget.setLayout(QtWidgets.QVBoxLayout())
        self.validation_list_description_layout = (
            self.validation_list_description_widget.layout()
        )
        self.validation_list_description_layout.setContentsMargins(0, 0, 0, 0)
        self.validation_list_description_layout.setSpacing(0)

        self.list_btn_widget = QtWidgets.QWidget()
        self.list_btn_widget.setObjectName("list_button_widget")
        self.list_btn_widget.setLayout(QtWidgets.QHBoxLayout())
        self.list_btn_widget.setStyleSheet(
            """#list_button_widget {
border: 4px solid #555555;
border-bottom: none;
background-color: #353535;
}"""
        )
        self.list_btn_layout = self.list_btn_widget.layout()
        self.list_btn_layout.setContentsMargins(8, 4, 0, 0)
        self.validation_list_description_layout.addWidget(self.list_btn_widget)

        self.go_to_main_page_btn = QtWidgets.QPushButton()
        self.go_to_main_page_btn.setFixedSize(28, 28)
        self.go_to_main_page_btn.setFlat(True)
        self.go_to_main_page_btn.setIcon(
            QtGui.QIcon(f"{icon_dir}/chevron-left-grey.svg")
        )
        self.go_to_main_page_btn.clicked.connect(
            lambda _: self.stacked_widget.slide_to_index(0)
        )
        self.check_list_label = QtWidgets.QLabel("")
        self.list_btn_layout.addWidget(self.go_to_main_page_btn)
        self.list_btn_layout.addWidget(self.check_list_label)
        self.list_btn_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                20, 40, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
            )
        )

        self.list_description_widget = QtWidgets.QWidget()
        self.list_description_widget.setObjectName("list_description_widget")
        self.list_description_widget.setStyleSheet(
            """#list_description_widget {
border: 4px solid #555555;
background-color: #353535;
}
QTextBrowser {
background-color: #353535;
color: #E0E0E0;
padding: 12px;
border: 2px solid #555555;
font-size: 14px;
}
"""
        )
        self.list_description_layout = QtWidgets.QVBoxLayout(
            self.list_description_widget
        )

        self.description_text_browser = QtWidgets.QTextBrowser()
        self.description_text_browser.setMaximumSize(16777215, 100)
        self.list_description_layout.addWidget(self.description_text_browser)
        self.error_list_text_browser = QtWidgets.QTextBrowser()
        self.error_list_text_browser.setStyleSheet(
            """ul {
    margin-left: 8px;   /* 기본은 20px 이상입니다 */
    padding-left: 0px;
}
li {
    margin-bottom: 4px; /* 항목 간 여백 (선택) */
}"""
        )
        self.list_description_layout.addWidget(self.error_list_text_browser)
        self.solve_description_text_browser = QtWidgets.QTextBrowser()
        self.list_description_layout.addWidget(self.solve_description_text_browser)
        self.validation_list_description_layout.addWidget(self.list_description_widget)

        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.stacked_widget = AnimatedStackedWidget()
        self.stacked_widget.addWidget(self.validation_widget)
        self.stacked_widget.addWidget(self.validation_list_description_widget)
        self.main_layout.addWidget(self.stacked_widget)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._validate)
        self.is_running = False

    def add_check_list(self, title, f, msg):
        last_index = self.validation_list_layout.count() - 1
        w = CheckListWidget(
            title,
            f=f,
            msg=msg,
            btn_events=[partial(self.go_to_list_description_page, last_index)],
        )
        self._check_list.append(w)
        self.validation_list_layout.insertWidget(last_index, w)

    def add_target(self, title, scene):
        last_index = self.validation_target_layout.count() - 1
        w = TargetWidget(title, scene)
        self._targets.append(w)
        self.validation_target_layout.insertWidget(last_index, w)

    def _validate(self):
        if self.is_running:
            return

        # stop validate
        if not self._targets_queue and not self._check_list_queue:
            self.timer.stop()
            self.validate_btn.setIcon(QtGui.QIcon(f"{icon_dir}/refresh.svg"))
            return

        # new target
        if self._targets_queue and not self._check_list_queue:
            self._check_list_queue = self._check_list.copy()
            for check_list in self._check_list_queue:
                check_list.set_state(INITIALIZE)
            return

        # initialize
        if self._targets_queue and self._check_list_queue == self._check_list:
            self._current_target = self._targets_queue.pop(0)
            if self._current_target.scene:
                cmds.file(self._current_target.scene, open=True, force=True)
            self._current_target.set_state(VALIDATING)

        self.is_running = True

        check_list = self._check_list_queue.pop(0)
        state, nodes, error_msg, description_msg, solve_msg = check_list._func()
        check_list.set_state(state)

        self._current_target_state = max(self._current_target_state, state)
        self._current_target.result.append(
            (state, nodes, error_msg, description_msg, solve_msg)
        )

        # result target
        if not self._check_list_queue:
            self._current_target.set_state(self._current_target_state)

        self.is_running = False

    def validate(self):
        # icon toggle
        self.validate_btn.setIcon(QtGui.QIcon(f"{icon_dir}/refresh-off.svg"))

        # stop
        if self.timer.isActive():
            self._targets_queue.clear()
            self._check_list_queue.clear()
            self.validate_btn.setIcon(QtGui.QIcon(f"{icon_dir}/refresh.svg"))
            self.is_running = False
            return

        self._targets_queue = self._targets.copy()
        self._check_list_queue = self._check_list.copy()

        for target in self._targets:
            target.set_state(INITIALIZE)
        for check_list in self._check_list:
            check_list.set_state(INITIALIZE)

        self.timer.start(20)

    def clear_layout(self):
        layout_stack = [self.validation_target_layout, self.validation_list_layout]
        while layout_stack:
            layout = layout_stack.pop()
            for i in reversed(range(layout.count())):
                item = layout.itemAt(i)
                widget = item.widget()
                child_layout = item.layout()

                if widget is not None:
                    layout.removeWidget(widget)
                    widget.setParent(None)
                    widget.deleteLater()
                elif child_layout is not None:
                    layout.removeItem(child_layout)
                    layout_stack.append(child_layout)
        self._targets = []
        self._check_list = []

    def go_to_list_description_page(self, list_index):
        if self._current_target is None:
            return
        state, nodes, error_msg, description_msg, solvee_msg = (
            self._current_target.result[list_index]
        )
        self.check_list_label.setText(self._check_list[list_index].label.text())
        self.description_text_browser.setText(description_msg)
        node_text = ""
        if nodes:
            node_text = "".join(
                [f"""<p style="margin: 2px;">• {node}</p>\n""" for node in nodes]
            )
            node_text += "<br>"
            node_text += error_msg
        self.error_list_text_browser.setHtml(node_text)
        self.solve_description_text_browser.setText(solvee_msg)
        self.stacked_widget.slide_to_index(1)

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def show_ui():
    ins = ValidateUI.get_instance()
    ins.clear_layout()

    ins.add_target(f"Current Scene", "")
    ins.add_check_list("Clash", check_clashs, "clash node 를 찾습니다.")
    ins.add_check_list("Same Name", check_same_name, "same name node 를 찾습니다.")
    ins.add_check_list("Namespaces", check_namespace, "namespace 를 찾습니다.")
    ins.add_check_list(
        "Display Layer", check_display_layer, "display layer 를 찾습니다."
    )
    ins.add_check_list("Anim Layer", check_anim_layer, "anim layer 를 찾습니다.")
    ins.add_check_list(
        "Unknown Plug-ins", check_unknown_plugins, "unknown plug-ins 를 찾습니다."
    )
    ins.add_check_list("Unknown node", check_unknown_nodes, "unknown node 를 찾습니다.")
    ins.add_check_list("Expression", check_expression, "expression node 를 찾습니다.")
    ins.add_check_list("Script", check_script, "script node 를 찾습니다.")
    ins.add_check_list(
        "Default Controller Value",
        check_default_value_controller,
        "script node 를 찾습니다.",
    )
    ins.add_check_list("Keyframe", check_keyframe, "script node 를 찾습니다.")
    ins.show()
