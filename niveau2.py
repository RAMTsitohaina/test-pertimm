"""
Test Technique Pertimm - Niveau 2
Résolution automatique du labyrinthe avec algorithme de pathfinding optimisé (Frontier Exploration)
"""

import requests
from typing import Dict, List, Tuple, Optional, Set
from collections import deque


class MazeCell:
    """Représente une cellule du labyrinthe."""
    
    def __init__(self, x: int, y: int, value: str, movable: bool):
        """
        Initialise une cellule du labyrinthe.
        
        Args:
            x: Position sur l'axe X
            y: Position sur l'axe Y
            value: Nature de la case (wall, path, trap, home, stop)
            movable: Indique si le déplacement est possible
        """
        self.x = x
        self.y = y
        self.value = value
        self.movable = movable
    
    def __repr__(self) -> str:
        """Représentation textuelle de la cellule."""
        return f"Cell({self.x}, {self.y}, {self.value})"


class MazeSolver:
    """Résolveur de labyrinthe optimisé utilisant l'exploration par frontière."""
    
    BASE_URL = "https://hire-game-maze.pertimm.dev"
    
    def __init__(self, player_name: str):
        """
        Initialise le résolveur de labyrinthe.
        
        Args:
            player_name: Nom du joueur
        """
        self.player_name = player_name
        self.session = requests.Session()
        
        # État du jeu
        self.position_x: Optional[int] = None
        self.position_y: Optional[int] = None
        self.url_move: Optional[str] = None
        self.url_discover: Optional[str] = None
        
        # Connaissance du monde
        self.discovered_map: Dict[Tuple[int, int], MazeCell] = {}
        self.scanned_positions: Set[Tuple[int, int]] = set() # Lieux où on a fait discover()
        
        self.move_count = 0
        self.move_history: List[Tuple[int, int]] = []
    
    @property
    def current_pos(self) -> Tuple[int, int]:
        return (self.position_x, self.position_y)

    def start_game(self) -> Dict:
        """Démarre une nouvelle partie."""
        url = f"{self.BASE_URL}/start-game/"
        data = {"player": self.player_name}
        
        response = self.session.post(url, data=data)
        response.raise_for_status()
        
        result = response.json()
        print ("************Result : ", result)
        self._update_state(result)
        
        # Reset knowledge
        self.discovered_map = {}
        self.scanned_positions = set()
        self.move_count = 0
        self.move_history = []
        
        return result
    
    def discover_surroundings(self) -> List[MazeCell]:
        """Découvre les cases environnantes."""
        response = self.session.get(self.url_discover)
        response.raise_for_status()
        
        cells_data = response.json()
        new_cells = []
        
        for cell_data in cells_data:
            cell = MazeCell(
                x=cell_data["x"],
                y=cell_data["y"],
                value=cell_data["value"],
                movable=cell_data["move"]
            )
            self.discovered_map[(cell.x, cell.y)] = cell
            new_cells.append(cell)
            
        # Marquer la position actuelle comme scannée
        if self.current_pos not in self.scanned_positions:
            self.scanned_positions.add(self.current_pos)
            
        return new_cells
    
    def move_to(self, x: int, y: int) -> Dict:
        """Se déplace vers une nouvelle position."""
        data = {"position_x": x, "position_y": y}
        
        response = self.session.post(self.url_move, data=data)
        response.raise_for_status()
        
        result = response.json()
        self._update_state(result)
        self.move_count += 1
        self.move_history.append((x, y))
        
        return result
    
    def _update_state(self, response: Dict) -> None:
        """Met à jour l'état interne à partir de la réponse du serveur."""
        self.position_x = response["position_x"]
        self.position_y = response["position_y"]
        self.url_move = response["url_move"]
        self.url_discover = response["url_discover"]
    
    def find_path_bfs(self, start: Tuple[int, int], target_condition_func) -> Optional[List[Tuple[int, int]]]:
        """
        Trouve le chemin le plus court vers la première case qui satisfait `target_condition_func`.
        
        Args:
            start: Position de départ (x, y)
            target_condition_func: Fonction qui prend une pos (x,y) et retourne True si c'est une cible valide.
            
        Returns:
            Liste de coordonnées [start, ..., target] ou None.
        """
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            current, path = queue.popleft()
            
            # Si on atteint une cible
            if target_condition_func(current):
                return path
            
            # Explorer voisins
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = current[0] + dx, current[1] + dy
                neighbor_pos = (nx, ny)
                
                if neighbor_pos in visited:
                    continue
                
                # On ne peut traverser que des cases connues et ""movable"" (et pas de pièges)
                # Exception: la cible peut être hors map si c'est ce qu'on cherche, 
                # mais ici on navigue DANS discovered_map pour atteindre la frontière.
                cell = self.discovered_map.get(neighbor_pos)
                
                if cell and cell.movable and cell.value != "trap":
                    visited.add(neighbor_pos)
                    queue.append((neighbor_pos, path + [neighbor_pos]))
                    
        return None

    def solve_optimized(self) -> bool:
        """
        Résout le labyrinthe avec une stratégie d'exploration optimisée (Frontier Based).
        """
        max_iterations = 2000 
        
        for _ in range(max_iterations):
            # 1. Observer
            self.discover_surroundings()
            
            # 2. Vérifier si on voit la SORTIE (stop)
            stop_pos = None
            for pos, cell in self.discovered_map.items():
                if cell.value == "stop":
                    stop_pos = pos
                    break
            
            target_path = None
            
            if stop_pos:
                # Si on voit la sortie, on y va directement
                print(f"   ! Sortie détectée en {stop_pos}. Calcul du chemin...")
                target_path = self.find_path_bfs(
                    self.current_pos, 
                    lambda p: p == stop_pos
                )
            else:
                # Sinon, on cherche la case "Frontière" la plus proche.
                # Une frontière est une case connue (reachable) mais non scannée.
                target_path = self.find_path_bfs(
                    self.current_pos,
                    lambda p: p in self.discovered_map and p not in self.scanned_positions
                )
            
            if not target_path:
                print("   ✗ Aucun chemin trouvé vers un objectif. Labyrinthe impossible ?")
                return False
                
            # target_path contient [current_pos, next_step, ... target]
            # On avance d'UN PAS seulement, puis on re-discover (pour mettre à jour la map).
            # Sauf si on fonce vers le 'stop', on pourrait optimiser, mais la prudence est de re-scanner.
            
            if len(target_path) < 2:
                # On est déjà sur la cible ? (ex: sortie atteinte au tour précédent mais pas détectée?)
                if stop_pos and self.current_pos == stop_pos:
                    print("   ✓ Arrivé sur la case stop (déjà là).")
                    return True
                # Sinon bug
                print("   ? Chemin vide ou longueur 1 alors qu'on cherche à bouger.")
                return False

            next_step = target_path[1] # Le prochain pas immédiat
            
            # Exécuter le mouvement
            # print(f"   Mouvement: {self.current_pos} -> {next_step}")
            result = self.move_to(next_step[0], next_step[1])
            
            if result.get("win"):
                print("   ✓ VICTOIRE !")
                return True
            if result.get("dead"):
                print("   ✗ MORT (Piège).")
                return False
                
        print("   ✗ Trop d'itérations.")
        return False
    
    def visualize_map(self) -> None:
        """Affiche une représentation visuelle de la carte."""
        if not self.discovered_map:
            return
        
        xs = [c.x for c in self.discovered_map.values()]
        ys = [c.y for c in self.discovered_map.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        symbols = {"wall": "█", "path": " ", "trap": "X", "home": "H", "stop": "E"}
        
        print(f"\n   === Carte ({len(self.discovered_map)} cases) ===")
        for y in range(min_y, max_y + 1):
            line = ""
            for x in range(min_x, max_x + 1):
                if (x, y) == self.current_pos:
                    line += "●"
                elif (x, y) in self.discovered_map:
                    line += symbols.get(self.discovered_map[(x, y)].value, "?")
                else:
                    line += "░" # Inconnu
            print("   " + line)
        print()


def main():
    PLAYER_NAME = "Tsitohaina"
    print(f"=== Solver Niveau 2 Optimisé pour {PLAYER_NAME} ===\n")
    
    solver = MazeSolver(PLAYER_NAME)
    
    try:
        solver.start_game()
        print(f"   Départ: {solver.current_pos}")
        
        if solver.solve_optimized():
            print(f"\n✓ SUCCÈS en {solver.move_count} coups.")
            print(f"Liste des mouvements : {solver.move_history}")
        else:
            print("\n✗ ÉCHEC.")
            
        solver.visualize_map()
        
    except Exception as e:
        print(f"\n✗ ERREUR: {e}")
        # import traceback; traceback.print_exc()

if __name__ == "__main__":
    main()