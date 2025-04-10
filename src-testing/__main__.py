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

def find_first_adinkra(parent_item):
    for i in range(parent_item.childCount()):
        child = parent_item.child(i)
        if isinstance(child.value, Adinkra):
            return child
    return None  # Not found

class DraggableBoson(QGraphicsEllipseItem):
    def __init__(self, x, y, grid_size_x=100, grid_size_y=800):
        super().__init__(x, y, 50, 50)  # (x, y, width, height)
        self.setBrush(Qt.GlobalColor.white)
        self.setPen(QPen(Qt.GlobalColor.black))
        self.setFlags(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable |
                      QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.grid_size_x = grid_size_x
        self.grid_size_y = grid_size_y
        self.edges = []  # List of edges connected to this node

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
    def __init__(self, x, y, grid_size_x=100, grid_size_y=800):
        super().__init__(x, y, 50, 50)  # (x, y, width, height)
        self.setBrush(Qt.GlobalColor.black)
        self.setPen(QPen(Qt.GlobalColor.black))
        self.setFlags(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsMovable |
                      QGraphicsEllipseItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.grid_size_x = grid_size_x
        self.grid_size_y = grid_size_y
        self.edges = []  # List of edges connected to this node

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
        # self setup graphics
        self.setupUi(self)
        self.refresh_graph()

        # Connect menu actions to functions
        self.actionOpen_Library.triggered.connect(self.open_library_file)
        self.actionSave_Library.triggered.connect(self.save_library_file)
        self.actionCreate_Theory.triggered.connect(self.add_theory)
        self.actionImportAdinkra.triggered.connect(self.import_adinkra)
        self.actionComment.triggered.connect(self.add_comment)
        self.actionLagrangian.triggered.connect(self.add_lagrangian)
        self.actionEquations_of_Motion.triggered.connect(self.add_equations_of_motion)
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
            self.refresh_graph()

        elif isinstance(selected_item, TreeNode):
            # Access the theory node level
            # Ensure it's not the root node
            if not selected_item.parent():
                return
            # Traverse up to the theory node. if no parent, then we are at the root node. 
            theory = selected_item
            while theory.parent() and theory.parent().parent():
                theory = theory.parent()
            self.theory = theory
            self.adinkra = find_first_adinkra(theory)
            self.refresh_graph()

    def refresh_graph(self):
        if self.theory is not None and self.adinkra is not None:
            self.scene = QGraphicsScene()
            self.scene.setSceneRect(0, 0, 2000, 2000)  # Large scene size

            self.graphicsView.setScene(self.scene)
            self.graphicsView.setBackgroundBrush(QBrush(QColor(255, 255, 255, 255)))
            self.graphicsView.scale(0.5, 0.5)  # Zoom out 2x

            # defined 
            self.nodes = []
            self.edges = []
            self.draw_graph()
    
    def new_library(self):
        try:
            if self.library is not None:
                userpressed = self.show_save_option_box()
                if userpressed == "Save":
                    self.save_library_file()
                elif userpressed == "Don't Save":
                    pass
                elif userpressed == "Cancel":
                    return 0
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

    def add_lagrangian(self):
        try:
            pass
        except Exception as e:
            ic(f"Exception Caught: {e}")
            QMessageBox.information(self, "Note", f"No Lagrangian Created:\n{str(e)}")

    def add_equations_of_motion(self):
        try:
            pass
        except Exception as e:
            ic(f"Exception Caught: {e}")
            QMessageBox.information(self, "Note", f"No Equations of Motion Created:\n{str(e)}")
    
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
        if isinstance(adinkra, Adinkra):
            print("self.adinkra.value is an Adinkra object.")
            boson_positions = []
            fermion_positions = []
            #bosons
            for i in range(adinkra.adinkra_size[0]):
                boson_positions.append((x_center+1400 - int((adinkra.adinkra_size[0]/2 + i) * 100), y_center+400*adinkra.boson_elevations[i]))
            # Create draggable nodes
            for x, y in boson_positions:
                node = DraggableBoson(x, y)
                self.scene.addItem(node)
                self.nodes.append(node)
            #fermions
            for i in range(adinkra.adinkra_size[1]):
                fermion_positions.append((x_center+1400 - int((adinkra.adinkra_size[1]/2 + i) * 100), y_center + 400*adinkra.fermion_elevations[i]))
            # Create draggable nodes
            for x, y in fermion_positions:
                node = DraggableFermion(x, y)
                self.scene.addItem(node)
                self.nodes.append(node)

            # Create edges
            for n, edges in enumerate(adinkra.edges):
                hue_fl = n/adinkra.adinkra_colors
                for nc, (i, j) in enumerate(edges):
                    edge = Edge(self.nodes[i], self.nodes[j+ adinkra.adinkra_size[0]], hue_fl, adinkra.dashing[n,nc])
                    self.scene.addItem(edge)
                    self.edges.append(edge)

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
        if not hasattr(self, 'library'):
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
                print(adinkra)
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