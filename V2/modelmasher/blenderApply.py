import bpy
import sys
import os


def save_image_as(image: bpy.types.Image, path: str=bpy.app.tempdir, name: str='Untitled', file_format: str='PNG', color: str='RGB', color_depth: str='16', compression: int=0):
    scene = bpy.data.scenes.new("Temp")
    
    show_name = image.name
    image.name = name
    
    # use docs.blender.org/api/current/bpy.types.ImageFormatSettings.html for more properties
    settings = scene.render.image_settings
    settings.file_format = file_format  # Options: 'BMP', 'IRIS', 'PNG', 'JPEG', 'JPEG2000', 'TARGA', 'TARGA_RAW', 'CINEON', 'DPX', 'OPEN_EXR_MULTILAYER', 'OPEN_EXR', 'HDR', 'TIFF', 'WEBP'
    settings.color_mode = color  # Options: 'BW', 'RGB', 'RGBA' (depends on file_format)
    settings.color_depth = color_depth  # Options: '8', '10', '12', '16', '32' (depends on file_format)
    settings.compression = compression  # Range: 0 - 100
    
    print(str(path))
    image.save_render(path, scene=scene)
    
    bpy.data.scenes.remove(scene)
    image.name = show_name

def get_all_mesh_objects(base_object):
    """Recursively get all mesh children of an object."""
    meshes = []
    if base_object.type == 'MESH':
        meshes.append(base_object)
    for child in base_object.children:
        meshes.extend(get_all_mesh_objects(child))
    return meshes

# The first arguments after '--' are stored starting from index 1
args = sys.argv[sys.argv.index("--") + 1:]

# Extract arguments
obj_path = args[0]
output_path = args[1]
dimensions = int(args[2])
input_texture_paths = args[3:]  # All arguments starting from the third one are treated as texture paths


# Parameters
file_path = obj_path
material_name = "Apply"
image_path = output_path
bake_image_name = "BakeImage2"
env_texture_path = input_texture_paths[0]
# Create an image for baking
if bake_image_name not in bpy.data.images:
    image = bpy.data.images.new(bake_image_name, width=dimensions, height=dimensions, float_buffer=True)

# Get a set of all current objects in the scene
current_objects = set(bpy.data.objects)

# 1. Import the model
bpy.ops.import_scene.obj(filepath=file_path)

# Determine which objects are new
new_objects = set(bpy.data.objects) - current_objects

# Get all mesh objects, including children
all_mesh_objects = []
for obj in new_objects:
    all_mesh_objects.extend(get_all_mesh_objects(obj))

if not all_mesh_objects:
    raise ValueError("No mesh objects found after importing. Check the model file.")

# 2. Apply a specific material to all mesh objects
material = bpy.data.materials.get(material_name)

if material:
    for obj in all_mesh_objects:
        # Ensure the object has a UV map
        if not obj.data.uv_layers:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.uv.smart_project()
            bpy.ops.object.mode_set(mode='OBJECT')


        # Assign material
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)

        # Ensure an image texture node with the bake image is present and selected
        mat_nodes = obj.data.materials[0].node_tree.nodes
        image_node = mat_nodes.new(type='ShaderNodeTexImage')
        image_node.image = bpy.data.images[bake_image_name]
        image_node.select = True
        mat_nodes.active = image_node
        

for i, imgPath in enumerate(input_texture_paths):
    # Normalize path
    imgPath = os.path.normpath(imgPath)

    # Check if the file exists
    if not os.path.exists(imgPath):
        raise ValueError(f"The file does not exist at path: {imgPath}")

    image_name = bpy.path.basename(imgPath)
    concat_name = image_name[0:63] # Blender concats the name if long
    # Check if the image is already loaded in Blender
    if concat_name in bpy.data.images:
        env_texture = bpy.data.images[concat_name]
    else:
        # If not loaded, try opening it
        bpy.ops.image.open(filepath=imgPath)
        
        # Check again if the image is loaded successfully
        if concat_name in bpy.data.images:
            env_texture = bpy.data.images[concat_name]
        else:
            raise ValueError(f"Failed to load the image from path: {concat_name}")

    # Set the environment texture to the "Environment Texture" node of the "Apply" material
    if material_name in bpy.data.materials:
        material = bpy.data.materials[material_name]
        if 'Image Texture.001' in material.node_tree.nodes:
            environment_texture_node = material.node_tree.nodes['Image Texture.001']
            environment_texture_node.image = env_texture
        else:
            raise ValueError("Node 'Environment Texture' not found in the material")
        if 'Image Texture.006' in material.node_tree.nodes:
            environment_texture_node = material.node_tree.nodes['Image Texture.006']
            environment_texture_node.image = env_texture
        else:
            raise ValueError("Node 'Environment Texture' not found in the material")
    else:
        raise ValueError("Material 'Apply' not found")

    # 3. Bake the material
    # Ensure we are in Object Mode and the mesh objects are selected
    for obj in bpy.data.objects:
        obj.select_set(False)  # Deselect all objects

    for obj in all_mesh_objects:
        obj.select_set(True)

    # Set the first mesh as the active object
    bpy.context.view_layer.objects.active = all_mesh_objects[0]
    bpy.ops.object.mode_set(mode='OBJECT')

    # Ensure the renderer is set to Cycles
    bpy.context.scene.render.engine = 'CYCLES'        
    bpy.context.scene.render.image_settings.color_mode = 'RGB'
    bpy.context.scene.render.image_settings.color_depth = '16'

    # Perform the bake
    bpy.context.scene.cycles.bake_type = "DIFFUSE"  # Change based on what you want to bake
    bpy.ops.object.bake(type="DIFFUSE")

    # 4. Save the image
    if bake_image_name in bpy.data.images:
        image = bpy.data.images[bake_image_name]
        #image.save_render(image_path+"_"+str(i)+".png")
        save_image_as(image, image_path+"_"+str(i)+".png")
    else:
        raise ValueError("Baked image not found. Check bake settings.")
    

