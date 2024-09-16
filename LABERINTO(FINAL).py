import tkinter as tk
import tkinter.messagebox as messagebox
import time
from PIL import Image, ImageDraw, ImageTk
import heapq  # Para PriorityQueue

class Node():
    def __init__(self, state, parent, action, cost=0):
        self.state = state
        self.parent = parent
        self.action = action
        self.cost = cost

    def __lt__(self, other):
        return self.cost < other.cost

class StackFrontier():
    def __init__(self):
        self.frontier = []

    def add(self, node):
        self.frontier.append(node)

    def contains_state(self, state):
        return any(node.state == state for node in self.frontier)

    def empty(self):
        return len(self.frontier) == 0

    def remove(self):
        if self.empty():
            raise Exception("empty frontier")
        else:
            node = self.frontier.pop()  # LIFO para DFS
            return node

class QueueFrontier(StackFrontier):
    def remove(self):
        if self.empty():
            raise Exception("empty frontier")
        else:
            node = self.frontier.pop(0)  # FIFO para BFS
            return node

class GreedyFrontier():
    def __init__(self, goal):
        self.frontier = []
        self.goal = goal

    def add(self, node):
        priority = self.heuristic(node.state)
        heapq.heappush(self.frontier, (priority, node))

    def contains_state(self, state):
        return any(node.state == state for _, node in self.frontier)

    def empty(self):
        return len(self.frontier) == 0

    def remove(self):
        if self.empty():
            raise Exception("empty frontier")
        else:
            node = heapq.heappop(self.frontier)[1]
            return node

    def heuristic(self, state):
        row, col = state
        goal_row, goal_col = self.goal
        return abs(row - goal_row) + abs(col - goal_col)  # Distancia Manhattan

class AStarFrontier(GreedyFrontier):
    def add(self, node):
        priority = node.cost + self.heuristic(node.state)  # g(n) + h(n)
        heapq.heappush(self.frontier, (priority, node))

class Maze():
    def __init__(self, filename):
        with open(filename) as f:
            contents = f.read()

        if contents.count("A") != 1 or contents.count("B") != 1:
            raise Exception("Laberinto debe tener exactamente un inicio 'A' y un final 'B'")

        contents = contents.splitlines()
        self.height = len(contents)
        self.width = max(len(line) for line in contents)

        self.walls = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                try:
                    if contents[i][j] == "A":
                        self.start = (i, j)
                        row.append(False)
                    elif contents[i][j] == "B":
                        self.goal = (i, j)
                        row.append(False)
                    elif contents[i][j] == " ":
                        row.append(False)
                    else:
                        row.append(True)
                except IndexError:
                    row.append(False)
            self.walls.append(row)

        self.solution = None
        self.explored = set()

    def print(self):
        solution = self.solution[1] if self.solution is not None else None
        print()
        for i, row in enumerate(self.walls):
            for j, col in enumerate(row):
                if col:
                    print("█", end="")
                elif (i, j) == self.start:
                    print("A", end="")
                elif (i, j) == self.goal:
                    print("B", end="")
                elif solution is not None and (i, j) in solution:
                    print("*", end="")
                else:
                    print(" ", end="")
            print()
        print()

    def neighbors(self, state):
        row, col = state
        candidates = [
            ("up", (row - 1, col)),
            ("down", (row + 1, col)),
            ("left", (row, col - 1)),
            ("right", (row, col + 1))
        ]

        result = []
        for action, (r, c) in candidates:
            if 0 <= r < self.height and 0 <= c < self.width and not self.walls[r][c]:
                result.append((action, (r, c)))
        return result

    def solve(self, step_callback=None):
        self.num_explored = 0

        start = Node(state=self.start, parent=None, action=None, cost=0)

        # Inicializar el algoritmo seleccionado correctamente
        if selected_algorithm in ["Greedy", "A*"]:
            frontier = selected_frontier(self.goal)  # Para Greedy y A*
        else:
            frontier = selected_frontier()  # Para BFS y DFS

        frontier.add(start)

        self.explored = set()

        while True:
            if frontier.empty():
                raise Exception("no solution")

            node = frontier.remove()
            self.num_explored += 1

            if step_callback:
                step_callback(node.state)

            if node.state == self.goal:
                actions = []
                cells = []
                while node.parent is not None:
                    actions.append(node.action)
                    cells.append(node.state)
                    node = node.parent
                actions.reverse()
                cells.reverse()
                self.solution = (actions, cells)
                return

            self.explored.add(node.state)

            for action, state in self.neighbors(node.state):
                if not frontier.contains_state(state) and state not in self.explored:
                    child = Node(state=state, parent=node, action=action, cost=node.cost + 1)
                    frontier.add(child)

    def output_image(self, filename, show_solution=True, show_explored=False, current_state=None):
        cell_size = 50
        cell_border = 2

        img = Image.new(
            "RGBA",
            (self.width * cell_size, self.height * cell_size),
            "black"
        )
        draw = ImageDraw.Draw(img)

        solution = self.solution[1] if self.solution is not None else None
        for i, row in enumerate(self.walls):
            for j, col in enumerate(row):
                if col:
                    fill = (40, 40, 40)
                elif (i, j) == self.start:
                    fill = (255, 0, 0)
                elif (i, j) == self.goal:
                    fill = (0, 171, 28)
                elif current_state is not None and (i, j) == current_state:
                    fill = (255, 255, 0)
                elif solution is not None and show_solution and (i, j) in solution:
                    fill = (220, 235, 113)
                elif show_explored and (i, j) in self.explored:
                    fill = (212, 97, 85)
                else:
                    fill = (237, 240, 252)

                draw.rectangle(
                    ([(j * cell_size + cell_border, i * cell_size + cell_border),
                      ((j + 1) * cell_size - cell_border, (i + 1) * cell_size - cell_border)]),
                    fill=fill
                )

        img.save(filename)

