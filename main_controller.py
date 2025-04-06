# Import necessary PyQt6 modules for GUI components
from PyQt6.QtWidgets import QApplication, QMessageBox  # Main app and message dialogs
from PyQt6.QtCore import Qt, QPointF  # Core functionalities and point coordinates
from PyQt6.QtGui import QPen, QColor  # Drawing tools and color management

# Import standard libraries
import math  # For mathematical operations (e.g., sqrt, atan2)
import sys  # System-specific functions and variables

# Import custom modules
from graph_elements import GraphManager, GraphicsNode  # Graph logic and node visualization
from ui_components import MainWindowUI, ResourceDialog, EdgeDialog  # GUI components

class RAGSimulator(MainWindowUI):
    """Main controller class that inherits from the UI and manages application logic"""
    
    def __init__(self):
        """Initialize the simulator"""
        super().__init__()  # Initialize parent UI class
        self.graph_manager = GraphManager()  # Create graph management instance
        self.connect_buttons()  # Set up button event handlers
        self.graph_manager.save_state()  # Save initial empty state

    def connect_buttons(self):
        """Connect UI buttons to their respective functions"""
        self.add_process_btn.clicked.connect(self.add_process)
        self.add_resource_btn.clicked.connect(self.add_resource)
        # Lambda functions for edge dialogs with preset type
        self.request_edge_btn.clicked.connect(lambda: self.show_add_edge_dialog('request')) 
        self.allocation_edge_btn.clicked.connect(lambda: self.show_add_edge_dialog('allocation'))
        self.check_deadlock_btn.clicked.connect(self.check_deadlock)
        self.undo_btn.clicked.connect(self.undo_last_action)

    def add_process(self):
        """Create a new process node"""
        self.graph_manager.process_count += 1  # Increment counter
        name = f"P{self.graph_manager.process_count}"  # Generate ID (P1, P2...)
        # Position nodes in a grid pattern
        x = (self.graph_manager.process_count * 100) % 700  
        y = 100  # Fixed Y position for processes
        node = GraphicsNode(x, y, name, 'process')  # Create visual node
        self.scene.addItem(node)  # Add to graphics scene
        self.graph_manager.nodes[name] = node  # Register in graph manager
        self.graph_manager.graph.add_node(name, node_type='process')  # Add to NetworkX graph
        self.graph_manager.save_state()  # Save current state for undo

    def add_resource(self):
        """Create a new resource node with configurable instances"""
        dialog = ResourceDialog(self)  # Create instance configuration dialog
        if dialog.exec():  # Show dialog and wait for user input
            self.graph_manager.resource_count += 1
            name = f"R{self.graph_manager.resource_count}"  # Generate ID (R1, R2...)
            x = (self.graph_manager.resource_count * 100) % 700
            y = 300  # Fixed Y position for resources
            instances = dialog.instance_spinbox.value()  # Get user-specified instances
            node = GraphicsNode(x, y, name, 'resource', instances)  # Create node
            self.scene.addItem(node)
            self.graph_manager.nodes[name] = node
            # Store instances in graph metadata
            self.graph_manager.graph.add_node(name, node_type='resource', instances=instances)
            self.graph_manager.save_state()

    def show_add_edge_dialog(self, edge_type):
        """Show edge creation dialog and handle results"""
        dialog = EdgeDialog(list(self.graph_manager.nodes.keys()), edge_type, self)
        if dialog.exec():  # If user clicked "Add"
            from_node = dialog.from_combo.text()
            to_node = dialog.to_combo.text()
            instances = dialog.instances_spinbox.value()
            
            # Validate before creation
            if self.validate_edge_creation(from_node, to_node, edge_type, instances):
                self.create_edge(from_node, to_node, edge_type, instances)

    def validate_edge_creation(self, from_node, to_node, edge_type, instances):
        """Validate edge creation parameters"""
        # Check if nodes exist
        if from_node not in self.graph_manager.nodes or to_node not in self.graph_manager.nodes:
            QMessageBox.warning(self, "Error", "Invalid node names!")
            return False

        if edge_type == 'request':
            # Request edges must be Process → Resource
            if not (self.graph_manager.nodes[from_node].node_type == 'process' and 
                   self.graph_manager.nodes[to_node].node_type == 'resource'):
                QMessageBox.warning(self, "Error", 
                    "Request edges must go from Process to Resource!")
                return False
        else:  # allocation
            # Allocation edges must be Resource → Process
            if not (self.graph_manager.nodes[from_node].node_type == 'resource' and 
                   self.graph_manager.nodes[to_node].node_type == 'process'):
                QMessageBox.warning(self, "Error", 
                    "Allocation edges must go from Resource to Process!")
                return False
            
            # Check available instances
            resource_node = self.graph_manager.nodes[from_node]
            if resource_node.available_instances < instances:
                QMessageBox.warning(self, "Error", 
                    f"Only {resource_node.available_instances} instances available!")
                return False
        
        return True  # All validations passed

    def create_edge(self, from_node, to_node, edge_type, instances):
        """Create a validated edge between nodes"""
        if edge_type == 'allocation':
            # Deduct available instances when allocating
            resource_node = self.graph_manager.nodes[from_node]
            resource_node.available_instances -= instances
            resource_node.update()  # Trigger visual update

        # Add edge to graph with metadata
        self.graph_manager.graph.add_edge(
            from_node, 
            to_node, 
            edge_type=edge_type, 
            instances=instances
        )
        self.update_edges()  # Redraw all edges
        self.graph_manager.save_state()  # Save state

    def update_edges(self):
        """Redraw all edges in the graph"""
        # Clear existing edges
        for edge in self.graph_manager.edges:
            self.scene.removeItem(edge)
        self.graph_manager.edges.clear()

        # Draw each edge from the NetworkX graph
        for edge in self.graph_manager.graph.edges(data=True):
            from_node = self.graph_manager.nodes[edge[0]]
            to_node = self.graph_manager.nodes[edge[1]]
            edge_type = edge[2].get('edge_type', 'request')  # Default to request
            instances = edge[2].get('instances', 1)  # Default to 1 instance
            is_deadlock = (edge[0], edge[1]) in self.graph_manager.deadlock_edges

            self.draw_edge(from_node, to_node, edge_type, instances, is_deadlock)

    def draw_edge(self, from_node, to_node, edge_type, instances, is_deadlock):
        """Render an edge with proper styling and arrowheads"""
        # Calculate positions
        start_pos = from_node.pos()
        end_pos = to_node.pos()
        # Center points on nodes
        base_start_x = start_pos.x() + from_node.size/2
        base_start_y = start_pos.y() + from_node.size/2
        base_end_x = end_pos.x() + to_node.size/2
        base_end_y = end_pos.y() + to_node.size/2

        # Set visual properties
        color = QColor(255, 0, 0) if is_deadlock else (
            Qt.GlobalColor.red if edge_type == 'request' else Qt.GlobalColor.green
        )
        pen = QPen(color, 4 if is_deadlock else 2)  # Thicker for deadlocks

        # Calculate edge path geometry
        dx = end_pos.x() - start_pos.x()
        dy = end_pos.y() - start_pos.y()
        length = math.sqrt(dx*dx + dy*dy)
        if length == 0:  # Skip if same node
            return

        # Calculate perpendicular offset for multiple instances
        normal_x = -dy/length * 5  
        normal_y = dx/length * 5

        # Draw each instance (parallel lines for multiple instances)
        for i in range(instances):
            offset = (i - (instances-1)/2)  # Center the bundle
            # Calculate offset positions
            start_x = base_start_x + normal_x * offset
            start_y = base_start_y + normal_y * offset
            end_x = base_end_x + normal_x * offset
            end_y = base_end_y + normal_y * offset

            # Draw main line
            line = self.scene.addLine(start_x, start_y, end_x, end_y, pen)
            self.graph_manager.edges.append(line)

            # Draw arrowhead (triangle)
            arrow_size = 10
            angle = math.atan2(end_y - start_y, end_x - start_x)  # Edge angle
            # Calculate arrow points
            arrow_p1 = QPointF(
                end_x - arrow_size * math.cos(angle - math.pi/6),
                end_y - arrow_size * math.sin(angle - math.pi/6)
            )
            arrow_p2 = QPointF(
                end_x - arrow_size * math.cos(angle + math.pi/6),
                end_y - arrow_size * math.sin(angle + math.pi/6)
            )
            
            # Draw arrow lines
            arrow1 = self.scene.addLine(end_x, end_y, arrow_p1.x(), arrow_p1.y(), pen)
            arrow2 = self.scene.addLine(end_x, end_y, arrow_p2.x(), arrow_p2.y(), pen)
            self.graph_manager.edges.extend([arrow1, arrow2])

    def check_deadlock(self):
        """Check for deadlock conditions in the graph"""
        has_deadlock, message = self.graph_manager.check_deadlock()
        if has_deadlock:
            self.update_edges()  # Redraw with highlights
            QMessageBox.warning(self, "Deadlock Detection", message)
        else:
            QMessageBox.information(self, "Deadlock Detection", message)

    def undo_last_action(self):
        """Revert to the previous graph state"""
        if len(self.graph_manager.history) > 1:  # Must have previous state
            self.graph_manager.history.pop()  # Remove current state
            previous_state = self.graph_manager.history[-1]  # Get previous
            
            # Clear current visualization
            self.scene.clear()
            self.graph_manager.edges.clear()
            self.graph_manager.deadlock_edges.clear()
            
            # Restore graph data
            self.graph_manager.graph = previous_state['graph'].copy()
            self.graph_manager.process_count = previous_state['process_count']
            self.graph_manager.resource_count = previous_state['resource_count']
            self.graph_manager.nodes = {}
            
            # Recreate all nodes
            for name, pos_data in previous_state['node_positions'].items():
                node_type = 'process' if name.startswith('P') else 'resource'
                instances = pos_data[2]
                available_instances = pos_data[3]
                node = GraphicsNode(pos_data[0], pos_data[1], name, node_type, instances)
                node.available_instances = available_instances
                node.is_in_deadlock = False
                self.scene.addItem(node)
                self.graph_manager.nodes[name] = node
            
            self.update_edges()  # Redraw edges

def main():
    """Application entry point"""
    app = QApplication(sys.argv)  # Create Qt application
    window = RAGSimulator()  # Create main window
    window.show()  # Display UI
    sys.exit(app.exec())  # Start event loop

if __name__ == "__main__":
    main()  # Run only when executed directly
