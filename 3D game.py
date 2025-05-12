import OpenGL.GL as gl
import OpenGL.GLUT as glut
import OpenGL.GLU as glu
import math
import random
import numpy as np
import time

GROUND_SIZE = 600  # half-size, so land is -600 to +600

# Window dimensions
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 900

# Camera variables
cam_pos = [0.0, 50.0, 400.0]  # x, y, z
cam_yaw = 0.0  # horizontal angle (degrees)
cam_pitch = 20.0  # vertical angle (degrees, up/down)
cam_speed = 10.0
mouse_last_x = WINDOW_WIDTH // 2
mouse_last_y = WINDOW_HEIGHT // 2
mouse_sensitivity = 0.12
move_forward = move_backward = move_left = move_right = False

# Sun/Moon properties
SUN_RADIUS = 30
MOON_RADIUS = 20
STAR_COUNT = 200  # Increased for denser night sky

# Celestial
class CelestialBodyManager:
    def __init__(self):
        self.sun_position = 0
        self.is_day = True
        self.stars = [
            (random.uniform(-GROUND_SIZE, GROUND_SIZE), random.uniform(600, 900), random.uniform(-GROUND_SIZE, GROUND_SIZE))
            for _ in range(STAR_COUNT)
        ]

    def update_background_color(self):
        if not self.is_day:
            gl.glClearColor(0.05, 0.05, 0.15, 1.0)  # Night sky
        elif current_season == 2:
            gl.glClearColor(0.7, 0.7, 0.7, 1.0)  # Light grey for rain
        else:
            gl.glClearColor(0.53, 0.81, 0.98, 1.0)  # Sky blue

    def toggle_day_night(self):
        self.sun_position += 5
        if self.sun_position >= 180:
            self.sun_position = 0
            self.is_day = not self.is_day

    def draw_sun_or_moon(self):
        angle = self.sun_position
        radius = 800  # Set radius to 800 units to move sun further from center
        x = math.cos(math.radians(angle)) * radius + 100  # Offset to the right
        y = math.sin(math.radians(angle)) * 400  # Allow sun to go below ground
        z = 0
        gl.glPushMatrix()
        gl.glTranslatef(x, y, z)
        if self.is_day:
            gl.glColor3f(1.0, 1.0, 0.0)
            glut.glutSolidSphere(SUN_RADIUS, 32, 32)
        else:
            gl.glColor3f(0.9, 0.9, 1.0)
            glut.glutSolidSphere(MOON_RADIUS, 32, 32)
        gl.glPopMatrix()

    def draw_stars(self):
        gl.glColor3f(1.0, 1.0, 1.0)
        gl.glPointSize(2.0)
        gl.glBegin(gl.GL_POINTS)
        for x, y, z in self.stars:
            gl.glVertex3f(x, y, z)
        gl.glEnd()

    def update_and_draw(self):
        # Sun is up from 0 to 180, moon from 180 to 360
        if 0 <= self.sun_position < 180:
            self.is_day = True
        else:
            self.is_day = False
        self.update_background_color()
        self.draw_sun_or_moon()
        if not self.is_day:
            self.draw_stars()

celestial_manager = CelestialBodyManager()

# Ground
def draw_ground():
    if current_season == 3:
        gl.glColor3f(1.0, 1.0, 1.0)  # White for winter
    else:
        gl.glColor3f(0.0, 0.8, 0.0)
    gl.glBegin(gl.GL_QUADS)
    gl.glVertex3f(-GROUND_SIZE, 0, -GROUND_SIZE)
    gl.glVertex3f(GROUND_SIZE, 0, -GROUND_SIZE)
    gl.glVertex3f(GROUND_SIZE, 0, GROUND_SIZE)
    gl.glVertex3f(-GROUND_SIZE, 0, GROUND_SIZE)
    gl.glEnd()

