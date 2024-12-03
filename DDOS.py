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

# Define colors
WHITE = (255, 255, 255)  # Background color
BLACK = (0, 0, 0)  # Road lines
MALICIOUS_LINE_COLOR = (255, 0, 0)  # Red color for malicious vehicle communication indicators
LEGITIMATE_LINE_COLOR = (0, 255, 0)  # Green color for legitimate vehicle communication indicators
RED = (255, 0, 0)  # Red color for RSU inoperability
QUESTION_MARK_COLOR = (0, 0, 255)  # Blue color for question mark symbols indicating errors

# Load and scale vehicle images
malicious_car_icon = pygame.image.load(r'D:/HONS/Images/MALICIOUS_CAR.png')  # Load image for malicious cars
malicious_car_icon = pygame.transform.scale(malicious_car_icon, (50, 30))  # Scale the image to desired size

legitimate_car_icon = pygame.image.load(r'D:/HONS/Images/LEGITIMATE_CAR.png')  # Load image for legitimate cars
legitimate_car_icon = pygame.transform.scale(legitimate_car_icon, (50, 30))  # Scale the image to desired size

# Load and scale RSU image
rsu_icon = pygame.image.load(r'D:/HONS/Images/RSU.png')
rsu_icon = pygame.transform.scale(rsu_icon, (90, 90))

# Timer setup for the DDoS simulation
ddos_timer = pygame.time.get_ticks()  # Get the current time in milliseconds
ddos_duration = 10000  # Set the duration to 10 seconds


# Vehicle class represents both malicious and legitimate vehicles
class Vehicle(pygame.sprite.Sprite):
    def __init__(self, start_node, path, image, offset=(0, 0), is_malicious=False):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(center=scaled_positions[start_node])
        self.rect.x += offset[0]  # Adjust the x position
        self.rect.y += offset[1]  # Adjust the y position
        self.path = path  # Path for the vehicle to follow
        self.current_target_index = 0  # Index to track path progress
        self.communication_error = False  # Flag to indicate communication errors
        self.sent_packets = 0  # Count packets sent by the vehicle
        self.legitimate_received_packets = 0  # Count packets received by legitimate vehicles
        self.malicious_received_packets = 0  # Count packets received by malicious vehicles
        self.is_malicious = is_malicious  # Flag to identify if vehicle is malicious

    def send_packet(self, rsu):
        self.sent_packets += 1  # Increment sent packet count
        rsu.receive_message(self)  # Send a message to the RSU

    def update(self):
        if len(self.path) > 0:
            target_pos = scaled_positions[self.path[self.current_target_index]]  # Get target position
            dx, dy = target_pos[0] - self.rect.x, target_pos[1] - self.rect.y  # Calculate distances
            distance = math.sqrt(dx ** 2 + dy ** 2)  # Calculate Euclidean distance
            if distance > 1:
                self.rect.x += dx / distance  # Move towards the target
                self.rect.y += dy / distance
            else:
                self.current_target_index += 1  # Move to the next target in the path
                if self.current_target_index >= len(self.path):
                    self.current_target_index = 0  # Loop back to the start of the path

    def distance_to(self, rsu):
        # Calculate the distance from the vehicle to the RSU
        dx = self.rect.centerx - rsu.rect.centerx
        dy = self.rect.centery - rsu.rect.centery
        return math.sqrt(dx ** 2 + dy ** 2)

    def draw_communication_error_marker(self, screen):
        # Draw a question mark to indicate a communication error
        if self.communication_error:
            font = pygame.font.Font(None, 36)
            error_marker = font.render("?", True, (255, 0, 0))  # Red question mark
            screen.blit(error_marker, (self.rect.centerx - 15, self.rect.centery - 20))


# Specialized class for malicious vehicles
class MaliciousVehicle(Vehicle):
    def __init__(self, start_node, path, image, offset=(0, 0)):
        super().__init__(start_node, path, image, offset, is_malicious=True)
        self.last_sent_time = time.time()  # Initialize the timer for sending messages

    def send_packet(self, rsu):
        current_time = time.time()  # Get the current time
        if current_time - self.last_sent_time > 0.0001:  # Check if enough time has passed
            self.last_sent_time = current_time  # Update the last sent time
            print(f"Malicious Vehicle {malicious_vehicles.index(self) + 1} sending DDoS messages to RSU")
            self.sent_packets += 1  # Increment sent packet count
            rsu.receive_message(self)  # Send a message to the RSU


