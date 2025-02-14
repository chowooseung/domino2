# maya
from maya import cmds
from maya.utils import MayaGuiLogHandler  # type: ignore

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

error_handler = MayaGuiLogHandler()
formatter = logging.Formatter("%(message)s")
error_handler.setFormatter(formatter)
error_handler.addFilter(lambda record: record.levelno == logging.ERROR)

logger.addHandler(debug_handler)
logger.addHandler(info_handler)
logger.addHandler(error_handler)


def build_log(level):
    """로깅 데코레이터.

    데코레이터를 사용한 함수의 이름, 실행시간, argument, return 을 출력합니다."""

    def deco(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()

            try:
                call_msg = f"Calling `{func.__module__}` `{func.__name__}`"
                if level == logging.DEBUG:
                    call_msg += "\n\targs\n\t\t"

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
                    call_msg += ", ".join(args_msg)

                    call_msg += "\n\tkwargs\n\t\t"

                    if func.__name__ == "print_context":
                        call_msg += f"Identifier {kwargs['identifier']}\n\n"
                        call_msg += "\t\tController\n"
                        for ctl in kwargs["controller"]:
                            call_msg += f"\t\t\tdescription \"{ctl['description']}\"\n"
                            call_msg += f"\t\t\t\tparent controller\n"
                            for parent_ctl in ctl["parent_controllers"]:
                                parent_identifier = "_".join(
                                    [str(x) for x in parent_ctl[0] if x]
                                )
                                call_msg += f'\t\t\t\t\tidentifier : {parent_identifier}, description : "{parent_ctl[1]}"\n'
                            if (
                                kwargs["identifier"] == "origin"
                                and ctl["description"] == ""
                            ):
                                call_msg += f"\t\t\t\t\tROOT\n"
                            elif not ctl["parent_controllers"]:
                                call_msg += f"\t\t\t\t\t**WARNING parent controller 를 설정해주세요**\n"
                        call_msg += "\t\tOutput\n"
                        for output in kwargs["output"]:
                            call_msg += f"\t\t\tdescription {output['description']} extension {output['extension']}\n"
                        call_msg += "\t\tOutput Joint\n"
                        for output_joint in kwargs["output_joint"]:
                            call_msg += (
                                f"\t\t\tdescription {output_joint['description']}\n"
                            )
                    else:
                        kwargs_msg = []
                        for k, v in kwargs.items():
                            kwargs_msg.append(f"{k}: {v}")
                        call_msg += ", ".join(kwargs_msg)

                logger.log(level, call_msg)

                result = func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time

                completed_msg = ""
                if level == logging.DEBUG:
                    completed_msg += f"return\n\t\t{result}\n\t"
                completed_msg += f"Completed `{func.__module__}` `{func.__name__}` Execution Time : {execution_time:.4f} second"

                logger.log(level, completed_msg)
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


def maya_version() -> str:
    return cmds.about(version=True)


def used_plugins() -> list:
    return cmds.pluginInfo(query=True, pluginsInUse=True) or []