# Grass
class GrassBlade:
    def __init__(self, x, z, height, width, color):
        self.x = x
        self.z = z
        self.height = height
        self.width = width
        self.color = color
        self.bend = 0

    def draw(self):
        gl.glColor3f(*self.color)
        gl.glBegin(gl.GL_LINES)
        gl.glVertex3f(self.x, 0, self.z)
        gl.glVertex3f(self.x + self.bend, self.height, self.z)
        gl.glEnd()

    def update(self, wind_strength, wind_direction):
        self.bend += wind_strength * wind_direction
        self.bend += random.uniform(-0.5, 0.5)
        self.bend = max(min(self.bend, self.height // 2), -self.height // 2)

class GrassField:
    def __init__(self, blade_count=4000):
        self.blades = []
        self.wind_strength = 0
        self.wind_direction = 0
        self.initialize_blades(blade_count)

    def initialize_blades(self, blade_count=4000):
        self.blades = []
        for _ in range(blade_count):
            x = random.randint(-GROUND_SIZE, GROUND_SIZE)
            z = random.randint(-GROUND_SIZE, GROUND_SIZE)
            # Skip grass if inside pond radius
            pond_x, pond_z, pond_r = -200, 0, 60
            dist = ((x - pond_x)**2 + (z - pond_z)**2)**0.5
            if dist < pond_r + 8:
                continue
            height = 18
            width = random.randint(10, 30)
            green = random.uniform(0.4, 1.0)
            color = (0, green, 0)
            self.blades.append(GrassBlade(x, z, height, width, color))

    def update_and_draw(self):
        for blade in self.blades:
            blade.update(self.wind_strength, self.wind_direction)
            blade.draw()
        self.wind_strength *= 0.5

grass_field = GrassField(4000)

# Tree

def draw_cylinder(x, y, z, height, radius, color):
    gl.glPushMatrix()
    gl.glTranslatef(x, y, z)
    gl.glColor3f(*color)
    quad = glu.gluNewQuadric()
    glu.gluCylinder(quad, radius, radius * 0.8, height, 8, 1)
    gl.glPopMatrix()

def draw_pond():
    pond_radius = 60
    pond_height = 8
    gl.glColor3f(0.0, 0.5, 1.0)
    gl.glPushMatrix()
    gl.glTranslatef(-200, 0, 0)  # y=0 so bottom is at ground
    gl.glRotatef(-90, 1, 0, 0)
    quad = glu.gluNewQuadric()
    glu.gluCylinder(quad, pond_radius, pond_radius, pond_height, 40, 1)
    glu.gluDisk(quad, 0, pond_radius, 40, 1)  # top
    gl.glTranslatef(0, 0, pond_height)
    glu.gluDisk(quad, 0, pond_radius, 40, 1)  # bottom
    gl.glPopMatrix()

# Character

player_facing = 0.0  # degrees
walk_anim_phase = 0.0
walk_anim_speed = 0.18  # radians per frame
last_time = time.time()

def draw_minecraft_player(x, y, z, facing):
    head_size = 8
    body_w, body_h, body_d = 6, 12, 4
    arm_w, arm_h, arm_d = 2.5, 10, 2.5
    leg_w, leg_h, leg_d = 2.5, 10, 2.5
    global walk_anim_phase
    swing = math.sin(walk_anim_phase) * 30
    gl.glPushMatrix()
    gl.glTranslatef(x, y, z)
    gl.glRotatef(facing, 0, 1, 0)
    # Head
    gl.glColor3f(0.0, 0.0, 0.0)  # Black head
    gl.glPushMatrix()
    gl.glTranslatef(0, body_h + head_size/2, 0)
    glut.glutSolidCube(head_size)
    gl.glPopMatrix()
    # Body
    gl.glColor3f(1.0, 0.0, 0.0)  # Red body
    gl.glPushMatrix()
    gl.glTranslatef(0, body_h/2, 0)
    gl.glScalef(body_w, body_h, body_d)
    glut.glutSolidCube(1)
    gl.glPopMatrix()
    # Left Arm
    gl.glColor3f(0.55, 0.27, 0.07)  # Brown arms
    gl.glPushMatrix()
    gl.glTranslatef(-(body_w/2 + arm_w/2), body_h - arm_h/2, 0)
    gl.glRotatef(swing, 1, 0, 0)
    gl.glScalef(arm_w, arm_h, arm_d)
    glut.glutSolidCube(1)
    gl.glPopMatrix()
    # Right Arm
    gl.glColor3f(0.55, 0.27, 0.07)  # Brown arms
    gl.glPushMatrix()
    gl.glTranslatef((body_w/2 + arm_w/2), body_h - arm_h/2, 0)
    gl.glRotatef(-swing, 1, 0, 0)
    gl.glScalef(arm_w, arm_h, arm_d)
    glut.glutSolidCube(1)
    gl.glPopMatrix()  # End right arm
    # Left Leg (closer to center)
    gl.glColor3f(0.0, 0.0, 0.0)  # Black legs
    gl.glPushMatrix()
    gl.glTranslatef(-body_w/6, -leg_h/2, 0)
    gl.glRotatef(-swing, 1, 0, 0)
    gl.glScalef(leg_w, leg_h, leg_d)
    glut.glutSolidCube(1)
    gl.glPopMatrix()
    # Right Leg (closer to center)
    gl.glColor3f(0.0, 0.0, 0.0)  # Black legs
    gl.glPushMatrix()
    gl.glTranslatef(body_w/6, -leg_h/2, 0)
    gl.glRotatef(swing, 1, 0, 0)
    gl.glScalef(leg_w, leg_h, leg_d)
    glut.glutSolidCube(1)
    gl.glPopMatrix()
    gl.glPopMatrix()

# Rain
class Raindrop:
    def __init__(self):
        self.x = random.uniform(-GROUND_SIZE, GROUND_SIZE)
        self.y = random.uniform(200, 400)
        self.z = random.uniform(-GROUND_SIZE, GROUND_SIZE)
        self.speed = 8
    def update(self):
        self.y -= self.speed
        return self.y > 0

def draw_rain(raindrops):
    gl.glColor3f(0.5, 0.5, 1.0)
    gl.glBegin(gl.GL_LINES)
    for drop in raindrops:
        gl.glVertex3f(drop.x, drop.y, drop.z)
        gl.glVertex3f(drop.x, drop.y - 15, drop.z)
    gl.glEnd()

# Snow
class Snowflake:
    def __init__(self):
        self.x = random.uniform(-GROUND_SIZE, GROUND_SIZE)
        self.y = random.uniform(200, 400)
        self.z = random.uniform(-GROUND_SIZE, GROUND_SIZE)
        self.speed = random.uniform(2, 4)
    def update(self):
        self.y -= self.speed
        if self.y < 0:
            self.x = random.uniform(-GROUND_SIZE, GROUND_SIZE)
            self.y = random.uniform(200, 400)
            self.z = random.uniform(-GROUND_SIZE, GROUND_SIZE)
            self.speed = random.uniform(2, 4)
        return True

def draw_snow(snowflakes):
    gl.glColor3f(1.0, 1.0, 1.0)
    gl.glPointSize(3.0)
    gl.glBegin(gl.GL_POINTS)
    for flake in snowflakes:
        gl.glVertex3f(flake.x, flake.y, flake.z)
    gl.glEnd()

# Falling leaves
class Leaf:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.speed = 2
        self.swing = random.uniform(-1, 1)
        if current_season == 3:
            self.color = [1.0, 1.0, 1.0]
        else:
            self.color = [0.0, 0.4, 0.0]  # Dark green
    def update(self):
        self.y -= self.speed
        self.x += math.sin(self.y / 20) * self.swing
        return self.y > 0

def draw_falling_leaves(leaves):
    for leaf in leaves:
        gl.glColor3f(*leaf.color)
        gl.glPushMatrix()
        gl.glTranslatef(leaf.x, leaf.y, leaf.z)
        glut.glutSolidSphere(5, 8, 8)
        gl.glPopMatrix()

# Global state
raindrops = []
snowflakes = []
falling_leaves = []
current_season = 1  # 1: Summer, 2: Rainy, 3: Winter
character_pos = [-120, 10, 0]
character_direction = 1
leaves_falling = False
leaves_falling_start_time = None  # Track when leaves started falling

tree_regrow_pending = False  # Track if regrow is pending

tree_regrow_start_time = None  # Track when regrow started

# Player movement
player_height = 24 + 12  # body + half head
player_pos = [0.0, player_height / 2, 200.0]  # Start offset from center tree
player_speed = 6.0
move_player_forward = move_player_backward = move_player_left = move_player_right = False

# Camera movement

is_first_person = False

# --- Speed boost toggle ---
player_speed_boosted = False
player_speed_normal = 6.0
player_speed_fast = 12.0

# --- Add trees_saved counter ---
trees_saved = 0

# --- Add total_pour_time for water pot ---
total_pour_time = 0.0

# --- Falling leaves chain state ---
falling_chain_active = False
falling_chain_next_time = None
falling_chain_last_tree = None
FALLING_CHAIN_DELAY = 5.0  # seconds between trees losing leaves
MAX_DEAD_TREES = 5
falling_chain_paused = True  # Start paused

game_state = "Paused"  # Possible: Paused, Playing, Game Over, Victory

def get_camera_pos():
    if is_first_person:
        head_height = 24
        yaw_rad = math.radians(cam_yaw)
        pitch_rad = math.radians(cam_pitch)
        cam_y = max(player_pos[1] + head_height, 10)  # Clamp above ground
        return [player_pos[0], cam_y, player_pos[2]]
    else:
        cam_distance = 120
        yaw_rad = math.radians(cam_yaw)
        pitch_rad = math.radians(cam_pitch)
        cam_x = player_pos[0] - cam_distance * math.sin(yaw_rad) * math.cos(-pitch_rad)
        cam_y = player_pos[1] + 24 + cam_distance * math.sin(-pitch_rad)  # Offset up to see over player
        cam_z = player_pos[2] + cam_distance * math.cos(yaw_rad) * math.cos(-pitch_rad)
        cam_y = max(cam_y, 10)  # Clamp camera above ground
        return [cam_x, cam_y, cam_z]

# --- Watering pot state ---
watering_pot_visible = False
watering_pot_fullness = 0  # 0 or 100
watering_pot_pouring = False
watering_pot_pour_timer = 0
watering_pot_pour_rate = 100.0 / (2 * 60)  # 2 seconds to empty

# --- Draw watering pot in player's right hand ---
def draw_player_hand():
    if not watering_pot_visible:
        return
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPushMatrix()
    gl.glLoadIdentity()
    glu.gluPerspective(60, WINDOW_WIDTH / float(WINDOW_HEIGHT), 1, 2000)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPushMatrix()
    gl.glLoadIdentity()
    gl.glTranslatef(0.7, -0.7, -2.0)
    gl.glRotatef(30, 1, 0, 0)
    gl.glRotatef(20, 0, 1, 0)
    # Draw watering pot (simple blue cylinder)
    gl.glColor3f(0.2, 0.2, 1.0)
    gl.glPushMatrix()
    gl.glScalef(1, 1.5, 1)
    quad = glu.gluNewQuadric()
    glu.gluCylinder(quad, 0.12, 0.12, 0.25, 16, 1)
    gl.glPopMatrix()
    # Draw handle
    gl.glColor3f(0.7, 0.7, 0.7)
    gl.glPushMatrix()
    gl.glTranslatef(0.12, 0.1, 0)
    gl.glRotatef(90, 0, 1, 0)
    glut.glutSolidTorus(0.025, 0.07, 8, 12)
    gl.glPopMatrix()
    gl.glPopMatrix()
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPopMatrix()
    gl.glMatrixMode(gl.GL_MODELVIEW)

# --- Animate water pouring at tree ---
def draw_water_pour():
    if not watering_pot_pouring:
        return
    # Find nearest tree
    nearest = min([main_tree]+other_trees, key=lambda t: ((player_pos[0]-t.x)**2 + (player_pos[2]-t.z)**2)**0.5)
    # Water falls from player's hand to a spot in front of player, then to tree
    hand_x = player_pos[0] + 12 * math.sin(math.radians(player_facing))
    hand_y = player_pos[1] + 18
    hand_z = player_pos[2] - 12 * math.cos(math.radians(player_facing))
    # Spot in front of player
    pour_spot_dist = 40
    spot_x = player_pos[0] + pour_spot_dist * math.sin(math.radians(player_facing))
    spot_y = 0
    spot_z = player_pos[2] - pour_spot_dist * math.cos(math.radians(player_facing))
    # Tree base
    tree_x, tree_y, tree_z = nearest.x, 0, nearest.z
    gl.glColor3f(0.2, 0.5, 1.0)
    gl.glLineWidth(4)
    gl.glBegin(gl.GL_LINES)
    # Water from hand to spot
    for i in range(3):
        sx = spot_x + random.uniform(-5, 5)
        sz = spot_z + random.uniform(-5, 5)
        gl.glVertex3f(hand_x, hand_y, hand_z)
        gl.glVertex3f(sx, 0, sz)
        # Water from spot to tree
        gl.glVertex3f(sx, 0, sz)
        gl.glVertex3f(tree_x + random.uniform(-10, 10), 0, tree_z + random.uniform(-10, 10))
    gl.glEnd()
    gl.glLineWidth(1)

# --- Add at the top, after global state ---
tree_has_leaves = True
leaves_regrow_progress = 0.0  # 0.0 (bare) to 1.0 (full leaves)
regrow_start_time = None
pour_start_time = None
pouring_duration = 0.0

# --- Tree class for multiple trees ---
class Tree:
    def __init__(self, x, z, size=1.0):
        self.x = x
        self.z = z
        self.size = size
        self.has_leaves = True
        self.leaves_regrow_progress = 0.0
        self.regrow_start_time = None
        self.leaves_falling = False
        self.leaves_falling_start_time = None
        self.falling_leaves = []
        self.pouring = False
        self.pour_start_time = None
        self.pouring_duration = 0.0
        self.pour_accumulated = 0.0  # Track accumulated pour time
    def update(self):
        # Falling logic
        if self.leaves_falling:
            if self.leaves_falling_start_time is not None:
                if time.time() - self.leaves_falling_start_time >= 10:
                    self.leaves_falling = False
                    self.falling_leaves.clear()
                    self.leaves_falling_start_time = None
                    self.has_leaves = False
                    self.leaves_regrow_progress = 0.0
            else:
                self.leaves_falling_start_time = time.time()
        else:
            self.leaves_falling_start_time = None
        # Regrow logic
        if self.regrow_start_time is not None:
            elapsed = time.time() - self.regrow_start_time
            self.leaves_regrow_progress = min(elapsed / 10.0, 1.0)
            if self.leaves_regrow_progress >= 1.0:
                self.regrow_start_time = None
                self.has_leaves = True
        # Pouring logic
        if self.pouring:
            if self.pour_start_time is None:
                self.pour_start_time = time.time()
                self.pouring_duration = 0.0
            else:
                now = time.time()
                delta = now - self.pour_start_time
                self.pouring_duration = delta
                self.pour_accumulated += delta
                self.pour_start_time = now
                if self.pouring_duration >= 20.0:
                    self.pouring = False
                    self.pour_start_time = None
            # Start regrow if not already, and only if poured for 5 seconds
            if not self.has_leaves and self.regrow_start_time is None and self.pour_accumulated >= 5.0:
                self.regrow_start_time = time.time()
        else:
            self.pour_start_time = None
            self.pour_accumulated = 0.0  # Reset if not pouring
        # Falling leaves animation
        if self.leaves_falling:
            block_size = 32 * self.size
            trunk_height = 6 * block_size
            top_y = 0 + trunk_height
            canopy_half = 5 * block_size
            if len(self.falling_leaves) < 30:
                lx = self.x + random.uniform(-canopy_half, canopy_half)
                lz = self.z + random.uniform(-canopy_half, canopy_half)
                ly = top_y
                self.falling_leaves.append(Leaf(lx, ly, lz))
            self.falling_leaves[:] = [leaf for leaf in self.falling_leaves if leaf.update()]
        else:
            self.falling_leaves.clear()
    def draw(self):
        draw_minecraft_tree(self.x, 0, self.z, self.size, self.has_leaves, self.leaves_regrow_progress)
        if self.leaves_falling:
            draw_falling_leaves(self.falling_leaves)

# --- Update tree placement to avoid pond ---
def is_too_close_to_pond(x, z):
    pond_x, pond_z, pond_r = -200, 0, 60
    dist = ((x - pond_x)**2 + (z - pond_z)**2)**0.5
    return dist < pond_r + 80

main_tree = Tree(0, 0, 1.0)  # Center of the land
other_trees = []
# Place 4 trees at the four sides of the land
side_offset = GROUND_SIZE - 80  # 80 units from the edge
positions = [
    (-side_offset, 0),   # Left
    (side_offset, 0),    # Right
    (0, side_offset),    # Top
    (0, -side_offset)    # Bottom
]
for tx, tz in positions:
    tsize = random.uniform(0.5, 0.95)
    other_trees.append(Tree(tx, tz, tsize))

# --- Scoring and game state ---
game_over = False
status_message = ""
status_message_timer = 0

def reset_game():
    global main_tree, other_trees, game_over, status_message, status_message_timer, watering_pot_fullness, watering_pot_visible, watering_pot_pouring, trees_saved, victory, total_pour_time
    global player_pos
    global falling_chain_active, falling_chain_next_time, falling_chain_last_tree, falling_chain_paused, game_state
    global move_player_forward, move_player_backward, move_player_left, move_player_right
    main_tree = Tree(0, 0, 1.0)
    other_trees.clear()
    side_offset = GROUND_SIZE - 80
    positions = [
        (-side_offset, 0),   # Left
        (side_offset, 0),    # Right
        (0, side_offset),    # Top
        (0, -side_offset)    # Bottom
    ]
    for tx, tz in positions:
        tsize = random.uniform(0.5, 0.95)
        other_trees.append(Tree(tx, tz, tsize))
    player_pos = [0.0, player_height / 2, 200.0]  # Reset player away from center
    game_over = False
    status_message = ""
    status_message_timer = 0
    watering_pot_fullness = 0
    watering_pot_visible = False
    watering_pot_pouring = False
    trees_saved = 0
    victory = False
    total_pour_time = 0.0
    falling_chain_active = False
    falling_chain_next_time = None
    falling_chain_last_tree = None
    falling_chain_paused = True
    game_state = "Paused"
    # Reset movement flags
    move_player_forward = False
    move_player_backward = False
    move_player_left = False
    move_player_right = False

# --- Draw score/status at top right ---
def draw_score_status():
    dead_count = sum(1 for t in [main_tree]+other_trees if not t.has_leaves and t.leaves_regrow_progress == 0.0)
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPushMatrix()
    gl.glLoadIdentity()
    gl.glOrtho(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, -1, 1)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPushMatrix()
    gl.glLoadIdentity()
    # Draw dead tree count
    gl.glColor3f(1, 1, 1)
    gl.glRasterPos2f(WINDOW_WIDTH - 320, WINDOW_HEIGHT - 40)
    if dead_count == 1:
        msg = b"1 Tree Has died"
    else:
        msg = f"{dead_count} Trees Have died".encode()
    for c in msg:
        glut.glutBitmapCharacter(glut.GLUT_BITMAP_HELVETICA_18, c)
    # Draw saved tree count
    gl.glRasterPos2f(WINDOW_WIDTH - 320, WINDOW_HEIGHT - 70)
    msg2 = f"Trees Saved: {trees_saved}".encode()
    for c in msg2:
        glut.glutBitmapCharacter(glut.GLUT_BITMAP_HELVETICA_18, c)
    # Draw water percentage
    percent = int(100 * max(0, 1 - total_pour_time / 40.0))
    gl.glRasterPos2f(WINDOW_WIDTH - 320, WINDOW_HEIGHT - 100)
    msg3 = f"Water: {percent}%".encode()
    for c in msg3:
        glut.glutBitmapCharacter(glut.GLUT_BITMAP_HELVETICA_18, c)
    # Draw status message
    if status_message:
        gl.glRasterPos2f(WINDOW_WIDTH - 320, WINDOW_HEIGHT - 130)
        for c in status_message.encode():
            glut.glutBitmapCharacter(glut.GLUT_BITMAP_HELVETICA_18, c)
    # Draw game state
    gl.glColor3f(1, 1, 0)
    gl.glRasterPos2f(WINDOW_WIDTH - 320, WINDOW_HEIGHT - 160)
    msg4 = f"Game State: {game_state}".encode()
    for c in msg4:
        glut.glutBitmapCharacter(glut.GLUT_BITMAP_HELVETICA_18, c)
    gl.glPopMatrix()
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPopMatrix()
    gl.glMatrixMode(gl.GL_MODELVIEW)

# --- Draw Game Over in center ---
def draw_game_over():
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPushMatrix()
    gl.glLoadIdentity()
    gl.glOrtho(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, -1, 1)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPushMatrix()
    gl.glLoadIdentity()
    gl.glColor3f(1, 0, 0)
    gl.glRasterPos2f(WINDOW_WIDTH//2 - 120, WINDOW_HEIGHT//2)
    msg = b"GAME OVER"
    for c in msg:
        glut.glutBitmapCharacter(glut.GLUT_BITMAP_TIMES_ROMAN_24, c)
    gl.glPopMatrix()
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPopMatrix()
    gl.glMatrixMode(gl.GL_MODELVIEW)

# --- Add victory state and display ---
victory = False

# --- Draw Victory in center, big and red ---
def draw_victory():
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPushMatrix()
    gl.glLoadIdentity()
    gl.glOrtho(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, -1, 1)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPushMatrix()
    gl.glLoadIdentity()
    gl.glColor3f(1, 0, 0)
    # Centered, big font
    gl.glRasterPos2f(WINDOW_WIDTH//2 - 200, WINDOW_HEIGHT//2 + 30)
    msg = b"VICTORY!"
    for c in msg:
        glut.glutBitmapCharacter(glut.GLUT_BITMAP_TIMES_ROMAN_24, c)
    gl.glRasterPos2f(WINDOW_WIDTH//2 - 200, WINDOW_HEIGHT//2 - 30)
    for c in msg:
        glut.glutBitmapCharacter(glut.GLUT_BITMAP_TIMES_ROMAN_24, c)
    gl.glPopMatrix()
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPopMatrix()
    gl.glMatrixMode(gl.GL_MODELVIEW)

# GLUT callbacks

def display():
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
    gl.glLoadIdentity()
    cam_x, cam_y, cam_z = get_camera_pos()
    if is_first_person:
        look_dist = 100
        yaw_rad = math.radians(cam_yaw)
        pitch_rad = math.radians(cam_pitch)
        look_x = cam_x + look_dist * math.sin(yaw_rad) * math.cos(pitch_rad)
        look_y = cam_y + look_dist * math.sin(pitch_rad)
        look_z = cam_z - look_dist * math.cos(yaw_rad) * math.cos(pitch_rad)
        glu.gluLookAt(cam_x, cam_y, cam_z,
                      look_x, look_y, look_z,
                      0, 1, 0)
    else:
        glu.gluLookAt(cam_x, cam_y, cam_z,
                      player_pos[0], player_pos[1] + 12, player_pos[2],
                      0, 1, 0)
    celestial_manager.update_and_draw()
    draw_ground()
    grass_field.update_and_draw()
    draw_pond()
    main_tree.draw()
    for t in other_trees:
        t.draw()
    if not is_first_person:
        draw_minecraft_player(player_pos[0], player_pos[1], player_pos[2], player_facing)
    draw_water_pour()
    if current_season == 2:
        draw_rain(raindrops)
    elif current_season == 3:
        draw_snow(snowflakes)
    for t in [main_tree]+other_trees:
        if t.leaves_falling:
            draw_falling_leaves(t.falling_leaves)
    draw_water_pot_ui()
    draw_score_status()
    if game_over and victory:
        draw_victory()
    elif game_over:
        draw_game_over()
    glut.glutSwapBuffers()

def idle():
    global pouring_duration, pour_start_time, watering_pot_pouring, watering_pot_fullness, game_over, status_message, status_message_timer, trees_saved, victory, total_pour_time
    global raindrops, snowflakes, falling_leaves
    global player_pos, player_facing, walk_anim_phase, last_time
    global player_speed, player_speed_boosted, player_speed_normal, player_speed_fast
    global falling_chain_active, falling_chain_next_time, falling_chain_last_tree, falling_chain_paused
    global game_state
    if victory:
        game_state = "Victory"
        glut.glutPostRedisplay()
        return
    if game_over:
        game_state = "Game Over"
        glut.glutPostRedisplay()
        return
    # Set player speed based on boost
    player_speed = player_speed_fast if player_speed_boosted else player_speed_normal
    # --- Falling leaves chain logic ---
    continue_falling_chain()
    move_vec = np.array([0.0, 0.0, 0.0])
    yaw_rad = math.radians(cam_yaw)
    # Movement relative to camera
    if move_player_forward:
        move_vec[0] += math.sin(yaw_rad)
        move_vec[2] -= math.cos(yaw_rad)
    if move_player_backward:
        move_vec[0] -= math.sin(yaw_rad)
        move_vec[2] += math.cos(yaw_rad)
    if move_player_left:
        move_vec[0] -= math.cos(yaw_rad)
        move_vec[2] -= math.sin(yaw_rad)
    if move_player_right:
        move_vec[0] += math.cos(yaw_rad)
        move_vec[2] += math.sin(yaw_rad)
    if np.linalg.norm(move_vec) > 0:
        move_vec = move_vec / np.linalg.norm(move_vec)
        new_x = player_pos[0] + move_vec[0] * player_speed * 0.1
        new_z = player_pos[2] + move_vec[2] * player_speed * 0.1
        # Clamp to the full ground edge
        new_x = clamp(new_x, -GROUND_SIZE + 6, GROUND_SIZE - 6)
        new_z = clamp(new_z, -GROUND_SIZE + 6, GROUND_SIZE - 6)
        if not player_collides_tree(new_x, new_z) and not player_collides_pond(new_x, new_z):
            player_pos[0] = new_x
            player_pos[2] = new_z
        now = time.time()
        walk_anim_phase += walk_anim_speed * (now - last_time) * 60
        last_time = now
        # Smoothly rotate player_facing to movement direction, with W/S inversion
        target_facing = math.degrees(math.atan2(move_vec[0], -move_vec[2]))
        # Check for W/S only
        if move_player_forward and not (move_player_left or move_player_right or move_player_backward):
            target_facing = (target_facing + 180) % 360
        # Interpolate angle (lerp with wrap-around)
        def lerp_angle(a, b, t):
            diff = (b - a + 180) % 360 - 180
            return a + diff * t
        global player_facing
        player_facing = lerp_angle(player_facing, target_facing, 0.2)  # 0.2 controls smoothness
    else:
        last_time = time.time()
    # Update all trees
    for t in [main_tree]+other_trees:
        was_dead = (not t.has_leaves and t.leaves_regrow_progress == 0.0)
        t.update()
        if was_dead and (t.has_leaves or t.leaves_regrow_progress > 0.0):
            trees_saved += 1
    # Water pouring logic (UI pot)
    if watering_pot_pouring and watering_pot_fullness > 0:
        # Find nearest tree
        nearest = min([main_tree]+other_trees, key=lambda t: ((player_pos[0]-t.x)**2 + (player_pos[2]-t.z)**2)**0.5)
        tree_x, tree_z, tree_r = nearest.x, nearest.z, 32*nearest.size
        dist = ((player_pos[0] - tree_x)**2 + (player_pos[2] - tree_z)**2)**0.5
        if dist > tree_r + 40:
            watering_pot_pouring = False
            nearest.pouring = False
            nearest.pour_accumulated = 0.0  # Reset if interrupted
        else:
            # Make player face the tree while pouring
            dx = tree_x - player_pos[0]
            dz = tree_z - player_pos[2]
            player_facing = math.degrees(math.atan2(dx, -dz))
            if pour_start_time is None:
                pour_start_time = time.time()
            else:
                elapsed = time.time() - pour_start_time
                total_pour_time += elapsed
                # Increment the tree's pour_accumulated
                nearest.pour_accumulated += elapsed
                pour_start_time = time.time()
                if total_pour_time >= 40.0:
                    watering_pot_fullness = 0
                    watering_pot_pouring = False
                    nearest.pouring = False
                    total_pour_time = 40.0
    else:
        pour_start_time = None
        # Reset pour_accumulated for all trees if not pouring
        for t in [main_tree]+other_trees:
            if not t.pouring:
                t.pour_accumulated = 0.0
    # Check for dead/saved trees
    dead_count = sum(1 for t in [main_tree]+other_trees if not t.has_leaves and t.leaves_regrow_progress == 0.0)
    if dead_count >= MAX_DEAD_TREES or dead_count == len([main_tree]+other_trees):
        game_over = True
        status_message = ""
    # Show status message for 2 seconds
    if status_message:
        if status_message_timer == 0:
            status_message_timer = time.time()
        elif time.time() - status_message_timer > 2:
            status_message = ""
            status_message_timer = 0
    # --- RAIN/SNOW/LEAVES ---
    if current_season == 2:
        raindrops = [drop for drop in raindrops if drop.update()]
        while len(raindrops) < 100:
            raindrops.append(Raindrop())
    elif current_season == 3:
        snowflakes = [flake for flake in snowflakes if flake.update()]
        while len(snowflakes) < 100:
            snowflakes.append(Snowflake())
    # --- Victory check ---
    if trees_saved >= 5:
        victory = True
        game_over = True
    glut.glutPostRedisplay()

def reshape(width, height):
    gl.glViewport(0, 0, width, height)
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    glu.gluPerspective(60, width / float(height), 1, 2000)
    gl.glMatrixMode(gl.GL_MODELVIEW)

def keyboard(key, x, y):
    global move_player_forward, move_player_backward, move_player_left, move_player_right
    global current_season, is_first_person
    global watering_pot_visible, watering_pot_fullness, watering_pot_pouring
    global game_over, status_message, status_message_timer, total_pour_time
    global player_speed_boosted
    global falling_chain_active, falling_chain_paused
    global game_state, victory
    # Allow reset (q) and exit (ESC) even after game over
    if key == b'q':
        reset_game()
        return
    if key == b'\x1b':
        if hasattr(glut, 'glutLeaveMainLoop'):
            glut.glutLeaveMainLoop()
        else:
            exit(0)
    if game_over:
        return
    if key == b'w':
        move_player_forward = True
    elif key == b's':
        move_player_backward = True
    elif key == b'a':
        move_player_left = True
    elif key == b'd':
        move_player_right = True
    elif key == b'1':
        current_season = 1
    elif key == b'2':
        current_season = 2
    elif key == b'3':
        current_season = 3
    elif key == b'f':
        # Toggle pause/resume if chain is active, else start chain
        if falling_chain_active:
            falling_chain_paused = not falling_chain_paused
            if falling_chain_paused:
                game_state = "Paused"
            else:
                game_state = "Playing"
        else:
            start_random_tree_falling()
            game_state = "Playing"
    elif key == b'g':
        # Only toggle watering pot visibility; do NOT re-initialize grass!
        watering_pot_visible = not watering_pot_visible
    elif key == b'h':
        pond_x, pond_z, pond_r = -200, 0, 60
        dist = ((player_pos[0] - pond_x)**2 + (player_pos[2] - pond_z)**2)**0.5
        if watering_pot_visible and dist < pond_r + 30:
            watering_pot_fullness = 100
            total_pour_time = 0.0
    elif key == b'j':
        nearest = min([main_tree]+other_trees, key=lambda t: ((player_pos[0]-t.x)**2 + (player_pos[2]-t.z)**2)**0.5)
        tree_x, tree_z, tree_r = nearest.x, nearest.z, 32*nearest.size
        dist = ((player_pos[0] - tree_x)**2 + (player_pos[2] - tree_z)**2)**0.5
        if watering_pot_visible and watering_pot_fullness > 0 and dist < tree_r + 40 and total_pour_time < 40.0:
            nearest.pouring = not nearest.pouring
            watering_pot_pouring = nearest.pouring
    elif key == b'k':
        watering_pot_pouring = False
    elif key == b'v':
        is_first_person = not is_first_person
    elif key == b'l':
        player_speed_boosted = not player_speed_boosted

def keyboard_up(key, x, y):
    global move_player_forward, move_player_backward, move_player_left, move_player_right
    if game_over:
        return
    if key == b'w':
        move_player_forward = False
    elif key == b's':
        move_player_backward = False
    elif key == b'a':
        move_player_left = False
    elif key == b'd':
        move_player_right = False

def mouse_motion(x, y):
    global mouse_last_x, mouse_last_y, cam_yaw, cam_pitch
    if game_over:
        return
    dx = x - mouse_last_x
    dy = y - mouse_last_y
    cam_yaw += dx * mouse_sensitivity
    cam_pitch -= dy * mouse_sensitivity
    cam_pitch = max(-80, min(80, cam_pitch))
    # Prevent looking below horizon
    if cam_pitch < -10:
        cam_pitch = -10
    mouse_last_x = x
    mouse_last_y = y
    glut.glutWarpPointer(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
    mouse_last_x = WINDOW_WIDTH // 2
    mouse_last_y = WINDOW_HEIGHT // 2

def special_keys(key, x, y):
    if game_over:
        return
    if key == glut.GLUT_KEY_LEFT:
        celestial_manager.sun_position = (celestial_manager.sun_position - 2) % 360
    elif key == glut.GLUT_KEY_RIGHT:
        celestial_manager.sun_position = (celestial_manager.sun_position + 2) % 360

def init():
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glClearColor(0.5, 0.7, 1.0, 1.0)
    grass_field.initialize_blades(4000)
    gl.glPointSize(2.0)
    glut.glutSetCursor(glut.GLUT_CURSOR_NONE)

# --- Collision helpers ---
def clamp(val, minv, maxv):
    return max(minv, min(maxv, val))

def player_collides_tree(px, pz):
    for t in [main_tree]+other_trees:
        tree_x, tree_z = t.x, t.z
        trunk_r = 12 * t.size
        if abs(px - tree_x) < trunk_r + 4 and abs(pz - tree_z) < trunk_r + 4:
            return True
    return False

def player_collides_pond(px, pz):
    pond_x, pond_z, pond_r = -200, 0, 60
    dist = ((px - pond_x)**2 + (pz - pond_z)**2)**0.5
    return dist < pond_r + 6

def draw_water_pot_ui():
    if not watering_pot_visible:
        return
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPushMatrix()
    gl.glLoadIdentity()
    gl.glOrtho(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, -1, 1)
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glPushMatrix()
    gl.glLoadIdentity()
    cx, cy, r = WINDOW_WIDTH - 60, 80, 30
    # Draw pot body (cylinder)
    gl.glColor3f(0.75, 0.75, 0.75)
    gl.glBegin(gl.GL_POLYGON)
    for i in range(32):
        angle = 2 * math.pi * i / 32
        gl.glVertex2f(cx + r * math.cos(angle), cy + r * 0.7 * math.sin(angle))
    gl.glEnd()
    # Draw pot base
    gl.glColor3f(0.6, 0.6, 0.6)
    gl.glBegin(gl.GL_POLYGON)
    for i in range(32):
        angle = 2 * math.pi * i / 32
        gl.glVertex2f(cx + r * 0.9 * math.cos(angle), cy - 18 + 6 * math.sin(angle))
    gl.glEnd()
    # Draw handle
    gl.glColor3f(0.7, 0.7, 0.7)
    gl.glBegin(gl.GL_LINE_STRIP)
    for i in range(17):
        angle = math.pi * i / 16
        gl.glVertex2f(cx + (r+12) * math.cos(angle), cy + (r+12) * math.sin(angle))
    gl.glEnd()
    # Draw spout
    gl.glColor3f(0.7, 0.7, 0.7)
    gl.glBegin(gl.GL_POLYGON)
    for i in range(6):
        angle = math.pi/4 + math.pi/8 * i
        gl.glVertex2f(cx + r * 0.9 * math.cos(angle) + 18, cy + r * 0.2 * math.sin(angle) - 5)
    gl.glEnd()
    # Draw blue fill bar inside pot
    fill_ratio = watering_pot_fullness / 100.0
    if fill_ratio > 0:
        gl.glColor3f(0.2, 0.5, 1.0)
        gl.glBegin(gl.GL_POLYGON)
        for i in range(32):
            angle = 2 * math.pi * i / 32
            gl.glVertex2f(cx + (r-6) * math.cos(angle), cy + (r-10) * fill_ratio * math.sin(angle) - (1-fill_ratio)*18)
        gl.glEnd()
    # Draw border
    gl.glColor3f(0.3, 0.3, 0.3)
    gl.glLineWidth(2)
    gl.glBegin(gl.GL_LINE_LOOP)
    for i in range(32):
        angle = 2 * math.pi * i / 32
        gl.glVertex2f(cx + r * math.cos(angle), cy + r * 0.7 * math.sin(angle))
    gl.glEnd()
    # Draw text below
    gl.glColor3f(1, 1, 1)
    gl.glRasterPos2f(cx - 18, cy - 45)
    status = b"full" if watering_pot_fullness > 0 else b"empty"
    for c in status:
        glut.glutBitmapCharacter(glut.GLUT_BITMAP_HELVETICA_18, c)
    gl.glPopMatrix()
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glPopMatrix()
    gl.glMatrixMode(gl.GL_MODELVIEW)

def draw_minecraft_tree(x, y, z, size=1.0, has_leaves=True, leaves_regrow_progress=1.0):
    global current_season
    # Draw cylindrical trunk
    gl.glColor3f(0.55, 0.27, 0.07)
    gl.glPushMatrix()
    gl.glTranslatef(x, y, z)
    gl.glScalef(size, size, size)
    gl.glRotatef(-90, 1, 0, 0)
    quad = glu.gluNewQuadric()
    trunk_height = 6 * 32
    trunk_radius = 16
    glu.gluCylinder(quad, trunk_radius, trunk_radius * 0.8, trunk_height, 16, 1)
    gl.glPopMatrix()
    block_size = 32 * size
    if has_leaves or leaves_regrow_progress > 0.0:
        progress = leaves_regrow_progress if not has_leaves else 1.0
        if current_season == 3:
            gl.glColor3f(1.0, 1.0, 1.0)
        else:
            gl.glColor3f(0.0, 0.4, 0.0)  # Dark green
        ly = y + 6 * block_size
        for dx in range(-5, 6):
            for dz in range(-5, 6):
                if progress >= 0.2:
                    gl.glPushMatrix()
                    gl.glTranslatef(x + dx * block_size, ly, z + dz * block_size)
                    glut.glutSolidCube(block_size)
                    gl.glPopMatrix()
        ly = y + 7 * block_size
        if progress >= 0.4:
            for dx in range(-4, 5):
                for dz in range(-4, 5):
                    gl.glPushMatrix()
                    gl.glTranslatef(x + dx * block_size, ly, z + dz * block_size)
                    glut.glutSolidCube(block_size)
                    gl.glPopMatrix()
        ly = y + 8 * block_size
        if progress >= 0.6:
            for dx in range(-3, 4):
                for dz in range(-3, 4):
                    gl.glPushMatrix()
                    gl.glTranslatef(x + dx * block_size, ly, z + dz * block_size)
                    glut.glutSolidCube(block_size)
                    gl.glPopMatrix()
        ly = y + 9 * block_size
        if progress >= 0.8:
            for dx in range(-2, 3):
                for dz in range(-2, 3):
                    gl.glPushMatrix()
                    gl.glTranslatef(x + dx * block_size, ly, z + dz * block_size)
                    glut.glutSolidCube(block_size)
                    gl.glPopMatrix()
        ly = y + 10 * block_size
        if progress >= 0.95:
            for dx in range(-1, 2):
                for dz in range(-1, 2):
                    gl.glPushMatrix()
                    gl.glTranslatef(x + dx * block_size, ly, z + dz * block_size)
                    glut.glutSolidCube(block_size)
                    gl.glPopMatrix()
        ly = y + 11 * block_size
        if progress >= 1.0:
            gl.glPushMatrix()
            gl.glTranslatef(x, ly, z)
            glut.glutSolidCube(block_size)
            gl.glPopMatrix()

def start_random_tree_falling():
    global falling_chain_active, falling_chain_next_time, falling_chain_last_tree, falling_chain_paused
    candidates = [t for t in [main_tree]+other_trees if t.has_leaves and not t.leaves_falling]
    if candidates:
        tree = random.choice(candidates)
        tree.leaves_falling = True
        falling_chain_active = True
        falling_chain_last_tree = tree
        falling_chain_next_time = None
        falling_chain_paused = False

def continue_falling_chain():
    global falling_chain_active, falling_chain_next_time, falling_chain_last_tree, falling_chain_paused
    # If no chain active, do nothing
    if not falling_chain_active or falling_chain_paused:
        return
    # If last tree finished losing leaves, start timer
    if falling_chain_last_tree and not falling_chain_last_tree.has_leaves and not falling_chain_last_tree.leaves_falling:
        if falling_chain_next_time is None:
            falling_chain_next_time = time.time() + FALLING_CHAIN_DELAY
        elif time.time() >= falling_chain_next_time:
            # Start next random tree
            candidates = [t for t in [main_tree]+other_trees if t.has_leaves and not t.leaves_falling]
            if candidates:
                tree = random.choice(candidates)
                tree.leaves_falling = True
                falling_chain_last_tree = tree
                falling_chain_next_time = None
            else:
                falling_chain_active = False
                falling_chain_last_tree = None
                falling_chain_next_time = None

def main():
    glut.glutInit()
    glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGB | glut.GLUT_DEPTH)
    glut.glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glut.glutCreateWindow(b"3D Seasonal Tree Environment")
    glut.glutDisplayFunc(display)
    glut.glutIdleFunc(idle)
    glut.glutReshapeFunc(reshape)
    glut.glutKeyboardFunc(keyboard)
    glut.glutKeyboardUpFunc(keyboard_up)
    glut.glutSpecialFunc(special_keys)
    glut.glutPassiveMotionFunc(mouse_motion)
    init()
    glut.glutMainLoop()

if __name__ == "__main__":
    main() 