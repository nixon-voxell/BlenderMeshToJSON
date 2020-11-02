# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

bl_info = {
  "name" : "Cloth Exporter",
  "author" : "Voxell",
  "description" : "Exports data of cloth mesh",
  "blender" : (2, 90, 0),
  "version" : (0, 1, 0),
  "location" : "View3D",
  "warning" : "This is still in an extremely early version, it might break your work or crash Blender...",
  "category" : "Generic"
}

import bpy

from .operator import ClothExporter_OT_Transform, ClothExporter_OT_Export
from .panel import ClothExporter_PT_Panel
from .properties import Properties

classes = (
  # operators
  ClothExporter_OT_Transform,
  ClothExporter_OT_Export,

  # panels
  ClothExporter_PT_Panel,

  # prop_ClothExp
  Properties
  )

def register():
  for c in classes:
    bpy.utils.register_class(c)
  
  bpy.types.Scene.prop_ClothExp = bpy.props.PointerProperty(type=Properties)

def unregister():
  for c in classes:
    bpy.utils.unregister_class(c)

  del bpy.types.Scene.prop_ClothExp

# register, unregister = bpy.utils.register_classes_factory(classes)