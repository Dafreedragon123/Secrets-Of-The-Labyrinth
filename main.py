import pygame # type: ignore
import sys
import random
import heapq
import time

pygame.init()

# width, height
SCREEN_WIDTH, SCREEN_HEIGHT = 600, 600
CELL_SIZE = 7
COLORS = {
    1: (30, 30, 30), #Wall dark  Grey
    0: (255, 255, 255), # Path white
    'E': (0, 0, 255), # Exit green
    'M': (255, 0, 0) # Minaotur red
    }
player_pos = [15, 15]
player_color = (0, 0, 255)
minotaur_pos = [5, 5]  # Starting position of the Minotaur
VISIBILITY_RADIUS = 5
start_time = time.time()
final_time = None

# set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Secrets of the Labyrinth")

# set recurssion increase 
sys.setrecursionlimit(10000000)

def generate_maze(width, height):
    """Generate a random maze using the depth-first search algorithm."""
    maze = [[1 for _ in range(width)] for _ in range(height)]

    def carve_passages(cx, cy):
        directions = [(0, 2), (2, 0), (0, -2), (-2, 0)]
        random.shuffle(directions)

        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < width and 0 <= ny < height and maze[ny][nx] == 1:
                maze[cy + dy // 2][cx + dx // 2] = 0
                maze[ny][nx] = 0
                carve_passages(nx, ny)

    # Start maze generation from a random point
    start_x, start_y = 1, 1
    maze[start_y][start_x] = 0
    carve_passages(start_x, start_y)

    # Place the exit at a random location far from the start
    exit_x, exit_y = width - 2, height - 2
    maze[exit_y][exit_x] = 'E'

    return maze, [start_y, start_x], [exit_y, exit_x]

# Randomly place the minatour at an open space
def place_minatour():
    while True:
        minotaur_pos = [random.randint(1, len(labyrinth_map) - 2), random.randint(1, len(labyrinth_map[0]) - 2)]
        if labyrinth_map[minotaur_pos[0]][minotaur_pos[1]] == 0 and minotaur_pos != player_pos and minotaur_pos != exit_pos:
            return minotaur_pos

labyrinth_map, player_start, exit_pos = generate_maze(SCREEN_WIDTH // CELL_SIZE, SCREEN_HEIGHT // CELL_SIZE)
player_pos = player_start.copy()
minotaur_pos = place_minatour()


def draw_map():
    """
    Draw the labyrinth with a fog of war effect, revealing more as the player progresses.
    
    The labyrinth is drawn by iterating over each cell in the 2D list and coloring it
    according to its type (wall, floor, minotaur, or exit). The visibility radius is used
    to only reveal cells that are within a certain range of the player.
    """
    for row_index, row in enumerate(labyrinth_map):
        for col_index, cell in enumerate(row):
            # Only reveal cells within the visibility radius of the player
            if abs(player_pos[0] - row_index) <= VISIBILITY_RADIUS and abs(player_pos[1] - col_index) <= VISIBILITY_RADIUS:
                color = COLORS.get(cell, (30, 30, 30))  # Normal color for the cell type
            else:
                color = (30, 30, 30)  # Fog color (dark gray)

            # Draw the cell
            x = col_index * CELL_SIZE
            y = row_index * CELL_SIZE
            pygame.draw.rect(screen, color, (x, y, CELL_SIZE, CELL_SIZE))

def draw_player():
    # Draw the player on the screen
    x = player_pos[1] * CELL_SIZE
    y = player_pos[0] * CELL_SIZE
    pygame.draw.rect(screen, player_color, (x, y, CELL_SIZE, CELL_SIZE))

def draw_minotaur():
    # Draw minatour on the screen
    if abs(player_pos[0] - minotaur_pos[0]) <= VISIBILITY_RADIUS and abs(player_pos[1] - minotaur_pos[1]) <= VISIBILITY_RADIUS:
        x = minotaur_pos[1] * CELL_SIZE
        y = minotaur_pos[0] * CELL_SIZE
        pygame.draw.rect(screen, COLORS['M'], (x, y, CELL_SIZE, CELL_SIZE))

def move_player(dx, dy):
    # move the player by dx and dy, if the target cell is not a wall

    new_x = player_pos[1] + dx
    new_y = player_pos[0] + dy

    # Boundary checking
    if (0 <= new_y < len(labyrinth_map) and 0 <= new_x < len(labyrinth_map[0]) and
        labyrinth_map[new_y][new_x] != 1):
        player_pos[0] = new_y
        player_pos[1] = new_x

def check_exit():
    return labyrinth_map[player_pos[0]][player_pos[1]] == 'E'

def check_game_over():
    return player_pos == minotaur_pos

def display_win_message():
    font = pygame.font.Font(None, 72)
    win_text = font.render("You Win!", True, (0, 0, 255))
    text_rect = win_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(win_text, text_rect)

def display_game_over_message():
    """Display the 'Game Over!' message if the player is caught by the Minotaur."""
    font = pygame.font.Font(None, 72)
    game_over_text = font.render("Game Over!", True, (255, 0, 0))  # Red color
    text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(game_over_text, text_rect)

def heuristic(position, goal):
    """Calculate the Manhattan distance between two points."""
    return abs(position[0] - goal[0]) + abs(position[1] - goal[1])

def reconstruct_path(came_from, current):
    """Reconstructs the path from the start to the goal."""
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()  # Reverse the path to start from the start position
    return path

def astar_find_path(maze, start, goal):
    """A* pathfinding algorithm to find the shortest path from start to goal in the maze."""
    rows, cols = len(maze), len(maze[0])
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == goal:
            return reconstruct_path(came_from, current)

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor = (current[0] + dx, current[1] + dy)
            if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols and maze[neighbor[0]][neighbor[1]] != 1:
                tentative_g_score = g_score[current] + 1
                if tentative_g_score < g_score.get(neighbor, float('inf')):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return None  # No path found

minotaur_path = []  # Store the current path
minotaur_last_move_time = 0  # Track the last move time
minotaur_move_interval = 0.05  # Move every 0.1 seconds

def move_minotaur():
    """Move the Minotaur towards the player using A* pathfinding and dynamically recalculate the path if stuck."""
    global minotaur_path, minotaur_last_move_time

    # Get the current time
    current_time = time.time()
    # Check if enough time has passed since the last move
    if current_time - minotaur_last_move_time < minotaur_move_interval:
        return  # Skip move if not enough time has passed

    # Update the last move time
    minotaur_last_move_time = current_time

    # Recalculate path if Minotaur has no path or gets stuck
    if not minotaur_path or minotaur_path[0] == (minotaur_pos[0], minotaur_pos[1]):
        # Use A* algorithm to find the path to the player
        minotaur_path = astar_find_path(labyrinth_map, (minotaur_pos[0], minotaur_pos[1]), (player_pos[0], player_pos[1]))

    # If there is a path, move Minotaur to the next position
    if minotaur_path:
        next_step = minotaur_path.pop(0)  # Get the next step in the path
        minotaur_pos[0], minotaur_pos[1] = next_step  # Update Minotaur's position

def display_restart_message():
    """Display the 'Press R to Restart' message on the screen."""
    # Initialize the font with size 36 for the restart message
    font = pygame.font.Font(None, 36)
    
    # Render the restart message text with white color
    restart_text = font.render("Press R to Restart", True, (255, 255, 255))
    
    # Get the rectangle of the rendered text and set its position below the center
    text_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    
    # Blit the text onto the screen at the specified position
    screen.blit(restart_text, text_rect)

def reset_game():
    """
    Reset the game state to start a new round.

    This function is called after the player has won or lost the game, to reset the
    game state to start a new round.
    """
    global labyrinth_map, player_pos, minotaur_pos, minotaur_path, start_time
    labyrinth_map, player_start, exit_pos = generate_maze(
        SCREEN_WIDTH // CELL_SIZE, SCREEN_HEIGHT // CELL_SIZE)
    player_pos[:] = player_start
    minotaur_pos[:] = place_minatour()
    minotaur_path = astar_find_path(
        labyrinth_map, tuple(minotaur_pos), tuple(player_pos))
    start_time = time.time()  # Reset the timer


def main():
    global minotaur_path, game_won, game_over
    minotaur_path = astar_find_path(labyrinth_map, tuple(minotaur_pos), tuple(player_pos))

    game_won = False
    game_over = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    move_player(0, -1)
                elif event.key == pygame.K_DOWN:
                    move_player(0, 1)
                elif event.key == pygame.K_LEFT:
                    move_player(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    move_player(1, 0)
                elif event.key == pygame.K_r:  # Restart the game when R is pressed
                    reset_game()
                    game_won = False
                    game_over = False

        if not game_won and not game_over:
            move_minotaur()

        if check_exit() and not game_won:
            game_won = True

        if check_game_over() and not game_over:
            game_over = True

        screen.fill((0, 0, 0))
        draw_map()
        draw_player()
        draw_minotaur()

        if game_over:
            display_game_over_message()
            display_restart_message()
        elif game_won:
            display_win_message()
            display_restart_message()

        # Always display the timer

        pygame.display.flip()

main()
