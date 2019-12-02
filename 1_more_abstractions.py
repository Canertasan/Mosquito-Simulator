import sys
import random
import queue
from SkyboxShader import SkyboxShader
from typing import Type

import glm
import numpy as np
from OpenGL import GL as gl, GLUT as glut
from glm import mat4x4
from numpy.f2py.crackfortran import tabchar

from IOUtilities import *
from GameUtilities import *
from StandardShader import *
from AABBShader import *
import time
from copy import deepcopy
import keyboard

# Initialize GLUT ------------------------------------------------------------------|
from UnlitBlendShader import UnlitBlendShader

glut.glutInit()
glut.glutInitDisplayMode(glut.GLUT_DOUBLE | glut.GLUT_RGBA)

# Create a window
screen_size = glm.vec2(800, 600)
glut.glutCreateWindow("Put Window Title Here")
glut.glutReshapeWindow(int(screen_size.x), int(screen_size.y))

# Configure GL -----------------------------------------------------------------------|

# Enable depth test
gl.glEnable(gl.GL_DEPTH_TEST)
# Accept fragment if it closer to the camera than the former one
gl.glDepthFunc(gl.GL_LESS)

# This command is necessary in our case to load different type of image formats.
# Read more on https://www.khronos.org/opengl/wiki/Common_Mistakes under "Texture upload and pixel reads"
gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)

# Creating Data Buffers -----------------------------------------------------------|

# With the ability of .obj file loading, all the data will be read from the files and bound to proper buffers
primitive_objs = {
    "plane": parse_and_bind_obj_file("Assets/Primitives/plane.obj"),
    "cube": parse_and_bind_obj_file("Assets/Primitives/cube.obj"),
    "cylinder": parse_and_bind_obj_file("Assets/Primitives/cylinder.obj"),
    "cone": parse_and_bind_obj_file("Assets/Primitives/cone.obj"),
    "sphere": parse_and_bind_obj_file("Assets/Primitives/sphere.obj"),
    "disc": parse_and_bind_obj_file("Assets/Primitives/disc.obj"),
    "mosquito": parse_and_bind_obj_file("Assets/mosquito/untitled.obj"),  # mosquito/untitled.obj
    "table": parse_and_bind_obj_file("Assets/table/tableJust.obj"),
    "chair": parse_and_bind_obj_file("Assets/table/chair.obj"),
    "soup": parse_and_bind_obj_file("Assets/table/soup/fishsoup.obj"),
    "fork": parse_and_bind_obj_file("Assets/fork/10290_Fork_v2_iterations-2.obj"),
    "garcon": parse_and_bind_obj_file("Assets/Primitives/cubeForGarcon.obj"),
}
# Mosquito and table objects are added! Didnt included yet! They can parsed with no error. Use this project files not the normal ones we use
# So i changed obj. and mtl. files a bit because we parse with our code!

# Create Shaders ---------------------------------------------------------------------|

standard_shader = StandardShader()
light_position = glm.vec3(0.0, 10, 10.0)

AABB_shader = AABBShader(deepcopy(primitive_objs["cube"]))
UI_shader = UnlitBlendShader()

skybox_shader = SkyboxShader(deepcopy(primitive_objs["cube"]))
# Create Camera and Game Objects -----------------------------------------------------|

perspective_projection = glm.perspective(glm.radians(45.0), screen_size.x / screen_size.y, 0.1, 100.0)
orthogonal_projection = glm.ortho(-10.0, 10.0, -10.0, 10.0)

collision_tester_parent = GameObject()

tableData = ReactiveAABB.copy_from(primitive_objs["table"].AABB)
# Collusion obj
table_Object = GameObject(
    Transform(
        position=glm.vec3(0, -1.785, 0),
        scale=glm.vec3(3.0, 3.0, 3.0),
        parent=collision_tester_parent.transform,
    ),
    deepcopy(primitive_objs["table"]),
    tableData,
)

fork_objects = []
fork_target_position = glm.vec3(0.0)

