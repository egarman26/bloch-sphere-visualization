from drafter import *
from dataclasses import dataclass, field
import numpy as np
from typing import Literal

type Axis = Literal["X", "Y", "Z"]

@dataclass
class State:
    X_coordinate: float
    Y_coordinate: float
    Z_coordinate: float
    gate_history: list[Gate]
    background_color: str
    Sphere_shown: bool
    show_notation: bool

@dataclass
class Gate:
    name: str
    description: str 
    gate_type: str 

GATES = {
    "X": Gate("X", "Pauli-X Gate", "Pauli"),
    "Y": Gate("Y", "Pauli-Y Gate", "Pauli"),
    "Z": Gate("Z", "Pauli-Z Gate", "Pauli"),
    "H": Gate("H", "Hadamard Gate", "Hadamard"),
    "S": Gate("S", "Phase Gate", "Phase"),
    "T": Gate("T", "T Gate", "Phase"),
    "RX": Gate("RX", "Rotation around the X-axis", "Rotation"),
    "RY": Gate("RY", "Rotation around the Y-axis", "Rotation"),
    "RZ": Gate("RZ", "Rotation around the Z-axis", "Rotation")
}

@route
def index(state: State) -> Page:
    return Page(state, [
        Header("Qubit Simulator"),
        Paragraph("Welcome to the Quantum Simulator!"),
        Button("Open Simulator", "simulator")
    ])

# brings to main simulator page
@route
def simulator(state: State) -> Page:
    return Page(state, [
        Header("Qubit Simulator"),

        Header("Bloch Sphere", 2),
        Paragraph("Your Bloch sphere visualization will appear here."),

        HorizontalRule(),

        Header("Standard Gates", 2),
        Row([
            Button("X", "apply_gate", [Argument("gate_name", "X")]),
            Button("Y", "apply_gate", [Argument("gate_name", "Y")]),
            Button("Z", "apply_gate", [Argument("gate_name", "Z")]),
        ]),
        Row([
            Button("H", "apply_gate", [Argument("gate_name", "H")]),
            Button("S", "apply_gate", [Argument("gate_name", "S")]),
            Button("T", "apply_gate", [Argument("gate_name", "T")])
        ]),

        HorizontalRule(),

        Header("Rotation Gates", 2),
        Paragraph("Select a rotation axis:"),
        SelectBox("rotation_axis", ["RX", "RY", "RZ"]),

        Paragraph("Rotation angle (degrees):"),
        TextBox("rotation_angle", 90, "number"),

        Button("Apply Rotation", "simulator"),

        HorizontalRule(),

        Header("Simulator Controls", 2),
        Button("Undo", "undo_gate"),
        Button("Reset", "reset"),
        Button("Gate History", "gate_history"),

        HorizontalRule(),

        Button("Help", "help"),
        Button("Settings", "settings"),

        Button("Home", "index")
    ])

# applies chosen gate
@route
def apply_gate(state: State, gate_name: str, rotation_axis: str = "RX", rotation_angle: float = 90.0) -> Page:
    
    selected_gate = GATES[gate_name]
    state.gate_history.append(selected_gate)

    if gate_name == "X":
        apply_pauli_x(state)
    elif gate_name == "Y":
        apply_pauli_y(state)
    elif gate_name == "Z":
        apply_pauli_z(state)
    elif gate_name == "S":
        apply_s_gate(state)
    elif gate_name == "T":
        apply_t_gate(state)
    elif gate_name == "H":
        apply_hadamard(state)
    elif gate_name in ("RX", "RY", "RZ"):
        rotation_axes: dict[str, Axis] = {
            "RX": "X",
            "RY": "Y",
            "RZ": "Z"
        }
        rotation_axis = rotation_axes[gate_name]
        apply_rotation(state, rotation_axis, rotation_angle * np.pi / 180)

    return Page(state, [
        Header(selected_gate.name),
        Paragraph(selected_gate.description),
        Paragraph(selected_gate.gate_type),
        Button("Back to Simulator", "simulator")
    ])