def seleccionar_nivel(nivel):
    global solving_mode

    filename = f"laberinto{nivel}.txt"
    m = Maze(filename)
    print(f"Laberinto nivel {nivel}:")
    m.print()
    print("Selecciona el algoritmo y luego inicia el recorrido.")

    def paso_a_paso(state):
        actualizar_imagen(m, current_state=state)
        ventana.update()
        time.sleep(0.1)

    def iniciar_recorrido():
        if solving_mode == "None":
            messagebox.showwarning("Selección de Algoritmo", "Por favor, selecciona un algoritmo.")
            return
        
        m.solve(step_callback=paso_a_paso)
        print("Estados explorados:", m.num_explored)
        print("Solución:")
        m.print()

        actualizar_imagen(m)
        indicador_algoritmo.config(text=f"Algoritmo Seleccionado: {selected_algorithm}")

        # Mostrar un mensaje cuando se termine el nivel
        messagebox.showinfo("Nivel Completo", f"Nivel {nivel} completado usando {selected_algorithm}.")
        ventana.update()

    # Mostrar el laberinto
    actualizar_imagen(m)
    
    # Mostrar los botones para seleccionar el algoritmo
    frame_algoritmo.pack(pady=10)

    # Configurar el botón para iniciar el recorrido
    boton_iniciar.config(command=iniciar_recorrido)

def actualizar_imagen(m, current_state=None):
    m.output_image("laberinto_gui.png", show_explored=True, current_state=current_state)
    img = Image.open("laberinto_gui.png")
    img = img.resize((400, 400))
    img_tk = ImageTk.PhotoImage(img)
    label_img.config(image=img_tk)
    label_img.image = img_tk

def set_frontier(frontera):
    global selected_frontier, selected_algorithm, solving_mode
    if frontera == "BFS":
        selected_frontier = QueueFrontier
        selected_algorithm = "BFS"
    elif frontera == "DFS":
        selected_frontier = StackFrontier
        selected_algorithm = "DFS"
    elif frontera == "Greedy":
        selected_frontier = GreedyFrontier
        selected_algorithm = "Greedy"
    elif frontera == "A*":
        selected_frontier = AStarFrontier
        selected_algorithm = "A*"
    indicador_algoritmo.config(text=f"Algoritmo Seleccionado: {selected_algorithm}")
    solving_mode = selected_algorithm

ventana = tk.Tk()
ventana.title("Laberinto")
ventana.geometry("450x500")
ventana.configure(bg="#f0f0f0")  # Color de fondo de la ventana

frame_algoritmo = tk.Frame(ventana, bg="#f0f0f0")
frame_algoritmo.pack(pady=20)
frame_botones = tk.Frame(ventana, bg="#f0f0f0")
frame_botones.pack()
niveles = [1, 2, 3, 4, 5]
for nivel in niveles:
    boton = tk.Button(frame_botones, text=f"Nivel {nivel}", font=("Arial", 14), 
                    command=lambda n=nivel: seleccionar_nivel(n),bg="#4CAF50", fg="white", borderwidth=2, relief="groove")
    boton.grid(row=0, column=nivel-1, padx=10, pady=10, sticky="nsew")

label_img = tk.Label(ventana)
label_img.pack()

boton_iniciar = tk.Button(ventana, text="Iniciar Recorrido", bg="green", fg="white")
boton_iniciar.pack(pady=20)

frame_boton = tk.Frame(ventana, bg="#f0f0f0")
frame_boton.pack()

bfs_btn = tk.Button(frame_boton,  text="BFS", font=("Arial", 14), command=lambda: set_frontier("BFS"), bg="#2196F3", fg="white", borderwidth=2, relief="groove")
bfs_btn.grid(row=0, column=0, padx=10)

dfs_btn = tk.Button(frame_boton, text="DFS", font=("Arial", 14), command=lambda: set_frontier("DFS"),bg="#6A0D91", fg="white", borderwidth=2, relief="groove")
dfs_btn.grid(row=0, column=1, padx=10)

greedy_btn = tk.Button(frame_boton, text="Greedy", font=("Arial", 14), command=lambda: set_frontier("Greedy"),bg="#3357FF", fg="white", borderwidth=2, relief="groove")
greedy_btn.grid(row=0, column=2, padx=10)

astar_btn = tk.Button(frame_boton, text="A*",  font=("Arial", 14),command=lambda: set_frontier("A*"),bg="#FF5733", fg="white", borderwidth=2, relief="groove")
astar_btn.grid(row=0, column=3, padx=10)

indicador_algoritmo = tk.Label(ventana, text="Algoritmo Seleccionado: Ninguno")
indicador_algoritmo.pack()

ventana.mainloop()