fork_target_positions = []


def throw_fork(index):
    joke_x = obstacle_objects[index].transform.position.x
    joke_y = obstacle_objects[index].transform.position.y
    joke_z = obstacle_objects[index].transform.position.z
    starting_position = glm.vec3(joke_x, joke_y, joke_z)

    fork_object = GameObject(
        Transform(
            position=starting_position,
            scale=glm.vec3(0.3),
        ),
        deepcopy(primitive_objs["fork"]),
        ReactiveAABB.copy_from(primitive_objs["fork"].AABB),
    )

    fork_objects.append(fork_object)
    fork_object.join_set(collision_testers)
    diffVec = mosquito_Object.transform.position - starting_position
    total = diffVec.x ** 2 + diffVec.y ** 2 + diffVec.z ** 2
    total = total ** (1 / 2.0)
    distanceForIndex = 0
    if total <= 3:
        distanceForIndex = 1
    elif 3 < total <= 6:
        distanceForIndex = 2
    elif 6 < total <= 9:
        distanceForIndex = 3
    elif 9 < total <= 12:
        distanceForIndex = 4
    elif 12 < total <= 15:
        distanceForIndex = 5
    target_position = mosquito_Object.transform.position + glm.vec3(mosquito_Object.velocity.x * distanceForIndex,
                                                                    mosquito_Object.velocity.y * distanceForIndex,
                                                                    mosquito_Object.velocity.z * distanceForIndex)

    travel_position = target_position - starting_position
    return glm.normalize(travel_position / 100)


collision_testers: GameObjectSet = set()
obstacle_objects = []
for i in range(1, 4):
    rand_x = random.randint(-2, 2)
    moving_obstacle_object = GameObject(  # OK
        Transform(
            position=glm.vec3(rand_x, 2, 16 - (i * 4)),
            scale=glm.vec3(0.5, 2, 0.5),
            parent=collision_tester_parent.transform,
        ),
        deepcopy(primitive_objs["garcon"]),
        ReactiveAABB.copy_from(primitive_objs["garcon"].AABB),
    )
    obstacle_objects.append(moving_obstacle_object)
    moving_obstacle_object.join_set(collision_testers)

chair_Object = GameObject(  # OK
    Transform(
        position=glm.vec3(0.0, -0.46, -0.8),  # tableData.max.y + chairData.get_center().y + chairData.min.y*3
        scale=glm.vec3(1.8, 1.8, 1.8),
        parent=collision_tester_parent.transform,
    ),
    deepcopy(primitive_objs["chair"]),
    ReactiveAABB.copy_from(primitive_objs["chair"].AABB),
)

chair_Object1 = GameObject(
    Transform(
        position=glm.vec3(-3.0, -0.46, 0.0),  # tableData.max.y + chairData.get_center().y + chairData.min.y*3
        scale=glm.vec3(1.8, 1.8, 1.8),
        parent=collision_tester_parent.transform,
    ),
    deepcopy(primitive_objs["chair"]),
    ReactiveAABB.copy_from(primitive_objs["chair"].AABB),
)

chair_Object2 = GameObject(
    Transform(
        position=glm.vec3(0.0, -0.46, 3.0),  # tableData.max.y + chairData.get_center().y + chairData.min.y*3
        scale=glm.vec3(1.8, 1.8, 1.8),
        parent=collision_tester_parent.transform,
    ),
    deepcopy(primitive_objs["chair"]),
    ReactiveAABB.copy_from(primitive_objs["chair"].AABB),
)

chair_Object3 = GameObject(
    Transform(
        position=glm.vec3(0.0, -0.46, 0.0),  # tableData.max.y + chairData.get_center().y + chairData.min.y*3
        scale=glm.vec3(1.8, 1.8, 1.8),
        parent=collision_tester_parent.transform,
    ),
    deepcopy(primitive_objs["chair"]),
    ReactiveAABB.copy_from(primitive_objs["chair"].AABB),
)

