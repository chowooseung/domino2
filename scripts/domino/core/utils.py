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

debugHandler = MayaGuiLogHandler()
formatter = logging.Formatter("\t%(message)s")
debugHandler.setFormatter(formatter)
debugHandler.addFilter(lambda record: record.levelno == logging.DEBUG)

infoHandler = MayaGuiLogHandler()
formatter = logging.Formatter("%(levelname)s %(message)s")
infoHandler.setFormatter(formatter)
infoHandler.addFilter(lambda record: record.levelno == logging.INFO)

errorHandler = MayaGuiLogHandler()
formatter = logging.Formatter("%(message)s")
errorHandler.setFormatter(formatter)
errorHandler.addFilter(lambda record: record.levelno == logging.ERROR)

logger.addHandler(debugHandler)
logger.addHandler(infoHandler)
logger.addHandler(errorHandler)


def buildLog(level):
    """로깅 데코레이터.

    데코레이터를 사용한 함수의 이름, 실행시간, argument, return 을 출력합니다."""

    def deco(func):

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            startTime = time.perf_counter()

            try:
                callMsg = f"Calling `{func.__module__}` `{func.__name__}`"
                if level == logging.DEBUG:
                    callMsg += "\n\targs\n\t\t"

                    argsMsg = []
                    for arg in args:
                        if hasattr(arg, "identifier"):
                            name, side, index = arg.identifier
                            argsMsg.append(f"`{name} {side} {index}(identifier)`")
                        else:
                            argsMsg.append(arg)
                    callMsg += ", ".join(argsMsg)

                    callMsg += "\n\tkwargs\n\t\t"

                    kwargsMsg = []
                    for k, v in kwargs.items():
                        kwargsMsg.append(f"{k}: {v}")
                    callMsg += ", ".join(kwargsMsg)

                logger.log(level, callMsg)

                result = func(*args, **kwargs)
                executionTime = time.perf_counter() - startTime

                completedMsg = ""
                if level == logging.DEBUG:
                    completedMsg += f"return\n\t\t{result}\n\t"
                completedMsg += f"Completed `{func.__module__}` `{func.__name__}` Execution Time : {executionTime:.4f} second"

                logger.log(level, completedMsg)
                return result
            except Exception as e:
                errorMsg = f"`{func.__module__}` `{func.__name__}`"
                errorMsg += "\n\targs"

                argsMsg = []
                for arg in args:
                    msg = ""
                    if hasattr(arg, "identifier"):
                        for k, v in arg.items():
                            if k == "children":
                                continue
                            msg += f"\n\t\t{k}: {v}"
                    else:
                        msg += f"\n\t\t{arg}"
                    argsMsg.append(f"{msg}")
                errorMsg += "\n".join(argsMsg)

                errorMsg += "\n\tkwargs\n\t\t"
                kwargsMsg = []
                for k, v in kwargs.items():
                    kwargsMsg.append(f"{k}: {v}")
                errorMsg += ", ".join(kwargsMsg)

                logger.error(errorMsg, exc_info=True)
                raise

        return wrapper

    return deco


def mayaVersion() -> str:
    return cmds.about(version=True)


def usedPlugins() -> list:
    return cmds.pluginInfo(query=True, pluginsInUse=True) or []


def localizeBifrostGraph():
    pass
