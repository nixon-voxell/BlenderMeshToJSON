import bpy
import operator

class ClothExporter_PT_Panel(bpy.types.Panel):
  bl_idname = "ClothExporter_PT_Panel"
  bl_label = "Cloth Exporter for Unity"
  bl_description = "Exports cloth data in a unique form for Unity"
  bl_space_type = "VIEW_3D"
  bl_region_type = "UI"
  bl_category = "Cloth Exporter"

  def draw(self, context):
    layout = self.layout
    obj = context.object
    scene = context.scene

    properties = scene.properties

    if (bpy.context.object.mode == "EDIT"):
      row = layout.row()
      row.operator("cloth_exporter.transform", text="Transform Mesh for PBD")

      row = layout.row()
      row.prop(properties, "mass")
      row = layout.row()
      row.prop(properties, "inv_mass")
      row.enabled = False
      row = layout.row()
      row.prop(properties, "filename")
      row = layout.row()
      row.prop(properties, "directory")

      row = layout.row()
      row.operator("cloth_exporter.export", text="Export data for Unity")

    else:
      layout.label(text="Enter edit mode to access the features.")
      # row = layout.row()
      # row.prop(properties, "max_frame")
      # box = layout.box()
      # row = box.row()
      # row.label(text="Distance Constraint")
      # row = box.row()
      # row.prop(properties, "compression_stiffness")
      # row = box.row()
      # row.prop(properties, "strech_stiffness")
