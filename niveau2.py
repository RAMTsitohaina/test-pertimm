"""
Test Technique Pertimm - Niveau 2
Résolution automatique du labyrinthe avec algorithme de pathfinding
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
    """Résolveur de labyrinthe utilisant l'algorithme BFS."""
    
    BASE_URL = "https://hire-game-maze.pertimm.dev"
    
    def __init__(self, player_name: str):
        """
        Initialise le résolveur de labyrinthe.
        
        Args:
            player_name: Nom du joueur
        """
        self.player_name = player_name
        self.session = requests.Session()
        self.position_x: Optional[int] = None
        self.position_y: Optional[int] = None
        self.url_move: Optional[str] = None
        self.url_discover: Optional[str] = None
        self.discovered_map: Dict[Tuple[int, int], MazeCell] = {}
        self.move_count = 0
        self.visited_positions: Set[Tuple[int, int]] = set()
    
    def start_game(self) -> Dict:
        """
        Démarre une nouvelle partie.
        
        Returns:
            Réponse JSON du serveur
        """
        url = f"{self.BASE_URL}/start-game/"
        data = {"player": self.player_name}
        
        headers = {"Content-Type": "application/json"}

        response = self.session.post(url, data=data)#, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        self._update_state(result)
        return result
    
    def discover_surroundings(self) -> List[MazeCell]:
        """
        Découvre les cases environnantes.
        
        Returns:
            Liste des cellules découvertes
        """
        response = self.session.get(self.url_discover)
        response.raise_for_status()
        
        cells_data = response.json()
        cells = []
        
        for cell_data in cells_data:
            cell = MazeCell(
                x=cell_data["x"],
                y=cell_data["y"],
                value=cell_data["value"],
                movable=cell_data["move"]
            )
            cells.append(cell)
            self.discovered_map[(cell.x, cell.y)] = cell
        
        return cells
    
    def move_to(self, x: int, y: int) -> Dict:
        """
        Se déplace vers une nouvelle position.
        
        Args:
            x: Position X cible
            y: Position Y cible
            
        Returns:
            Réponse JSON du serveur
        """
        data = {"position_x": x, "position_y": y}
        
        response = self.session.post(self.url_move, data=data)
        response.raise_for_status()
        
        result = response.json()
        self._update_state(result)
        self.move_count += 1
        self.visited_positions.add((x, y))
        
        return result
    
    def _update_state(self, response: Dict) -> None:
        """
        Met à jour l'état interne à partir de la réponse du serveur.
        
        Args:
            response: Réponse JSON du serveur
        """
        self.position_x = response["position_x"]
        self.position_y = response["position_y"]
        self.url_move = response["url_move"]
        self.url_discover = response["url_discover"]
    
    def find_shortest_path(self) -> Optional[List[Tuple[int, int]]]:
        """
        Trouve le chemin le plus court vers la sortie avec BFS.
        
        Returns:
            Liste des positions formant le chemin, ou None si aucun chemin
        """
        start = (self.position_x, self.position_y)
        queue = deque([(start, [start])])
        visited: Set[Tuple[int, int]] = {start}
        
        while queue:
            (x, y), path = queue.popleft()
            
            # Vérifier si on a atteint la sortie
            cell = self.discovered_map.get((x, y))
            if cell and cell.value == "stop":
                return path
            
            # Explorer les voisins (haut, bas, gauche, droite)
            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (nx, ny) in visited:
                    continue
                
                neighbor = self.discovered_map.get((nx, ny))
                
                # Si la case n'est pas découverte, on ne peut pas planifier
                if neighbor is None:
                    continue
                
                # Vérifier si on peut se déplacer (pas de mur, pas de piège)
                if neighbor.movable and neighbor.value != "trap":
                    visited.add((nx, ny))
                    queue.append(((nx, ny), path + [(nx, ny)]))
        
        return None
    
    def solve_with_exploration(self) -> bool:
        """
        Résout le labyrinthe avec exploration progressive.
        
        Returns:
            True si le labyrinthe est résolu, False sinon
        """
        max_iterations = 1000  # Sécurité contre les boucles infinies
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            # Découvrir l'environnement actuel
            cells = self.discover_surroundings()
            
            # Vérifier si on est à la sortie
            current_cell = self.discovered_map.get(
                (self.position_x, self.position_y)
            )
            if current_cell and current_cell.value == "stop":
                return True
            
            # Chercher la sortie dans les cases découvertes
            stop_found = False
            for cell in cells:
                if cell.value == "stop":
                    stop_found = True
                    break
            
            # Trouver le chemin optimal vers la sortie
            path = self.find_shortest_path()
            
            if path and len(path) > 1:
                # Se déplacer vers la prochaine case
                next_x, next_y = path[1]
                
                print(f"   Déplacement {self.move_count + 1}: "
                      f"({self.position_x}, {self.position_y}) -> "
                      f"({next_x}, {next_y})")
                
                result = self.move_to(next_x, next_y)
                
                if result.get("win"):
                    return True
                if result.get("dead"):
                    print("   ✗ Piège détecté! Partie perdue.")
                    return False
            else:
                # Pas de chemin connu, explorer une case adjacente non visitée
                moved = self._explore_adjacent()
                
                if not moved:
                    # Aucune case explorable, essayer de revenir en arrière
                    moved = self._backtrack()
                    
                    if not moved:
                        print("   ✗ Bloqué! Impossible de continuer.")
                        return False
        
        print(f"   ✗ Limite d'itérations atteinte ({max_iterations})")
        return False
    
    def _explore_adjacent(self) -> bool:
        """
        Explore une case adjacente non visitée et sans danger connu.
        
        Returns:
            True si un déplacement a été effectué, False sinon
        """
        # Ordre de priorité: bas, droite, haut, gauche
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        for dx, dy in directions:
            nx = self.position_x + dx
            ny = self.position_y + dy
            
            # Vérifier si déjà visité
            if (nx, ny) in self.visited_positions:
                continue
            
            neighbor = self.discovered_map.get((nx, ny))
            
            # Si case non découverte ou non accessible, continuer
            if not neighbor:
                continue
            
            # Se déplacer si possible et pas un piège
            if neighbor.movable and neighbor.value != "trap":
                print(f"   Exploration: ({self.position_x}, {self.position_y}) "
                      f"-> ({nx}, {ny})")
                result = self.move_to(nx, ny)
                
                if result.get("win"):
                    return True
                if result.get("dead"):
                    return False
                
                return True
        
        return False
    
    def _backtrack(self) -> bool:
        """
        Revient en arrière vers une case visitée avec des voisins non explorés.
        
        Returns:
            True si un déplacement a été effectué, False sinon
        """
        # Chercher une case adjacente déjà visitée
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        for dx, dy in directions:
            nx = self.position_x + dx
            ny = self.position_y + dy
            
            if (nx, ny) not in self.visited_positions:
                continue
            
            neighbor = self.discovered_map.get((nx, ny))
            
            if neighbor and neighbor.movable and neighbor.value != "trap":
                print(f"   Retour: ({self.position_x}, {self.position_y}) "
                      f"-> ({nx}, {ny})")
                result = self.move_to(nx, ny)
                
                if result.get("win"):
                    return True
                if result.get("dead"):
                    return False
                
                return True
        
        return False
    
    def visualize_map(self) -> None:
        """Affiche une représentation visuelle de la carte découverte."""
        if not self.discovered_map:
            print("   Aucune carte à afficher")
            return
        
        min_x = min(cell.x for cell in self.discovered_map.values())
        max_x = max(cell.x for cell in self.discovered_map.values())
        min_y = min(cell.y for cell in self.discovered_map.values())
        max_y = max(cell.y for cell in self.discovered_map.values())
        
        symbols = {
            "wall": "█",
            "path": "·",
            "trap": "X",
            "home": "H",
            "stop": "E"
        }
        
        print("\n   === Carte du labyrinthe ===")
        print(f"   Taille: {max_x - min_x + 1}x{max_y - min_y + 1}")
        print()
        
        for y in range(min_y, max_y + 1):
            row = "   "
            for x in range(min_x, max_x + 1):
                if (x, y) == (self.position_x, self.position_y):
                    row += "●"  # Position actuelle
                elif (x, y) in self.discovered_map:
                    cell = self.discovered_map[(x, y)]
                    row += symbols.get(cell.value, "?")
                else:
                    row += " "  # Non découvert
            print(row)
        
        print(f"\n   Légende: ● = Joueur, H = Départ, E = Sortie, "
              f"█ = Mur, X = Piège, · = Chemin")


