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
pygame.display.set_caption('Blockchain Mitigation Against DDoS Attack')

# Define colors
WHITE = (255, 255, 255)  # Background color
BLACK = (0, 0, 0)  # Road lines
MALICIOUS_LINE_COLOR = (255, 0, 0)  # Red for malicious vehicle communication
LEGITIMATE_LINE_COLOR = (0, 255, 0)  # Green for legitimate vehicle communication
RED = (255, 0, 0)  # Red for key revocation indicators and text

# Load and scale vehicle icons
malicious_car_icon = pygame.image.load(r'D:/HONS/Images/BC/MVKEY.png')  # Image for malicious cars
malicious_car_icon = pygame.transform.scale(malicious_car_icon, (50, 50))

legitimate_car_icon = pygame.image.load(r'D:/HONS/Images/BC/LVKEY.png')  # Image for legitimate cars
legitimate_car_icon = pygame.transform.scale(legitimate_car_icon, (50, 50))

# Load and scale RSU icon
rsu_icon = pygame.image.load(r'D:/HONS/Images/BC/RSULedger.png')
rsu_icon = pygame.transform.scale(rsu_icon, (60, 60))


# Define the Vehicle class, representing both malicious and legitimate vehicles
class Vehicle(pygame.sprite.Sprite):
    def __init__(self, start_node, path, is_malicious=False, offset=(0, 0)):
        super().__init__()
        self.image = malicious_car_icon if is_malicious else legitimate_car_icon  # Set vehicle image based on type
        self.rect = self.image.get_rect(center=scaled_positions[start_node])  # Set position based on node
        self.rect.x += offset[0]
        self.rect.y += offset[1]
        self.path = path  # Path for the vehicle to follow
        self.current_target_index = 0  # Track progress along the path
        self.revoked = False  # Flag for key revocation status
        self.sent_packets = 0  # Packet counter for sent packets
        self.packets_received = 0  # Packet counter for packets received
        self.is_malicious = is_malicious  # Type flag
        self.last_sent_time = time.time()  # Initialize the packet sending timer
        self.key = f"Key{id(self)}"  # Unique key for identification
        self.authenticated = False  # Flag for authentication status

    def update(self):
        # Method to update vehicle's position along its path
        if self.current_target_index < len(self.path):
            target_pos = scaled_positions[self.path[self.current_target_index]]
            dx, dy = target_pos[0] - self.rect.x, target_pos[1] - self.rect.y
            distance = math.sqrt(dx ** 2 + dy ** 2)
            if distance > 1:
                self.rect.x += dx / distance
                self.rect.y += dy / distance
            else:
                self.current_target_index += 1
                if self.current_target_index >= len(self.path):
                    self.current_target_index = 0  # Reset to the start of path

    def distance_to(self, target):
        # Method to calculate distance to a target (e.g., RSU)
        dx = self.rect.centerx - target.rect.centerx
        dy = self.rect.centery - target.rect.centery
        return math.sqrt(dx ** 2 + dy ** 2)

    def send_packet(self, rsu):
        # Method to send packet to RSU
        current_time = time.time()
        if not self.revoked:  # Check for key revocation
            if not self.authenticated:
                print(
                    f"{'Malicious' if self.is_malicious else 'Legitimate'} Vehicle {self.get_vehicle_number()} authenticates with {self.key}")
                self.authenticated = True  # Set authenticated flag to True

            send_msg = f"{'Malicious' if self.is_malicious else 'Legitimate'} Vehicle {self.get_vehicle_number()} Sends message to RSU"

            if self.is_malicious:  # Send packet at a high rate if malicious
                if current_time - self.last_sent_time > 0.0001:
                    self.last_sent_time = current_time
                    self.sent_packets += 1
                    rsu.receive_message(self)
                    print(send_msg)
            else:  # Send packet at a normal rate if legitimate
                if current_time - self.last_sent_time > 0.05:
                    self.last_sent_time = current_time
                    self.sent_packets += 1
                    rsu.receive_message(self)
                    print(send_msg)

    def draw_x(self):
        # Draw 'X' on the vehicle icon if its key is revoked
        if self.revoked:
            pygame.draw.line(screen, RED, self.rect.topleft, self.rect.bottomright, 3)
            pygame.draw.line(screen, RED, self.rect.bottomleft, self.rect.topright, 3)

    def revoke_key(self):
        # Revoke the key of a malicious vehicle
        self.revoked = True
        print(f"Key Revoked From Malicious Vehicle {self.get_vehicle_number()}, further communication will be blocked")

    def get_vehicle_number(self):
        # Get the vehicle number from its list
        if self.is_malicious:
            return malicious_vehicles.index(self) + 1
        else:
            return legitimate_vehicles.index(self) + 1


