import bpy
import operator

class ClothExporter_PT_Panel(bpy.types.Panel):
  bl_idname = "ClothExporter_PT_Panel"
  bl_label = "Cloth Exporter for Unity"
  bl_description = "Exports cloth data in a unique topology for Unity"
  bl_space_type = "VIEW_3D"
  bl_region_type = "UI"
  bl_category = "Cloth Exporter"

  def draw(self, context):
    layout = self.layout
    obj = context.object
    scene = context.scene

    prop_ClothExp = scene.prop_ClothExp

    if (obj != None):
      if (obj.data.is_editmode):
        row = layout.row()
        row.operator("cloth_exporter.transform", text="Transform Mesh for PBD")

        row = layout.row()
        row.prop(prop_ClothExp, "mass")
        row = layout.row()
        row.prop(prop_ClothExp, "inv_mass")
        row.enabled = False
        row = layout.row()
        row.prop(prop_ClothExp, "filename")
        row = layout.row()
        row.prop(prop_ClothExp, "directory")

        row = layout.row()
        row.operator("cloth_exporter.export", text="Export data for Unity")

      else:
        layout.label(text="Enter edit mode to access the features.")
        # box = layout.box()
        # row = box.row()
        # row.label(text="Distance Constraint")
        # row = box.row()
        # row.prop(prop_ClothExp, "compression_stiffness")
        # row = box.row()
        # row.prop(prop_ClothExp, "strech_stiffness")
