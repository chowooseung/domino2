# maya
from maya import cmds

cmds.evalDeferred("import domino;domino.install()", lowestPriority=True)