def main():
    """Fonction principale pour résoudre le labyrinthe."""
    # Configuration - MODIFIEZ LE NOM DU JOUEUR
    PLAYER_NAME = "Tsitohaina"
    
    print("=== Test Technique Pertimm - Niveau 2: Maze Solver ===\n")
    
    solver = MazeSolver(PLAYER_NAME)
    
    try:
        # Démarrer le jeu
        print(f"1. Démarrage du jeu pour '{PLAYER_NAME}'...")
        result = solver.start_game()
        print(f"   ✓ Partie démarrée")
        print(f"   ✓ Position initiale: ({result['position_x']}, "
              f"{result['position_y']})")
        print(f"   ✓ Statut: Win={result['win']}, Dead={result['dead']}")
        
        # Résoudre le labyrinthe
        print("\n2. Résolution du labyrinthe...")
        print("   Exploration en cours...\n")
        
        success = solver.solve_with_exploration()
        
        # Afficher les résultats
        print("\n" + "="*60)
        
        if success:
            print("✓✓✓ LABYRINTHE RÉSOLU AVEC SUCCÈS! ✓✓✓")
            print(f"Nombre total de déplacements: {solver.move_count}")
            print(f"Cases découvertes: {len(solver.discovered_map)}")
            print(f"Cases visitées: {len(solver.visited_positions)}")
        else:
            print("✗✗✗ ÉCHEC DE LA RÉSOLUTION ✗✗✗")
            print(f"Déplacements effectués: {solver.move_count}")
        
        print("="*60)
        
        # Visualiser la carte finale
        solver.visualize_map()
        
    except requests.exceptions.HTTPError as e:
        print(f"\n✗ Erreur HTTP {e.response.status_code}: {e}")
        print(f"   URL: {e.response.url}")
        print(f"   Réponse: {e.response.text}")
        raise
    except Exception as e:
        print(f"\n✗ Erreur: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()