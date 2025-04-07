# Import necessary PyQt6 modules
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QSpinBox, QPushButton, QLineEdit, QGraphicsScene,
                           QGraphicsView, QMainWindow, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut, QPainter

class ResourceDialog(QDialog):
  #Dialog window to add a new resource with a specified number of instances.
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Resource") # Window title
        layout = QVBoxLayout(self)  # Main vertical layout
      
      # Layout for specifying the number of resource instances
        instance_layout = QHBoxLayout() # Horizontal layout for instance input
        instance_layout.addWidget(QLabel("Number of instances:")) # Label
        self.instance_spinbox = QSpinBox()  # Number input
        self.instance_spinbox.setMinimum(1)
        self.instance_spinbox.setMaximum(99)
        self.instance_spinbox.setValue(1)
        instance_layout.addWidget(self.instance_spinbox)
        layout.addLayout(instance_layout)
       # Button to confirm adding the resource
        add_button = QPushButton("Add")
        add_button.clicked.connect(self.accept)  # Close dialog on click
        layout.addWidget(add_button)

class EdgeDialog(QDialog):
  #Dialog window for adding edges between nodes (processes and resources).
    def __init__(self, nodes, edge_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Add {edge_type.capitalize()} Edge") # Dynamic title based on edge type
        layout = QVBoxLayout(self)
       # Layout for specifying the source node
        from_layout = QHBoxLayout()
      # Input field for "From" node
        from_layout.addWidget(QLabel("From:"))
        self.from_combo = QLineEdit()
        from_layout.addWidget(self.from_combo)
        layout.addLayout(from_layout)
       # Input field for "To" node
        to_layout = QHBoxLayout()
    
        to_layout.addWidget(QLabel("To:"))
        self.to_combo = QLineEdit()
        to_layout.addWidget(self.to_combo)
        layout.addLayout(to_layout)
      
       # SpinBox to set number of instances (can be multiple)
        instances_layout = QHBoxLayout()
        instances_layout.addWidget(QLabel("Number of instances:"))
        self.instances_spinbox = QSpinBox()
        self.instances_spinbox.setMinimum(1)
        self.instances_spinbox.setMaximum(99)
        self.instances_spinbox.setValue(1)
        instances_layout.addWidget(self.instances_spinbox)
        layout.addLayout(instances_layout)
      
      # Hint to help users understand valid connections
        hint_text = ("Note: Request edges must go from Process to Resource"
                    if edge_type == 'request' else
                    "Note: Allocation edges must go from Resource to Process")
        hint_label = QLabel(hint_text)
        layout.addWidget(hint_label)

      # Add button to confirm edge creation
      
        add_button = QPushButton("Add")
        add_button.clicked.connect(self.accept)
        layout.addWidget(add_button)
# Main Application Window UI 
class MainWindowUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Resource Allocation Graph Simulator")# Main window title
        self.setGeometry(100, 100, 800, 600) # Window size and position
        # Set up the main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
         # Graphics scene and view (for drawing the graph)
        self.scene = QGraphicsScene()
        self.scene.setParent(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        layout.addWidget(self.view)

      # Create buttons panel at the bottom
        self.create_button_panel(layout)

    # Create UI buttons and shortcuts
    def create_button_panel(self, layout):
        button_panel = QHBoxLayout()
         # Add Process button with keyboard shortcut (P)
        self.add_process_btn = QPushButton("Add Process (P)")
        QShortcut(QKeySequence("P"), self).activated.connect(self.add_process)
        button_panel.addWidget(self.add_process_btn)
        # Add Resource button with shortcut (R)
        self.add_resource_btn = QPushButton("Add Resource (R)")
        QShortcut(QKeySequence("R"), self).activated.connect(self.add_resource)
        button_panel.addWidget(self.add_resource_btn)
         # Add Request Edge button with shortcut (Q)
        self.request_edge_btn = QPushButton("Request Edge (Q)")
        QShortcut(QKeySequence("Q"), self).activated.connect(lambda: self.show_add_edge_dialog('request'))
        button_panel.addWidget(self.request_edge_btn)
        # Add Allocation Edge button with shortcut (A)
        self.allocation_edge_btn = QPushButton("Allocation Edge (A)")
        QShortcut(QKeySequence("A"), self).activated.connect(lambda: self.show_add_edge_dialog('allocation'))
        button_panel.addWidget(self.allocation_edge_btn)
     # Check Deadlock button with shortcut (D)
        self.check_deadlock_btn = QPushButton("Check Deadlock (D)")
        QShortcut(QKeySequence("D"), self).activated.connect(self.check_deadlock)
        button_panel.addWidget(self.check_deadlock_btn)
  # Undo last action button with Left Arrow shortcut
        self.undo_btn = QPushButton("Undo (←)")
        QShortcut(QKeySequence(Qt.Key.Key_Left), self).activated.connect(self.undo_last_action)
        button_panel.addWidget(self.undo_btn)

        # Add the button panel to the main layout
        layout.addLayout(button_panel)
