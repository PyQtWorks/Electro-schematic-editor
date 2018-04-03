from ElectroScene import *
from PyQt4.QtGui import *
from PyQt4.Qt import QPoint
from pprint import *
import json
from curses.textpad import rectangle
import copy


MAX_GRID_SIZE = 20


graphicsItemLastId = 0

# TODO: implements enum
NOT_DEFINED_TYPE = QGraphicsItem.UserType + 1
LINE_TYPE = QGraphicsItem.UserType + 2
GROUP_TYPE = QGraphicsItem.UserType + 3
RECT_TYPE = QGraphicsItem.UserType + 4

graphicsObjectsTypeNames = {
    NOT_DEFINED_TYPE: "not_defined",
    LINE_TYPE: "line",
    GROUP_TYPE: "group",
    RECT_TYPE: "rectangle",
}


def typeByName(name):
    for type, value in graphicsObjectsTypeNames.items():
        if name == value:
            return type
    return NOT_DEFINED_TYPE


def mapToGrid(arg, gridSize):
    argType = arg.__class__.__name__
    if argType == 'QPointF':
        point = arg
        s = gridSize
        x = round(point.x() / s) * s
        y = round(point.y() / s) * s
        return QPointF(x, y)

    if argType == 'QRectF':
        rect = arg
        x = rect.topLeft().x() - gridSize
        y = rect.topLeft().y() - gridSize
        topLeft = mapToGrid(QPointF(x, y), gridSize)
        x = rect.bottomRight().x() + gridSize
        y = rect.bottomRight().y() + gridSize
        bottomRight = mapToGrid(QPointF(x, y), gridSize)
        rect = QRectF(topLeft, bottomRight)
        print("mapToGrid rect = %s" % rect)
        return rect


def createGraphicsObjectByProperties(ogjectProperties):
    from GraphicsItemLine import *
    from GraphicsItemRect import *
    from GraphicsItemGroup import *

    item = None
    if typeByName(ogjectProperties['type']) == GROUP_TYPE:
        item = GraphicsItemGroup()
        item.setProperties(ogjectProperties)

    if typeByName(ogjectProperties['type']) == LINE_TYPE:
        item = GraphicsItemLine()
        item.setProperties(ogjectProperties)

    if typeByName(ogjectProperties['type']) == RECT_TYPE:
        item = GraphicsItemRect()
        item.setProperties(ogjectProperties)

    return item


def createGraphicsObjectsByProperties(properties):
    items = []
    for itemProp in properties:
        item = createGraphicsObjectByProperties(itemProp)
        if item:
            items.append(item)

    return items


class GraphicsItem():
    MARK_SIZE = 8
    normalPen = QPen(QColor(0, 0, 200), 2, Qt.SolidLine, Qt.RoundCap)
    selectedPen = QPen(Qt.magenta, 3, Qt.SolidLine, Qt.RoundCap)
    highLightPen = QPen(Qt.blue, 4, Qt.SolidLine, Qt.RoundCap)

    def __init__(self):
        self.selected = False
        self.copyOf = None
        self.deltaCenter = None
        self.graphicsItemsList = []
        self._name = ""
        self._parentItem = None
        self.mouseMoveDelta = None

        global graphicsItemLastId
        graphicsItemLastId += 1
        self.itemId = graphicsItemLastId


    def type(self):
        return NOT_DEFINED_TYPE


    def typeName(self):
        return graphicsObjectsTypeNames[self.type()]


    def id(self):
        return self.itemId


    def setName(self, name):
        self._name = name


    def name(self):
        return self._name


    def setItemsPen(self, pen):
        if not len(self.graphicsItemsList):
            return
        for item in self.graphicsItemsList:
            if item.type() == GROUP_TYPE:
                item.setItemsPen(pen)
                continue
            item.setPen(pen)


    def setColor(self, color):
        self.normalPen.setColor(color)
        self.setItemsPen(self.normalPen)


    def color(self):
        return self.normalPen.color()


    def setThickness(self, size):
        self.normalPen.setWidth(size)
        self.setItemsPen(self.normalPen)


    def thickness(self):
        return self.normalPen.width()


    def isSelected(self):
        return self.selected


    def select(self):
        self.setItemsPen(self.selectedPen)
        self.selected = True


    def resetSelection(self):
        self.markPointsHide()
        self.setItemsPen(self.normalPen)
        self.selected = False


    def highlight(self):
        self.setItemsPen(self.highLightPen)


    def unHighlight(self):
        if self.isSelected():
            self.setItemsPen(self.selectedPen)
        else:
            self.setItemsPen(self.normalPen)


    def setCenter(self, point):
        self.deltaCenter = self.pos() - point


    def moveByCenter(self, point):
        self.setPos(QPointF(point + self.deltaCenter))
        if self.isSelected():
            self.markPointsShow()


    def items(self):
        return self.graphicsItemsList


    def setParent(self, parentItem):
        self._parentItem = parentItem


    def parent(self):
        return self._parentItem


    def root(self):
        if self.parent():
            return self.parent().root()
        return self


    def setSelectPoint(self, point):
        return False


    def resetSelectionPoint(self):
        pass


    def isPointSelected(self):
        return False


    def markPointsShow(self):
        return


    def markPointsHide(self):
        return


    def properties(self):
        properties = {}
        properties['id'] = self.id()
        properties['type'] = self.typeName()
        properties['name'] = self.name()
        properties['mountPoint'] = {'x': self.posFromParent().x(),
                                    'y': self.posFromParent().y()}
        return properties;


    def setProperties(self, properties):
        properties = copy.deepcopy(properties)
        self.resetSelection()

        newMountPoint = QPointF(properties['mountPoint']['x'],
                                properties['mountPoint']['y'])
        if self.parent():
            newMountPoint += self.parent().pos()
        self.setPos(newMountPoint)

        self.setName(properties['name'])


    def compareProperties(self, properties):
        for name, value in self.properties().items():
            if not name in properties or properties[name] != value:
                print("%d base not matched" % self.id())
                return False

        print("%d base matched" % self.id())
        return True


    def setScene(self, scene):
        scene.addItem(self)


    def removeFromQScene(self):
        self.resetSelection()
        scene = self.scene()
        if scene:
            scene.removeItem(self)


    def __str__(self):
        str = "%d: (%d:%d) Graphic type:%s" % (self.id(),
                                                self.pos().x(),
                                                self.pos().y(),
                                                self.typeName())

        if self.parent():
            str += ", parent: %d" % self.parent().id()

        if self.name():
            str += ", name: '%s'" % self.name()

        if self.copyOf:
            str += ", copyOf: %d" % self.copyOf

        if self.isSelected():
            str += ", selected"

        return str





