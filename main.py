from dataclasses import dataclass
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
from bakery import assert_equal
from drafter import *

set_website_title("Qubit Visualization")
set_site_information(
    author="Evan Garman",
    description="Allows the user to visual what happens to a qubit after applying different quantum gates",
    sources="Thanks Drafter Doc and ChatGPT",
    planning=["Planning.pdf"],
    links=[]
)
hide_debug_information()
set_website_framed(False)

type Axis = Literal["X", "Y", "Z"]

@dataclass
class Gate:
    """Store the information needed to describe an applied quantum gate.

    Parameters:
    name (str): The short name of the gate.
    description (str): A readable explanation of the gate.
    gate_type (str): The category the gate belongs to.
    rotation_angle (float | None): The applied angle for rotation gates.

    Returns:
    None: This dataclass stores gate information.
    """

    name: str
    description: str
    gate_type: str
    rotation_angle: float | None = None


@dataclass
class State:
    """Store the simulator's qubit, history, and display settings.

    Parameters:
    coordinates (np.ndarray): The current Bloch-sphere coordinates.
    coordinate_history (list[np.ndarray]): Previous qubit coordinates.
    gate_history (list[Gate]): The gates applied to the qubit.
    background_color (str): The website and plot background color.
    sphere_shown (bool): Whether the Bloch sphere is displayed.
    show_notation (bool): Whether state-vector notation is displayed.

    Returns:
    None: This dataclass stores the simulator's current state.
    """

    coordinates: np.ndarray
    coordinate_history: list[np.ndarray]
    gate_history: list[Gate]
    background_color: str
    sphere_shown: bool
    show_notation: bool


GATES: dict[str, Gate] = {
    "X": Gate("X", "Pauli-X Gate", "Pauli"),
    "Y": Gate("Y", "Pauli-Y Gate", "Pauli"),
    "Z": Gate("Z", "Pauli-Z Gate", "Pauli"),
    "H": Gate("H", "Hadamard Gate", "Hadamard"),
    "S": Gate("S", "Phase Gate", "Phase"),
    "T": Gate("T", "T Gate", "Phase"),
    "RX": Gate("RX", "Rotation around the X-axis", "Rotation"),
    "RY": Gate("RY", "Rotation around the Y-axis", "Rotation"),
    "RZ": Gate("RZ", "Rotation around the Z-axis", "Rotation"),
}

ROTATION_AXES: dict[str, Axis] = {
    "RX": "X",
    "RY": "Y",
    "RZ": "Z",
}
BACKGROUND_COLORS = ["white", "lightblue", "lightgray", "lavender"]
INITIAL_COORDINATES = np.array([0.0, 0.0, 1.0])


def create_page(state: State, content: list) -> Page:
    """Create a full page using the selected website background color.

    Parameters:
    state (State): The current simulator state.
    content (list): The components and text to display on the page.

    Returns:
    Page: A Drafter page carrying the state and styled content.
    """
    css = f"""
    #drafter-body-- {{
        background-color: {state.background_color};
    }}
    """
    return Page(state, content, css=css)


def create_simulator_display(state: State, message: str) -> list:
    """Build the portion of the simulator that changes after gate operations.

    Parameters:
    state (State): The current simulator state.
    message (str): Feedback describing the latest simulator operation.

    Returns:
    list: Components showing the plot, notation, and operation feedback.
    """
    if state.sphere_shown:
        draw_bloch_sphere(state)
        plot_display = MatPlotLibPlot()
    else:
        plot_display = Paragraph("The Bloch sphere is currently hidden.")

    if state.show_notation:
        notation_display = Paragraph(get_state_notation(state))
    else:
        notation_display = Paragraph("")

    return [
        Header("Bloch Sphere", 2),
        plot_display,
        notation_display,
        Paragraph(message),
    ]


@route
def index(state: State) -> Page:
    """Display the simulator's home page.

    Parameters:
    state (State): The current simulator state.

    Returns:
    Page: The themed home page with a link to the simulator.
    """
    return create_page(state, [
        Header("Qubit Simulator"),
        Paragraph("Welcome to the Quantum Simulator!"),
        Button("Open Simulator", "simulator"),
    ])


