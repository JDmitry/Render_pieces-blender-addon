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

def find_next_shot_name(directory):
    dirs = []
    for i in os.listdir(directory):
        if re.match(r'^[0-9]{3}$', i):
            dirs.append(i)
    return "{0:03d}".format(int(dirs[-1])+1)

def main(context):
    scene = ""
    working_directory = bpy.path.abspath("//")
    data = []
    first_frame = []
    last_frame = []
    fps = bpy.context.scene.render.fps
    output = bpy.context.scene.render.filepath
   
    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    format_file = bpy.context.scene.render.image_settings.file_format
    
    if not os.path.exists(working_directory + "shots"):
        os.mkdir(os.path.join(working_directory, "shots"))
        
    if not os.listdir(os.path.join(working_directory, "shots")):
        #scene = find_next_shot_name(working_directory + "shots/")
        scene = context.scene.my_tool.new_shot_name
    else:
        dirs = []
        for i in os.listdir(os.path.join(working_directory, "shots")):
            if i != ".DS_Store":
                dirs.append(i)
        dirs.sort()
        print(dirs)
        name = dirs[-1]
        num = ''
        ost = ''
        for i in name:
            if i.isdigit():
                num += i
                continue
            ost += i
        # scene = ost + str((int(num) + 1))
        scene = "{0}{1:03d}".format(ost, (int(num) + 10))

    for i in bpy.data.scenes['Scene'].sequence_editor.sequences:
        if i.select:
            first_frame.append(i.frame_final_start)
            last_frame.append(i.frame_final_end)
            
    first_frame.sort()
    last_frame.sort()
    
    bpy.context.scene.frame_start = first_frame[0]
    bpy.context.scene.frame_end = (last_frame[-1] - 1)
    
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.filepath = "//shots/{}/extras/file.".format(scene)
    bpy.ops.render.render(animation=True)
    bpy.ops.sound.mixdown(filepath="//shots/{}/extras/sound.wav".format(scene), container='WAV', codec='PCM')
    
    os.mkdir("{0}/shots/{1}/drawings".format(working_directory, scene))
    os.mkdir("{0}/shots/{1}/inputs".format(working_directory, scene))
    os.mkdir("{0}/shots/{1}/scripts".format(working_directory, scene))
    
    shutil.copy2(os.path.join(working_directory, "template", "main.tnz"), os.path.join(working_directory, "shots", scene, "main.tnz"))
    shutil.copy2(os.path.join(working_directory, "template", "07-1000_otprj.xml"), os.path.join(working_directory,"shots", scene, "{}_otprj.xml".format(scene)))
    shutil.copy2(os.path.join(working_directory, "template", "project.conf"), os.path.join(working_directory, "shots", scene, "project.conf"))
    shutil.copy2(os.path.join(working_directory, "template", "scenes.xml"), os.path.join(working_directory, "shots", scene, "scenes.xml"))
    shutil.copy2(os.path.join(working_directory, "template", "drawings", "scenes.xml"), os.path.join(working_directory, "shots", scene, "drawings", "scenes.xml"))
    shutil.copy2(os.path.join(working_directory, "template", "extras", "scenes.xml"), os.path.join(working_directory, "shots", scene, "extras", "scenes.xml"))
    shutil.copy2(os.path.join(working_directory, "template", "inputs", "scenes.xml"), os.path.join(working_directory, "shots", scene, "inputs", "scenes.xml"))
    shutil.copy2(os.path.join(working_directory, "template", "scripts", "scenes.xml"), os.path.join(working_directory, "shots", scene, "scripts", "scenes.xml"))
    
    data = []
    first_frame = bpy.context.scene.frame_start
    last_frame = bpy.context.scene.frame_end
    with open(os.path.join(working_directory, "shots", scene, "main.tnz"), "r") as file:
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
                
    with open(os.path.join(working_directory, "shots", scene, "main.tnz"), "w") as file:
            new_file = file.writelines(data)
            
    bpy.context.scene.render.image_settings.file_format = format_file
    bpy.context.scene.frame_start = start
    bpy.context.scene.frame_end = end
    bpy.context.scene.render.filepath = output
    
    if platform.system() == "Linux":
        subprocess.Popen([r'opentoonz', '{0}shots/{1}/main.tnz'.format(working_directory, scene)])
    elif platform.system() == "Darwin":
        subprocess.Popen([r'/Applications/OpenToonz.app/Contents/MacOS/OpenToonz', '{0}shots/{1}/main.tnz'.format(working_directory, scene)])
    elif platform.system() == "Windows":
        subprocess.Popen([r'opentoonz', '{0}shots\\{1}\\main.tnz'.format(working_directory, scene)])

class AF_PluginSettings(bpy.types.PropertyGroup):

    new_shot_name: bpy.props.StringProperty(
        name="New shot name",
        description=":",
        default="001",
        maxlen=1024,
        )

class ScriptOperator(bpy.types.Operator):
    bl_idname = "object.script_operator"
    bl_label = "Render"
    
    def execute(self, context):
        main(context)
        return {'FINISHED'}
        
class Script(bpy.types.Panel): 
    bl_label = "Rendering frames"
    bl_idname = "script_PT_render"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_context = "scene"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mytool = scene.my_tool
        layout.prop( mytool, "new_shot_name")
        row = layout.row()
        row.scale_y = 1.5
        row.operator("object.script_operator")
        
def register():
  bpy.utils.register_class(Script)
  bpy.utils.register_class(ScriptOperator)
  bpy.utils.register_class(AF_PluginSettings)
  bpy.types.Scene.my_tool = bpy.props.PointerProperty(type=AF_PluginSettings)
 
def unregister():	
  bpy.utils.unregister_class(Script)   
  bpy.utils.unregister_class(ScriptOperator)
 
if __name__ == "__main__":
  register()