for i in range(0, 25, 6):
    plane_Object = GameObject(
        Transform(
            position=glm.vec3(0, 0, 0 + i),
            scale=glm.vec3(3.0, 3.0, 3.0),
            parent=collision_tester_parent.transform,
        ),
        deepcopy(primitive_objs["plane"]),
        ReactiveAABB.copy_from(primitive_objs["plane"].AABB),
    )
    plane_Object.transform.rotation = glm.quat(glm.vec3(glm.radians(90), 0.0, 0.0))

soup_Object = GameObject(
    Transform(
        position=glm.vec3(0.32, 1.2, -2.3),
        scale=glm.vec3(0.25),
        parent=collision_tester_parent.transform,
    ),
    deepcopy(primitive_objs["soup"]),
    ReactiveAABB.copy_from(primitive_objs["soup"].AABB),
)

# plane_Object.transform.rotation = glm.quat(glm.vec3(glm.radians(90), 0.0, 0.0))


"""
cubeMap = GameObject(
    Transform(
        position=glm.vec3(0.0, 0.0, 0.0),
        scale=glm.vec3(20.0, 20.0, 20.0),
        parent=collision_tester_parent.transform,
    ),
    deepcopy(primitive_objs["cube"]),
    ReactiveAABB.copy_from(primitive_objs["cube"].AABB),
)
"""
mosquito_Object = GameObject(
    Transform(
        position=glm.vec3(0.0, 3.0, 18.0),
        scale=glm.vec3(0.02, 0.02, 0.02),
        parent=collision_tester_parent.transform,
    ),
    deepcopy(primitive_objs["mosquito"]),
    ReactiveAABB.copy_from(primitive_objs["mosquito"].AABB),
)
# mosquito_Object.obj_data.meshes[0].material.Ka = glm.vec3(1.0, 0.0, 0.0)
mosquito_Object.velocity = glm.vec3(0.0)
mosquito_Object.gravity = glm.vec3(0.0, -0.098, 0.0)
mosquito_Object.started = False
mosquito_Object.transform.rotation = glm.quat(glm.vec3(0.0, glm.radians(90), 0.0))
camera = Camera(Transform(position=glm.vec3(0.0, 3.21, 18.35)),
                target=mosquito_Object.transform.position)  # target=mouse_chaser
camera.velocity = glm.vec3(0.0)
# set camera as target mosquito 3,3

mouse_follower = GameObject(
    Transform(
        scale=glm.vec3(1.0)
    ),

)
mouse_chaser = glm.vec3(0.0, 3.0, 0.0)

# collision_tester_parent.transform.rotation = glm.quat(glm.vec3(0.0, 0.0, glm.radians(time_passed * 10.0)))
chair_Object1.transform.rotation = glm.quat(glm.vec3(0.0, glm.radians(180), 0.0))
chair_Object2.transform.rotation = glm.quat(glm.vec3(0.0, glm.radians(-90), 0.0))
chair_Object3.transform.rotation = glm.quat(glm.vec3(0.0, glm.radians(90), 0.0))

chair_Object1.transform.position = glm.vec3(-0.25, -0.46, -3.70)
chair_Object2.transform.position = glm.vec3(-2.1, -0.46, -2.8)
chair_Object3.transform.position = glm.vec3(0.7, -0.46, -1.70)
# create collusion tester set

# add table to collusion tester
table_Object.join_set(collision_testers)
chair_Object.join_set(collision_testers)
chair_Object1.join_set(collision_testers)
chair_Object2.join_set(collision_testers)
chair_Object3.join_set(collision_testers)
plane_Object.join_set(collision_testers)
# mosquito_Object.transform.rotation = glm.quat(glm.vec3(0.0, glm.radians(90), 0.0))

