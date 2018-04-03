from GraphicsItem import *
from GraphicsItemLine import *
from GraphicsItemRect import *



class GraphicsItemGroup(GraphicsItem):


    def __init__(self):
        GraphicsItem.__init__(self)
        self.selectedPoint = None
        self.markRect = None
        self._scene = None
        self.mountPoint = QPointF(0, 0)


    def type(self):
        return GROUP_TYPE


    def posFromParent(self):
        return self.mountPoint


    def setPos(self, point):
        parentMountPoint = QPointF(0, 0)
        if self.parent():
            parentMountPoint = self.parent().pos()

        newMountPoint = point - parentMountPoint
        delta = newMountPoint - self.mountPoint
        for item in self.items():
            item.setPos(item.pos() + delta)

        self.mountPoint = newMountPoint
        # print("%d setPos %s, mountPoint = %s, pos = %s" % (self.id(), point, self.mountPoint, self.pos()))


    def addItems(self, items):
        if len(items) < 2:
            return False

        for item in items:
            item.removeFromQScene()
            self.graphicsItemsList.append(item)

        return True


    def calculateMountPoint(self):
        poligon = QPolygonF()
        for item in self.items():
            rect = item.boundingRect()
            p = QPolygonF([rect.topLeft() + item.pos(),
                           rect.topRight() + item.pos(),
                           rect.bottomRight() + item.pos(),
                           rect.bottomLeft() + item.pos()])

            poligon += p
        if not poligon:
            return

        parentMountPoint = QPointF(0, 0)
        if self.parent():
            parentMountPoint = self.parent().pos()

        ItemsBoundingRect = poligon.boundingRect()
        self.mountPoint = mapToGrid(ItemsBoundingRect.topLeft() -
                                    parentMountPoint,
                                    MAX_GRID_SIZE)


    def setScene(self, scene):
        self._scene = scene

        for item in self.items():
            item.setScene(scene)

        if not self.pos():
            self.calculateMountPoint()

        for item in self.items():
            item.setParent(self)


    def scene(self):
        return self._scene


    def setParent(self, parentItem):
        if self.parent() and parentItem:
            return
        GraphicsItem.setParent(self, parentItem)
        if parentItem:
            self.mountPoint -= parentItem.pos()


    def pos(self):
        if not self.parent():
            return self.mountPoint
        return self.parent().pos() + self.mountPoint


    def mapToScene(self, arg):
        argType = arg.__class__.__name__
        if argType == 'QRectF':
            rect = arg
            return QPolygonF([rect.topLeft() + self.pos(),
                              rect.topRight() + self.pos(),
                              rect.bottomRight() + self.pos(),
                              rect.bottomLeft() + self.pos()])

        if argType == 'QPointF':
            point = arg
            return point + self.pos()


    def boundingRect(self):
        poligon = QPolygonF()
        for item in self.items():
            rect = item.boundingRect()
            p = QPolygonF([rect.topLeft() + item.pos(),
                           rect.topRight() + item.pos(),
                           rect.bottomRight() + item.pos(),
                           rect.bottomLeft() + item.pos()])

            poligon += p
        if not poligon:
            return None

        sceneRect = poligon.boundingRect()
        return QRectF(sceneRect.topLeft() - self.pos(),
                      sceneRect.bottomRight() - self.pos())


    def properties(self):
        properties = {}
        properties['id'] = self.id()
        properties['name'] = self.name()
        properties['type'] = self.typeName()
        properties['mountPoint'] = {'x': self.mountPoint.x(),
                                    'y': self.mountPoint.y()}

        itemProperties = []
        for item in self.items():
            itemProperties.append(item.properties())
        properties['graphicsObjects'] = itemProperties

        return properties


    def setProperties(self, properties):
        properties = copy.deepcopy(properties)
        if typeByName(properties['type']) != GROUP_TYPE:
            return

        self.markPointsHide()
        self.setName(properties['name'])
        newMountPoint = QPointF(properties['mountPoint']['x'],
                                properties['mountPoint']['y'])
        if self.parent():
            newMountPoint += self.parent().pos()
        self.setPos(newMountPoint)

        if not len(properties['graphicsObjects']):
            return

        newItems = []
        for itemProperties in properties['graphicsObjects']:
            found = False
            for item in self.graphicsItemsList:
                if item.id() == itemProperties['id']:
                    item.setProperties(itemProperties)
                    found = True
                    break
            if not found:
                itemMountPoint = QPointF(itemProperties['mountPoint']['x'],
                                         itemProperties['mountPoint']['y'])
                itemMountPoint += self.pos()
                itemProperties['mountPoint']['x'] = itemMountPoint.x()
                itemProperties['mountPoint']['y'] = itemMountPoint.y()

                if typeByName(itemProperties['type']) == LINE_TYPE:
                    item = GraphicsItemLine()
                    item.setProperties(itemProperties)
                    newItems.append(item)

                if typeByName(itemProperties['type']) == RECT_TYPE:
                    item = GraphicsItemRect()
                    item.setProperties(itemProperties)
                    newItems.append(item)

                if typeByName(itemProperties['type']) == GROUP_TYPE:
                    item = GraphicsItemGroup()
                    item.setProperties(itemProperties)
                    newItems.append(item)

        self.addItems(newItems)


    def compareProperties(self, properties):
        selfProperties = self.properties()

        for name, value in selfProperties.items():
            if name == 'graphicsObjects':
                continue
            if not name in properties or properties[name] != value:
                print("%d group not matched" % self.id())
                return False

        if len(properties['graphicsObjects']) != len(selfProperties['graphicsObjects']):
            print("%d group not matched count subitems" % self.id())
            return False

        for itemProperties in properties['graphicsObjects']:
            for item in self.graphicsItemsList:
                if item.id() != itemProperties['id']:
                    continue

                if not item.compareProperties(itemProperties):
                    print("%d group not matched sub item %d" % (self.id(), item.id()))
                    return False

        print("%d group matched" % self.id())
        return True


    def rotate(self, center, angle):
        for item in self.items():
            item.rotate(center, angle)
#        self.calculateMountPoint()


    def __str__(self):
        str = GraphicsItem.__str__(self)
        if not len(self.graphicsItemsList):
            return str

        str += ", contained items:\n"
        for item in self.graphicsItemsList:
            str += "\t\t\t%s\n" % item.__str__()

        return str


    def removeAllItems(self):
        self.removeFromQScene()
        self.graphicsItemsList = []


    def removeFromQScene(self):
        self.resetSelection()

        for item in self.items():
            item.setParent(None)
            item.removeFromQScene()


