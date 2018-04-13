from GraphicsItemGroup import *
from GraphicsItemLine import *
from GraphicsItemEllipse import *



class GraphicsItemLink(GraphicsItem):
    def __init__(self, pos=None, arrowPos=None):
        GraphicsItem.__init__(self)
        self._connection = None
        self._scene = None

        self.line = GraphicsItemLine()
        self.ellipse = GraphicsItemEllipse()
        self.ellipse.setBrush(QBrush(self.normalPen.color()))
        self.addrText = GraphicsItemText()
        self.addrText.setAlignment(Qt.AlignCenter)
        self.addItems([self.line, self.ellipse, self.addrText])

        if pos:
            self.setPos(pos)
        if arrowPos:
            self.setArrowPos(arrowPos)
        else:
            self.setArrowPos(self.pos() + QPointF(MAX_GRID_SIZE, 0))


    def setScene(self, scene):
        print("setScene")
        self._scene = scene

        for item in self.items():
            item.setScene(scene)

        for item in self.items():
            item.setParent(self)


    def scene(self):
        return self._scene


    def type(self):
        return LINK_TYPE


    def pos(self):
        pos = self.line.p1()
        return pos


    def arrowPos(self):
        return self.line.p2()


    def setPos(self, pos):
        delta = self.arrowPos() - self.pos()
        self.line.setP1(pos)
        self.setArrowPos(pos + delta)
        self.updateView()


    def setArrowPos(self, arrowPos):
        self.ellipse.setPos(arrowPos - QPointF(3, 3))
        self.ellipse.setRect(QRectF(QPointF(0, 0), QSizeF(6, 6)))
        self.line.setP2(arrowPos)


    def direction(self):
        x1 = self.pos().x()
        x2 = self.arrowPos().x()
        y1 = self.pos().y()
        y2 = self.arrowPos().y()

        if x1 < x2:
            return 'right'
        if x1 > x2:
            return 'left'
        if y1 > y2:
            return 'top'
        if y1 < y2:
            return 'bottom'


    def posFromParent(self):
        return self.pos()


    def addItems(self, items):
        for item in items:
            self.graphicsItemsList.append(item)


    def rotate(self, center, angle):
        for item in self.items():
            if item == self.addrText:
                continue
            item.rotate(center, angle)
        self.updateView()


    def properties(self):
        properties = GraphicsItem.properties(self)
        arrowPos = self.arrowPos() - self.pos()
        properties['arrowPoint'] = {'x': arrowPos.x(),
                                    'y': arrowPos.y()}
        return properties;


    def setProperties(self, properties):
        GraphicsItem.setProperties(self, properties)
        x = properties['arrowPoint']['x']
        y = properties['arrowPoint']['y']
        arrowPos = QPointF(x, y) + self.pos()
        print("arrowPos = %s" % arrowPos)
        self.setArrowPos(arrowPos)


    def compareProperties(self, properties):
        return GraphicsItem.compareProperties(self, properties)


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
            if item == self.addrText and not len(item.text()):
                continue

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


    def setConnection(self, conn):
        self._connection = conn
        self.updateView()


    def updateView(self, selfOnly=False):
        self.addrText.setText("")
        self.addrText.setRect(QRectF(0, 0, 0, 0))
        if not self.scene():
            return

        conn = self.connection()
        if not conn:
            return
        text = "%d" % conn.id()
        remoteLinkPoint = self.remoteLinkPoint()
        if remoteLinkPoint:
            text += "(%s)" % remoteLinkPoint.addr()
            self.addrText.setText(text)
            if not selfOnly:
                remoteLinkPoint.updateView(True)

        self.addrText.setText(text)

        direction = self.direction()
        print("direction %s" % direction)
        if direction == 'top':
            pos = self.arrowPos() + QPointF(-MAX_GRID_SIZE / 2, -MAX_GRID_SIZE * 3)
            rect = QRectF(0, 0, MAX_GRID_SIZE, MAX_GRID_SIZE * 3)
            angle = 90
        elif direction == 'bottom':
            pos = self.arrowPos() + QPointF(-MAX_GRID_SIZE / 2, 0)
            rect = QRectF(0, 0, MAX_GRID_SIZE, MAX_GRID_SIZE * 3)
            angle = 90
        elif direction == 'left':
            pos = self.arrowPos() + QPointF(-MAX_GRID_SIZE * 3, -MAX_GRID_SIZE / 2)
            rect = QRectF(0, 0, MAX_GRID_SIZE * 3, MAX_GRID_SIZE)
            angle = 0
        elif direction == 'right':
            pos = self.arrowPos() + QPointF(0, -MAX_GRID_SIZE / 2)
            rect = QRectF(0, 0, MAX_GRID_SIZE * 3, MAX_GRID_SIZE)
            angle = 0

        self.addrText.resetRotation()
        self.addrText.rotate(pos, angle)
        self.addrText.setPos(pos)
        self.addrText.setRect(rect)


    def addr(self):
        scene = self.scene()
        quadrant = scene.quadrantByPos(self.pos())
        return "%d/%s" % (scene.num(), quadrant)


    def connection(self):
        return self._connection


    def remoteLinkPoint(self):
        if not self._connection:
            return None
        remoteLinkPoint = None
        for linkPoint in self._connection.linkPoints():
            if linkPoint != self:
                remoteLinkPoint = linkPoint
        return remoteLinkPoint


    def removeFromQScene(self):
        self.resetSelection()
        for item in self.items():
            item.removeFromQScene()
        self._scene = None

        conn = self.connection()
        if not conn:
            return
        remoteLinkPoint = self.remoteLinkPoint()
        conn.remove()
        self.updateView()
        remoteLinkPoint.updateView()


    def __str__(self):
        str = GraphicsItem.__str__(self)
        if self.deltaCenter:
            str += " | deltaCenter %d:%d" % (self.deltaCenter.x(),
                                             self.deltaCenter.y())

        return str



connection_last_id = 0
class Connection():
    def __init__(self, editor, linkPoint1, linkPoint2):
        global connection_last_id
        self._editor = editor
        self._linkPoints = []
        self._linkPoints.append(linkPoint1)
        self._linkPoints.append(linkPoint2)
        connection_last_id += 1
        self._id = connection_last_id
        for linkPoint in self._linkPoints:
            linkPoint.setConnection(self)


    def id(self):
        return self._id


    def linkPoints(self):
        return self._linkPoints


    def remove(self):
        for linkPoint in self._linkPoints:
            linkPoint.setConnection(None)
        self._editor.connectionsList.remove(self)