@route
def simulator(state: State) -> Page:
    """Display the Bloch sphere, gate controls, and simulator navigation.

    Parameters:
    state (State): The current simulator state.

    Returns:
    Page: The complete simulator interface.
    """
    return create_page(state, [
        Header("Qubit Simulator"),
        Output(
            "simulator_display",
            create_simulator_display(state, "Ready to apply a gate."),
        ),
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
            Button("T", "apply_gate", [Argument("gate_name", "T")]),
        ]),
        HorizontalRule(),
        Header("Rotation Gates", 2),
        Paragraph("Select a rotation axis:"),
        SelectBox("rotation_axis", ["RX", "RY", "RZ"]),
        Paragraph("Rotation angle (degrees):"),
        TextBox("rotation_angle", "90", "text"),
        Button("Apply Rotation", "apply_rotation_gate"),
        HorizontalRule(),
        Header("Simulator Controls", 2),
        Button("Undo", "undo_gate"),
        Button("Reset", "reset"),
        Button("Gate History", "gate_history"),
        HorizontalRule(),
        Button("Help", "help"),
        Button("Settings", "settings"),
        Button("Home", "index"),
    ])


@route
def apply_gate(state: State, gate_name: str) -> Fragment:
    """Apply a standard gate and refresh the simulator display region.

    Parameters:
    state (State): The current simulator state.
    gate_name (str): The name of the standard gate to apply.

    Returns:
    Fragment: Updated simulator display content, or an invalid-gate message.
    """
    if gate_name not in GATES or gate_name in ROTATION_AXES:
        message = "That gate is not recognized. Select a listed standard gate."
        return Fragment(
            state,
            create_simulator_display(state, message),
            target="#simulator_display",
        )

    selected_gate = GATES[gate_name]
    state.coordinate_history.append(state.coordinates.copy())
    state.gate_history.append(selected_gate)

    gate_functions = {
        "X": apply_pauli_x,
        "Y": apply_pauli_y,
        "Z": apply_pauli_z,
        "H": apply_hadamard,
        "S": apply_s_gate,
        "T": apply_t_gate,
    }
    gate_functions[gate_name](state)

    return Fragment(
        state,
        create_simulator_display(
            state, f"Applied {selected_gate.name}: {selected_gate.description}"
        ),
        target="#simulator_display",
    )


@route
def apply_rotation_gate(
    state: State,
    rotation_axis: str,
    rotation_angle: str,
) -> Fragment:
    """Validate and apply a rotation gate entered in the simulator.

    Parameters:
    state (State): The current simulator state.
    rotation_axis (str): The selected rotation gate, RX, RY, or RZ.
    rotation_angle (str): The angle entered by the user in degrees.

    Returns:
    Fragment: Updated simulator display or a helpful validation message.
    """
    error_message = validate_rotation_input(rotation_axis, rotation_angle)
    if error_message:
        return Fragment(
            state,
            create_simulator_display(state, error_message),
            target="#simulator_display",
        )

    angle_degrees = float(rotation_angle)
    gate_info = GATES[rotation_axis]
    selected_gate = Gate(
        gate_info.name,
        gate_info.description,
        gate_info.gate_type,
        angle_degrees,
    )

    state.coordinate_history.append(state.coordinates.copy())
    state.gate_history.append(selected_gate)
    apply_rotation(
        state,
        ROTATION_AXES[rotation_axis],
        np.deg2rad(angle_degrees),
    )

    return Fragment(
        state,
        create_simulator_display(
            state,
            f"Applied {rotation_axis} rotation of {angle_degrees:g} degrees.",
        ),
        target="#simulator_display",
    )


def validate_rotation_input(rotation_axis: str, rotation_angle: str) -> str:
    """Check the axis and angle before changing the qubit state.

    Parameters:
    rotation_axis (str): The selected rotation gate name.
    rotation_angle (str): The angle entered by the user.

    Returns:
    str: An error message, or an empty string when the input is valid.
    """
    if rotation_axis not in ROTATION_AXES:
        return "Choose a valid rotation axis: RX, RY, or RZ."
    if not rotation_angle or not rotation_angle.strip():
        return "Enter a rotation angle before applying the gate."

    try:
        angle = float(rotation_angle)
    except (TypeError, ValueError):
        return "The rotation angle must be a number."

    if not np.isfinite(angle):
        return "Enter a finite number for the rotation angle."
    return ""