# Shows the help page
@route
def help(state: State) -> Page:
    return Page(state, [
        Header("Help"),
        Paragraph("Learn about quantum gates."),
        Button("Home", "index")
    ])

# Show the history of all gates used on the Qubit
@route
def gate_history(state: State) -> Page:
    content = [
        Header("Gate History")
    ]

    for gate in state.gate_history:
        content.append(Paragraph(gate.name + " - " + gate.description))

    content.append(Button("Back to Simulator", "simulator"))

    return Page(state, content)

# Undoes the previous gate called
@route
def undo_gate(state: State) -> Page:
    if state.gate_history:
        state.gate_history.pop()

    return Page(state, [
        Header("Undo"),
        Paragraph("Most recent gate removed from history."),
        Button("Back to Simulator", "simulator")
    ])

# shows settings page
@route
def settings(state: State) -> Page:
    return Page(state, [
        Header("Settings"),
        Paragraph("Configure your simulator."),
        Button("Home", "index")
    ])

# When called Bloch Sphere will reset to original state
@route
def reset(state: State) -> Page:
    state.X_coordinate = 0.0
    state.Y_coordinate = 0.0
    state.Z_coordinate = 1.0
    state.gate_history.clear()

    return Page(state, [
        Header("Simulator Reset"),
        Paragraph("Qubit returned to its initial state."),
        Button("Back to Simulator", "simulator")
    ])

def apply_pauli_x(state: State) -> State:
    state.Y_coordinate *= -1
    state.Z_coordinate *= -1
    return state

def apply_pauli_y(state: State) -> State:
    state.X_coordinate *= -1
    state.Z_coordinate *= -1
    return state

def apply_pauli_z(state: State) -> State:
    state.X_coordinate *= -1
    state.Y_coordinate *= -1
    return state

def apply_hadamard(state: State) -> State:
    state.X_coordinate, state.Z_coordinate = state.Z_coordinate, state.X_coordinate
    state.Y_coordinate *= -1
    return state 

def apply_phase_gate(state: State, angle: float) -> State:
    original_x = state.X_coordinate
    original_y = state.Y_coordinate

    new_x = original_x * np.cos(angle) - original_y * np.sin(angle)
    new_y = original_x * np.sin(angle) + original_y * np.cos(angle)

    state.X_coordinate = new_x
    state.Y_coordinate = new_y

    return state


def apply_rotation(state: State, axis: Axis, angle: float) -> State:

    rotation_matrices = {
        "X": np.array([
        [1, 0, 0],
        [0, np.cos(angle), -np.sin(angle)],
        [0, np.sin(angle), np.cos(angle)]
        ]),
        "Y": np.array([
        [np.cos(angle), 0, np.sin(angle)],
        [0, 1, 0],
        [-np.sin(angle), 0, np.cos(angle)]
        ]),
        "Z": np.array([
        [np.cos(angle), -np.sin(angle), 0],
        [np.sin(angle), np.cos(angle), 0],
        [0, 0, 1]
        ]) 
    }

    coordinates = np.array([state.X_coordinate, state.Y_coordinate, state.Z_coordinate])

    new_coordinates = rotation_matrices[axis] @ coordinates 

    state.X_coordinate = new_coordinates[0]
    state.Y_coordinate = new_coordinates[1]
    state.Z_coordinate = new_coordinates[2]

    return state
    
def apply_s_gate(state: State) -> State:
    return apply_rotation(state, "Z", np.pi / 2)

def apply_t_gate(state: State) -> State:
    return apply_rotation(state, "Z", np.pi / 4)


start_server(State(
    X_coordinate=0.0,
    Y_coordinate=0.0,
    Z_coordinate=1.0,
    gate_history=[],
    background_color="white",
    Sphere_shown=True,
    show_notation=True
))
