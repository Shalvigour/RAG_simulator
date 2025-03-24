# Resource Allocation Graph Simulator

A graphical tool for simulating and analyzing deadlock scenarios using Resource Allocation Graphs (RAG). This simulator helps in understanding and visualizing deadlock conditions in operating systems, particularly with multiple resource instances.

## Features

- Interactive graphical interface for creating and manipulating RAGs
- Support for multiple resource instances
- Draggable nodes for easy graph organization
- Visual representation of request and allocation edges
- Real-time deadlock detection
- Undo functionality
- Keyboard shortcuts for quick actions

## Requirements

- Python 3.x
- PyQt6==6.6.1
- networkx==3.2.1

## Installation

1. Clone the repository or download the source code
2. Create a virtual environment (recommended):
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
3. Install the required packages:
pip install PyQt6==6.6.1 networkx==3.2.1

## Running the Application

python rag_simulator.py

## Usage

### Adding Nodes

1. **Add Process Node**
   - Click "Add Process" button or press 'P'
   - Process nodes are represented as blue circles

2. **Add Resource Node**
   - Click "Add Resource" button or press 'R'
   - Enter the number of instances for the resource
   - Resource nodes are represented as green squares
   - Shows available/total instances

### Creating Edges

1. **Request Edge**
   - Click "Request Edge" button or press 'Q'
   - Enter source process and target resource
   - Enter number of instances requested
   - Represented by red arrows

2. **Allocation Edge**
   - Click "Allocation Edge" button or press 'A'
   - Enter source resource and target process
   - Enter number of instances to allocate
   - Represented by green arrows

### Other Operations

- **Move Nodes**: Click and drag nodes to reposition them
- **Undo**: Press left arrow key or click "Undo" button
- **Check Deadlock**: Click "Check Deadlock" button or press 'D'

## Keyboard Shortcuts

| Key           | Action                |
|--------------|----------------------|
| P            | Add Process          |
| R            | Add Resource         |
| Q            | Add Request Edge     |
| A            | Add Allocation Edge  |
| D            | Check Deadlock       |
| ←  (Left Arrow) | Undo Last Action    |

## Understanding the Interface

### Node Types
- **Process Nodes**: Blue circles labeled as P1, P2, etc.
- **Resource Nodes**: Green squares labeled as R1, R2, etc.
  - Shows available/total instances (e.g., "3/5")

### Edge Types
- **Request Edges**: Red arrows from process to resource
- **Allocation Edges**: Green arrows from resource to process
- Multiple parallel arrows indicate multiple instances

### Deadlock Detection
- Deadlocked nodes are highlighted in red
- Edges involved in deadlock are shown thicker and in bright red
- A message shows the exact cycle causing the deadlock

## Deadlock Conditions

A deadlock is detected when:
1. Processes are holding some resources
2. Processes are requesting more instances than available
3. A circular wait condition exists

## Example Scenarios

### Basic Deadlock
1. Create two processes (P1, P2) and two resources (R1, R2)
2. Allocate R1 to P1
3. Allocate R2 to P2
4. Create request from P1 to R2
5. Create request from P2 to R1
6. Check for deadlock

### Multiple Instance Deadlock
1. Create processes P1, P2 and resource R1 with 3 instances
2. Allocate 2 instances from R1 to P1
3. Allocate 1 instance from R1 to P2
4. Create request for 2 instances from P2 to R1
5. Check for deadlock

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

