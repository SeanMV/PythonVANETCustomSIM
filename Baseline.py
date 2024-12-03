import pygame
import osmnx as ox
import math
import time

# Initialize Pygame
pygame.init()

# Set up the display
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Vehicle Simulation with Roads')

# Define colors for clarity in visual representation
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LEGITIMATE_LINE_COLOR = (0, 255, 0)  # Green for legitimate vehicles
RED = (255, 0, 0)

# Load and scale vehicle and RSU icons
legitimate_car_icon = pygame.image.load(r'D:/HONS/Images/LEGITIMATE_CAR.png')
legitimate_car_icon = pygame.transform.scale(legitimate_car_icon, (50, 30))
rsu_icon = pygame.image.load(r'D:/HONS/Images/RSU.png')
rsu_icon = pygame.transform.scale(rsu_icon, (90, 90))

# Timer setup - set simulation duration
simulation_duration = 10  # 10 seconds


# Vehicle class representing the vehicles in the simulation
class Vehicle(pygame.sprite.Sprite):
    def __init__(self, start_node, path, image, offset=(0, 0)):
        super().__init__()
        self.image = image  # Vehicle image
        self.rect = self.image.get_rect(center=scaled_positions[start_node])  # Initial position
        self.rect.x += offset[0]  # Offset for visual distinction
        self.rect.y += offset[1]
        self.path = path  # Predefined path for movements
        self.current_target_index = 0  # Index for tracking path targets
        self.communication_error = False  # Flag for communication error with RSU
        self.sent_packets = 0  # Count of sent packets
        self.legitimate_received_packets = 0  # Count of packets successfully received

    def send_packet(self, rsu):
        """Simulate sending a packet to an RSU."""
        self.sent_packets += 1
        rsu.receive_message(self)

    def update(self):
        """Update vehicle position along the path."""
        if len(self.path) > 0:
            target_pos = scaled_positions[self.path[self.current_target_index]]
            dx, dy = target_pos[0] - self.rect.x, target_pos[1] - self.rect.y
            distance = math.sqrt(dx ** 2 + dy ** 2)
            if distance > 1:
                self.rect.x += dx / distance  # Normalize movement
                self.rect.y += dy / distance
            else:
                self.current_target_index += 1
                if self.current_target_index >= len(self.path):
                    self.current_target_index = 0  # Loop back to start

    def distance_to(self, rsu):
        """Calculate distance to the RSU."""
        dx = self.rect.centerx - rsu.rect.centerx
        dy = self.rect.centery - rsu.rect.centery
        return math.sqrt(dx ** 2 + dy ** 2)

    def draw_communication_error_marker(self, screen):
        """Draw a marker to indicate communication error."""
        if self.communication_error:
            font = pygame.font.Font(None, 36)
            error_marker = font.render("?", True, RED)  # Red question mark
            screen.blit(error_marker, (self.rect.centerx - 15, self.rect.centery - 20))


# LegitimateVehicle subclass that adds timing to packet sending
class LegitimateVehicle(Vehicle):
    def __init__(self, start_node, path, image, offset=(0, 0)):
        super().__init__(start_node, path, image, offset)
        self.last_sent_time = time.time()  # Track time for packet sending interval

    def send_packet(self, rsu):
        """Send packets at specified intervals."""
        current_time = time.time()
        if current_time - self.last_sent_time > 0.05:  # Adjust sending interval
            self.last_sent_time = current_time
            self.sent_packets += 1  # Increment packet count
            print(f"Legitimate Vehicle {legitimate_vehicles.index(self) + 1} sending normal packets to RSU")
            rsu.receive_message(self)