# Specialized class for legitimate vehicles
class LegitimateVehicle(Vehicle):
    def __init__(self, start_node, path, image, offset=(0, 0)):
        super().__init__(start_node, path, image, offset, is_malicious=False)
        self.last_sent_time = time.time()  # Initialize the timer for sending messages

    def send_packet(self, rsu):
        current_time = time.time()  # Get the current time
        if current_time - self.last_sent_time > 0.05:  # Check if enough time has passed
            self.last_sent_time = current_time  # Update the last sent time
            self.sent_packets += 1  # Increment sent packet count
            print(f"Legitimate Vehicle {legitimate_vehicles.index(self) + 1} sending normal packets to RSU")
            rsu.receive_message(self)  # Send a message to the RSU


# RSU (Roadside Unit) class to receive messages from vehicles
class RSU(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = rsu_icon  # Set the RSU image
        self.rect = self.image.get_rect(center=(x, y))  # Set the RSU position
        self.message_count = 0  # Initialize message counter
        self.max_messages = 2500  # Set message limit before RSU becomes non-operational
        self.operational = True  # Flag to indicate if RSU is operational
        self.malicious_received = 0  # Count messages received from malicious vehicles
        self.legitimate_received = 0  # Count messages received from legitimate vehicles

    def receive_message(self, vehicle):
        if not self.operational:  # If RSU is not operational, stop processing
            return
        self.message_count += 1  # Increment the message count

        if vehicle.is_malicious:
            vehicle.malicious_received_packets += 1  # Track packets for malicious vehicles
            self.malicious_received += 1  # Increment count of malicious messages
        else:
            vehicle.legitimate_received_packets += 1  # Track packets for legitimate vehicles
            self.legitimate_received += 1  # Increment count of legitimate messages

        if self.message_count > self.max_messages:  # Check if RSU exceeds message limit
            self.operational = False
            print("RSU is no longer operational due to DDoS attack.")  # Print inoperability message

    def reset(self):
        # Reset RSU state for message counting and operational status
        self.message_count = 0
        self.operational = True

# Load and process the road graph from an OSM file
osm_file = 'D:/HONS/Edinburgh.osm'
G = ox.graph_from_xml(osm_file, simplify=True)  # Create a graph from the OSM file

positions = {node: (data['x'], data['y']) for node, data in G.nodes(data=True)}  # Extract node positions
edges = list(G.edges())  # Extract edges to represent roads

# Minimum and maximum coordinates for scaling
min_x = min(x for x, y in positions.values())
max_x = max(x for x, y in positions.values())
min_y = min(y for x, y in positions.values())
max_y = max(y for x, y in positions.values())

def scale_and_translate(pos):
    # Scale and translate node positions for screen rendering
    x, y = pos
    x = int((x - min_x) / (max_x - min_x) * screen_width)
    y = int((y - min_y) / (max_y - min_y) * screen_height)
    return x, y

scaled_positions = {node: scale_and_translate(pos) for node, pos in positions.items()}  # Apply scaling

all_sprites = pygame.sprite.LayeredUpdates()  # Group to manage all sprites

# Define paths for malicious vehicles
malicious_vehicle_paths = [
    [list(positions.keys())[i], list(positions.keys())[i + 1], list(positions.keys())[i + 2]]
    for i in range(0, 5)
]

# Create malicious vehicle instances
malicious_vehicles = [MaliciousVehicle(path[0], path, malicious_car_icon) for path in malicious_vehicle_paths]

# Define paths for legitimate vehicles
legitimate_vehicle_paths = [
    [list(positions.keys())[i], list(positions.keys())[i + 3], list(positions.keys())[i + 6]]
    for i in range(5, 10)
]

# Offsets to prevent overlap of legitimate vehicles
offsets = [(5, 0), (0, 5), (-5, 0), (0, -5), (5, 5)]

# Create legitimate vehicle instances
legitimate_vehicles = [
    LegitimateVehicle(path[0], path, legitimate_car_icon, offset=offset) for path, offset in
    zip(legitimate_vehicle_paths, offsets)
]

# Font setup for displaying text
font = pygame.font.Font(None, 36)

rsu1 = RSU(400, 250)  # Define a single RSU

all_sprites.add(*malicious_vehicles)  # Add malicious vehicles to the sprite group
all_sprites.add(*legitimate_vehicles)  # Add legitimate vehicles to the sprite group
all_sprites.add(rsu1)  # Add RSU to the sprite group

# Main simulation loop
running = True
start_time = time.time()  # Record start time for elapsed time calculation

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:  # Quit event to close the simulation
            running = False

    all_sprites.update()  # Update all vehicle positions and states
    screen.fill(WHITE)  # Clear the screen with white background

    # Draw road lines
    for edge in edges:
        node1, node2 = edge
        pos1 = scaled_positions[node1]
        pos2 = scaled_positions[node2]
        pygame.draw.line(screen, BLACK, pos1, pos2, 2)  # Draw black lines for roads

    all_sprites.draw(screen)  # Draw all sprites on the screen

    # Manage communication
    for vehicle in malicious_vehicles + legitimate_vehicles:
        if vehicle.distance_to(rsu1) < 300:  # Check if vehicle is within communication range
            vehicle.send_packet(rsu1)  # Send packet to RSU
            if rsu1.operational:
                line_color = MALICIOUS_LINE_COLOR if vehicle.is_malicious else LEGITIMATE_LINE_COLOR
                pygame.draw.line(screen, line_color, vehicle.rect.center, rsu1.rect.center, 2)  # Indicate communication
                if vehicle.is_malicious:
                    print(f"Malicious Vehicle {malicious_vehicles.index(vehicle) + 1} sending DDoS messages to RSU")
                else:
                    print(f"Legitimate Vehicle {legitimate_vehicles.index(vehicle) + 1} communicating with RSU")
            else:
                if vehicle in legitimate_vehicles:
                    vehicle.communication_error = True  # Flag communication error
                    print(
                        f"Legitimate Vehicle {legitimate_vehicles.index(vehicle) + 1} cannot communicate with RSU (RSU offline)")

    # Check if the RSU is operational
    if not rsu1.operational:
        # Draw a red rectangle around the RSU to indicate it is inoperable
        pygame.draw.rect(screen, RED, (rsu1.rect.x - 10, rsu1.rect.y - 10, rsu1.rect.width + 20, rsu1.rect.height + 20),
                         5)
        font = pygame.font.Font(None, 36)
        text = font.render('RSU INOPERABLE', True, (255, 0, 0))
        screen.blit(text, (rsu1.rect.x + 10, rsu1.rect.y - 30))  # Display text for RSU inoperability

        # Display communication error markers on legitimate vehicles
        for vehicle in legitimate_vehicles:
            if vehicle.communication_error:
                vehicle.draw_communication_error_marker(screen)

    # Calculate elapsed time
    elapsed_time = time.time() - start_time

    # Display elapsed time on the screen
    timer_text = font.render(f"Time: {elapsed_time:.1f}s", True, RED)
    screen.blit(timer_text, (10, 10))

    pygame.display.flip()  # Refresh the display
    if elapsed_time > 10:  # End simulation after 10 seconds
        running = False
    time.sleep(0.01)  # Delay for smoother animation

pygame.quit()  # Terminate the simulation

print("\nSimulation ended.\n")

# Output diagnostic information about sent and received packets
print(f"Malicious vehicles sent packets: {sum(vehicle.sent_packets for vehicle in malicious_vehicles)}")
print(
    f"Malicious vehicles received packets: {sum(vehicle.malicious_received_packets for vehicle in malicious_vehicles)}")
print("\n")
print("-- Detailed Malicious Vehicle Data --")
for idx, vehicle in enumerate(malicious_vehicles, start=1):
    print(f"Malicious Vehicle {idx}: Sent {vehicle.sent_packets} - Received {vehicle.malicious_received_packets}")

print("\n")

print(f"Legitimate vehicles sent packets: {sum(vehicle.sent_packets for vehicle in legitimate_vehicles)}")
print(
    f"Legitimate vehicles received packets: {sum(vehicle.legitimate_received_packets for vehicle in legitimate_vehicles)}")
print("\n")
print("-- Detailed Legitimate Vehicle Data --")
for idx, vehicle in enumerate(legitimate_vehicles, start=1):
    print(f"Legitimate Vehicle {idx}: Sent {vehicle.sent_packets} - Received {vehicle.legitimate_received_packets}")

print("\n")