@route
def help(state: State) -> Page:
    """Display explanations of qubits, the Bloch sphere, and gate controls.

    Parameters:
    state (State): The current simulator state.

    Returns:
    Page: The themed help page.
    """
    return create_page(state, [
        Header("Help"),
        Header("What is a Qubit?", 2),
        Paragraph(
            "A qubit is the basic unit of quantum information. Unlike a "
            "classical bit, which is either 0 or 1, a qubit can be in a "
            "superposition of the two computational basis states."
        ),
        Paragraph("|ψ⟩ = α|0⟩ + β|1⟩"),
        Paragraph(
            "Alpha and beta are probability amplitudes. Their squared "
            "magnitudes give the probabilities of measuring 0 and 1, "
            "and those probabilities add up to 1."
        ),
        HorizontalRule(),
        Header("Understanding the Bloch Sphere", 2),
        Paragraph(
            "The Bloch sphere represents the state of a pure single qubit "
            "as a point on its surface. The north pole is |0⟩ and the "
            "south pole is |1⟩. The X, Y, and Z coordinates describe "
            "the direction of the state vector."
        ),
        Paragraph(
            "The Z coordinate determines computational-basis measurement "
            "probabilities: P(0) = (1 + z) / 2 and P(1) = (1 - z) / 2. "
            "The equator therefore gives equal probabilities."
        ),
        Paragraph(
            "The simulator displays pure states. A general mixed state "
            "would be represented inside the sphere rather than only "
            "on its surface."
        ),
        HorizontalRule(),
        Header("Understanding Quantum Gates", 2),
        Paragraph(
            "Quantum gates transform a qubit's state. The simulator "
            "represents their effects as transformations of the "
            "Bloch-sphere coordinates."
        ),
        Header("Pauli Gates", 3),
        Paragraph(
            "X, Y, and Z are 180-degree rotations around their respective "
            "axes. The X gate swaps the north and south poles; its effect "
            "on other states is a rotation around X."
        ),
        Header("Hadamard Gate", 3),
        Paragraph(
            "The Hadamard gate maps |0⟩ to an equal superposition of |0⟩ "
            "and |1⟩. It also transforms other states by exchanging the "
            "X and Z coordinates and reversing Y."
        ),
        Header("Phase Gates", 3),
        Paragraph(
            "S and T change relative phase without changing computational- "
            "basis measurement probabilities. S rotates the Bloch vector "
            "90 degrees around Z; T rotates it 45 degrees around Z."
        ),
        Header("Rotation Gates", 3),
        Paragraph(
            "RX, RY, and RZ rotate the state around the selected axis. "
            "Enter an angle in degrees. Positive and negative angles are "
            "accepted, as are angles larger than one full turn."
        ),
        HorizontalRule(),
        Header("Using the Simulator", 2),
        Paragraph("Select a standard gate or choose an axis and angle."),
        Paragraph(
            "Undo reverses the most recently applied gate. Reset returns "
            "the qubit to |0⟩ and clears both histories."
        ),
        Paragraph(
            "Gate History lists applied operations. Settings controls "
            "the background, Bloch sphere visibility, and state notation."
        ),
        HorizontalRule(),
        Button("Back to Simulator", "simulator"),
        Button("Home", "index"),
    ])


@route
def gate_history(state: State) -> Page:
    """Display the ordered list of gates applied to the qubit.

    Parameters:
    state (State): The current simulator state.

    Returns:
    Page: The gate history page, including an empty-history message.
    """
    content = [Header("Gate History")]
    if not state.gate_history:
        content.append(Paragraph("No gates have been applied yet."))
    else:
        for number, gate in enumerate(state.gate_history, start=1):
            description = f"{number}. {gate.name} - {gate.description}"
            if gate.rotation_angle is not None:
                description += f" ({gate.rotation_angle:g} degrees)"
            content.append(Paragraph(description))

    content.append(Button("Back to Simulator", "simulator"))
    return create_page(state, content)


@route
def undo_gate(state: State) -> Fragment:
    """Undo the latest gate and refresh the simulator display.

    Parameters:
    state (State): The current simulator state.

    Returns:
    Fragment: The refreshed simulator display and an undo status message.
    """
    if state.coordinate_history and state.gate_history:
        state.coordinates = state.coordinate_history.pop()
        removed_gate = state.gate_history.pop()
        message = f"Undid the {removed_gate.name} gate."
    else:
        message = "There are no gates to undo."

    return Fragment(
        state,
        create_simulator_display(state, message),
        target="#simulator_display",
    )


@route
def settings(state: State) -> Page:
    """Display controls for the simulator's appearance and visible content.

    Parameters:
    state (State): The current simulator state.

    Returns:
    Page: The themed settings page.
    """
    return create_page(state, [
        Header("Settings"),
        Paragraph("Background Color:"),
        SelectBox(
            "background_color", BACKGROUND_COLORS, state.background_color
        ),
        Paragraph("Show Bloch Sphere:"),
        CheckBox("sphere_shown", state.sphere_shown),
        Paragraph("Show State Notation:"),
        CheckBox("show_notation", state.show_notation),
        Button("Save Settings", "save_settings"),
        Button("Back to Simulator", "simulator"),
    ])


