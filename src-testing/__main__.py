import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsEllipseItem, QGraphicsLineItem
from PyQt6.QtGui import QPen, QColor, QBrush
from PyQt6.QtCore import Qt
from SimpleOutput import Ui_MainWindow  # Import the generated UI class
from PyQt6.QtCore import QPointF
import os
import pickle
from icecream import ic 
from PyQt6.QtWidgets import QTreeWidgetItem
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtWidgets import QInputDialog
from Adinkra import Adinkra
from PyQt6.QtWidgets import QPushButton
from rich import print
from PyQt6.QtWidgets import QGraphicsTextItem
from PyQt6.QtGui import QFont

def find_first_adinkra(parent_item):
    for i in range(parent_item.childCount()):
        child = parent_item.child(i)
        if isinstance(child.value, Adinkra):
            return child
    return None  # Not found

class DraggableBoson(QGraphicsEllipseItem):
    def __init__(self, x, y, label="", grid_size_x=100, grid_size_y=400, fontsize=12):
        super().__init__(x - 25, y - 25, 50, 50)  # (x, y, width, height)
        self.setBrush(Qt.GlobalColor.white)
        self.setPen(QPen(Qt.GlobalColor.black))
        self.setFlags(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable |
                      QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.grid_size_x = grid_size_x
        self.grid_size_y = grid_size_y
        self.edges = []  # List of connected edges

        # Add centered text
        self.text_item = QGraphicsTextItem(label, self)  # Add text as child
        self.text_item.setFont(QFont("Arial", fontsize))
        self.text_item.setDefaultTextColor(Qt.GlobalColor.black)
        self.center_text()

    def center_text(self):
        """Center the text in the ellipse."""
        bounding_rect = self.text_item.boundingRect()
        ellipse_rect = self.rect()
        x = ellipse_rect.x() + (ellipse_rect.width() - bounding_rect.width()) / 2
        y = ellipse_rect.y() + (ellipse_rect.height() - bounding_rect.height()) / 2
        self.text_item.setPos(x, y)

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionChange:
            new_x = round(value.x() / self.grid_size_x) * self.grid_size_x
            new_y = round(value.y() / self.grid_size_y) * self.grid_size_y
            return QPointF(new_x, new_y)

        elif change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_position()

        return super().itemChange(change, value)

class DraggableFermion(QGraphicsEllipseItem):
    def __init__(self, x, y, label="", grid_size_x=100, grid_size_y=400, fontsize=12):
        super().__init__(x - 25, y - 25, 50, 50)  # (x, y, width, height)
        self.setBrush(Qt.GlobalColor.black)
        self.setPen(QPen(Qt.GlobalColor.black))
        self.setFlags(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable |
                    QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges)

        self.grid_size_x = grid_size_x
        self.grid_size_y = grid_size_y
        self.edges = []  # List of connected edges

        # Add centered text
        self.text_item = QGraphicsTextItem(label, self)  # Add text as child
        self.text_item.setFont(QFont("Arial", fontsize))
        self.text_item.setDefaultTextColor(Qt.GlobalColor.white)
        self.center_text()

    def center_text(self):
        """Center the text in the ellipse."""
        bounding_rect = self.text_item.boundingRect()
        ellipse_rect = self.rect()
        x = ellipse_rect.x() + (ellipse_rect.width() - bounding_rect.width()) / 2
        y = ellipse_rect.y() + (ellipse_rect.height() - bounding_rect.height()) / 2
        self.text_item.setPos(x, y)

    def itemChange(self, change, value):
        if change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionChange:
            new_x = round(value.x() / self.grid_size_x) * self.grid_size_x
            new_y = round(value.y() / self.grid_size_y) * self.grid_size_y
            return QPointF(new_x, new_y)

        elif change == QGraphicsEllipseItem.GraphicsItemChange.ItemPositionHasChanged:
            for edge in self.edges:
                edge.update_position()

        return super().itemChange(change, value)


class Edge(QGraphicsLineItem):
    def __init__(self, node1, node2, color, dashing):
        super().__init__()
        self.node1 = node1
        self.node2 = node2
        self.color = color
        self.dashing = dashing
        if self.dashing == 1:
            style = Qt.PenStyle.DashLine
        else:
            style = Qt.PenStyle.SolidLine
        
        qcolor = QColor.fromHsv(int(359*color), 255, 255, alpha=255)
        self.setPen(QPen(qcolor, 3, style))
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
        self.fontsize = 24
        # self setup graphics
        self.setupUi(self)
        self.refresh_graph()
        self.graphicsView.scale(0.5, 0.5)  # Zoom out 2x

        # Connect menu actions to functions
        self.actionOpen_Library.triggered.connect(self.open_library_file)
        self.actionClose.triggered.connect(self.close_library)
        self.actionSave_Library.triggered.connect(self.save_library_file)
        self.actionCreate_Theory.triggered.connect(self.add_theory)
        self.actionImportAdinkra.triggered.connect(self.import_adinkra)
        self.actionCreate_Library.triggered.connect(self.new_library)
        self.actionComment.triggered.connect(self.add_comment)
        self.treeWidget.itemSelectionChanged.connect(self.on_item_selected)

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
            
            self.refresh_graph()

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
            self.refresh_graph()

    def refresh_graph(self):
        if self.theory is not None and self.adinkra is not None:
            self.scene = QGraphicsScene()
            self.scene.setSceneRect(0, 0, 2000, 2000)  # Large scene size

            self.graphicsView.setScene(self.scene)
            self.graphicsView.setBackgroundBrush(QBrush(QColor(255, 255, 255, 255)))

            self.draw_graph()
    
    def new_library(self):
        try:
#            if self.library is not None:
                #userpressed = self.show_save_option_box()
                #if userpressed == "Save":
                    #self.save_library_file()
                #elif userpressed == "Don't Save":
                    #pass
                #elif userpressed == "Cancel":
                    #return 0
            #self.reset_library()
            name = self.get_user_input("Creating new Library: Enter Library Name", "Library Name")
            if name:  # If the user pressed OK and entered text
                self.library = TreeNode(name)
                self.treeWidget.addTopLevelItem(self.library)
                self.theory = None
                self.adinkra = None
                QMessageBox.information(self, "Note", f"New Library: {name} created.")
                return 0
            else:
                raise Exception("No name provided for the new library.")
             
        except Exception as e:
            ic(f"Exception Caught: {e}")
            QMessageBox.information(self, "Note", f"No Library Created:\n{str(e)}")
            return 1

    def add_theory(self):
        try:
            """check for existence of a library."""
            if not isinstance(self.library, TreeNode):
                buttonpressed = self.show_create_library_option_box()
                if buttonpressed == "Yes":
                    if self.new_library():
                        raise Exception("Library not created")
                elif buttonpressed == "No":
                    return 0
                elif buttonpressed == "Cancel":
                    return 0
            """Add a new theory to the library."""
            theory_name = self.get_user_input("New Theory in Current Library", "Theory Name")
            if theory_name:
                new_theory = TreeNode(theory_name)
                self.library.addChild(new_theory)
                self.theory = new_theory
                QMessageBox.information(self, "Note", f"New Theory: {theory_name} created.")
            else:
                raise Exception("No name provided for the new theory.")
        except Exception as e:
            ic(f"Exception Caught: {e}")
            QMessageBox.information(self, "Note", f"No Theory Created:\n{str(e)}")
    
    def add_comment(self):
        try:
            pass
        except Exception as e:
            ic(f"Exception Caught: {e}")
            QMessageBox.information(self, "Note", f"No Comment Created:\n{str(e)}")

    def import_adinkra(self):
        try:
            if not isinstance(self.theory, TreeNode):
                if self.add_theory():
                    raise Exception("Theory not created")
            """Add an Adinkra to the library."""
            adinkra = self.open_adinkra_file()
            if adinkra:
                adinkra_name = self.get_user_input("New Adinkra in Current Theory", "Adinkra Name")
                self.adinkra = TreeNode(adinkra_name, value=adinkra)
                self.theory.addChild(self.adinkra)
                self.refresh_graph()
                QMessageBox.information(self, "Note", f"New Adinkra: {adinkra_name} created.")
            else:
                raise Exception("No Adinkra provided.")
        except Exception as e:
            ic(f"Exception Caught: {e}")
            QMessageBox.information(self, "Note", f"No Adinkra Created:\n{str(e)}")

    def draw_graph(self):
        # initialize positions for Fermions and Bosons
        view_rect = self.graphicsView.viewport().rect()  # Visible area in view coordinates
        center_in_view = view_rect.center()  # Center in view coordinates
        center_in_scene = self.graphicsView.mapToScene(center_in_view)
        x_center, y_center = center_in_scene.x(), center_in_scene.y()
        adinkra = self.adinkra.value
        # defined 
        self.nodes = [] 
        self.edges = []
        if isinstance(adinkra, Adinkra):
            if adinkra.node_positions is None:
                adinkra.node_positions = []
                #bosons
                for i in range(adinkra.adinkra_size[0]):
                    adinkra.node_positions.append((x_center - int((adinkra.adinkra_size[0]/2 - i) * 100), y_center - 200 +400*adinkra.boson_elevations[i]))
                #fermions
                for i in range(adinkra.adinkra_size[1]):
                    adinkra.node_positions.append((x_center - int((adinkra.adinkra_size[1]/2 - i) * 100), y_center - 200 + 400*adinkra.fermion_elevations[i]))

            if adinkra.custom_node_labels is None or len(adinkra.custom_node_labels) != adinkra.adinkra_size[0] + adinkra.adinkra_size[1]:
                labels = [str(i) for i in range(adinkra.adinkra_size[0])].extend([str(i) for i in range(adinkra.adinkra_size[1])])
            else:
                labels = adinkra.custom_node_labels
            # Create draggable nodes
            for i, (x, y) in enumerate(adinkra.node_positions[:adinkra.adinkra_size[0]]):
                node = DraggableBoson(x, y, label = labels[i],fontsize=self.fontsize)
                self.nodes.append(node)
            # Create draggable nodes
            for i, (x, y) in enumerate(adinkra.node_positions[adinkra.adinkra_size[0]:]):
                node = DraggableFermion(x, y, label = labels[i],fontsize=self.fontsize)
                self.nodes.append(node)

            # Create edges
            for n, edges in enumerate(adinkra.edges):
                hue_fl = n/adinkra.adinkra_colors
                for nc, (i, j) in enumerate(edges):
                    edge = Edge(self.nodes[i], self.nodes[j+ adinkra.adinkra_size[0]], hue_fl, adinkra.dashing[n,nc])
                    self.scene.addItem(edge)
                    self.edges.append(edge)
            for i, n in enumerate(self.nodes):
                self.scene.addItem(n)

    def open_library_file(self):
        """Open a file dialog and load file contents."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;Adinkra Library (*.pkl)") 
        if not file_path:
            return
        # Check if the file is a .pkl file
        if os.path.splitext(file_path)[1]==".pkl":
            try:
                self.library = TreeNode.load_tree(self.treeWidget, file_path)
                print(f"Opened file: {file_path}")  # Handle data as needed
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file:\n{str(e)}")
        else:
            QMessageBox.warning(self, "Warning", "File type not supported. Please select an Adinkra Library (.pkl) file.")

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
                print(f"Saved file: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")

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
            return 0
        self.reset_library()
        return 0

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
        self.nodes = {}
        self.node_labels = {}
        self.edges = []
        self.refresh_graph()

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


    def show_create_library_option_box(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("No current Library: Create a new one?")
        msg.setText("No current Library: Create a new one?")

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())