# RSU class for handling received messages from vehicles
class RSU(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = rsu_icon  # RSU image
        self.rect = self.image.get_rect(center=(x, y))  # Set initial position
        self.message_count = 0  # Track message count
        self.max_messages = 2500  # Threshold for RSU capacity
        self.operational = True  # RSU operational status
        self.legitimate_received = 0  # Count of legitimate messages received

    def receive_message(self, vehicle):
        """Handle incoming messages from vehicles."""
        if not self.operational:
            return
        self.message_count += 1  # Increment message count
        vehicle.legitimate_received_packets += 1  # Increment received count
        self.legitimate_received += 1

        # Check if RSU exceeds message capacity
        if self.message_count > self.max_messages:
            self.operational = False
            print("RSU is no longer operational due to high traffic.")

    def reset(self):
        """Reset RSU to initial state."""
        self.message_count = 0
        self.operational = True


# Load and process road graph using osmnx
osm_file = 'D:/HONS/Edinburgh.osm'
G = ox.graph_from_xml(osm_file, simplify=True)

positions = {node: (data['x'], data['y']) for node, data in G.nodes(data=True)}
edges = list(G.edges())

# Find min and max coordinates for scaling
min_x = min(x for x, y in positions.values())
max_x = max(x for x, y in positions.values())
min_y = min(y for x, y in positions.values())
max_y = max(y for x, y in positions.values())


def scale_and_translate(pos):
    """Scale and translate coordinates for screen rendering."""
    x, y = pos
    x = int((x - min_x) / (max_x - min_x) * screen_width)
    y = int((y - min_y) / (max_y - min_y) * screen_height)
    return x, y


# Apply scaling to positions of nodes
scaled_positions = {node: scale_and_translate(pos) for node, pos in positions.items()}

# Create sprite groups for organized updates and drawing
all_sprites = pygame.sprite.LayeredUpdates()

# Define paths for legitimate vehicles
legitimate_vehicle_paths = [
    [list(positions.keys())[i], list(positions.keys())[i + 3], list(positions.keys())[i + 6]]
    for i in range(5)
]

offsets = [(5, 0), (0, 5), (-5, 0), (0, -5), (5, 5)]

# Initialize legitimate vehicles with paths, images, and offsets
legitimate_vehicles = [
    LegitimateVehicle(path[0], path, legitimate_car_icon, offset=offset) for path, offset in
    zip(legitimate_vehicle_paths, offsets)
]

# Font for displaying timing
font = pygame.font.Font(None, 36)

# Create and position the RSU
rsu1 = RSU(400, 250)

# Add vehicles and RSU to sprite groups
all_sprites.add(*legitimate_vehicles)
all_sprites.add(rsu1)

# Simulation loop to animate vehicles and process updates
running = True
start_time = time.time()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    all_sprites.update()  # Update all sprite positions
    screen.fill(WHITE)  # Clear screen with white background

    # Draw road edges
    for edge in edges:
        node1, node2 = edge
        pos1 = scaled_positions[node1]
        pos2 = scaled_positions[node2]
        pygame.draw.line(screen, BLACK, pos1, pos2, 2)

    all_sprites.draw(screen)  # Draw all sprites

    # Process communication between vehicles and RSU
    for vehicle in legitimate_vehicles:
        if vehicle.distance_to(rsu1) < 300:  # Communication range
            vehicle.send_packet(rsu1)  # Send packets to RSU
            if rsu1.operational:
                pygame.draw.line(screen, LEGITIMATE_LINE_COLOR, vehicle.rect.center, rsu1.rect.center, 2)
                print(f"Legitimate Vehicle {legitimate_vehicles.index(vehicle) + 1} communicating with RSU")
            else:
                vehicle.communication_error = True  # Set communication error flag
                print(
                    f"Legitimate Vehicle {legitimate_vehicles.index(vehicle) + 1} cannot communicate with RSU (RSU offline)")

    # If RSU is inoperable, display a message
    if not rsu1.operational:
        pygame.draw.rect(screen, RED, (rsu1.rect.x - 10, rsu1.rect.y - 10, rsu1.rect.width + 20, rsu1.rect.height + 20),
                         5)
        text = font.render('RSU INOPERABLE', True, RED)
        screen.blit(text, (rsu1.rect.x + 10, rsu1.rect.y - 30))

        # Display communication error marker for vehicles with errors
        for vehicle in legitimate_vehicles:
            if vehicle.communication_error:
                vehicle.draw_communication_error_marker(screen)

    # Display timer on screen
    elapsed_time = time.time() - start_time
    timer_text = font.render(f"Time: {elapsed_time:.1f}s", True, RED)
    screen.blit(timer_text, (10, 10))

    # Update display and check simulation duration
    pygame.display.flip()
    if elapsed_time > simulation_duration:
        running = False
    time.sleep(0.01)

pygame.quit()

print("\nSimulation ended.\n")

# Diagnostics to understand packet distribution
print(f"Legitimate vehicles sent packets: {sum(vehicle.sent_packets for vehicle in legitimate_vehicles)}")
print(
    f"Legitimate vehicles received packets: {sum(vehicle.legitimate_received_packets for vehicle in legitimate_vehicles)}")
print("\n")
print("-- Detailed Legitimate Vehicle Data --")
for idx, vehicle in enumerate(legitimate_vehicles, start=1):
    print(f"Legitimate Vehicle {idx}: Sent {vehicle.sent_packets} - Received {vehicle.legitimate_received_packets}")
print("\n")