@route
def save_settings(
    state: State,
    background_color: str,
    sphere_shown: bool,
    show_notation: bool,
) -> Page:
    """Validate and save display preferences, then return to the simulator.

    Parameters:
    state (State): The current simulator state.
    background_color (str): The selected website background color.
    sphere_shown (bool): Whether the Bloch sphere should be displayed.
    show_notation (bool): Whether state notation should be displayed.

    Returns:
    Page: The simulator page with the saved display preferences.
    """
    if background_color in BACKGROUND_COLORS:
        state.background_color = background_color
    state.sphere_shown = sphere_shown
    state.show_notation = show_notation
    return simulator(state)


@route
def reset(state: State) -> Fragment:
    """Restore the initial qubit state and clear both operation histories.

    Parameters:
    state (State): The current simulator state.

    Returns:
    Fragment: The refreshed simulator display and reset confirmation.
    """
    state.coordinates = INITIAL_COORDINATES.copy()
    state.coordinate_history.clear()
    state.gate_history.clear()
    return Fragment(
        state,
        create_simulator_display(
            state, "The qubit was reset to its initial state."
        ),
        target="#simulator_display",
    )


def apply_gate_matrix(state: State, matrix: np.ndarray) -> State:
    """Transform the qubit coordinates using a three-by-three matrix.

    Parameters:
    state (State): The current simulator state.
    matrix (np.ndarray): The matrix applied to the Bloch coordinates.

    Returns:
    State: The state containing the transformed coordinates.
    """
    state.coordinates = matrix @ state.coordinates
    return state


def get_rotation_matrix(axis: Axis, angle: float) -> np.ndarray:
    """Build a Bloch-sphere rotation matrix for the selected axis.

    Parameters:
    axis (Axis): The axis of rotation: X, Y, or Z.
    angle (float): The rotation angle in radians.

    Returns:
    np.ndarray: The three-by-three rotation matrix.
    """
    rotation_matrices = {
        "X": np.array([
            [1, 0, 0],
            [0, np.cos(angle), -np.sin(angle)],
            [0, np.sin(angle), np.cos(angle)],
        ]),
        "Y": np.array([
            [np.cos(angle), 0, np.sin(angle)],
            [0, 1, 0],
            [-np.sin(angle), 0, np.cos(angle)],
        ]),
        "Z": np.array([
            [np.cos(angle), -np.sin(angle), 0],
            [np.sin(angle), np.cos(angle), 0],
            [0, 0, 1],
        ]),
    }
    return rotation_matrices[axis]


def apply_rotation(state: State, axis: Axis, angle: float) -> State:
    """Rotate the current Bloch vector around one selected axis.

    Parameters:
    state (State): The current simulator state.
    axis (Axis): The axis of rotation: X, Y, or Z.
    angle (float): The rotation angle in radians.

    Returns:
    State: The state containing the rotated coordinates.
    """
    matrix = get_rotation_matrix(axis, angle)
    return apply_gate_matrix(state, matrix)


def apply_pauli_x(state: State) -> State:
    """Apply the Pauli-X transformation to the Bloch coordinates.

    Parameters:
    state (State): The current simulator state.

    Returns:
    State: The state after the Pauli-X transformation.
    """
    matrix = np.diag([1.0, -1.0, -1.0])
    return apply_gate_matrix(state, matrix)


def apply_pauli_y(state: State) -> State:
    """Apply the Pauli-Y transformation to the Bloch coordinates.

    Parameters:
    state (State): The current simulator state.

    Returns:
    State: The state after the Pauli-Y transformation.
    """
    matrix = np.diag([-1.0, 1.0, -1.0])
    return apply_gate_matrix(state, matrix)


def apply_pauli_z(state: State) -> State:
    """Apply the Pauli-Z transformation to the Bloch coordinates.

    Parameters:
    state (State): The current simulator state.

    Returns:
    State: The state after the Pauli-Z transformation.
    """
    matrix = np.diag([-1.0, -1.0, 1.0])
    return apply_gate_matrix(state, matrix)


def apply_hadamard(state: State) -> State:
    """Apply the Hadamard transformation to the Bloch coordinates.

    Parameters:
    state (State): The current simulator state.

    Returns:
    State: The state after the Hadamard transformation.
    """
    matrix = np.array([
        [0.0, 0.0, 1.0],
        [0.0, -1.0, 0.0],
        [1.0, 0.0, 0.0],
    ])
    return apply_gate_matrix(state, matrix)


