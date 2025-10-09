#----------AdinkraWorks----------#
# Copyright (c) 2025 Gabriel W. Yerger
# Licensed under the MIT License - see LICENSE file for details

import sys
import os
import pickle
from icecream import ic 
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QPen, QColor, QBrush, QPainter, QPolygonF
from PyQt6.QtGui import QFont, QFontDatabase
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtCore import QPoint, QRectF
from PyQt6.QtCore import pyqtSignal
from SimpleOutput import Ui_MainWindow  # Import the generated UI class
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem
from PyQt6.QtWidgets import QTreeWidgetItem
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtWidgets import QInputDialog
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSpinBox, QLabel, QPushButton
from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QSlider, QDialog, QGroupBox, QFrame, QFontComboBox, QLabel, QTextEdit
from PyQt6.QtWidgets import QGraphicsTextItem, QComboBox
from PyQt6.QtCore import pyqtSignal as Signal                         
from Adinkra import Adinkra
from rich import print
from rich.console import Console
from rich.traceback import install
import math
console = Console()
install(show_locals=True)  # Optional: shows local variables
import functools

def catch_nicely(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        #console.log(f"[bold yellow]Calling:[/] {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            return func(*args, **kwargs)
        except Exception:
            console.print_exception()
            return None
    return wrapper

@catch_nicely
def find_first_adinkra(parent_item):
    for i in range(parent_item.childCount()):
        child = parent_item.child(i)
        if isinstance(child.value, Adinkra):
            return child
    return None  # Not found

class DraggableBoson(QGraphicsEllipseItem):
    def __init__(self, x, y, label="", parent_adinkra = None, grid_size_x=100, grid_size_y=400, font = QFont('Arial', 12), radius=3):
        super().__init__(x - 25, y - 25, 35 + 5*radius, 35 + 5*radius)  # (x, y, width, height)
        self.parent_adinkra = parent_adinkra
        self.label = label
        self.setBrush(Qt.GlobalColor.white)
        self.setPen(QPen(Qt.GlobalColor.black))
        self.setFlags(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable |
                      QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.scene_x = x
        self.scene_y = y
        self.grid_size_x = grid_size_x
        self.grid_size_y = grid_size_y
        self.edges = []  # List of connected edges

        # Add centered text
        self.text_item = QGraphicsTextItem(label, self)  # Add text as child
        self.text_item.setFont(font)
        self.text_item.setDefaultTextColor(Qt.GlobalColor.black)
        self.center_text()

    def mouseReleaseEvent(self, event):
        scene = self.scene()
        if not scene:
            return super().mouseReleaseEvent(event)

        # Try to find the view displaying this scene
        views = scene.views()
        if not views:
            return super().mouseReleaseEvent(event)

        view = views[0]  # Usually just one view
        rect = scene.itemsBoundingRect()
        margin = 100
        rect.adjust(-2*margin, -2*margin, 2*margin, 2*margin)
        view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        view.centerOn(rect.center())
        rect.adjust(-rect.width(), -rect.height(), rect.width(), rect.height())

        scene.setSceneRect(rect)

        return super().mouseReleaseEvent(event)

    def center_text(self):
        """Center the text in the ellipse."""
        bounding_rect = self.text_item.boundingRect()
        ellipse_rect = self.rect()
        x = ellipse_rect.x() + (ellipse_rect.width() - bounding_rect.width()) / 2
        y = ellipse_rect.y() + (ellipse_rect.height() - bounding_rect.height()) / 2
        self.text_item.setPos(x, y)

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionChange:
            grid_size_x = self.grid_size_x // 4
            grid_size_y = self.grid_size_y // 4
            new_x = round(value.x() / grid_size_x) * grid_size_x
            new_y = round(value.y() / grid_size_y) * grid_size_y
            if self.parent_adinkra is not None:
                self.parent_adinkra.boson_positions[self.label][0] = self.scene_x + new_x
                self.parent_adinkra.boson_positions[self.label][1] = self.scene_y + new_y
            return QPointF(new_x, new_y)

        elif change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_position()
        return super().itemChange(change, value)

class DraggableFermion(QGraphicsEllipseItem):
    def __init__(self, x, y, label="", parent_adinkra = None, grid_size_x=100, grid_size_y=400, font = QFont('Arial', 12), radius=3):
        super().__init__(x - 25, y - 25, 35 + 5*radius, 35 + 5*radius)  # (x, y, width, height)
        self.parent_adinkra = parent_adinkra
        self.label = label
        self.setBrush(Qt.GlobalColor.black)
        self.setPen(QPen(Qt.GlobalColor.black))
        self.setFlags(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable |
                    QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.grid_size_x = grid_size_x
        self.grid_size_y = grid_size_y
        self.edges = []  # List of connected edges

        self.scene_x = x
        self.scene_y = y
        # Add centered text
        self.text_item = QGraphicsTextItem(label, self)  # Add text as child
        self.text_item.setFont(font)
        self.text_item.setDefaultTextColor(Qt.GlobalColor.white)
        self.center_text()

    def mouseReleaseEvent(self, event):
        scene = self.scene()
        if not scene:
            return super().mouseReleaseEvent(event)

        # Try to find the view displaying this scene
        views = scene.views()
        if not views:
            return super().mouseReleaseEvent(event)

        view = views[0]  # Usually just one view
        rect = scene.itemsBoundingRect()
        margin = 100
        rect.adjust(-2*margin, -2*margin, 2*margin, 2*margin)
        view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
        view.centerOn(rect.center())
        rect.adjust(-rect.width(), -rect.height(), rect.width(), rect.height())
        scene.setSceneRect(rect)
        return super().mouseReleaseEvent(event)

    def center_text(self):
        """Center the text in the ellipse."""
        bounding_rect = self.text_item.boundingRect()
        ellipse_rect = self.rect()
        x = ellipse_rect.x() + (ellipse_rect.width() - bounding_rect.width()) / 2
        y = ellipse_rect.y() + (ellipse_rect.height() - bounding_rect.height()) / 2
        self.text_item.setPos(x, y)

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionChange:
            grid_size_x = self.grid_size_x // 4
            grid_size_y = self.grid_size_y // 4
            new_x = round(value.x() / grid_size_x) * grid_size_x
            new_y = round(value.y() / grid_size_y) * grid_size_y
            if self.parent_adinkra is not None:
                self.parent_adinkra.fermion_positions[self.label][0] = self.scene_x + new_x
                self.parent_adinkra.fermion_positions[self.label][1] = self.scene_y + new_y

            return QPointF(new_x, new_y)

        elif change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_position()

        return super().itemChange(change, value)

class Edge(QGraphicsLineItem):
    def __init__(self, node1, node2, color, dashing, thickness:int = 3):
        super().__init__()
        self.node1 = node1
        self.node2 = node2
        self.color = color 
        self.dashing = dashing
        if self.dashing == -1:
            style = Qt.PenStyle.DashLine
        else:
            style = Qt.PenStyle.SolidLine
        
        self.setPen(QPen(color, thickness, style))
        # Attach this edge to the nodes
        node1.edges.append(self)
        node2.edges.append(self)
        # Initial position
        self.update_position()

    def update_position(self):
        """Update the edge position based on node locations."""
        x1 = self.node1.sceneBoundingRect().center().x()
        y1 = self.node1.sceneBoundingRect().center().y()
        x2 = self.node2.sceneBoundingRect().center().x()
        y2 = self.node2.sceneBoundingRect().center().y()
        self.setLine(x1, y1, x2, y2)

class TreeNode(QTreeWidgetItem):
    def __init__(self, label, value=None):
        super().__init__([label])
        self.value = value  # store custom value

    def to_dict(self):
        """Convert this node and its children to a serializable dictionary."""
        return {
            "label": self.text(0),
            "value": self.value,
            "children": [child.to_dict() for child in self.iter_children()]
        }

    @staticmethod
    def from_dict(data):
        """Reconstruct a SerializableTreeItem from dict."""
        item = TreeNode(data["label"], data["value"])
        for child_data in data["children"]:
            item.addChild(TreeNode.from_dict(child_data))
        return item

    def iter_children(self):
        return (self.child(i) for i in range(self.childCount()))

    def save_tree(self, filename):
        tree_data = self.to_dict()
        with open(filename, "wb") as f:
            pickle.dump(tree_data, f)
    
    @staticmethod
    def load_tree(treeWidget, filepath):
        with open(filepath, "rb") as f:
            tree_data = pickle.load(f)
        root_item = TreeNode.from_dict(tree_data)
        print(root_item.to_dict())
        treeWidget.addTopLevelItem(root_item)
        return root_item
    
    def delete_child_by_label(self, label):
        """Delete the first child node with the matching label."""
        for i in range(self.childCount()):
            child = self.child(i)
            if child.text(0) == label:
                self.takeChild(i)
                return True
        return False

    def delete_all_children(self):
        """Delete all child nodes."""
        while self.childCount() > 0:
            self.takeChild(0)



class MainWindow(QMainWindow, Ui_MainWindow):

    def __init__(self):
        super().__init__()
        # interactive options
        self.node_size = 30
        self.color_set = "place_holder"
        self.show_labels = True
        self.library = None
        self.theory = None
        self.adinkra = None
        self.current_font = QFont('Arial', 12)
        self.edge_thickness = 3
        self.node_radius = 3
        # self setup graphics
        self.setupUi(self)
        self.refresh_graph(init=True)
        self.aspect_modifier = 1

        # Connect menu actions to functions
        self.actionOpen_Library.triggered.connect(self.wrap_for_trigger(self.open_library_file))
        self.actionClose.triggered.connect(self.wrap_for_trigger(self.close_library))
        self.actionSave_Library.triggered.connect(self.wrap_for_trigger(self.save_library_file))
        self.actionCreate_Theory.triggered.connect(self.wrap_for_trigger(self.add_theory))
        self.actionImportAdinkra.triggered.connect(self.wrap_for_trigger(self.import_adinkra))
        self.actionCreate_Library.triggered.connect(self.wrap_for_trigger(self.new_library))
        self.actionComment.triggered.connect(self.wrap_for_trigger(self.add_comment))
        self.treeWidget.itemSelectionChanged.connect(self.wrap_for_trigger(self.on_item_selected))
        self.actionAdinkra_as_Image.triggered.connect(self.wrap_for_trigger(self.export_graphics))
        self.actionColorsDefinition.triggered.connect(self.wrap_for_trigger(self.pick_colors_def))
        self.actionColorsIndividual.triggered.connect(self.wrap_for_trigger(self.pick_colors_ind))
        self.actionLabeling.triggered.connect(self.wrap_for_trigger(self.open_font_dialog))
        self.actionEdgeThickness.triggered.connect(self.wrap_for_trigger(self.pick_edge_thickness))
        self.actionNodeRadius.triggered.connect(self.wrap_for_trigger(self.pick_node_size))
        self.actionOpen_Manual.triggered.connect(self.wrap_for_trigger(show_terms_from_action))
        self.actionDelete_This_Adinkra.triggered.connect(self.wrap_for_trigger(self.delete_adinkra))
        self.actionDelete_Theory.triggered.connect(self.wrap_for_trigger(self.delete_theory))
    
    def wrap_for_trigger(self, fn):
        def wrapped(*_):  # Ignore any signal arguments
            return fn()
        return wrapped

    @catch_nicely
    def get_user_input(self, window_title, default_value):
        """Show a larger floating text input box."""
        dialog = QInputDialog(self)
        dialog.setWindowTitle(window_title)
        dialog.setLabelText(default_value)
        dialog.resize(400, 200)  # Resize the dialog
        
        if dialog.exec() == QInputDialog.DialogCode.Accepted:
            text = dialog.textValue()
            return text
        return None

    @catch_nicely
    def on_item_selected(self):
        selected_item = self.treeWidget.currentItem()
        if not selected_item:
            return
        if isinstance(selected_item.value, Adinkra):
            self.adinkra = selected_item
            theory = selected_item
            while theory.parent() and theory.parent().parent():
                theory = theory.parent()
            self.theory = theory
            self.library = theory.parent()

            tableitem = self.tableWidget.item(0, 0)
            tableitem.setText(f"    {self.library.text(0)} ")
            tableitem = self.tableWidget.item(1, 0)
            tableitem.setText(f"    {self.theory.text(0)} ")
            tableitem = self.tableWidget.item(2, 0)
            tableitem.setText(f"    {self.adinkra.text(0)} ")
            
            self.refresh_graph(init=True)

        elif isinstance(selected_item, TreeNode):
            # Access the theory node level
            # Ensure it's not the root node
            if not selected_item.parent():
                self.library = selected_item
                self.theory = None
                self.adinkra = None
                tableitem = self.tableWidget.item(0, 0)
                tableitem.setText(f"    {selected_item.text(0)} ")
                return
            # Traverse up to the theory node. if no parent, then we are at the root node. 
            theory = selected_item
            while theory.parent() and theory.parent().parent():
                theory = theory.parent()
            self.library = theory.parent()
            self.theory = theory
            self.adinkra = find_first_adinkra(theory)
            
            tableitem = self.tableWidget.item(0, 0)
            tableitem.setText(f"    {self.library.text(0)} ")
            tableitem = self.tableWidget.item(1, 0)
            tableitem.setText(f"    {self.theory.text(0)} ")
            if self.adinkra is not None:
                tableitem = self.tableWidget.item(2, 0)
                tableitem.setText(f"    {self.adinkra.text(0)} ")
            else:
                tableitem = self.tableWidget.item(2, 0)
                tableitem.setText("    None")
            self.refresh_graph(init = True)

    @catch_nicely
    def refresh_graph(self, init:bool=False):
        if self.theory is not None and self.adinkra is not None:
            self.scene = QGraphicsScene()
            self.scene.setSceneRect(0, 0, 2000, 2000)  # Large scene size

            self.graphicsView.setScene(self.scene)
            self.graphicsView.setBackgroundBrush(QBrush(QColor(255, 255, 255, 255)))

            self.draw_graph(init = init)
    
    @catch_nicely
    def new_library(self):
        name = self.get_user_input("Creating new Library: Enter Library Name", "Library Name")
        if name:  # If the user pressed OK and entered text
            self.library = TreeNode(name)
            self.treeWidget.addTopLevelItem(self.library)
            self.theory = None
            self.adinkra = None
            QMessageBox.information(self, "Note", f"New Library: {name} created.")
            self.treeWidget.expandAll()
            return 0
        else:
            return 1

    @catch_nicely
    def add_theory(self):
            """check for existence of a library."""
            if not isinstance(self.library, TreeNode):
                buttonpressed = self.show_create_library_option_box()
                if buttonpressed == "Yes":
                    if self.new_library():
                        return 1
                elif buttonpressed == "No":
                    return 1
                elif buttonpressed == "Cancel":
                    return 1
            """Add a new theory to the library."""
            theory_name = self.get_user_input("New Theory in Current Library", "Theory Name")
            if theory_name:
                new_theory = TreeNode(theory_name)
                self.library.addChild(new_theory)
                self.theory = new_theory
                QMessageBox.information(self, "Note", f"New Theory: {theory_name} created.")
                self.treeWidget.expandAll()
            else:
                return
    
    @catch_nicely
    def delete_adinkra(self):
        if isinstance(self.adinkra, TreeNode):
            buttonpressed = self.show_create_library_option_box(txt="Deleting Current Adinkra. Are you sure?")
            if buttonpressed == "Yes":
                self.theory.delete_child_by_label(self.adinkra.text(0))
                del self.adinkra
                self.adinkra = find_first_adinkra(self.theory)
                return 1
            elif buttonpressed == "No":
                return 1
            elif buttonpressed == "Cancel":
                return 1
    
    @catch_nicely
    def delete_theory(self):
        if isinstance(self.theory, TreeNode):
            buttonpressed = self.show_create_library_option_box(txt="Deleting Current Theory and Adinkras in it. Are you sure?")
            if buttonpressed == "Yes":
                self.theory.delete_all_children()
                self.library.delete_child_by_label(self.theory.text(0))
                if len(list(self.library.iter_children())) >0:
                    self.theory = self.library.iter_children()[0]
                    self.adinkra = find_first_adinkra(self.theory)
                else:
                    self.theory = None
                    self.adinkra = None
                return 1
            elif buttonpressed == "No":
                return 1
            elif buttonpressed == "Cancel":
                return 1
   
    @catch_nicely
    def add_comment(self):
        return

    @catch_nicely
    def import_adinkra(self):
            if not isinstance(self.theory, TreeNode):
                if self.add_theory():
                    QMessageBox.information(self, "Note", f"No Adinkra Created")
                    return
            adinkra_name = self.get_user_input("New Adinkra in Current Theory", "Adinkra Name")
            if adinkra_name is None:
                QMessageBox.information(self, "Note", f"No Adinkra Created")
                return
            """Add an Adinkra to the library."""
            adinkra = self.open_adinkra_file()
            if adinkra:
                self.adinkra = TreeNode(adinkra_name, value=adinkra)
                self.theory.addChild(self.adinkra)
                self.refresh_graph()
                tableitem = self.tableWidget.item(2, 0)
                tableitem.setText(f"    {self.adinkra.text(0)} ")
                QMessageBox.information(self, "Note", f"New Adinkra: {adinkra_name} created.")
                self.treeWidget.expandAll()
            else:
                QMessageBox.information(self, "Note", f"No Adinkra Created")
                return

    @catch_nicely
    def draw_graph(self, init:bool=False):
        # initialize positions for Fermions and Bosons
        x_center, y_center = 1000,1000 
        adinkra = self.adinkra.value
        self.aspect_modifier = max(1,max(adinkra.adinkra_size[0], adinkra.adinkra_size[1])/16)
        # defined for viewing 
        self.nodes = [] 
        self.edges = []
        if isinstance(adinkra, Adinkra):

            if adinkra.boson_labels is None or len(adinkra.boson_labels) != adinkra.adinkra_size[0]:
                boson_labels = [str(i) for i in range(adinkra.adinkra_size[0])]
            else:
                boson_labels = adinkra.boson_labels

            if adinkra.fermion_labels is None or len(adinkra.fermion_labels) != adinkra.adinkra_size[1]:
                fermion_labels = [str(i) for i in range(adinkra.adinkra_size[1])]
            else:
                fermion_labels = adinkra.fermion_labels


            if adinkra.boson_positions is None or adinkra.fermion_positions is None:
                adinkra.boson_positions = {}
                adinkra.fermion_positions = {}
                #bosons
                for i in range(adinkra.adinkra_size[0]):
                    adinkra.boson_positions[boson_labels[i]] = [x_center - int((adinkra.adinkra_size[0]/2 - i) * 100), y_center - (200 - 400*adinkra.boson_elevations[i])*self.aspect_modifier]
                #fermions
                for i in range(adinkra.adinkra_size[1]):
                    adinkra.fermion_positions[fermion_labels[i]] = [x_center - int((adinkra.adinkra_size[1]/2 - i) * 100), y_center - (200 - 400*adinkra.fermion_elevations[i])*self.aspect_modifier]

            # Create draggable nodes
            for i, (x, y) in enumerate(adinkra.boson_positions.values()):
                node = DraggableBoson(x, y, label = boson_labels[i], parent_adinkra=adinkra,font=self.current_font, grid_size_x = 100, grid_size_y = int(self.aspect_modifier*400), radius=self.node_radius)
                self.nodes.append(node)
            # Create draggable nodes
            for i, (x, y) in enumerate(adinkra.fermion_positions.values()):
                node = DraggableFermion(x, y, label = fermion_labels[i], parent_adinkra=adinkra,font=self.current_font, grid_size_x = 100, grid_size_y = int(self.aspect_modifier*400), radius=self.node_radius)
                self.nodes.append(node)

            # Create edges
            if adinkra.edge_colors is None:
                edge_colors = []
            for n, edges in enumerate(adinkra.edges):
                if adinkra.edge_colors == None:
                    color = QColor.fromHsvF(n/adinkra.adinkra_colors, 1.0, 1.0)
                    edge_colors.append(color)
                #elif isinstance(adinkra.edge_colors, list) and len(adinkra.edge_colors) == adinkra.adinkra_colors:
                else:
                    color = adinkra.edge_colors[n]
                #else:
                #    raise Exception("This state should not be reached")
                for nc, (i, j) in enumerate(edges):
                    edge = Edge(self.nodes[i], self.nodes[j+ adinkra.adinkra_size[0]], color, adinkra.dashing[n,nc], thickness = self.edge_thickness)
                    self.scene.addItem(edge)
                    self.edges.append(edge)

            if adinkra.edge_colors is None:
                adinkra.edge_colors = edge_colors

            for i, nd in enumerate(self.nodes):
                self.scene.addItem(nd)

            rect = self.scene.itemsBoundingRect()
            margin = 100
            rect.adjust(-margin, -margin, margin, margin)
            
            if init:
                self.graphicsView.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
                self.graphicsView.centerOn(rect.center())
            
            rect.adjust(-2*rect.width(), -2*rect.height(), 2*rect.width(), 2*rect.height())
            self.scene.setSceneRect(rect)
    
    @catch_nicely
    def open_library_file(self):
        """Open a file dialog and load file contents."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;Adinkra Library (*.pkl)") 
        if not file_path:
            return
        # Check if the file is a .pkl file
        if os.path.splitext(file_path)[1]==".pkl":
            try:
                self.library = TreeNode.load_tree(self.treeWidget, file_path)
                QMessageBox.information(self, "Information", f"Opened file: {file_path}")
                self.treeWidget.expandAll()
                return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file:\n{str(e)}")
                return
        else:
            QMessageBox.warning(self, "Warning", "File type not supported. Please select an Adinkra Library (.pkl) file.")
            return

    @catch_nicely
    def save_library_file(self):
        # Check if library is loaded
        if self.library is None:  
            QMessageBox.warning(self, "Warning", "No library loaded to save.")
            return

        """Open a file dialog to save data."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", f"{self.library.text(0)}.pkl", "All Files (*);;Adinkra Library (*.pkl)")
        if file_path:
            try:
                self.library.save_tree(file_path)
                QMessageBox.information(self, "Information", f"Saved file: {file_path}")
                return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")
                return

    @catch_nicely
    def close_library(self):
        if self.library is None:
            QMessageBox.warning(self, "Information", "No library loaded.")
            return
        userpressed = self.show_save_option_box()
        if userpressed == "Save":
            self.save_library_file()
        elif userpressed == "Don't Save":
            pass
        elif userpressed == "Cancel":
            return
        self.reset_library()
        return

    @catch_nicely
    def reset_library(self):
        index = self.treeWidget.indexOfTopLevelItem(self.library)
        if index != -1:
            self.treeWidget.takeTopLevelItem(index)
        self.tableWidget.item(0, 0).setText("    None Loaded")
        self.tableWidget.item(1, 0).setText("    None Loaded")
        self.tableWidget.item(2, 0).setText("    None Loaded")
        self.library = None
        self.theory = None
        self.adinkra = None
        self.nodes = []
        self.node_labels = {}
        self.edges = []
        self.refresh_graph()

    @catch_nicely
    def open_adinkra_file(self):
        """Open a file dialog and load file contents."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;Adinkra Matrices File (*.csv)") 
        if not file_path:
            return
        # Check if the file is a .pkl file
        if os.path.splitext(file_path)[1]==".csv":
            try:
                adinkra = Adinkra(file_path)    
                print(f"Opened Adinkra: {file_path}")  # Handle data as needed
                return adinkra
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file:\n{str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "File type not supported. Please select an Adinkra Matrices (.csv) file.")
    
    @catch_nicely
    def show_save_option_box(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Do you wish to save your current Library?")
        msg.setText("Unsaved changes will be discarded;")

        # Add standard and custom buttons
        btn_save = msg.addButton("Save", QtWidgets.QMessageBox.ButtonRole.ActionRole)
        btn_nosave = msg.addButton("Don't Save", QtWidgets.QMessageBox.ButtonRole.RejectRole)
        btn_cancel = msg.addButton("Cancel", QtWidgets.QMessageBox.ButtonRole.ResetRole)

        msg.setIcon(QMessageBox.Icon.Question)
        msg.exec()
        if msg.clickedButton() == btn_save :
            return "Save" 
        elif msg.clickedButton() == btn_nosave :
            return "Don't Save"
        elif msg.clickedButton() == btn_cancel: 
            return "Cancel"
        else:
            return None

    @catch_nicely
    def show_create_library_option_box(self, txt="No current Library: Create a new one?"):
        msg = QMessageBox(self)
        msg.setWindowTitle(txt)
        msg.setText(txt)

        # Add standard and custom buttons
        btn_yes = msg.addButton("Yes", QMessageBox.ButtonRole.YesRole)
        btn_no = msg.addButton("No", QMessageBox.ButtonRole.NoRole)
        btn_cancel = msg.addButton("Cancel", QMessageBox.ButtonRole.ResetRole)

        msg.setIcon(QMessageBox.Icon.Question)
        msg.exec()
        if msg.clickedButton() == btn_yes :
            return "Yes" 
        elif msg.clickedButton() == btn_no :
            return "No"
        elif msg.clickedButton() == btn_cancel: 
            return "Cancel"
        else:
            return None
     
    @catch_nicely
    def pick_colors_ind(self):
        # Show the color picker dialog
        if self.adinkra is not None:
            num_colors = self.adinkra.value.adinkra_colors
            colors = self.adinkra.value.edge_colors
        else: 
            num_colors = 1
            colors = None

        dialog = SimpleColorEditorDialog(initial_colors = colors)
        
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            colors = dialog.get_colors()
            print("Selected colors:")
            for i, color in enumerate(colors):
                print(f"  Color {i+1}: {color.name()} (H:{color.hue()}, S:{color.saturation()}, V:{color.value()})")
            if self.adinkra is not None:
                self.adinkra.value.edge_colors = colors
                self.refresh_graph()

    @catch_nicely
    def pick_colors_def(self):
        # Show the color picker dialog
        if self.adinkra is not None:
            num_colors = self.adinkra.value.adinkra_colors
            colors = self.adinkra.value.edge_colors
        else: 
            num_colors = 1
            colors = None

        dialog = ColorPickerDialog(num_colors, colors)
        
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            colors = dialog.get_selected_colors()
            print("Selected colors:")
            for i, color in enumerate(colors):
                print(f"  Color {i+1}: {color.name()} (H:{color.hue()}, S:{color.saturation()}, V:{color.value()})")
            if self.adinkra is not None:
                self.adinkra.value.edge_colors = colors
                self.refresh_graph()

    @catch_nicely
    def export_graphics(self):
        """Export graphics with user choice of scope and format"""
        
        # Check if graphics view/scene exists
        if not hasattr(self, 'graphicsView') or not hasattr(self, 'scene'):
            QMessageBox.warning(self, "Warning", "No graphics view available to export.")
            return
        
        if self.scene is None or self.graphicsView is None:
            QMessageBox.warning(self, "Warning", "Graphics view not properly initialized.")
            return
        
        # First dialog: Choose export scope (Full Scene vs Current View)
        scope_options = ["Full Scene (all content)", "Current View (visible area only)"]
        scope_choice, scope_ok = QInputDialog.getItem(
            self, 
            "Export Scope", 
            "Choose what to export:", 
            scope_options, 
            0, 
            False
        )
        
        if not scope_ok:
            return  # User cancelled
        
        export_full_scene = scope_choice.startswith("Full Scene")
        
        default_name = f"{self.theory.text(0)}-{self.adinkra.text(0)}"
        
        # File dialog for format and location
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, 
            "Export Graphics", 
            f"{default_name}.png", 
            "PNG Image (*.png);;SVG Vector (*.svg)"
        )
        
        if not file_path:
            return  # User cancelled
        
        try:
            # Determine format from selected filter or file extension
            if selected_filter.startswith("SVG") or file_path.lower().endswith('.svg'):
                # SVG Export
                if export_full_scene:
                    success = GraphicsExporter.export_scene_to_svg(self.scene, file_path)
                else:
                    success = GraphicsExporter.export_view_to_svg(self.graphicsView, file_path)
            else:
                # PNG Export (default)
                if export_full_scene:
                    success = GraphicsExporter.export_scene_to_image(self.scene, file_path, format='PNG')
                else:
                    success = GraphicsExporter.export_view_to_image(self.graphicsView, file_path, format='PNG')
            
            if success:
                QMessageBox.information(self, "Information", f"Successfully exported: {file_path}")
            else:
                QMessageBox.critical(self, "Error", "Failed to export graphics file.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export graphics:\n{str(e)}")
     
    @catch_nicely
    def open_font_dialog(self):
        """Open the font selection dialog"""
        dialog = FontSelectionDialog(self.current_font, self)
        
        # Connect to the custom signal
        dialog.fontSelected.connect(self.on_font_selected)
        
        # Show the dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Font was selected - signal already emitted
            pass
        else:
            # Dialog was cancelled
            print("Font selection cancelled")

    @catch_nicely
    def on_font_selected(self, font_name, font_size):
        """Handle font selection from dialog"""
        print(f"Selected font: {font_name}, size: {font_size}")
        
        # Update current font
        self.current_font = QFont(font_name, font_size)
        
        # Update UI
        self.refresh_graph()
    
    @catch_nicely
    def pick_edge_thickness(self):
        """Open slider dialog - exactly like your font dialog pattern"""
        dialog = SliderDialog("Line Thickness", 1, 20, self.edge_thickness, self)
        
        # Connect to the custom signal
        dialog.valueSelected.connect(self.on_edge_thickness_selected)
        
        # Show the dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Value was selected - signal already emitted
            pass
        else:
            # Dialog was cancelled
            print("Selection cancelled")

    @catch_nicely
    def on_edge_thickness_selected(self, value):
        """Handle value selection from dialog"""
        self.edge_thickness = value
        # Update UI
        self.refresh_graph()
    
    @catch_nicely
    def pick_node_size(self):
        """Open slider dialog - exactly like your font dialog pattern"""
        dialog = SliderDialog("Node Radius", 1, 20, self.node_radius, self)
        
        # Connect to the custom signal
        dialog.valueSelected.connect(self.on_node_radius_selected)
        
        # Show the dialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Value was selected - signal already emitted
            pass
        else:
            # Dialog was cancelled
            print("Selection cancelled")

    @catch_nicely
    def on_node_radius_selected(self, value):
        """Handle value selection from dialog"""
        self.node_radius = value
        # Update UI
        self.refresh_graph()

class GraphicsExporter:
    """Utility class for exporting QGraphicsView/QGraphicsScene"""
    
    @staticmethod
    def export_scene_to_image(scene, filename, width=None, height=None, margin = 20, format='PNG'):
        """Export QGraphicsScene to image file"""
        scene_rect = scene.itemsBoundingRect()
        scene_rect.adjust(-margin, -margin, margin, margin)
        if width is None or height is None:
            output_size = scene_rect.size().toSize()
        else:
            output_size = QtCore.QSize(width, height)
        
        image = QtGui.QImage(output_size, QtGui.QImage.Format.Format_ARGB32)
        image.fill(QtCore.Qt.GlobalColor.white)
        
        painter = QtGui.QPainter(image)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        scene.render(painter, QtCore.QRectF(image.rect()), scene_rect)
        painter.end()
        
        return image.save(filename, format)
    
    @staticmethod
    def export_view_to_image(graphics_view, filename, format='PNG'):
        """Export current view to image file"""
        viewport_rect = graphics_view.viewport().rect()
        
        image = QtGui.QImage(viewport_rect.size(), QtGui.QImage.Format.Format_ARGB32)
        image.fill(QtCore.Qt.GlobalColor.white)
        
        painter = QtGui.QPainter(image)
        graphics_view.render(painter)
        painter.end()
        
        return image.save(filename, format)
    
    @staticmethod
    def export_scene_to_svg(scene, filename, margin=20):
        """Export QGraphicsScene to SVG"""
        try:
            from PyQt6.QtSvg import QSvgGenerator
        except ImportError:
            raise ImportError("SVG export requires PyQt6.QtSvg module")
        
        # Use the same scene rectangle calculation as PNG export
        scene_rect = scene.itemsBoundingRect()
        scene_rect.adjust(-margin, -margin, margin, margin)
        
        svg_generator = QSvgGenerator()
        svg_generator.setFileName(filename)
        svg_generator.setSize(scene_rect.size().toSize())
        svg_generator.setViewBox(QtCore.QRectF(0, 0, scene_rect.width(), scene_rect.height()))
        svg_generator.setTitle("Graphics Scene Export")
        svg_generator.setDescription("Exported from QGraphicsScene")
        
        # Use the same painter setup and render call as PNG export
        painter = QtGui.QPainter(svg_generator)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        scene.render(painter, QtCore.QRectF(0, 0, scene_rect.width(), scene_rect.height()), scene_rect)
        painter.end()
        
        return True

    @staticmethod
    def export_view_to_svg(graphics_view, filename):
        """Export current view to SVG"""
        try:
            from PyQt6.QtSvg import QSvgGenerator
        except ImportError:
            raise ImportError("SVG export requires PyQt6.QtSvg module")
        
        viewport_rect = graphics_view.viewport().rect()
        
        svg_generator = QSvgGenerator()
        svg_generator.setFileName(filename)
        svg_generator.setSize(viewport_rect.size())
        svg_generator.setViewBox(QtCore.QRectF(viewport_rect))
        svg_generator.setTitle("Graphics View Export")
        svg_generator.setDescription("Exported from QGraphicsView")
        
        painter = QtGui.QPainter(svg_generator)
        graphics_view.render(painter)
        painter.end()
        
        return True

class HexagonalColorPicker(QWidget):
    """Custom hexagonal color picker widget"""
    
    colorChanged = QtCore.pyqtSignal(list)  # Emit list of selected colors
    
    def __init__(self, num_colors, colors, parent=None):
        super().__init__(parent)
        self.setMinimumSize(350, 350)
        
        # Color selection parameters
        self.num_colors = num_colors
        if colors is None:
            self.first_color = 0
            self.saturation = 0.8
            self.brightness = 0.9
        elif isinstance(colors, list) and len(colors) == num_colors:
            self.first_color = colors[0].hue()/360
            self.saturation = colors[0].saturation()/255
            self.brightness = colors[0].value()/255
        else:
            print(colors)
            raise Exception("This state should never be reached")

        self.selected_colors = []
        
        # Hexagon parameters
        self.center = QPointF(175, 175)
        self.radius = 150
        self.hex_radius = 8  # Radius of individual color hexagons
        
        # Track mouse interaction
        self.dragging_saturation = False
        #self.dragging_brightness = False
        self.dragging_hue = False
        
        self.update_colors()
    
    def set_num_colors(self, n):
        """Set the number of colors to generate"""
        self.num_colors = max(1, n)
        self.update_colors()
        self.update()

    def set_first_hue(self, hue):
        """
        Set the first color
        """
        self.first_color  = max(0.0, min(1.0, hue))
        self.update_colors()
        self.update()


    def set_saturation(self, sat):
        """Set saturation (0.0 to 1.0)"""
        self.saturation = max(0.0, min(1.0, sat))
        self.update_colors()
        self.update()
    
    def set_brightness(self, bright):
        """Set brightness/value (0.0 to 1.0)"""  
        self.brightness = max(0.0, min(1.0, bright))
        self.update_colors()
        self.update()
    
    def update_colors(self):
        """Update the selected colors based on current parameters"""
        self.selected_colors = []
        for i in range(self.num_colors):
            hue = (self.first_color*360 + i * 360 / self.num_colors) % 360
            color = QColor.fromHsvF(hue/360.0, self.saturation, self.brightness)
            self.selected_colors.append(color)
        
        self.colorChanged.emit(self.selected_colors)
    
    def create_hexagon_pattern(self):
        """Create hexagonal grid of colors in proper hexagonal arrangement"""
        hexagons = []
        
        # Hexagon grid spacing
        hex_spacing = self.hex_radius * 1.8  # Space between hexagon centers
        
        # Create concentric hexagonal layers
        for layer in range(8):  # 8 layers of hexagons
            if layer == 0:
                # Center hexagon
                hexagons.append({
                    'pos': self.center,
                    'color': QColor.fromHsvF(0, 0, 1),  # White center
                    'layer': 0
                })
            else:
                # Get hexagonal positions for this layer
                hex_positions = self.get_hexagonal_ring_positions(layer, hex_spacing)
                
                for pos in hex_positions:
                    # Calculate HSV based on hexagonal position
                    dx = pos.x() - self.center.x()
                    dy = pos.y() - self.center.y()
                    
                    # Hue from angle
                    angle = math.atan2(dy, dx)
                    hue = (math.degrees(angle) + 180) % 360
                    
                    # Saturation from layer (distance from center in hex grid)
                    max_layer = 7
                    sat = min(1.0, layer / max_layer)
                    
                    
                    color = QColor.fromHsvF(hue/360.0, sat, self.brightness)
                    hexagons.append({
                        'pos': pos,
                        'color': color,
                        'layer': layer
                    })
        
        return hexagons
    
    def get_hexagonal_ring_positions(self, layer, spacing):
        """Get positions for hexagons in a hexagonal ring at given layer"""
        positions = []
        
        if layer == 0:
            return [self.center]
        
        # Start at the rightmost point of the hexagon
        start_x = self.center.x() + layer * spacing
        start_y = self.center.y()
        
        # Six directions for hexagonal grid
        # Each direction is 60 degrees apart
        hex_directions = [
            (-0.5, -math.sqrt(3)/2),    # Top-left
            (-1.0, 0),                  # Left  
            (-0.5, math.sqrt(3)/2),     # Bottom-left
            (0.5, math.sqrt(3)/2),      # Bottom-right
            (1.0, 0),                   # Right
            (0.5, -math.sqrt(3)/2)      # Top-right
        ]
        
        current_x, current_y = start_x, start_y
        
        # Walk around the hexagonal perimeter
        for side in range(6):
            # Number of steps along this side
            steps = layer
            
            direction = hex_directions[side]
            step_x = direction[0] * spacing
            step_y = direction[1] * spacing
            
            # Add hexagons along this side
            for step in range(steps):
                positions.append(QPointF(current_x, current_y))
                current_x += step_x
                current_y += step_y
        
        return positions

   
    def draw_hexagon(self, painter, center, radius, color):
        """Draw a single hexagon"""
        points = []
        for i in range(6):
            angle = i * math.pi / 3 + math.pi / 6
            x = center.x() + radius * math.cos(angle)
            y = center.y() + radius * math.sin(angle)
            points.append(QPointF(x, y))
        
        polygon = QPolygonF(points)
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.GlobalColor.black, 0.5))
        painter.drawPolygon(polygon)
    
    def draw_selected_color_indicators(self, painter):
        """Draw indicators for the currently selected colors"""
        for i, color in enumerate(self.selected_colors):
            # Calculate position on the hex ring
            hue_angle = (math.pi + self.first_color*2*math.pi + i * 2 * math.pi / self.num_colors)
            indicator_radius = self.radius
            
            x = self.center.x() + indicator_radius * math.cos(hue_angle)
            y = self.center.y() + indicator_radius * math.sin(hue_angle)
            
            # Draw larger indicator hexagon
            indicator_pos = QPointF(x, y)
            
            # Draw white outline
            painter.setBrush(QBrush(Qt.GlobalColor.white))
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            self.draw_hexagon(painter, indicator_pos, self.hex_radius * 1.5, Qt.GlobalColor.white)
            
            # Draw color hexagon inside
            painter.setPen(QPen(Qt.GlobalColor.black, 1))
            self.draw_hexagon(painter, indicator_pos, self.hex_radius * 1.2, color)
            
            # Draw index number
            painter.setPen(QPen(Qt.GlobalColor.white, 2))
            painter.setFont(QtGui.QFont("Arial", 8, QtGui.QFont.Weight.Bold))
            text_rect = QRectF(x - 10, y - 6, 20, 12)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, str(i + 1))

    def paintEvent(self, event):
        """Custom paint event"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        try:
            # Update center based on current widget size
            self.center = QPointF(self.width() / 2, self.height() / 2)
            self.radius = min(self.width(), self.height()) / 3
            
            # Clear background
            painter.fillRect(self.rect(), Qt.GlobalColor.white)
            
            # Draw hexagonal color pattern
            hexagons = self.create_hexagon_pattern()
            for hex_data in hexagons:
                self.draw_hexagon(painter, hex_data['pos'], self.hex_radius, hex_data['color'])
            
            # Draw saturation ring
            sat_radius = self.radius
            painter.setPen(QPen(Qt.GlobalColor.black, 2))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(self.center, sat_radius, sat_radius)

            # Draw selected color indicators
            self.draw_selected_color_indicators(painter)
            
            ## Draw brightness indicator (vertical bar on right)
            #bright_bar_x = int(self.width() - 30)
            #bright_bar_height = int(self.height() - 40)
            #bright_y = int(20 + (1.0 - self.brightness) * bright_bar_height)
            #
            ## Brightness bar background
            #painter.fillRect(bright_bar_x, 20, 20, bright_bar_height, Qt.GlobalColor.lightGray)
            #
            ## Brightness indicator
            #painter.fillRect(bright_bar_x - 2, bright_y - 2, 24, 4, Qt.GlobalColor.red)
            
        finally:
            # Ensure painter is properly ended
            painter.end()

    def mousePressEvent(self, event):
        """Handle mouse press for interactive adjustment"""
        pos = event.position()
        
        ## Check if clicking on brightness bar
        #bright_bar_x = self.width() - 30
        #if pos.x() >= bright_bar_x - 5 and pos.x() <= bright_bar_x + 25:
        #    self.dragging_brightness = True
        #    self.update_brightness_from_mouse(pos.y())
        #    return
        
        # Check if clicking within saturation ring area
        distance = math.sqrt((pos.x() - self.center.x())**2 + (pos.y() - self.center.y())**2)
        angle = math.atan2((pos.y() - self.center.y()), (pos.x() - self.center.x()))
        print(angle)
        if distance <= self.radius:
            self.dragging_saturation = True
            self.update_saturation_from_mouse(distance)
            self.dragging_hue = True
            self.update_hue_from_mouse(angle)
    

    def mouseMoveEvent(self, event):
        """Handle mouse drag"""
        pos = event.position()
        
        #if self.dragging_brightness:
        #    self.update_brightness_from_mouse(pos.y())
        if self.dragging_saturation:
            angle = math.atan2((pos.y() - self.center.y()), (pos.x() - self.center.x()))
            distance = math.sqrt((pos.x() - self.center.x())**2 + (pos.y() - self.center.y())**2)
            self.update_saturation_from_mouse(distance)
            self.update_hue_from_mouse(angle)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release"""
        #self.dragging_brightness = False
        self.dragging_saturation = False
        self.dragging_hue = False
    
    def update_hue_from_mouse(self,angle):
        hue = (angle + math.pi) / (2*math.pi)
        self.set_first_hue(hue)   

    def update_saturation_from_mouse(self, distance):
        """Update saturation based on mouse distance from center"""
        new_sat = min(1.0, max(0.0, distance / self.radius))
        self.set_saturation(new_sat)
    
    #def update_brightness_from_mouse(self, mouse_y):
    #     """Update brightness based on mouse Y position"""
    #     bright_bar_height = self.height() - 40
    #     relative_y = mouse_y - 20
    #     new_brightness = 1.0 - (relative_y / bright_bar_height)
    #     new_brightness = max(0.0, min(1.0, new_brightness))
    #     self.set_brightness(new_brightness)

class ColorPickerDialog(QtWidgets.QDialog):
    """Dialog containing the hexagonal color picker with controls"""
    
    def __init__(self, num_colors, colors, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edge Color Picker")
        self.setModal(True)
        self.num_colors = num_colors
        self.resize(600, 500)
        self.colors = colors
        self.selected_colors = colors
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Color picker widget
        self.color_picker = HexagonalColorPicker(self.num_colors, self.colors)
        self.color_picker.colorChanged.connect(self.on_colors_changed)
        layout.addWidget(self.color_picker)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Saturation
        controls_layout.addWidget(QLabel("Saturation:"))
        self.sat_spin = QtWidgets.QDoubleSpinBox()
        self.sat_spin.setRange(0.0, 1.0)
        self.sat_spin.setSingleStep(0.1)
        self.sat_spin.setValue(0.8)
        self.sat_spin.valueChanged.connect(self.color_picker.set_saturation)
        controls_layout.addWidget(self.sat_spin)
        
        # Brightness
        controls_layout.addWidget(QLabel("Brightness:"))
        self.bright_spin = QtWidgets.QDoubleSpinBox()
        self.bright_spin.setRange(0.0, 1.0)
        self.bright_spin.setSingleStep(0.1)
        self.bright_spin.setValue(0.9)
        self.bright_spin.valueChanged.connect(self.color_picker.set_brightness)
        controls_layout.addWidget(self.bright_spin)
        
        controls_layout.addStretch()
        
        # Preview colors
        self.color_preview = QLabel("Selected Colors:")
        layout.addWidget(self.color_preview)
        
        layout.addLayout(controls_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def on_colors_changed(self, colors):
        """Handle color selection change"""
        self.selected_colors = colors
        
        # Update spinboxes
        self.sat_spin.setValue(self.color_picker.saturation)
        self.bright_spin.setValue(self.color_picker.brightness)
        
        # Update preview
        preview_text = f"Selected {self.num_colors} Colors"
        self.color_preview.setText(preview_text)
    
    def get_selected_colors(self):
        """Return the selected colors"""
        return self.selected_colors

class ColorPreviewWidget(QWidget):
    """Small widget to display a color preview"""
    
    def __init__(self, color=None, size=40):
        super().__init__()
        self.color = color or QColor(255, 255, 255)
        self.setFixedSize(size, size)
    
    def set_color(self, color):
        """Update the color and repaint"""
        self.color = color
        self.update()
    
    def paintEvent(self, event):
        """Paint the color preview"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw color rectangle with border
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawRect(2, 2, self.width() - 4, self.height() - 4)

class ColorListItem(QWidget):
    """Custom widget for each color in the list"""
    
    def __init__(self, color_index, color):
        super().__init__()
        self.color_index = color_index
        self.color = color
        self.setup_ui()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Color number label
        self.number_label = QLabel(f"Color {self.color_index + 1}:")
        self.number_label.setMinimumWidth(60)
        layout.addWidget(self.number_label)
        
        # Color preview
        self.color_preview = ColorPreviewWidget(self.color, 30)
        layout.addWidget(self.color_preview)
        
        # Color info labels
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        self.hex_label = QLabel(f"#{self.color.name()[1:].upper()}")
        self.hsv_label = QLabel(f"H:{self.color.hue()}, S:{self.color.saturation()}, V:{self.color.value()}")
        
        info_layout.addWidget(self.hex_label)
        info_layout.addWidget(self.hsv_label)
        layout.addLayout(info_layout)
        
        layout.addStretch()
    
    def update_color(self, color):
        """Update the color and all displays"""
        self.color = color
        self.color_preview.set_color(color)
        self.hex_label.setText(f"#{color.name()[1:].upper()}")
        self.hsv_label.setText(f"H:{color.hue()}, S:{color.saturation()}, V:{color.value()}")

class HSVSliderGroup(QWidget):
    """Group of HSV sliders for editing a color"""
    
    colorChanged = pyqtSignal(QColor)
    
    def __init__(self):
        super().__init__()
        self.color = QColor(255, 0, 0)  # Default red
        self.updating = False  # Prevent feedback loops
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Hue slider (0-359)
        hue_group = QGroupBox("Hue (0-359°)")
        hue_layout = QHBoxLayout(hue_group)
        
        self.hue_slider = QSlider(Qt.Orientation.Horizontal)
        self.hue_slider.setRange(0, 359)
        self.hue_slider.setValue(0)
        self.hue_slider.valueChanged.connect(self.on_hue_changed)
        
        self.hue_spinbox = QSpinBox()
        self.hue_spinbox.setRange(0, 359)
        self.hue_spinbox.setValue(0)
        self.hue_spinbox.valueChanged.connect(self.on_hue_spinbox_changed)
        
        hue_layout.addWidget(self.hue_slider)
        hue_layout.addWidget(self.hue_spinbox)
        layout.addWidget(hue_group)
        
        # Saturation slider (0-255)
        sat_group = QGroupBox("Saturation (0-255)")
        sat_layout = QHBoxLayout(sat_group)
        
        self.sat_slider = QSlider(Qt.Orientation.Horizontal)
        self.sat_slider.setRange(0, 255)
        self.sat_slider.setValue(255)
        self.sat_slider.valueChanged.connect(self.on_sat_changed)
        
        self.sat_spinbox = QSpinBox()
        self.sat_spinbox.setRange(0, 255)
        self.sat_spinbox.setValue(255)
        self.sat_spinbox.valueChanged.connect(self.on_sat_spinbox_changed)
        
        sat_layout.addWidget(self.sat_slider)
        sat_layout.addWidget(self.sat_spinbox)
        layout.addWidget(sat_group)
        
        # Value/Brightness slider (0-255)
        val_group = QGroupBox("Value/Brightness (0-255)")
        val_layout = QHBoxLayout(val_group)
        
        self.val_slider = QSlider(Qt.Orientation.Horizontal)
        self.val_slider.setRange(0, 255)
        self.val_slider.setValue(255)
        self.val_slider.valueChanged.connect(self.on_val_changed)
        
        self.val_spinbox = QSpinBox()
        self.val_spinbox.setRange(0, 255)
        self.val_spinbox.setValue(255)
        self.val_spinbox.valueChanged.connect(self.on_val_spinbox_changed)
        
        val_layout.addWidget(self.val_slider)
        val_layout.addWidget(self.val_spinbox)
        layout.addWidget(val_group)
        
        # Large color preview
        preview_group = QGroupBox("Color Preview")
        preview_layout = QHBoxLayout(preview_group)
        
        self.large_preview = ColorPreviewWidget(self.color, 100)
        preview_layout.addWidget(self.large_preview)
        preview_layout.addStretch()
        
        # Color info
        info_layout = QVBoxLayout()
        self.preview_hex = QLabel(f"#{self.color.name()[1:].upper()}")
        self.preview_hex.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.preview_hsv = QLabel(f"HSV: ({self.color.hue()}, {self.color.saturation()}, {self.color.value()})")
        self.preview_rgb = QLabel(f"RGB: ({self.color.red()}, {self.color.green()}, {self.color.blue()})")
        
        info_layout.addWidget(self.preview_hex)
        info_layout.addWidget(self.preview_hsv)
        info_layout.addWidget(self.preview_rgb)
        info_layout.addStretch()
        
        preview_layout.addLayout(info_layout)
        layout.addWidget(preview_group)
    
    def set_color(self, color):
        """Set the color and update all controls"""
        self.updating = True
        self.color = color
        
        # Update sliders and spinboxes
        self.hue_slider.setValue(color.hue() if color.hue() >= 0 else 0)
        self.hue_spinbox.setValue(color.hue() if color.hue() >= 0 else 0)
        self.sat_slider.setValue(color.saturation())
        self.sat_spinbox.setValue(color.saturation())
        self.val_slider.setValue(color.value())
        self.val_spinbox.setValue(color.value())
        
        # Update preview
        self.update_preview()
        self.updating = False
    
    def update_preview(self):
        """Update the color preview and info labels"""
        self.large_preview.set_color(self.color)
        self.preview_hex.setText(f"#{self.color.name()[1:].upper()}")
        self.preview_hsv.setText(f"HSV: ({self.color.hue()}, {self.color.saturation()}, {self.color.value()})")
        self.preview_rgb.setText(f"RGB: ({self.color.red()}, {self.color.green()}, {self.color.blue()})")
    
    def update_color_from_hsv(self):
        """Update color from current HSV values"""
        if self.updating:
            return
        
        h = self.hue_slider.value()
        s = self.sat_slider.value() 
        v = self.val_slider.value()
        
        self.color = QColor.fromHsv(h, s, v)
        self.update_preview()
        self.colorChanged.emit(self.color)
    
    # Slider change handlers
    def on_hue_changed(self, value):
        self.hue_spinbox.setValue(value)
        self.update_color_from_hsv()
    
    def on_hue_spinbox_changed(self, value):
        self.hue_slider.setValue(value)
        self.update_color_from_hsv()
    
    def on_sat_changed(self, value):
        self.sat_spinbox.setValue(value)
        self.update_color_from_hsv()
    
    def on_sat_spinbox_changed(self, value):
        self.sat_slider.setValue(value)
        self.update_color_from_hsv()
    
    def on_val_changed(self, value):
        self.val_spinbox.setValue(value)
        self.update_color_from_hsv()
    
    def on_val_spinbox_changed(self, value):
        self.val_slider.setValue(value)
        self.update_color_from_hsv()

class SimpleColorListEditor(QWidget):
    """Main widget for editing a list of colors with HSV sliders"""
    
    colorsChanged = pyqtSignal(list)  # Emit updated color list
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.colors = [QColor.fromHsv(i * 60, 255, 255) for i in range(1)]  # Default colors
        self.current_color_index = 0
        self.color_list_items = []
        self.setup_ui()
        self.update_color_list()
    
    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        # Left side - Color list
        left_layout = QVBoxLayout()
        
        # Number of colors control
        controls_layout = QHBoxLayout()
        controls_layout.addWidget(QLabel(f"Number of Colors: {len(self.colors)}"))
        controls_layout.addStretch()
        
        left_layout.addLayout(controls_layout)
        
        # Color list
        list_label = QLabel("Colors:")
        list_label.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(list_label)
        
        self.color_list = QListWidget()
        self.color_list.setMaximumWidth(300)
        self.color_list.currentRowChanged.connect(self.on_color_selected)
        left_layout.addWidget(self.color_list)
        
        layout.addLayout(left_layout)
        
        # Vertical separator
        separator = QFrame()
        separator.setFrameStyle(QFrame.Shape.VLine | QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Right side - HSV editor
        right_layout = QVBoxLayout()
        
        editor_label = QLabel("Edit Selected Color:")
        editor_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_layout.addWidget(editor_label)
        
        self.hsv_editor = HSVSliderGroup()
        self.hsv_editor.colorChanged.connect(self.on_color_edited)
        right_layout.addWidget(self.hsv_editor)
        
        right_layout.addStretch()
        
        layout.addLayout(right_layout)
        
        # Set initial selection
        if self.colors:
            self.color_list.setCurrentRow(0)
    
    def set_colors(self, colors):
        """Set the color list from external source"""
        self.colors = colors[:]  # Make a copy
        self.update_color_list()
        if self.colors:
            self.color_list.setCurrentRow(0)
    
    def get_colors(self):
        """Get the current color list"""
        return self.colors[:]

    def update_color_list(self):
        """Refresh the color list display"""
        self.color_list.clear()
        self.color_list_items = []
        
        for i, color in enumerate(self.colors):
            # Create custom widget for this color
            item_widget = ColorListItem(i, color)
            
            # Create list item
            list_item = QListWidgetItem()
            list_item.setSizeHint(item_widget.sizeHint())
            
            # Add to list
            self.color_list.addItem(list_item)
            self.color_list.setItemWidget(list_item, item_widget)
            
            self.color_list_items.append(item_widget)
    
    def on_color_selected(self, row):
        """Handle color selection in the list"""
        if 0 <= row < len(self.colors):
            self.current_color_index = row
            self.hsv_editor.set_color(self.colors[row])
    
    def on_color_edited(self, new_color):
        """Handle color being edited in HSV sliders"""
        if 0 <= self.current_color_index < len(self.colors):
            self.colors[self.current_color_index] = new_color
            
            # Update the list item
            if self.current_color_index < len(self.color_list_items):
                self.color_list_items[self.current_color_index].update_color(new_color)
            
            self.colorsChanged.emit(self.colors)

class SimpleColorEditorDialog(QDialog):
    """Dialog wrapper for the simple color editor"""
    
    def __init__(self, initial_colors=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Color Editor")
        self.setModal(True)
        self.resize(700, 500)
        
        self.setup_ui()
        
        if initial_colors:
            self.color_editor.set_colors(initial_colors)
            self.num_colors = len(initial_colors)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Color editor widget
        self.color_editor = SimpleColorListEditor()
        layout.addWidget(self.color_editor)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("Reset to Default")
        self.reset_button.clicked.connect(self.reset_colors)
        button_layout.addWidget(self.reset_button)
        
        button_layout.addStretch()
        
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def reset_colors(self):
        """Reset to default rainbow colors"""
        default_colors = [QColor.fromHsv(i * 360//self.num_colors, 255, 255) for i in range(self.num_colors)]
        self.color_editor.set_colors(default_colors)
    
    def get_colors(self):
        """Get the selected colors"""
        return self.color_editor.get_colors()

class FontSelectionDialog(QDialog):
    """Standalone font selection dialog that emits font information when accepted"""
    
    # Custom signal that emits font name and size
    fontSelected = Signal(str, int)  # font_name, font_size
    
    def __init__(self, initial_font=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Font")
        self.setModal(True)
        self.resize(450, 350)
        
        # Store the selected font info
        self.selected_font_name = ""
        self.selected_font_size = 12
        
        self.setup_ui()
        self.connect_signals()
        
        # Set initial font if provided
        if initial_font:
            self.set_initial_font(initial_font)
        else:
            self.update_font_preview()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        # Font family selection
        font_family_layout = QHBoxLayout()
        font_family_layout.addWidget(QLabel("Font Family:"))
        self.font_combo_box = QFontComboBox(self)
        self.font_combo_box.setWritingSystem(QFontDatabase.WritingSystem.Any)
        font_family_layout.addWidget(self.font_combo_box)
        layout.addLayout(font_family_layout)
        
        # Font size selection
        font_size_layout = QHBoxLayout()
        font_size_layout.addWidget(QLabel("Font Size:"))
        self.size_combo = QComboBox(self)
        self.size_combo.setEditable(True)  # Allow custom sizes
        sizes = [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 32, 36, 48, 72]
        for size in sizes:
            self.size_combo.addItem(str(size))
        self.size_combo.setCurrentText("12")
        font_size_layout.addWidget(self.size_combo)
        layout.addLayout(font_size_layout)
        
        # Current selection info
        self.font_info_label = QLabel("Font: ", self)
        layout.addWidget(self.font_info_label)
        
        # Preview section
        layout.addWidget(QLabel("Preview:"))
        self.preview_text = QTextEdit(self)
        self.preview_text.setText(
            "The quick brown fox jumps over the lazy dog.\n"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ\n"
            "abcdefghijklmnopqrstuvwxyz\n"
            "1234567890 !@#$%^&*()"
        )
        self.preview_text.setMaximumHeight(120)
        layout.addWidget(self.preview_text)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK", self)
        self.cancel_button = QPushButton("Cancel", self)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
        # Set OK as default button
        self.ok_button.setDefault(True)
    
    def connect_signals(self):
        """Connect signals to slots"""
        self.font_combo_box.currentFontChanged.connect(self.update_font_preview)
        self.size_combo.currentTextChanged.connect(self.update_font_preview)
        
        self.ok_button.clicked.connect(self.accept_selection)
        self.cancel_button.clicked.connect(self.reject)
    
    def update_font_preview(self):
        """Update the preview with current font selection"""
        font = self.font_combo_box.currentFont()
        
        # Get size from combo box
        try:
            size = int(self.size_combo.currentText())
            if size <= 0:
                size = 12
        except ValueError:
            size = 12
            self.size_combo.setCurrentText("12")
        
        font.setPointSize(size)
        
        # Update preview
        self.preview_text.setFont(font)
        
        # Update info label
        self.font_info_label.setText(f"Font: {font.family()}, Size: {size}")
        
        # Store current selection
        self.selected_font_name = font.family()
        self.selected_font_size = size
    
    def set_initial_font(self, font):
        """Set the initial font selection"""
        self.font_combo_box.setCurrentFont(font)
        self.size_combo.setCurrentText(str(font.pointSize()))
        self.update_font_preview()
    
    def accept_selection(self):
        """Accept the current selection and emit the signal"""
        self.fontSelected.emit(self.selected_font_name, self.selected_font_size)
        self.accept()
    
    def get_selected_font(self):
        """Get the selected font as a QFont object"""
        font = QFont(self.selected_font_name, self.selected_font_size)
        return font
    
    def get_font_info(self):
        """Get font name and size as tuple"""
        return (self.selected_font_name, self.selected_font_size)

class SliderDialog(QDialog):
    """Simple slider dialog that emits value when accepted"""
    
    # Custom signal that emits the selected value
    valueSelected = Signal(int)  # emits the slider value
    
    def __init__(self, label="Value", min_value=0, max_value=100, initial_value=50, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Value")
        self.setModal(True)
        self.resize(350, 200)
        
        # Store parameters
        self.label_text = label
        self.min_value = min_value
        self.max_value = max_value
        self.selected_value = initial_value
        
        self.setup_ui()
        self.connect_signals()
        
        # Set initial value
        self.slider.setValue(initial_value)
        self.spinbox.setValue(initial_value)
        self.update_display()
    
    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)
        
        # Label
        layout.addWidget(QLabel(self.label_text))
        
        # Slider and spinbox layout
        slider_layout = QHBoxLayout()
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(self.min_value)
        self.slider.setMaximum(self.max_value)
        slider_layout.addWidget(self.slider)
        
        # Spinbox for precise input
        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(self.min_value)
        self.spinbox.setMaximum(self.max_value)
        self.spinbox.setFixedWidth(80)
        slider_layout.addWidget(self.spinbox)
        
        layout.addLayout(slider_layout)
        
        # Current value display
        self.value_label = QLabel()
        layout.addWidget(self.value_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
        # Set OK as default button
        self.ok_button.setDefault(True)
    
    def connect_signals(self):
        """Connect signals to slots"""
        self.slider.valueChanged.connect(self.on_slider_changed)
        self.spinbox.valueChanged.connect(self.on_spinbox_changed)
        
        self.ok_button.clicked.connect(self.accept_selection)
        self.cancel_button.clicked.connect(self.reject)
    
    def on_slider_changed(self, value):
        """Handle slider value changes"""
        self.selected_value = value
        
        # Update spinbox without triggering its signal
        self.spinbox.blockSignals(True)
        self.spinbox.setValue(value)
        self.spinbox.blockSignals(False)
        
        self.update_display()
    
    def on_spinbox_changed(self, value):
        """Handle spinbox value changes"""
        self.selected_value = value
        
        # Update slider without triggering its signal
        self.slider.blockSignals(True)
        self.slider.setValue(value)
        self.slider.blockSignals(False)
        
        self.update_display()
    
    def update_display(self):
        """Update the value display"""
        self.value_label.setText(f"Current Value: {self.selected_value}")
    
    def accept_selection(self):
        """Accept the current selection and emit the signal"""
        self.valueSelected.emit(self.selected_value)
        self.accept()
    
    def get_selected_value(self):
        """Get the selected value"""
        return self.selected_value

class MarkdownViewer(QDialog):
    def __init__(self, markdown_content=None, parent=None):
        super().__init__(parent)
        self.markdown_content = markdown_content
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle('AdinkraWorks Manual')
        self.setGeometry(100, 100, 800, 600)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create QTextEdit for markdown display
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)  # Make it read-only like T&C
        
        # Use provided content or default sample
        if self.markdown_content is None:
            self.markdown_content = """
# AdinkraWorks v1.0 Guide

## 1. Introduction

Welcome to AdinkraWorks! This app is a specialized viewer for Adinkras. 

## 2. How to use:

* Currenly, only importing Adinkras is supported, not creation from scratch. Details on how to write out your own adinkras can be found below.
* Using AdinkraWorks, the user can create Adinkra Libraries, consisting of Theories, further consisting of Adinkras. AdinkraWorks also supports opening multiple libraries at once.
* Adinkras can be manipulated on-screen by clicking on and dragging nodes.
* To pan the viewing window, simply drag around the white space with the mouse.
* To Zoom in and out, hold ctrl/cmd and scroll with the mouse wheel.
* Changing Edge thickness, color, node size, and label size/font is supported via the preferences menu.   
* Export the current Adinkra as an image/vector with option to fit screen view or full view via File > Export Adinkra. 

## 3. Writing Adinkras

* To write an Adinkra from Mathematica or Python, instructions on how to do so can be found in the Adinkra.py module. If using Python, simply import and call Adinkra_to_CSV. If using Mathematica, then the following syntax is necessary:
```
Export["/home/pathto/My_Adinkra_Matrices.csv", {{{Ls, Rs}}}, "CSV"] 
```

With questions or additional thoughts, please contact gabeyerger@gmail.com.
---

*Last updated: October 2025*
"""
        
        # Set markdown content
        self.text_edit.setMarkdown(self.markdown_content)
        
        # Add to layout
        layout.addWidget(self.text_edit)
        
        # Create close button
        close_button = QPushButton('Close')
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)


# Example: How to call from your existing action
@catch_nicely
def show_terms_from_action():
    """
    Call this function from your QAction's triggered signal.
    
    Example usage in your main window:
        terms_action = QAction('Terms and Conditions', self)
        terms_action.triggered.connect(show_terms_from_action)
    
    Or with custom markdown:
        terms_action.triggered.connect(lambda: show_custom_terms(parent=self))
    """
    dialog = MarkdownViewer()
    dialog.exec()

def show_custom_terms(markdown_text=None, parent=None):
    """
    Show terms dialog with custom markdown content.
    
    Args:
        markdown_text: Custom markdown string to display
        parent: Parent widget (usually your main window)
    """
    dialog = MarkdownViewer(markdown_content=markdown_text, parent=parent)
    dialog.exec_()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