# Define the RSU class
class RSU(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = rsu_icon
        self.rect = self.image.get_rect(center=(x, y))
        self.ledger = {}  # Ledger to track vehicle keys and their status
        self.vehicle_packet_counts = {}  # Track packet counts for each vehicle

    def receive_message(self, vehicle):
        # Method to receive and process messages from vehicles
        key = id(vehicle)  # Simulate the vehicle's key using its object id

        if key not in self.ledger:
            # Register the vehicle for the first time
            self.ledger[key] = 'active'

        if self.ledger.get(key, 'active') == 'revoked':
            print(f"Message Blocked From Vehicle {vehicle.get_vehicle_number()}, packet dropped")
            return  # Block packet if key is revoked

        # Process the incoming packet and update count
        self.vehicle_packet_counts[vehicle] = self.vehicle_packet_counts.get(vehicle, 0) + 1
        vehicle.packets_received += 1

        if vehicle.is_malicious:
            if self.vehicle_packet_counts[vehicle] > 50:  # Threshold for detecting attacks
                vehicle.revoke_key()
                self.ledger[key] = 'revoked'
                print(f"DDoS attack detected by RSU from Malicious Vehicle {vehicle.get_vehicle_number()}")


# Load and process the road graph from an OSM file
osm_file = 'D:/HONS/Edinburgh.osm'
G = ox.graph_from_xml(osm_file, simplify=True)

positions = {node: (data['x'], data['y']) for node, data in G.nodes(data=True)}  # Extract node positions
edges = list(G.edges())  # Extract list of edges (roads)

# Set bounds for scaling node positions to the screen size
min_x = min(x for x, y in positions.values())
max_x = max(x for x, y in positions.values())
min_y = min(y for x, y in positions.values())
max_y = max(y for x, y in positions.values())


# Function to scale and translate positions to fit the screen
def scale_and_translate(pos):
    x, y = pos
    x = int((x - min_x) / (max_x - min_x) * screen_width)
    y = int((y - min_y) / (max_y - min_y) * screen_height)
    return x, y


scaled_positions = {node: scale_and_translate(pos) for node, pos in positions.items()}  # Apply scaling

# Manage all sprites in a group
all_sprites = pygame.sprite.LayeredUpdates()

# Define paths for malicious vehicles
malicious_vehicle_paths = [
    [list(positions.keys())[i], list(positions.keys())[i + 1], list(positions.keys())[i + 2]]
    for i in range(0, 5)
]

# Create instances of malicious vehicles
malicious_vehicles = [Vehicle(path[0], path, is_malicious=True) for path in malicious_vehicle_paths]

# Define paths for legitimate vehicles
legitimate_vehicle_paths = [
    [list(positions.keys())[i], list(positions.keys())[i + 3], list(positions.keys())[i + 6]]
    for i in range(5, 10)
]

# Offsets for legitimate vehicles to avoid overlap
offsets = [(5, 0), (0, 5), (-5, 0), (0, -5), (5, 5)]

# Create instances of legitimate vehicles
legitimate_vehicles = [Vehicle(path[0], path, is_malicious=False, offset=offset) for path, offset in
                       zip(legitimate_vehicle_paths, offsets)]

font = pygame.font.Font(None, 36)  # Font for displaying texts

# Create RSU instance
rsu1 = RSU(400, 250)

# Add all vehicles and RSU to the sprite group
all_sprites.add(*malicious_vehicles)
all_sprites.add(*legitimate_vehicles)
all_sprites.add(rsu1)

# Collection of all vehicles for processing
vehicles = malicious_vehicles + legitimate_vehicles

start_time = time.time()  # Record simulation start time

# Main simulation loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # Check for quit event
            running = False

    all_sprites.update()  # Update sprite states
    screen.fill(WHITE)  # Clear screen with white background

    # Draw roads
    for edge in edges:
        node1, node2 = edge
        pos1 = scaled_positions[node1]
        pos2 = scaled_positions[node2]
        pygame.draw.line(screen, BLACK, pos1, pos2, 2)

    all_sprites.draw(screen)  # Draw sprites on screen

    # Manage communication
    for vehicle in vehicles:
        if vehicle.distance_to(rsu1) < 300:  # Check communication range
            vehicle.send_packet(rsu1)
            if rsu1.ledger.get(id(vehicle), 'active') == 'active':
                line_color = MALICIOUS_LINE_COLOR if vehicle.is_malicious else LEGITIMATE_LINE_COLOR
                pygame.draw.line(screen, line_color, vehicle.rect.center, rsu1.rect.center, 2)

    for vehicle in vehicles:
        vehicle.draw_x()  # Draw 'X' if the vehicle's key is revoked

    # Draw the timer
    elapsed_time = time.time() - start_time
    timer_text = font.render(f"Time: {elapsed_time:.1f}s", True, RED)
    screen.blit(timer_text, (10, 10))

    pygame.display.flip()  # Update the display

    if elapsed_time > 10:  # End simulation after 10 seconds
        running = False
    time.sleep(0.01)  # Delay for smoother animation

pygame.quit()  # Quit the simulation

# Print diagnostics after simulation ends
print("\nSimulation ended.\n")

# Output diagnostic information about sent and received packets
print(f"Malicious vehicles sent packets: {sum(vehicle.sent_packets for vehicle in malicious_vehicles)}")
print(f"Malicious vehicles received packets: {sum(vehicle.packets_received for vehicle in malicious_vehicles)}")

print("-- Detailed Malicious Vehicle Data --")
for idx, vehicle in enumerate(malicious_vehicles, start=1):
    print(f"Malicious Vehicle {idx}: Sent {vehicle.sent_packets}, Received {vehicle.packets_received}")

print("\n")

print(f"Legitimate vehicles sent packets: {sum(vehicle.sent_packets for vehicle in legitimate_vehicles)}")
print(f"Legitimate vehicles received packets: {sum(vehicle.packets_received for vehicle in legitimate_vehicles)}")

print("-- Detailed Legitimate Vehicle Data --")
for idx, vehicle in enumerate(legitimate_vehicles, start=1):
    print(f"Legitimate Vehicle {idx}: Sent {vehicle.sent_packets}, Received {vehicle.packets_received}")