def apply_s_gate(state: State) -> State:
    """Apply the S phase gate as a 90-degree Z-axis rotation.

    Parameters:
    state (State): The current simulator state.

    Returns:
    State: The state after the S gate.
    """
    return apply_rotation(state, "Z", np.pi / 2)


def apply_t_gate(state: State) -> State:
    """Apply the T phase gate as a 45-degree Z-axis rotation.

    Parameters:
    state (State): The current simulator state.

    Returns:
    State: The state after the T gate.
    """
    return apply_rotation(state, "Z", np.pi / 4)


def get_state_notation(state: State) -> str:
    """Convert Bloch coordinates into a normalized qubit-state expression.

    Parameters:
    state (State): The current simulator state.

    Returns:
    str: The qubit ket expression using alpha and beta amplitudes.
    """
    x, y, z = state.coordinates
    z = float(np.clip(z, -1.0, 1.0))

    if np.isclose(z, -1.0, atol=1e-10):
        alpha = 0.0
        beta = 1.0 + 0.0j
    else:
        alpha = float(np.sqrt((1.0 + z) / 2.0))
        denominator = np.sqrt(2.0 * (1.0 + z))
        beta = complex((x + 1j * y) / denominator)

    beta_text = format_complex_amplitude(beta)
    return f"|ψ⟩ = {alpha:.3f}|0⟩ + {beta_text}|1⟩"


def format_complex_amplitude(amplitude: complex) -> str:
    """Format a complex probability amplitude for state notation.

    Parameters:
    amplitude (complex): The complex amplitude to display.

    Returns:
    str: A readable amplitude rounded to three decimal places.
    """
    real = 0.0 if np.isclose(amplitude.real, 0.0) else amplitude.real
    imaginary = (
        0.0 if np.isclose(amplitude.imag, 0.0) else amplitude.imag
    )
    if imaginary == 0.0:
        return f"{real:.3f}"
    if real == 0.0:
        return f"{imaginary:.3f}i"
    sign = "+" if imaginary > 0 else "-"
    return f"({real:.3f} {sign} {abs(imaginary):.3f}i)"


