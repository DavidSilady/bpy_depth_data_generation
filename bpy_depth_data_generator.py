import bpy
import random
import os
import time
from pathlib import Path
import mathutils
from mathutils import Vector, Matrix

HUMAN_OBJS = []
    
def setup_depth_renderer(normalize=False, clear=True):
    # https://blender.stackexchange.com/a/42667
    # Set up rendering of depth map:
    bpy.context.scene.use_nodes = True
    
    tree = bpy.context.scene.node_tree
    links = tree.links
    
    if clear:
        # clear default nodes
        for n in tree.nodes:
            tree.nodes.remove(n)
    
    # create input render layer node
    rl = tree.nodes.new('CompositorNodeRLayers')
    map = None;
    
    if normalize:
        map = tree.nodes.new(type="CompositorNodeNormalize")
    else:
        map = tree.nodes.new(type="CompositorNodeMapValue")
        # Size is chosen kind of arbitrarily, try out until you're satisfied with resulting depth map.
        map.size = [0.025]
        map.offset = [-6.0]
        map.use_min = False
        map.use_max = False
        
    links.new(rl.outputs[2], map.inputs[0])
    
    less_than = tree.nodes.new(type="CompositorNodeMath")
    less_than.operation = "LESS_THAN"
    less_than.inputs[1].default_value = 1
    
    links.new(map.outputs[0], less_than.inputs[0])
    
    mix = tree.nodes.new(type="CompositorNodeMixRGB")
    mix.inputs[1].default_value = (0, 0, 0, 1)
    
    links.new(less_than.outputs[0], mix.inputs[0])
    
    links.new(map.outputs[0], mix.inputs[2])    

#    invert = tree.nodes.new(type="CompositorNodeInvert")
#    links.new(map.outputs[0], invert.inputs[1])
    
    # Setup color ramp (to map to RGB)
#    cr = tree.nodes.new(type="CompositorNodeValToRGB")
#    cr.color_ramp.color_mode = "RGB"
#    cr.color_ramp.interpolation = "LINEAR"
#    # Change the initial first element
#    cr.color_ramp.elements[0].color=[1.0, 0.0, 0.0, 1.0]
#    # Create third in the middle and change its color
#    cr.color_ramp.elements.new(0.5)
#    cr.color_ramp.elements[1].color=[0.0, 1.0, 0.0, 1.0]
#    # Change the color of the last initial element
#    cr.color_ramp.elements[2].color=[0.0, 0.0, 1.0, 1.0]
    
#    links.new(invert.outputs[0], cr.inputs[0])
    
    return mix

def render(index, cr, output_folder):
#    randomize_camera_lens()
#    randomize_camera_location()
    
    output_dir = Path('C:/bp/' + output_folder)
    tree = bpy.context.scene.node_tree
    links = tree.links
    
#    bpy.context.scene.render.engine = 'CYCLES'
    
    render_path = str(output_dir / f"/render/{str(index).zfill(4)}.png")
    depth_path = str(output_dir / f"/depth/{str(index).zfill(4)}.png")
    
    # set up path and render
    bpy.context.scene.render.filepath = render_path
    bpy.ops.render.render(write_still=True)
    
#    bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
    bpy.data.cameras["Camera"].dof.use_dof = False
    # set up composite to render using compositor
    composite = tree.nodes.new(type="CompositorNodeComposite")
    links.new(cr.outputs[0], composite.inputs[0])
    
#    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    
    bpy.data.scenes["Scene"].render.image_settings.color_mode = "BW"
    # set up path and render
    bpy.context.scene.render.filepath = depth_path
    bpy.ops.render.render(write_still=True)
    bpy.data.scenes["Scene"].render.image_settings.color_mode = "RGB"
    
    # clean up
    tree.nodes.remove(composite)
    bpy.data.cameras["Camera"].dof.use_dof = True
    
def randomize_camera_lens():
    camera = bpy.data.cameras["Camera"]
    camera.lens = random.uniform(21, 135)
    
def setup_dof(target_obj):
    bpy.data.cameras["Camera"].dof.use_dof = True
#    bpy.data.cameras["Camera"].dof.focus_object = target_obj
    TARGET.location.x = target_obj.location.x
    TARGET.location.y = target_obj.location.y
    bpy.data.cameras["Camera"].dof.aperture_fstop = random.uniform(2, 20) 
    bpy.data.cameras["Camera"].dof.aperture_ratio = random.uniform(1, 2)
#    empty_obj = bpy.data.objects["Camera"].constraints["Track To"].target
#    bpy.data.objects["Camera"].constraints["Track To"].target = target_obj
    return None
    
def turn_off_dof(new_target):
    bpy.data.cameras["Camera"].dof.use_dof = False
#    bpy.data.objects["Camera"].constraints["Track To"].target = new_target
    
def randomize_sun_direction():
    bpy.data.worlds["World"].node_tree.nodes["Mapping"].inputs[2].default_value[2] = random.uniform(0, 360)
    
def randomize_camera_location():
    camera_object = bpy.data.objects['Camera']
    
    camera_range = [
        (0, 8),
        (0, 8),
        (0.1, 3)
    ]
    
    camera_x = random.uniform(camera_range[0][0], camera_range[0][1])
    camera_y = random.uniform(camera_range[1][0], camera_range[1][1])
    if camera_x < camera_range[0][1] / 2:
        camera_x -= camera_range[0][1]
    if camera_y < camera_range[1][1] / 2:
        camera_y -= camera_range[1][1]
    
    camera_object.location.x = camera_x
    camera_object.location.y = camera_y
    camera_object.location.z = random.uniform(camera_range[2][0], camera_range[2][1])
   