# Lets create cones orbiting around the origin and give each of them unique mesh data so we can modify them easily
"""
radius = 4.0
count = 32
collision_testers: GameObjectSet = set()
for i in range(count):
    angle = glm.radians(360.0 * i / count)
    game_object = GameObject(
        Transform(
            position=glm.vec3(glm.cos(angle) + (random() * 2.0 - 1.0), glm.sin(angle) + (random() * 2.0 - 1.0), 0.0) * radius,
            scale=glm.vec3(random(), random(), random()),
            parent=collision_tester_parent.transform,
        ),
        deepcopy(primitive_objs["cube"]),
        ReactiveAABB.copy_from(primitive_objs["cube"].AABB),
    )
    game_object.join_set(collision_testers)

# Lets create a game object to demonstrate dynamic parent changes
red_obj = deepcopy(primitive_objs["cone"])
red_obj.meshes[0].material.Kd = glm.vec3(1.0, 0.0, 0.0)
red_obj.meshes[0].material.Ka = glm.vec3(1.0, 0.0, 0.0)

mouse_follower = GameObject(
    Transform(
        scale=glm.vec3(0.5),
    ),
    red_obj,
    ReactiveAABB.copy_from(red_obj.AABB)
)
"""

boost_cooldown = 2
last_boost = 0.0

boost_count = 4
boosts: GameObjectSet = set()
boosts_parent = GameObject(
    Transform(
        position=glm.vec3(0.0, 0.0, 0.0),
    )
)
boost_obj = deepcopy(primitive_objs["plane"])
boost_obj.meshes[0].material.Kd = glm.vec3(0.0)
boost_obj.meshes[0].material.Tr = 0.0
boost_obj.meshes[0].material.map_Kd = load_image_to_texture("Assets/boost.png")

temp_boosts = []
boost_remove_order = queue.Queue()
for i in range(boost_count):
    boost = GameObject(
        Transform(
            position=glm.vec3(-4 + i * 3.0, -8.0, 0.0),
            parent=boosts_parent.transform,
        ),
        obj_data=boost_obj,
    )
    boost.leave_set(GameObject.WithObjData)
    boost.join_set(boosts)
    temp_boosts.append(boost)

temp_boosts.reverse()
for boost in temp_boosts:
    boost_remove_order.put(boost)

lives = 3

hit_recovery_time = 1.5
last_hit_at = 0.0

fork_throw_cooldown = 2
last_thrown = 0.0

hearts: GameObjectSet = set()
hearts_parent = GameObject(
    Transform(
        position=glm.vec3(0.0, 0.0, 0.0),
    )
)

hearth_obj = deepcopy(primitive_objs["plane"])
hearth_obj.meshes[0].material.Kd = glm.vec3(0.0)
hearth_obj.meshes[0].material.Tr = 0.0
hearth_obj.meshes[0].material.map_Kd = load_image_to_texture("Assets/heart.png")

heart_remove_order = queue.Queue()
for i in range(3):
    heart = GameObject(
        Transform(
            position=glm.vec3(-12.0, -4.0 + i * 3.0, 0.0),
            parent=hearts_parent.transform,
        ),
        obj_data=hearth_obj,
    )
    heart.leave_set(GameObject.WithObjData)
    heart.join_set(hearts)
    heart_remove_order.put(heart)

win_and_lose_obj: GameObjectSet = set()
win_and_lose_obj_parent = GameObject(
    Transform(
        position=glm.vec3(0.0, 0.0, 0.0),
    )
)

win_lose_remove_order = queue.Queue()

# you win obj
won_obj = deepcopy(primitive_objs["plane"])
won_obj.meshes[0].material.Kd = glm.vec3(0.0)
won_obj.meshes[0].material.Tr = 0.0
won_obj.meshes[0].material.map_Kd = load_image_to_texture("Assets/won.png")

win = GameObject(
    Transform(
        position=glm.vec3(0.0, 2.0, 0.0),
        # glm.vec3(mosquito_Object.transform.position.x, mosquito_Object.transform.position.y + 0.5, mosquito_Object.transform.position.z),
        scale=glm.vec3(5.0),
        parent=win_and_lose_obj_parent.transform,
    ),
    obj_data=won_obj,
)
win.leave_set(GameObject.WithObjData)
win_lose_remove_order.put(win)

