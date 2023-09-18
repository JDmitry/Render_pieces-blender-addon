import bpy
import os
import re
import shutil
import platform
import subprocess

bl_info = {
    "name": "Render frames",
    "author": "dmitry sysoev",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "category": "Import-Export"
}

shots = ""
scenes = ""

def main(context):
    
    working_directory = ""
    working_directory_shots = ""
    data_package = ""
    first_frame = []
    last_frame = []
    data_package = "data"
    alpha_part_name = ""
    digit_part_name = ""
    fps = bpy.context.scene.render.fps
    output = bpy.context.scene.render.filepath
    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    format_file = bpy.context.scene.render.image_settings.file_format
    
    shots = context.scene.my_tool.new_shot_name
    scenes = context.scene.my_tool.new_scene_name
        
    working_directory = bpy.path.abspath("//")
    working_directory_shots = os.path.join(working_directory, shots)
    print(working_directory_shots)
    working_directory_data = os.path.join(working_directory, data_package)
    working_directory_data_shots = os.path.join(working_directory_data, shots)
    
    if not os.path.exists(working_directory_shots):
        os.mkdir(working_directory_shots)
        
    if not os.path.exists(working_directory_data):
        os.mkdir(working_directory_data)
        
    if not os.path.exists(working_directory_data_shots):
        os.mkdir(working_directory_data_shots)
        
    if not os.path.exists(os.path.join(working_directory_shots, scenes)):
        os.mkdir(os.path.join(working_directory_shots, scenes))
        count = 0
        for i in range(len(scenes) - 1, 0, -1):
            if not scenes[i].isdigit():
                break
            digit_part_name += scenes[i]
            count += 1
        digit_part_name = digit_part_name[::-1] 
        alpha_part_name = scenes[:-(count)]
        with open(os.path.join(working_directory_data_shots, f"number_{alpha_part_name}.txt"), "w") as f:
            f.write(digit_part_name)
    else:
        n = ''
        try:
            for i in scenes:
                if not i.isdigit():
                    alpha_part_name += i
                else:
                    digit_part_name += i
            with open(os.path.join(working_directory_data_shots, f"number_{alpha_part_name}.txt"), "r") as f:
                digit_part_name = f.read()
            n = "{0:03d}".format(int(digit_part_name) + 1)
            with open(os.path.join(working_directory_data_shots, f"number_{alpha_part_name}.txt"), "w") as f:
                f.write(n)
            scenes = alpha_part_name + n
            os.mkdir(os.path.join(working_directory_shots, scenes))
        except FileNotFoundError:
            return
        except FileExistsError:
            return
    
    os.mkdir("{}/{}/drawings".format(working_directory_shots, scenes))
    os.mkdir("{}/{}/inputs".format(working_directory_shots, scenes))
    os.mkdir("{}/{}/scripts".format(working_directory_shots, scenes))
    os.mkdir("{}/{}/extras".format(working_directory_shots, scenes))

    shutil.copy2(os.path.join(working_directory, "template", "main.tnz"), os.path.join(working_directory_shots, scenes, "main.tnz"))
    shutil.copy2(os.path.join(working_directory, "template", "07-1000_otprj.xml"), os.path.join(working_directory_shots, scenes, "{}_otprj.xml".format(scenes)))
    shutil.copy2(os.path.join(working_directory, "template", "project.conf"), os.path.join(working_directory_shots, scenes, "project.conf"))
    shutil.copy2(os.path.join(working_directory, "template", "scenes.xml"), os.path.join(working_directory_shots, scenes, "scenes.xml"))
    shutil.copy2(os.path.join(working_directory, "template", "drawings", "scenes.xml"), os.path.join(working_directory_shots, scenes, "drawings", "scenes.xml"))
    shutil.copy2(os.path.join(working_directory, "template", "extras", "scenes.xml"), os.path.join(working_directory_shots, scenes, "extras", "scenes.xml"))
    shutil.copy2(os.path.join(working_directory, "template", "inputs", "scenes.xml"), os.path.join(working_directory_shots, scenes, "inputs", "scenes.xml"))
    shutil.copy2(os.path.join(working_directory, "template", "scripts", "scenes.xml"), os.path.join(working_directory_shots, scenes, "scripts", "scenes.xml"))

    for i in bpy.data.scenes['Scene'].sequence_editor.sequences:
        if i.select:
            first_frame.append(i.frame_final_start)
            last_frame.append(i.frame_final_end)
                
    first_frame.sort()
    last_frame.sort()
        
    bpy.context.scene.frame_start = first_frame[0]
    bpy.context.scene.frame_end = (last_frame[-1] - 1)
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.filepath = os.path.join(working_directory_shots, scenes, "extras/file.")
    bpy.ops.render.render(animation=True)
    bpy.ops.sound.mixdown(filepath=os.path.join(working_directory_shots, scenes, "extras/sound.wav"), container='WAV', codec='PCM')

    data = []
    first_frame = bpy.context.scene.frame_start
    last_frame = bpy.context.scene.frame_end
    
    with open(os.path.join(working_directory_shots, scenes, "main.tnz"), "r") as file:
            data = file.readlines()
            for i in data:
                if re.match("          24", i):
                    index = data.index(i)
                    i = i.replace("24", str(fps))
                    data[index] = i
                        
                if re.search("0 59 <level id='1'/>0001 1", i):
                    index = data.index(i)
                    i = i.replace("59", str(last_frame-first_frame))
                    i = i.replace("0001", "{0:04d}".format(first_frame))
                    data[index] = i
                    break
                    
    with open(os.path.join(working_directory_shots, scenes, "main.tnz"), "w") as file:
            new_file = file.writelines(data)
                
    bpy.context.scene.render.image_settings.file_format = format_file
    bpy.context.scene.frame_start = start
    bpy.context.scene.frame_end = end
    bpy.context.scene.render.filepath = output
    bpy.context.scene.render.fps = fps

    if platform.system() == "Linux":
       subprocess.Popen([r'opentoonz', '{}/main.tnz'.format(os.path.join(working_directory_shots, scenes))])
    elif platform.system() == "Darwin":
       subprocess.Popen([r'/Applications/OpenToonz.app/Contents/MacOS/OpenToonz', '{}/main.tnz'.format(os.path.join(working_directory_shots, scenes))])
    elif platform.system() == "Windows":
       subprocess.Popen([r'opentoonz', '{}\\main.tnz'.format(os.path.join(working_directory_shots, scenes))])

