# maya
from maya import cmds
from maya.utils import MayaGuiLogHandler

# built-ins
import logging
import functools
import time


logger = logging.getLogger("Domino")
logger.handlers.clear()
logger.propagate = False

debug_handler = MayaGuiLogHandler()
formatter = logging.Formatter("\t%(message)s")
debug_handler.setFormatter(formatter)
debug_handler.addFilter(lambda record: record.levelno == logging.DEBUG)

info_handler = MayaGuiLogHandler()
formatter = logging.Formatter("%(levelname)s %(message)s")
info_handler.setFormatter(formatter)
info_handler.addFilter(lambda record: record.levelno == logging.INFO)

warning_handler = MayaGuiLogHandler()
formatter = logging.Formatter("%(message)s")
warning_handler.setFormatter(formatter)
warning_handler.addFilter(lambda record: record.levelno == logging.WARNING)

error_handler = MayaGuiLogHandler()
formatter = logging.Formatter("%(message)s")
error_handler.setFormatter(formatter)
error_handler.addFilter(lambda record: record.levelno == logging.ERROR)

logger.addHandler(debug_handler)
logger.addHandler(info_handler)
logger.addHandler(warning_handler)
logger.addHandler(error_handler)


def log_format(indent, label, msg):
    if msg:
        if isinstance(msg, str):
            msg = "\t" * (indent + 1) + msg
        elif isinstance(msg, list):
            if len(msg) == 1:
                msg = "\t" * (indent + 1) + msg[0]
            else:
                msg = "\t" * (indent + 1) + ("\n" + "\t" * (indent + 1)).join(msg)
        elif isinstance(msg, tuple):
            msg = "\t" * (indent + 1) + str(msg)
    else:
        msg = ""
    return ("\t" * indent) + label + "\n" + msg + "\n"


def build_log(level):
    """로깅 데코레이터.

    데코레이터를 사용한 함수의 이름, 실행시간, argument, return 을 출력합니다."""

    def deco(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            try:
                call_msg = f"Calling `{func.__module__}` `{func.__name__}`\n"
                if level == logging.DEBUG:
                    args_msg = []
                    for arg in args:
                        if arg.__class__.__name__ == "Rig":
                            name, side, index = arg.identifier
                            args_msg.append(f"`{name} {side} {index}(Rig)`")
                        elif arg.__class__.__name__ == "_Controller":
                            args_msg.append(f"`{arg.name}(_Controller)`")
                        elif arg.__class__.__name__ == "_Output":
                            args_msg.append(f"`{arg.name}(_Output)`")
                        elif arg.__class__.__name__ == "_OutputJoint":
                            args_msg.append(f"`{arg.name}(_OutputJoint)`")
                        else:
                            args_msg.append(arg)

                    call_msg += log_format(indent=1, label="args", msg=args_msg)

                    if func.__name__ == "print_context":
                        call_msg += log_format(indent=1, label="kwargs", msg="")[:-1]
                        call_msg += log_format(
                            indent=2, label="Identifier", msg=kwargs["identifier"]
                        )
                        controller_msg = []
                        for ctl in kwargs["controller"]:
                            d = ctl["description"]
                            controller_msg.append(f"description {d}")
                        call_msg += log_format(
                            indent=2, label="Controller", msg=controller_msg
                        )
                        output_msg = []
                        for output in kwargs["output"]:
                            d = output["description"]
                            e = output["extension"]
                            output_msg.append(f"description {d} extension {e}")
                        call_msg += log_format(indent=2, label="Output", msg=output_msg)
                        output_joint_msg = []
                        for output_joint in kwargs["output_joint"]:
                            d = output_joint["description"]
                            output_joint_msg.append(f"description {d}")
                        call_msg += log_format(
                            indent=2, label="OutputJoint", msg=output_joint_msg
                        )
                    else:
                        kwargs_msg = []
                        for k, v in kwargs.items():
                            kwargs_msg.append(f"{k}: {v}")
                        call_msg += log_format(indent=1, label="kwargs", msg=kwargs_msg)

                result = func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time

                completed_msg = ""
                if level == logging.DEBUG:
                    completed_msg += log_format(indent=1, label="return", msg=result)
                completed_msg += f"Completed `{func.__module__}` `{func.__name__}` Execution Time : {execution_time:.4f} second"

                logger.log(level, call_msg + completed_msg)
                return result
            except Exception as e:
                error_msg = f"`{func.__module__}` `{func.__name__}`"
                error_msg += "\n\targs"

                args_msg = []
                for arg in args:
                    msg = ""
                    if hasattr(arg, "identifier"):
                        for k, v in arg.items():
                            if k == "children":
                                continue
                            msg += f"\n\t\t{k}: {v}"
                    else:
                        msg += f"\n\t\t{arg}"
                    args_msg.append(f"{msg}")
                error_msg += "\n".join(args_msg)

                error_msg += "\n\tkwargs\n\t\t"
                kwargs_msg = []
                for k, v in kwargs.items():
                    kwargs_msg.append(f"{k}: {v}")
                error_msg += ", ".join(kwargs_msg)

                logger.error(error_msg)
                raise

        return wrapper

    return deco


def maya_version():
    return cmds.about(version=True)


def used_plugins():
    return cmds.pluginInfo(query=True, pluginsInUse=True) or []