# Lose

lose_obj = deepcopy(primitive_objs["plane"])
lose_obj.meshes[0].material.Kd = glm.vec3(0.0)
lose_obj.meshes[0].material.Tr = 0.0
lose_obj.meshes[0].material.map_Kd = load_image_to_texture("Assets/lose.png")

lose = GameObject(
    Transform(
        position=glm.vec3(0.0, 2.0, 0.0),
        # glm.vec3(mosquito_Object.transform.position.x, mosquito_Object.transform.position.y + 0.5, mosquito_Object.transform.position.z),
        scale=glm.vec3(5.0),
        parent=win_and_lose_obj_parent.transform,
    ),
    obj_data=lose_obj,
)
lose.leave_set(GameObject.WithObjData)
win_lose_remove_order.put(lose)

skybox_texture = load_images_to_cubemap_texture(
    "Assets/skybox_bg/morningdew_rt.tga", "Assets/skybox_bg/morningdew_lf.tga",
    "Assets/skybox_bg/morningdew_up.png", "Assets/skybox_bg/morningdew_dn.png",
    "Assets/skybox_bg/morningdew_bk.tga", "Assets/skybox_bg/morningdew_ft.tga",
)
# skybox_texture = load_images_to_cubemap_texture(
#     "Assets/test.png", "Assets/test.png",
#     "Assets/test.png", "Assets/test.png",
#     "Assets/test.png", "Assets/test.png",
# )

# Set Callback Functions -------------------------------------------------------------|

time_passed = 0.0

color_r = 0
color_g = 0
color_b = 0
color_r_Instant = 0

fork_angle = 0

gameFinished = False

timerForColor = 2.0

initial_mosquito_Object = glm.vec3(mosquito_Object.transform.position.x, mosquito_Object.transform.position.y,
                                   mosquito_Object.transform.position.z)
initial_camera = glm.vec3(camera.transform.position.x, camera.transform.position.y, camera.transform.position.z)
initial_gameFinished = False
initial_win_lose_remove_order = win_lose_remove_order
initial_hearts: GameObjectSet = set()
initial_heart_remove_order = queue.Queue()
for i in hearts:
    i.join_set(initial_hearts)
    initial_heart_remove_order.put(i)
initial_boosts: GameObjectSet = set()
initial_boost_remove_order = queue.Queue()
for i in boosts:
    i.join_set(initial_boosts)
    initial_boost_remove_order.put(i)