class AF_PluginSettings(bpy.types.PropertyGroup):

    new_shot_name: bpy.props.StringProperty(
        name="New shot name",
        description=":",
        default="",
        maxlen=1024,
        )

    new_scene_name: bpy.props.StringProperty(
        name="New scene name",
        description=":",
        default="",
        maxlen=1024,
        )
        
    path: bpy.props.StringProperty(
        name="Path",
        description=":",
        default="",
        maxlen=1024,
        )

class ScriptOperator(bpy.types.Operator):
    bl_idname = "object.script_operator"
    bl_label = "Edit"
    
    def execute(self, context):
        main(context)
        return {'FINISHED'}
        
class Script(bpy.types.Panel): 
    bl_label = "Rendering frames"
    bl_idname = "script_PT_render"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Rendering"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool
        tool = scene.my_tool
        layout.prop(scene, 'path')
        layout.prop(mytool, "new_shot_name")
        layout.prop(tool, "new_scene_name")
        row = layout.row()
        row.scale_y = 1.5
        row.operator("object.script_operator")
        if shots == context.scene.my_tool.new_shot_name:
            row.enabled = False
        if  scenes == context.scene.my_tool.new_scene_name:
            row.enabled = False
        if not context.scene.my_tool.new_scene_name[-1].isdigit():
            row.enabled = False
            
def register():
  bpy.utils.register_class(Script)
  bpy.utils.register_class(ScriptOperator)
  bpy.utils.register_class(AF_PluginSettings)
  bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=AF_PluginSettings)
  bpy.types.Scene.paths = bpy.props.StringProperty(name="Path", subtype='DIR_PATH')
 
def unregister():	
  bpy.utils.unregister_class(Script)   
  bpy.utils.unregister_class(ScriptOperator)
  bpy.utils.unregister_class(AF_PluginSettings)
  bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=AF_PluginSettings)
 
if __name__ == "__main__":
  register()
