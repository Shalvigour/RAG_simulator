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

    def update_edges(self):
        for edge in self.graph_manager.edges:
            self.scene.removeItem(edge)
        self.graph_manager.edges.clear()

        for edge in self.graph_manager.graph.edges(data=True):
            from_node = self.graph_manager.nodes[edge[0]]
            to_node = self.graph_manager.nodes[edge[1]]
            edge_type = edge[2].get('edge_type', 'request')
            instances = edge[2].get('instances', 1)

            start_pos = from_node.pos()
            end_pos = to_node.pos()
            base_start_x = start_pos.x() + from_node.size/2
            base_start_y = start_pos.y() + from_node.size/2
            base_end_x = end_pos.x() + to_node.size/2
            base_end_y = end_pos.y() + to_node.size/2

            is_deadlock_edge = (edge[0], edge[1]) in self.graph_manager.deadlock_edges

            if is_deadlock_edge:
                color = QColor(255, 0, 0)
            else:
                color = Qt.GlobalColor.red if edge_type == 'request' else Qt.GlobalColor.green

            pen = QPen(color, 2)
            if is_deadlock_edge:
                pen.setWidth(4)

            dx = end_pos.x() - start_pos.x()
            dy = end_pos.y() - start_pos.y()
            length = math.sqrt(dx*dx + dy*dy)
            if length != 0:
                normal_x = -dy/length * 5
                normal_y = dx/length * 5

                for i in range(instances):
                    offset = (i - (instances-1)/2)
                    start_x = base_start_x + normal_x * offset
                    start_y = base_start_y + normal_y * offset
                    end_x = base_end_x + normal_x * offset
                    end_y = base_end_y + normal_y * offset

                    line = self.scene.addLine(start_x, start_y, end_x, end_y, pen)
                    self.graph_manager.edges.append(line)

                    arrow_size = 10
                    angle = math.atan2(end_y - start_y, end_x - start_x)
                    arrow_p1 = QPointF(end_x - arrow_size * math.cos(angle - math.pi/6),
                                     end_y - arrow_size * math.sin(angle - math.pi/6))
                    arrow_p2 = QPointF(end_x - arrow_size * math.cos(angle + math.pi/6),
                                     end_y - arrow_size * math.sin(angle + math.pi/6))
                    
                    arrow1 = self.scene.addLine(end_x, end_y, arrow_p1.x(), arrow_p1.y(), pen)
                    arrow2 = self.scene.addLine(end_x, end_y, arrow_p2.x(), arrow_p2.y(), pen)
                    self.graph_manager.edges.extend([arrow1, arrow2])

    def check_deadlock(self):
        has_deadlock, message = self.graph_manager.check_deadlock()
        if has_deadlock:
            self.update_edges()
            QMessageBox.warning(self, "Deadlock Detection", message)
        else:
            QMessageBox.information(self, "Deadlock Detection", message)

    def undo_last_action(self):
        if len(self.graph_manager.history) > 1:
            self.graph_manager.history.pop()
            previous_state = self.graph_manager.history[-1]
            self.scene.clear()
            self.graph_manager.edges.clear()
            self.graph_manager.deadlock_edges.clear()
            self.graph_manager.graph = previous_state['graph'].copy()
            self.graph_manager.process_count = previous_state['process_count']
            self.graph_manager.resource_count = previous_state['resource_count']
            self.graph_manager.nodes = {}
            for name, pos_data in previous_state['node_positions'].items():
                node_type = 'process' if name.startswith('P') else 'resource'
                instances = pos_data[2]
                available_instances = pos_data[3]
                node = GraphicsNode(pos_data[0], pos_data[1], name, node_type, instances)
                node.available_instances = available_instances
                node.is_in_deadlock = False
                self.scene.addItem(node)
                self.graph_manager.nodes[name] = node
            self.update_edges()

def main():
    app = QApplication(sys.argv)
    window = RAGSimulator()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
