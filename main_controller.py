from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPen, QColor
import math
import sys
from graph_elements import GraphManager, GraphicsNode
from ui_components import MainWindowUI, ResourceDialog, EdgeDialog

class RAGSimulator(MainWindowUI):
    def __init__(self):
        super().__init__()
        self.graph_manager = GraphManager()
        self.connect_buttons()
        self.graph_manager.save_state()

    def connect_buttons(self):
        self.add_process_btn.clicked.connect(self.add_process)
        self.add_resource_btn.clicked.connect(self.add_resource)
        self.request_edge_btn.clicked.connect(lambda: self.show_add_edge_dialog('request'))
        self.allocation_edge_btn.clicked.connect(lambda: self.show_add_edge_dialog('allocation'))
        self.check_deadlock_btn.clicked.connect(self.check_deadlock)
        self.undo_btn.clicked.connect(self.undo_last_action)

    def add_process(self):
        self.graph_manager.process_count += 1
        name = f"P{self.graph_manager.process_count}"
        x = (self.graph_manager.process_count * 100) % 700
        y = 100
        node = GraphicsNode(x, y, name, 'process')
        self.scene.addItem(node)
        self.graph_manager.nodes[name] = node
        self.graph_manager.graph.add_node(name, node_type='process')
        self.graph_manager.save_state()

    def add_resource(self):
        dialog = ResourceDialog(self)
        if dialog.exec():
            self.graph_manager.resource_count += 1
            name = f"R{self.graph_manager.resource_count}"
            x = (self.graph_manager.resource_count * 100) % 700
            y = 300
            instances = dialog.instance_spinbox.value()
            node = GraphicsNode(x, y, name, 'resource', instances)
            self.scene.addItem(node)
            self.graph_manager.nodes[name] = node
            self.graph_manager.graph.add_node(name, node_type='resource', instances=instances)
            self.graph_manager.save_state()

    def show_add_edge_dialog(self, edge_type):
        dialog = EdgeDialog(list(self.graph_manager.nodes.keys()), edge_type, self)
        if dialog.exec():
            from_node = dialog.from_combo.text()
            to_node = dialog.to_combo.text()
            instances = dialog.instances_spinbox.value()
            
            if from_node in self.graph_manager.nodes and to_node in self.graph_manager.nodes:
                if edge_type == 'request':
                    if not (self.graph_manager.nodes[from_node].node_type == 'process' and 
                           self.graph_manager.nodes[to_node].node_type == 'resource'):
                        QMessageBox.warning(self, "Error", 
                            "Request edges must go from Process to Resource!")
                        return
                else:
                    if not (self.graph_manager.nodes[from_node].node_type == 'resource' and 
                           self.graph_manager.nodes[to_node].node_type == 'process'):
                        QMessageBox.warning(self, "Error", 
                            "Allocation edges must go from Resource to Process!")
                        return
                    resource_node = self.graph_manager.nodes[from_node]
                    if resource_node.available_instances < instances:
                        QMessageBox.warning(self, "Error", 
                            f"Only {resource_node.available_instances} instances available!")
                        return
                    resource_node.available_instances -= instances
                    resource_node.update()

                self.graph_manager.graph.add_edge(from_node, to_node, edge_type=edge_type, instances=instances)
                self.update_edges()
                self.graph_manager.save_state()
            else:
                QMessageBox.warning(self, "Error", "Invalid node names!")

    

def main():
    app = QApplication(sys.argv)
    window = RAGSimulator()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
