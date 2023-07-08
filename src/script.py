import bpy
import os
import re
import shutil

def main(context):
    file_path = bpy.data.filepath
    directory = os.path.dirname(file_path)
    pattern = "{0:03d}0"
    dir_name = ""
    data = ""
    pattern2 = "0 59 <level id='1'/>0001 1"
    start = bpy.context.scene.frame_start
    end = bpy.context.scene.frame_end
    format = bpy.context.scene.render.image_settings.file_format

    dirs = []   
    content = os.listdir(directory)
    for i in content:
        if re.match(r'^[0-9][0-9][0-9]0$', i):
            dirs.append(i)
    dirs.sort()
    dir_name = pattern.format(len(dirs)+1)
    os.mkdir(os.path.join(directory, dir_name))

    sequence = bpy.data.scenes['Scene'].sequence_editor
    strip = sequence.active_strip
    bpy.ops.sequencer.set_range_to_strips()

    bpy.context.scene.render.image_settings.file_format='PNG'
    bpy.context.scene.render.filepath = "//"+dir_name+"/extras/file."
    bpy.ops.render.render(animation=True)
    bpy.ops.sound.mixdown(filepath="//{}/extras/sound.wav".format(dir_name), container='WAV', codec='PCM')

    drawings = directory + "/" + dir_name + "/drawings"
    os.mkdir(drawings)
    inputs = directory + "/" + dir_name + "/inputs"
    os.mkdir(inputs)
    scripts = directory + "/" + dir_name + "/scripts"
    os.mkdir(scripts)

    shutil.copy2(os.path.join(directory, "template", "main.tnz"), os.path.join(directory, dir_name, "main.tnz"))
    with open(os.path.join(directory, dir_name, "main.tnz"), "r") as f:
        data = f.readlines()
        for i in data:
            if re.search(pattern2, i):
                index = data.index(i)
                i = i.replace("59", str(bpy.data.scenes['Scene'].sequence_editor.active_strip.frame_final_duration))
                i = i.replace("0001", "{0:04d}".format(bpy.data.scenes['Scene'].sequence_editor.active_strip.frame_final_start))
                data[index] = i
                break

    with open(os.path.join(directory, dir_name, "main.tnz"), "w") as d:
        new_file = d.writelines(data)

    shutil.copy2(os.path.join(directory, "template", "07-1000_otprj.xml"), os.path.join(directory, dir_name, dir_name + "_otprj.xml"))
    shutil.copy2(os.path.join(directory, "template", "project.conf"), os.path.join(directory, dir_name, "project.conf"))
    shutil.copy2(os.path.join(directory, "template", "scenes.xml"), os.path.join(directory, dir_name, "scenes.xml"))
    shutil.copy2(os.path.join(directory, "template", "drawings", "scenes.xml"), os.path.join(directory, dir_name, "drawings", "scenes.xml"))
    shutil.copy2(os.path.join(directory, "template", "extras", "scenes.xml"), os.path.join(directory, dir_name, "extras", "scenes.xml"))
    shutil.copy2(os.path.join(directory, "template", "inputs", "scenes.xml"), os.path.join(directory, dir_name, "inputs", "scenes.xml"))
    shutil.copy2(os.path.join(directory, "template", "scripts", "scenes.xml"), os.path.join(directory, dir_name, "scripts", "scenes.xml"))

    bpy.context.scene.render.image_settings.file_format = format
    bpy.context.scene.frame_start = start
    bpy.context.scene.frame_end = end

class ScriptOperator(bpy.types.Operator):
    bl_idname = "object.script_operator"
    bl_label = "Render"
    
    def execute(self, context):
        main(context)
        return {'FINISHED'}
        
class Script(bpy.types.Panel): 
    bl_label = "Rendering frames"
    bl_idname = "script_PT_render2 "
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bi_context = "scene"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        row = layout.row()
        row.scale_y = 1.5
        row.operator("object.script_operator")
        
def register():	
  bpy.utils.register_class(Script)
  bpy.utils.register_class(ScriptOperator)
 
def unregister():	
  bpy.utils.unregister_class(Script)   
  bpy.utils.unregister_class(ScriptOperator)
 
if __name__ == "__main__":
  register()