def smart_unwrap(obj):
    # https://blender.stackexchange.com/a/120807
    context = bpy.context
    scene = context.scene
    vl = context.view_layer
    
    vl.objects.active = obj
    obj.select_set(True)
    print(obj.name)
    lm =  obj.data.uv_layers.get("LightMap")
    if not lm:
        lm = obj.data.uv_layers.new(name="LightMap")
    lm.active = True
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT') # for all faces
    bpy.ops.uv.smart_project(angle_limit=66, island_margin = 0.02)
    
    bpy.ops.object.editmode_toggle()
 
def assign_texture(obj, should_unwrap=True):
    if should_unwrap:
        smart_unwrap(obj)
    
    texture_dir = 'C:/bp/TEXTURES/'
    random_file = texture_dir + random.choice(os.listdir(texture_dir))
    
    mat = bpy.data.materials.new(name="New_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
    texImage.image = bpy.data.images.load(random_file)
    mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
    # ob = bpy.context.view_layer.objects.active
    # Assign it to object
    if obj.data.materials:
        obj.data.materials[0] = mat
    else:
        obj.data.materials.append(mat)
        
def get_n_random_textures(n):
    texture_dir = 'C:/bp/TEXTURES/'
    array = []
    for _ in range(n):
        random_file = texture_dir + random.choice(os.listdir(texture_dir))
        array.append(random_file)
    return array
    
def randomize_textures(obj):
    textures = get_n_random_textures(20)
    
    for mat in obj.data.materials:
        if mat is None:
            continue
        # Find random texture
        
        # Assign the random texture to the mat
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
        texImage.image = bpy.data.images.load(random.choice(textures))
        mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
        
def select_all(array):
    for obj in array:
        obj.select_set(True)
    
def deselect_all(array):
    for obj in array:
        obj.select_set(False)
        
def origin_to_bottom(ob, matrix=Matrix()):
    # https://blender.stackexchange.com/a/42110
    me = ob.data
    mw = ob.matrix_world
    local_verts = [matrix @ Vector(v[:]) for v in ob.bound_box]
    o = sum(local_verts, Vector()) / 8
    o.z = min(v.z for v in local_verts)
    o = matrix.inverted() @ o
    me.transform(Matrix.Translation(-o))
    

def add_random_human(min_x=-1, min_y=-1, max_x=1, max_y=1):
    obj_dir = 'C:/bp/HUMANS/'
    
    random_file = obj_dir + random.choice(os.listdir(obj_dir))
    bpy.ops.import_scene.obj(filepath=random_file)
    
    obj = bpy.context.selected_objects[0]
    
    # Track it for later deletion
    HUMAN_OBJS.append(obj)    
    
    # Set position
#    
#    mx = obj.matrix_world
#    miny = max((mx @ v.co)[1] for v in obj.data.vertices)
##    obj.location.z = -0.025
#    mx.translation.y -= miny
    origin_to_bottom(obj)
    obj.rotation_euler = (
        0, 
        0, 
        random.uniform(0, 6.28)
    )
    obj.location.x = random.uniform(min_x, max_x)
    obj.location.y = random.uniform(min_y, max_y)
    obj.location.z = 0
    
    assign_texture(obj)
    
    # Stop focus
    obj.select_set(False)
    
    return obj
    

def clean_up_humans(human_array, length):
    for i in range(length):
        # delete the imported object
        human_array[i].select_set(True)
        bpy.ops.object.delete()
    return human_array[length:]

def add_n_humans(n):
    array = []
    for _ in range(n):
        array.append(add_random_human(-7, -7, 7, 7))
    return array
        
        
print('starting exec')

TARGET = bpy.context.scene.objects["Empty.001"]
def render_algo(index=100):
    bpy.context.scene.render.engine = 'CYCLES'
    
    city_obj_r = bpy.context.scene.objects["NYC_Set_8"]
    city_obj_l = bpy.context.scene.objects["NYC_Set_8.001"]
    
    human_array = HUMAN_OBJS
    start = time.perf_counter()

    depth_r = setup_depth_renderer(normalize=True, clear=False)
    
    empty_obj = None
    for i in range(70):
        randomize_textures(city_obj_r)
        randomize_textures(city_obj_l)
        human_array = add_n_humans(round(random.uniform(5, 30)))
#        human_array = HUMAN_OBJS
        randomize_sun_direction()
        for _ in range(3):
            randomize_camera_location()
            for _ in range(2):
                target = random.choice(human_array)
                empty_obj = setup_dof(target)
                randomize_camera_lens()
                render(index, depth_r, "BW_OUT")
                index += 1
        turn_off_dof(empty_obj)
        human_array = clean_up_humans(human_array, len(human_array))
        current_time = time.perf_counter() - start
        print("Batch")
        print(i)
        print("rendered in:")
        print(current_time)
        
    end_time = time.perf_counter() - start
    print("END: ")
    print(end_time)
    
#add_n_humans(5)

#city_obj_r = bpy.context.scene.objects["NYC_Set_8"]
#city_obj_l = bpy.context.scene.objects["NYC_Set_8.001"]

#randomize_textures(city_obj_)

render_algo(1200)

#HUMAN_OBJS = clean_up_humans(HUMAN_OBJS, len(HUMAN_OBJS)

#for of in obj_dir.iterdir():
#    
#    bpy.ops.import_scene.obj(filepath=str(of))
#    obj = bpy.context.selected_objects[0]
#    obj.rotation_euler = (0, 0, random.uniform(-2, 2))
#    obj.location.x = random.uniform(-0.7, 0.7)
#    obj.location.y = random.uniform(-0.7, 0.7)

#    render(index, cr)
#    index+=1
#    
#    #delete the imported object
#    obj.select_set(True)
#    bpy.ops.object.delete()

print('exec done')

# https://blender.stackexchange.com/questions/80777/convert-depth-z-value-to-rgba