def create_sphere() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate the coordinate grids used to draw a unit sphere.

    Parameters:
    None: This function does not require input parameters.

    Returns:
    tuple[np.ndarray, np.ndarray, np.ndarray]: The X, Y, and Z grids.
    """
    longitude = np.linspace(0, 2 * np.pi, 100)
    latitude = np.linspace(0, np.pi, 100)
    x = np.outer(np.cos(longitude), np.sin(latitude))
    y = np.outer(np.sin(longitude), np.sin(latitude))
    z = np.outer(np.ones(np.size(longitude)), np.cos(latitude))
    return x, y, z


def draw_bloch_sphere(state: State) -> plt.Figure:
    """Create a Matplotlib Bloch sphere showing the current qubit state.

    Parameters:
    state (State): The current simulator state and plot background setting.

    Returns:
    plt.Figure: The Matplotlib figure containing the Bloch sphere.
    """
    sphere_x, sphere_y, sphere_z = create_sphere()
    figure = plt.figure()
    figure.patch.set_facecolor(state.background_color)
    axes = figure.add_subplot(111, projection="3d")
    axes.set_facecolor(state.background_color)
    draw_sphere_surface(axes, sphere_x, sphere_y, sphere_z)
    draw_sphere_axes(axes)
    draw_state_vector(axes, state.coordinates)
    axes.set_xlim([-1.2, 1.2])
    axes.set_ylim([-1.2, 1.2])
    axes.set_zlim([-1.2, 1.2])
    axes.set_box_aspect([1, 1, 1])
    return figure


def draw_sphere_surface(
    axes: plt.Axes,
    x: np.ndarray,
    y: np.ndarray,
    z: np.ndarray,
) -> None:
    """Draw the translucent sphere and its coordinate labels.

    Parameters:
    axes (plt.Axes): The three-dimensional Matplotlib axes.
    x (np.ndarray): The sphere's X-coordinate grid.
    y (np.ndarray): The sphere's Y-coordinate grid.
    z (np.ndarray): The sphere's Z-coordinate grid.

    Returns:
    None: The function draws directly onto the supplied axes.
    """
    axes.plot_surface(x, y, z, alpha=0.2)
    axes.text(0, 0, 1.12, "|0>", fontsize=12)
    axes.text(0, 0, -1.12, "|1>", fontsize=12)


def draw_sphere_axes(axes: plt.Axes) -> None:
    """Draw and label the X, Y, and Z axes of the Bloch sphere.

    Parameters:
    axes (plt.Axes): The three-dimensional Matplotlib axes.

    Returns:
    None: The function draws directly onto the supplied axes.
    """
    axes.plot([-1, 1], [0, 0], [0, 0], color="black", linewidth=1)
    axes.plot([0, 0], [-1, 1], [0, 0], color="black", linewidth=1)
    axes.plot([0, 0], [0, 0], [-1, 1], color="black", linewidth=1)
    axes.set_xlabel("X")
    axes.set_ylabel("Y")
    axes.set_zlabel("Z")


def draw_state_vector(axes: plt.Axes, coordinates: np.ndarray) -> None:
    """Draw the current state vector and its endpoint on the sphere.

    Parameters:
    axes (plt.Axes): The three-dimensional Matplotlib axes.
    coordinates (np.ndarray): The current X, Y, and Z coordinates.

    Returns:
    None: The function draws directly onto the supplied axes.
    """
    x, y, z = coordinates
    axes.quiver(
        0, 0, 0, x, y, z,
        color="red",
        linewidth=3,
        arrow_length_ratio=0.12,
    )
    axes.scatter(
        x, y, z,
        color="red",
        edgecolors="black",
        s=100,
    )


# ==========================================
# UNIT TESTS
# ==========================================


def make_test_state(coordinates: np.ndarray | None = None) -> State:
    """Create a fresh simulator state for an individual unit test.

    Parameters:
    coordinates (np.ndarray | None): Optional starting Bloch coordinates.

    Returns:
    State: A fresh state with empty histories and default display settings.
    """
    starting_coordinates = (
        INITIAL_COORDINATES.copy()
        if coordinates is None
        else coordinates.copy()
    )
    return State(
        starting_coordinates, [], [], "white", True, True
    )


def test_apply_gate_matrix() -> None:
    """Test identity, sign-change, and coordinate-swap matrix operations.

    Parameters:
    None: This test does not require input parameters.

    Returns:
    None: Assertions report whether each matrix transformation passed.
    """
    state = make_test_state(np.array([1.0, 0.0, 0.0]))
    apply_gate_matrix(state, np.eye(3))
    assert_equal(state.coordinates.tolist(), [1.0, 0.0, 0.0])

    state = make_test_state(np.array([0.0, 1.0, 0.0]))
    apply_gate_matrix(state, np.diag([1.0, -1.0, -1.0]))
    assert_equal(state.coordinates.tolist(), [0.0, -1.0, 0.0])

    state = make_test_state(np.array([0.0, 1.0, 0.0]))
    swap_matrix = np.array([
        [0.0, 1.0, 0.0],
        [1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0],
    ])
    apply_gate_matrix(state, swap_matrix)
    assert_equal(state.coordinates.tolist(), [1.0, 0.0, 0.0])


def test_rotation_matrices() -> None:
    """Test 90-degree rotations around all three Bloch-sphere axes.

    Parameters:
    None: This test does not require input parameters.

    Returns:
    None: Assertions report whether the three rotation matrices passed.
    """
    expected = {
        "X": [[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]],
        "Y": [[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]],
        "Z": [[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]],
    }
    for axis, matrix in expected.items():
        actual = get_rotation_matrix(axis, np.pi / 2)
        assert_equal(np.round(actual, 10).tolist(), matrix)


def test_apply_rotation() -> None:
    """Test that rotations move representative vectors as expected.

    Parameters:
    None: This test does not require input parameters.

    Returns:
    None: Assertions report whether each rotation passed.
    """
    cases = [
        ([0.0, 0.0, 1.0], "X", [0.0, -1.0, 0.0]),
        ([0.0, 0.0, 1.0], "Y", [1.0, 0.0, 0.0]),
        ([1.0, 0.0, 0.0], "Z", [0.0, 1.0, 0.0]),
    ]
    for start, axis, expected in cases:
        state = make_test_state(np.array(start))
        apply_rotation(state, axis, np.pi / 2)
        assert_equal(np.round(state.coordinates, 10).tolist(), expected)


def test_standard_gates() -> None:
    """Test Pauli, Hadamard, S, and T gate coordinate transformations.

    Parameters:
    None: This test does not require input parameters.

    Returns:
    None: Assertions report whether each standard gate passed.
    """
    gate_cases = [
        (apply_pauli_x, [1.0, 0.0, 0.0], [1.0, 0.0, 0.0]),
        (apply_pauli_x, [0.0, 1.0, 0.0], [0.0, -1.0, 0.0]),
        (apply_pauli_x, [0.0, 0.0, 1.0], [0.0, 0.0, -1.0]),
        (apply_pauli_y, [1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]),
        (apply_pauli_y, [0.0, 1.0, 0.0], [0.0, 1.0, 0.0]),
        (apply_pauli_y, [0.0, 0.0, 1.0], [0.0, 0.0, -1.0]),
        (apply_pauli_z, [1.0, 0.0, 0.0], [-1.0, 0.0, 0.0]),
        (apply_pauli_z, [0.0, 1.0, 0.0], [0.0, -1.0, 0.0]),
        (apply_pauli_z, [0.0, 0.0, 1.0], [0.0, 0.0, 1.0]),
        (apply_hadamard, [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]),
        (apply_hadamard, [0.0, 1.0, 0.0], [0.0, -1.0, 0.0]),
        (apply_hadamard, [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]),
    ]
    for gate_function, start, expected in gate_cases:
        state = make_test_state(np.array(start))
        gate_function(state)
        assert_equal(np.round(state.coordinates, 10).tolist(), expected)

    state = make_test_state(np.array([1.0, 0.0, 0.0]))
    apply_s_gate(state)
    assert_equal(np.round(state.coordinates, 10).tolist(), [0.0, 1.0, 0.0])

    state = make_test_state(np.array([1.0, 0.0, 0.0]))
    apply_t_gate(state)
    assert_equal(
        np.round(state.coordinates, 10).tolist(),
        [0.7071067812, 0.7071067812, 0.0],
    )


def test_state_notation() -> None:
    """Test notation for basis states and positive X/Y superpositions.

    Parameters:
    None: This test does not require input parameters.

    Returns:
    None: Assertions report whether the state expressions are correct.
    """
    cases = [
        ([0.0, 0.0, 1.0], "|ψ⟩ = 1.000|0⟩ + 0.000|1⟩"),
        ([1.0, 0.0, 0.0], "|ψ⟩ = 0.707|0⟩ + 0.707|1⟩"),
        ([0.0, 1.0, 0.0], "|ψ⟩ = 0.707|0⟩ + 0.707i|1⟩"),
        ([0.0, 0.0, -1.0], "|ψ⟩ = 0.000|0⟩ + 1.000|1⟩"),
    ]
    for coordinates, expected in cases:
        state = make_test_state(np.array(coordinates))
        assert_equal(get_state_notation(state), expected)


def test_rotation_input_validation() -> None:
    """Test missing, invalid, non-finite, and valid rotation inputs.

    Parameters:
    None: This test does not require input parameters.

    Returns:
    None: Assertions report whether validation accepts the right inputs.
    """
    assert_equal(bool(validate_rotation_input("RX", "")), True)
    assert_equal(bool(validate_rotation_input("RX", "   ")), True)
    assert_equal(bool(validate_rotation_input("RX", "abc")), True)
    assert_equal(bool(validate_rotation_input("RX", "nan")), True)
    assert_equal(bool(validate_rotation_input("bad", "90")), True)
    assert_equal(validate_rotation_input("RZ", "-450"), "")
    assert_equal(validate_rotation_input("RY", "720"), "")


def test_index_and_simulator_routes() -> None:
    """Test that the home and simulator routes return themed pages.

    Parameters:
    None: This test does not require input parameters.

    Returns:
    None: Assertions report whether the routes return valid pages.
    """
    state = make_test_state()
    home_page = index(state)
    simulator_page = simulator(state)
    assert_equal(isinstance(home_page, Page), True)
    assert_equal(isinstance(simulator_page, Page), True)
    assert_equal(home_page.state.background_color, "white")
    assert_equal(
        simulator_page.state.coordinates.tolist(),
        state.coordinates.tolist()
    )
    assert_equal(
        simulator_page.state.coordinate_history,
        state.coordinate_history
    )
    assert_equal(
        simulator_page.state.gate_history,
        state.gate_history
    )
    assert_equal(
        simulator_page.state.background_color,
        state.background_color
    )
    assert_equal(
        simulator_page.state.sphere_shown,
        state.sphere_shown
    )
    assert_equal(
        simulator_page.state.show_notation,
        state.show_notation
    )


def test_apply_gate_route() -> None:
    """Test standard gate routing, state changes, history, and invalid gates.

    Parameters:
    None: This test does not require input parameters.

    Returns:
    None: Assertions report whether the gate route behaves correctly.
    """
    state = make_test_state()
    response = apply_gate(state, "X")
    assert_equal(isinstance(response, Fragment), True)
    assert_equal(response.target, "#simulator_display")
    assert_equal(state.coordinates.tolist(), [0.0, 0.0, -1.0])
    assert_equal(len(state.coordinate_history), 1)
    assert_equal(len(state.gate_history), 1)

    previous_coordinates = state.coordinates.copy()
    apply_gate(state, "not-a-gate")
    assert_equal(state.coordinates.tolist(), previous_coordinates.tolist())
    assert_equal(len(state.gate_history), 1)


def test_rotation_route() -> None:
    """Test valid rotation input, angle history, and invalid input handling.

    Parameters:
    None: This test does not require input parameters.

    Returns:
    None: Assertions report whether the rotation route behaves correctly.
    """
    state = make_test_state()
    response = apply_rotation_gate(state, "RY", "90")
    assert_equal(isinstance(response, Fragment), True)
    assert_equal(np.round(state.coordinates, 10).tolist(), [1.0, 0.0, 0.0])
    assert_equal(state.gate_history[0].rotation_angle, 90.0)

    coordinates_before_error = state.coordinates.copy()
    apply_rotation_gate(state, "RX", "not-a-number")
    assert_equal(state.coordinates.tolist(), coordinates_before_error.tolist())
    assert_equal(len(state.gate_history), 1)


def test_help_and_history_routes() -> None:
    """Test help content and history output for standard and rotation gates.

    Parameters:
    None: This test does not require input parameters.

    Returns:
    None: Assertions report whether both informational routes work.
    """
    state = make_test_state()
    assert_equal(isinstance(help(state), Page), True)
    empty_history = gate_history(state)
    assert_equal(isinstance(empty_history, Page), True)

    apply_gate(state, "X")
    apply_rotation_gate(state, "RZ", "30")
    history_page = gate_history(state)
    assert_equal(isinstance(history_page, Page), True)
    assert_equal(len(state.gate_history), 2)
    assert_equal(state.gate_history[1].rotation_angle, 30.0)


def test_undo_and_reset_routes() -> None:
    """Test repeated undo, history restoration, and reset behavior.

    Parameters:
    None: This test does not require input parameters.

    Returns:
    None: Assertions report whether undo and reset preserve consistency.
    """
    state = make_test_state()
    apply_gate(state, "X")
    apply_rotation_gate(state, "RY", "90")
    undo_response = undo_gate(state)
    assert_equal(isinstance(undo_response, Fragment), True)
    assert_equal(len(state.gate_history), 1)
    assert_equal(state.coordinates.tolist(), [0.0, 0.0, -1.0])

    undo_gate(state)
    assert_equal(state.coordinates.tolist(), [0.0, 0.0, 1.0])
    undo_gate(state)
    assert_equal(len(state.gate_history), 0)

    apply_gate(state, "Y")
    reset_response = reset(state)
    assert_equal(isinstance(reset_response, Fragment), True)
    assert_equal(state.coordinates.tolist(), [0.0, 0.0, 1.0])
    assert_equal(len(state.coordinate_history), 0)
    assert_equal(len(state.gate_history), 0)
    undo_gate(state)
    assert_equal(state.coordinates.tolist(), [0.0, 0.0, 1.0])


def test_settings_routes() -> None:
    """Test settings display and saving of valid appearance preferences.

    Parameters:
    None: This test does not require input parameters.

    Returns:
    None: Assertions report whether settings are saved correctly.
    """
    state = make_test_state()
    assert_equal(isinstance(settings(state), Page), True)
    response = save_settings(state, "lavender", False, False)
    assert_equal(isinstance(response, Page), True)
    assert_equal(state.background_color, "lavender")
    assert_equal(state.sphere_shown, False)
    assert_equal(state.show_notation, False)

    save_settings(state, "not-a-color", True, True)
    assert_equal(state.background_color, "lavender")
    assert_equal(state.sphere_shown, True)
    assert_equal(state.show_notation, True)


def run_all_tests() -> None:
    """Run the simulator's mathematical, validation, and route unit tests.

    Parameters:
    None: This function does not require input parameters.

    Returns:
    None: The individual assertions report their results.
    """
    test_apply_gate_matrix()
    test_rotation_matrices()
    test_apply_rotation()
    test_standard_gates()
    test_state_notation()
    test_rotation_input_validation()
    test_index_and_simulator_routes()
    test_apply_gate_route()
    test_rotation_route()
    test_help_and_history_routes()
    test_undo_and_reset_routes()
    test_settings_routes()


run_all_tests()

start_server(State(
    coordinates=INITIAL_COORDINATES.copy(),
    coordinate_history=[],
    gate_history=[],
    background_color="white",
    sphere_shown=True,
    show_notation=True,
))

