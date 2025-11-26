#####################################################################################################################
# Copyright(C) 2011-2025 IT4Innovations National Supercomputing Center, VSB - Technical University of Ostrava
#
# This program is free software : you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#####################################################################################################################
import bpy

from . import braas_hpc_xmlmaterial_convert

class XMLMATERIAL_PT_MaterialPanel(bpy.types.Panel):
    bl_label = "XML"
    bl_idname = "XMLMATERIAL_PT_material_panel"
    bl_space_type = 'NODE_EDITOR'  # Ensures the panel appears in the Shader Editor
    bl_region_type = 'UI'  # Adds the panel to the right sidebar
    bl_category = 'XML'  # Tab name in the Shader Editor
    bl_context = 'shader'  # Restricts the panel to the Shader Editor context

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.operator("braas_hpc_xmlmaterial.export_shader", text="Export Shader")
        col.operator("braas_hpc_xmlmaterial.export_node", text="Export Node")
        #col.operator("braas_hpc_xmlmaterial.import", text="Import")

class XMLMATERIAL_OT_ExportShader(bpy.types.Operator):
    bl_idname = "braas_hpc_xmlmaterial.export_shader"
    bl_label = "Export Shader"

    def execute(self, context):
        node_tree = context.space_data.edit_tree
        shader = context.space_data.id

        pretty_xml = braas_hpc_xmlmaterial_convert.export_shader(shader, node_tree)

        # Define the text name
        text_name = "XML_EXPORT"

        # Check if the text exists in Blender's text editor
        if text_name in bpy.data.texts:
            text_data = bpy.data.texts[text_name]
        else:
            # Create a new text data block if it doesn't exist
            text_data = bpy.data.texts.new(name=text_name)

        # Add or modify content
        text_data.clear()  # Clear existing content (optional)
        text_data.write(pretty_xml)

        # Print confirmation
        print(f"Text '{text_name}' is ready in the Text Editor.")            

        return {'FINISHED'}
    
class XMLMATERIAL_OT_ExportNode(bpy.types.Operator):
    bl_idname = "braas_hpc_xmlmaterial.export_node"
    bl_label = "Export Node"

    def execute(self, context):
        node_tree = context.space_data.edit_tree
        shader = context.space_data.id
        active_node = node_tree.nodes.active
        if active_node:
            pretty_xml = braas_hpc_xmlmaterial_convert.export_node(shader, active_node)

            # Define the text name
            text_name = "XML_EXPORT"

            # Check if the text exists in Blender's text editor
            if text_name in bpy.data.texts:
                text_data = bpy.data.texts[text_name]
            else:
                # Create a new text data block if it doesn't exist
                text_data = bpy.data.texts.new(name=text_name)

            # Add or modify content
            text_data.clear()  # Clear existing content (optional)
            text_data.write(pretty_xml)

            # Print confirmation
            print(f"Text '{text_name}' is ready in the Text Editor.")            
        else:
            print(f"No Active Node")

        return {'FINISHED'}

class XMLMATERIAL_OT_Import(bpy.types.Operator):
    bl_idname = "braas_hpc_xmlmaterial.import"
    bl_label = "Import"

    def execute(self, context):
        return {'FINISHED'}
    
def register():
    bpy.utils.register_class(XMLMATERIAL_PT_MaterialPanel)
    bpy.utils.register_class(XMLMATERIAL_OT_ExportShader)
    bpy.utils.register_class(XMLMATERIAL_OT_ExportNode)
    bpy.utils.register_class(XMLMATERIAL_OT_Import)

def unregister():
    bpy.utils.unregister_class(XMLMATERIAL_PT_MaterialPanel)
    bpy.utils.unregister_class(XMLMATERIAL_OT_ExportShader)
    bpy.utils.unregister_class(XMLMATERIAL_OT_ExportNode)
    bpy.utils.unregister_class(XMLMATERIAL_OT_Import)

if __name__ == "__main__":
    register()