def display():
    if mosquito_Object.transform.position.x < -3:
        mosquito_Object.transform.position.x += 0.1
        camera.transform.position.x += 0.1
        mosquito_Object.velocity = 0
        camera.velocity = 0
    elif mosquito_Object.transform.position.x > 3:
        mosquito_Object.transform.position.x -= 0.1
        camera.transform.position.x -= 0.1
        mosquito_Object.velocity = 0
        camera.velocity = 0
    if mosquito_Object.transform.position.y < 0:
        mosquito_Object.transform.position.y += 0.1
        camera.transform.position.y += 0.1
        mosquito_Object.velocity = 0
        camera.velocity = 0
    elif mosquito_Object.transform.position.y > 4:
        mosquito_Object.transform.position.y -= 0.1
        camera.transform.position.y -= 0.1
        mosquito_Object.velocity = 0
        camera.velocity = 0
    # Calculate time between frames
    global time_passed, timerForColor, gameFinished
    delta_time = time.perf_counter() - time_passed
    time_passed += delta_time

    # Update all the AABBs
    for collider in GameObject.WithAABB:
        collider.AABB.update(collider.transform)
    global fork_target_positions
    global last_thrown, fork_throw_cooldown, fork_target_position
    if time_passed >= last_thrown + fork_throw_cooldown and mosquito_Object.started:
        for i in range(3):
            fork_target_positions.append(throw_fork(i))
            last_thrown = time_passed

    # Do the collision checking
    global last_hit_at, lives, boosts
    if time_passed >= last_hit_at + hit_recovery_time:
        for collision_tester in set(collision_testers):
            if mosquito_Object.AABB.check_collision(collision_tester.AABB):
                last_hit_at = time_passed
                lives -= 1
                if not heart_remove_order.empty():
                    heart_to_remove = heart_remove_order.get()
                    heart_to_remove.leave_set(hearts)

    global color_r, color_g, color_b, color_r_Instant
    color_r += random.randint(-1, 2)
    color_g += random.randint(-1, 2)
    color_b += random.randint(-1, 2)

    if color_r > 255:
        color_r %= 255
    if color_g > 255:
        color_g %= 255
    if color_b > 255:
        color_b %= 255

    if time_passed <= last_hit_at + timerForColor and not gameFinished:
        color_r_Instant += 127
        if color_r_Instant > 255:
            color_r_Instant %= 255
        mosquito_Object.obj_data.meshes[0].material.Kd = glm.vec3(float(color_r / 255), 0.0, 0.0)
    else:
        mosquito_Object.obj_data.meshes[0].material.Kd = glm.vec3(0.0, 0.0, 0.0)
        color_r_Instant = 0

    global fork_angle
    if len(fork_objects) > 0 and not gameFinished:
        for fork_obj, fork_target in zip(fork_objects, fork_target_positions):
            fork_obj.transform.position += (fork_target * delta_time * 2)
            fork_obj.transform.rotation = glm.quat(glm.vec3(glm.radians(fork_angle), 0.0, 0.0))

    fork_angle += delta_time * 90

    # print(moving_obstacle_object.transform.position.x > mosquito_Object.transform.position.x)

    if mosquito_Object.started:
        if obstacle_objects[0].transform.position.x > mosquito_Object.transform.position.x:
            obstacle_objects[0].transform.position -= glm.vec3(0.001, 0.0, 0.0)
        else:
            obstacle_objects[0].transform.position += glm.vec3(0.001, 0.0, 0.0)
        if mosquito_Object.transform.position.z < obstacle_objects[0].transform.position.z:
            if obstacle_objects[1].transform.position.x > mosquito_Object.transform.position.x:
                obstacle_objects[1].transform.position -= glm.vec3(0.0015, 0.0, 0.0)
            else:
                obstacle_objects[1].transform.position += glm.vec3(0.0015, 0.0, 0.0)
        if mosquito_Object.transform.position.z < obstacle_objects[1].transform.position.z:
            if obstacle_objects[2].transform.position.x > mosquito_Object.transform.position.x:
                obstacle_objects[2].transform.position -= glm.vec3(0.002, 0.0, 0.0)
            else:
                obstacle_objects[2].transform.position += glm.vec3(0.002, 0.0, 0.0)

    soup_Object.obj_data.meshes[0].material.Kd = glm.vec3(float(color_r / 255), float(color_g / 255),
                                                          float(color_b / 255))

    if keyboard.is_pressed(" "):
        mosquito_Object.started = True

    if not gameFinished:
        if mosquito_Object.started:
            mosquito_Object.velocity += mosquito_Object.gravity * delta_time
            mosquito_Object.transform.position += mosquito_Object.velocity * delta_time
            camera.velocity += mosquito_Object.gravity * delta_time
            camera.transform.position += camera.velocity * delta_time

    """if mosquito_Object.transform.position.y < 0.2:
        mosquito_Object.transform.position = glm.vec3(0.0, 3.0, 3.0)
        camera.transform.position = glm.vec3(0.0, 4.3, 4.5)"""

    custom_keyboard_input()

    # Do updates
    # collision_tester_parent.transform.rotation = glm.quat(glm.vec3(0.0, 0.0, glm.radians(time_passed * 10.0)))

    # Drawing part
    # Clear screen
    gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

    gl.glDepthMask(gl.GL_FALSE)
    gl.glCullFace(gl.GL_FRONT)
    skybox_shader.draw(
        perspective_projection,
        glm.mat4x4(glm.mat3x3(camera.get_view())),
        # glm.mat4x4(),
        skybox_texture
    )
    gl.glDepthMask(gl.GL_TRUE)
    gl.glCullFace(gl.GL_BACK)

    # Draw objects in a standard way
    standard_shader.draw(
        perspective_projection,
        camera.get_view(),
        camera.transform.get_final_position(),
        light_position,
        GameObject.WithObjData
    )

    # Draw AABB debuggers
    """AABB_shader.draw(
        perspective_projection,
        camera.get_view(),
        (game_object.AABB for game_object in GameObject.WithAABB)
    )"""
    global win, lose
    if mosquito_Object.AABB.check_collision(soup_Object.AABB) and not gameFinished and mosquito_Object.started:
        win.join_set(win_and_lose_obj)
        # check transparency in here! and position again with mosq
        gameFinished = True
    # print(mosquito_Object.transform.position)

    if lives == 0 and not gameFinished and mosquito_Object.started:
        lose.join_set(win_and_lose_obj)
        # check transparency in here! and position again with mosq
        gameFinished = True

    UI_shader.draw(
        orthogonal_projection,
        hearts,
        boosts,
        win_and_lose_obj,
    )
    """if mosquito_Object.AABB.check_collision(soup_Object.AABB):
        time.sleep(4)
        exit(0)
    # print(mosquito_Object.transform.position)

    if lives == 0:
        time.sleep(4)
        exit(0)"""

    # Swap the buffer we just drew on with the one showing on the screen
    glut.glutSwapBuffers()


