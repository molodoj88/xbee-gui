# -*- coding: utf-8 -*-
import sys
from PyQt4 import QtGui, QtCore

class Window(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)

        self.resize(600, 400)

        self.main_widget = QtGui.QWidget()
        self.main_layout = QtGui.QHBoxLayout(self)
        self.main_layout.addWidget(self.main_widget)

        self.scene = QtGui.QGraphicsScene(parent=self.main_widget)
        self.view = QtGui.QGraphicsView(self.scene)

        self.view_widget = QtGui.QHBoxLayout(self.main_widget)
        self.view_widget.addWidget(self.view)

        rect1 = QtGui.QGraphicsRectItem(20, 20, 100, 100, scene=self.scene)
        rect2 = QtGui.QGraphicsRectItem(30, 30, 100, 100, scene=self.scene)

        self.coord_pixmap = QtGui.QPixmap('images/icon.png')
        self.coord_item = QtGui.QGraphicsPixmapItem(self.coord_pixmap, scene=self.scene)
        self.coord_item.setOffset(50, 50)

def main():
    app = QtGui.QApplication(sys.argv)
    bl = Window()
    bl.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()