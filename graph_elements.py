from PyQt6.QtWidgets import QGraphicsItem
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor
import networkx as nx
import math

class GraphicsNode(QGraphicsItem):
    def __init__(self, x, y, name, node_type, instances=1):
        super().__init__()
        self.name = name
        self.node_type = node_type
        self.instances = instances
        self.available_instances = instances
        self.setPos(x, y)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.size = 50
        self.is_in_deadlock = False

    def boundingRect(self):
        return QRectF(0, 0, self.size, self.size)

    def paint(self, painter: QPainter, option, widget):
        if self.is_in_deadlock:
            process_color = QColor(255, 100, 100)
            resource_color = QColor(255, 150, 150)
        else:
            process_color = QColor(173, 216, 230)
            resource_color = QColor(144, 238, 144)

        if self.node_type == 'process':
            painter.setBrush(QBrush(process_color))
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawEllipse(0, 0, self.size, self.size)
            painter.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignCenter, self.name)
        else:
            painter.setBrush(QBrush(resource_color))
            painter.setPen(QPen(Qt.GlobalColor.black))
            painter.drawRect(0, 0, self.size, self.size)
            text = f"{self.name}\n({self.available_instances}/{self.instances})"
            painter.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignCenter, text)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            self.scene().parent().update_edges()
        return super().itemChange(change, value)

class GraphManager:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.nodes = {}
        self.edges = []
        self.process_count = 0
        self.resource_count = 0
        self.deadlock_edges = set()
        self.history = []

    def save_state(self):
        state = {
            'graph': self.graph.copy(),
            'nodes': dict(self.nodes),
            'process_count': self.process_count,
            'resource_count': self.resource_count,
            'node_positions': {name: (node.pos().x(), node.pos().y(), 
                                    node.instances if node.node_type == 'resource' else 1,
                                    node.available_instances if node.node_type == 'resource' else 1) 
                             for name, node in self.nodes.items()}
        }
        self.history.append(state)

    def check_deadlock(self):
        self.deadlock_edges.clear()
        for node in self.nodes.values():
            node.is_in_deadlock = False
            node.update()

        resource_status = {}
        for node in self.nodes.values():
            if node.node_type == 'resource':
                resource_status[node.name] = {
                    'total': node.instances,
                    'allocated': 0,
                    'requested': 0,
                    'available': node.available_instances
                }

        for edge in self.graph.edges(data=True):
            from_node, to_node, data = edge
            edge_type = data.get('edge_type')
            instances = data.get('instances', 1)
            
            if edge_type == 'allocation':
                resource_status[from_node]['allocated'] += instances

        allocation_graph = nx.DiGraph()
        for node in self.nodes.values():
            allocation_graph.add_node(node.name)

        for edge in self.graph.edges(data=True):
            from_node, to_node, data = edge
            edge_type = data.get('edge_type')
            instances = data.get('instances', 1)
            
            if edge_type == 'request':
                resource = to_node
                process = from_node
                
                holds_resources = False
                for e in self.graph.edges(data=True):
                    if (e[2].get('edge_type') == 'allocation' and 
                        e[1] == process):
                        holds_resources = True
                        break
                
                if (holds_resources and 
                    resource_status[resource]['available'] < instances):
                    allocation_graph.add_edge(from_node, to_node)
            else:
                allocation_graph.add_edge(from_node, to_node)

        try:
            cycles = list(nx.simple_cycles(allocation_graph))
            if cycles:
                for cycle in cycles:
                    for node_name in cycle:
                        self.nodes[node_name].is_in_deadlock = True
                        self.nodes[node_name].update()

                    for i in range(len(cycle)):
                        from_node = cycle[i]
                        to_node = cycle[(i + 1) % len(cycle)]
                        self.deadlock_edges.add((from_node, to_node))

                cycle_str = "\n".join([" → ".join(cycle) for cycle in cycles])
                return True, f"Deadlock detected!\nCycles found:\n{cycle_str}"
            else:
                return False, "No deadlock detected."
                
        except nx.NetworkXNoCycle:
            return False, "No deadlock detected."