glut.glutDisplayFunc(display)
glut.glutIdleFunc(display)


def resize(width, height):
    gl.glViewport(0, 0, width, height)
    screen_size.x = width
    screen_size.y = height
    screen_ratio = screen_size.x / screen_size.y
    global perspective_projection
    perspective_projection = glm.perspective(glm.radians(45.0), screen_size.x / screen_size.y, 0.1, 100.0)
    global orthogonal_projection
    orthogonal_projection = glm.ortho(-10.0 * screen_ratio, 10.0 * screen_ratio, -10.0, 10.0)


glut.glutReshapeFunc(resize)


# camView = glm::translate(camView, glm::vec3(0.0f, 0.0f, -0.01f));
# This function for movement of mosquito
def custom_keyboard_input():
    global mosquito_Object, camera, gameFinished, win_lose_remove_order, hearts, heart_remove_order, boost_remove_order, boosts, last_boost, boost_count, collision_testers, fork_objects, temp_boosts, lives, boost_count
    if keyboard.is_pressed('esc'):
        sys.exit()
    if keyboard.is_pressed('w') or keyboard.is_pressed('W'):
        mosquito_Object.velocity.z += -0.003
        camera.velocity.z += -0.003
        if mosquito_Object.velocity.z > -0.01 or camera.velocity.z > -0.01:
            mosquito_Object.velocity.z = -0.01
            camera.velocity.z = -0.01
    if keyboard.is_pressed('s') or keyboard.is_pressed('S'):
        mosquito_Object.velocity.z += 0.003
        camera.velocity.z += 0.003
        if mosquito_Object.velocity.z < 0.01 or camera.velocity.z < 0.01:
            mosquito_Object.velocity.z = 0.01
            camera.velocity.z = 0.01
    if keyboard.is_pressed('a') or keyboard.is_pressed('A'):
        mosquito_Object.velocity.x += -0.003
        camera.velocity.x += -0.003
        if mosquito_Object.velocity.x > -0.01 or camera.velocity.x > -0.01:
            mosquito_Object.velocity.x = -0.01
            camera.velocity.x = -0.01
    if keyboard.is_pressed('d') or keyboard.is_pressed('D'):
        mosquito_Object.velocity.x += 0.003
        camera.velocity.x += 0.003
        if mosquito_Object.velocity.x < 0.01 or camera.velocity.x < 0.01:
            mosquito_Object.velocity.x = 0.01
            camera.velocity.x = 0.01
    if keyboard.is_pressed(' '):
        mosquito_Object.velocity.y += 0.06
        camera.velocity.y += 0.06
        if mosquito_Object.velocity.y > 0.2 or camera.velocity.y > 0.2:
            mosquito_Object.velocity.y = 0.2
            camera.velocity.y = 0.2
    if keyboard.is_pressed("left shift") and (time_passed >= last_boost + boost_cooldown) and boost_count > 0:
        last_boost = time_passed
        boost_count -= 1
        if not boost_remove_order.empty():
            boost_to_remove = boost_remove_order.get()
            boost_to_remove.leave_set(boosts)
        if keyboard.is_pressed('w') or keyboard.is_pressed('W'):
            mosquito_Object.transform.position += glm.vec3(0.0, 0.0, -0.3)
            camera.transform.position += glm.vec3(0.0, 0.0, -0.3)
        if keyboard.is_pressed('s') or keyboard.is_pressed('S'):
            mosquito_Object.transform.position += glm.vec3(0.0, 0.0, 0.3)
            camera.transform.position += glm.vec3(0.0, 0.0, 0.3)
        if keyboard.is_pressed('a') or keyboard.is_pressed('A'):
            mosquito_Object.transform.position += glm.vec3(-0.3, 0.0, 0.0)
            camera.transform.position += glm.vec3(-0.3, 0.0, 0.0)
        if keyboard.is_pressed('d') or keyboard.is_pressed('D'):
            mosquito_Object.transform.position += glm.vec3(0.3, 0.0, 0.0)
            camera.transform.position += glm.vec3(0.3, 0.0, 0.0)
    if keyboard.is_pressed('o'):
        camera.transform.position += glm.vec3(0.0, -0.1, 0.0)
    if keyboard.is_pressed('p'):
        camera.transform.position += glm.vec3(0.0, 0.1, 0.0)
    if keyboard.is_pressed('k'):
        camera.transform.position += glm.vec3(1.0, 0.0, 0.0)
    if keyboard.is_pressed('l'):
        camera.transform.position += glm.vec3(-1.0, 0.1, 0.0)
    if keyboard.is_pressed('r') and gameFinished:
        lenghtOfList = len(fork_objects)
        for k in range(lenghtOfList):
            collision_testers.discard(fork_objects[k])
            GameObject.WithAABB.remove(fork_objects[k])
            GameObject.WithObjData.remove(fork_objects[k])
        fork_objects.clear()
        lives = 3
        boost_count = 4
        fork_target_positions.clear()
        mosquito_Object.velocity = glm.vec3(0.0)
        mosquito_Object.gravity = glm.vec3(0.0, -0.098, 0.0)
        mosquito_Object.started = False
        camera.transform.position = glm.vec3(0.0, 3.0, 18.0)
        camera.transform.position += glm.vec3(0.0, 0.21, 0.35)
        camera.velocity = glm.vec3(0.0)
        mosquito_Object.transform.position = glm.vec3(glm.vec3(0.0, 3.0, 18.0))
        camera.target = mosquito_Object.transform.position

        gameFinished = False
        win_and_lose_obj.pop()
        boosts.clear()
        heart_remove_order.queue.clear()
        boost_remove_order.queue.clear()
        hearts.clear()
        boost_remove_order_New = queue.Queue()
        heart_remove_order_New = queue.Queue()
        for j in initial_hearts:
            j.join_set(hearts)
            heart_remove_order_New.put(j)
        for k in temp_boosts:
            k.join_set(boosts)
            boost_remove_order_New.put(k)
        boost_remove_order = boost_remove_order_New
        heart_remove_order = heart_remove_order_New


# glut.glutKeyboardFunc(keyboard_input)

def mouse_passive_motion(x, y):
    # print(x, y)
    a = x


glut.glutSetCursor(glut.GLUT_CURSOR_NONE)
glut.glutPassiveMotionFunc(mouse_passive_motion)

# Start the Main Loop ----------------------------------------------------------------|

glut.glutMainLoop()
