import bpy

def update_inv_mass(self, context):
  self.inv_mass = 1 / self.mass

class Properties(bpy.types.PropertyGroup):
  props = bpy.props
  mass = props.FloatProperty(
    name="Mass",
    default=0.1,
    precision=2,
    update=update_inv_mass
    )

  inv_mass = props.FloatProperty(
    name="InvMass",
    default=1/0.1,
    precision=2
    )

  filename = props.StringProperty(
    name="Filename",
    default="ClothData"
  )

  directory = props.StringProperty(
    name="Directory",
    subtype="DIR_PATH"
    )

  # compression_stiffness = props.FloatProperty(
  #   name="Compression Stiffness",
  #   default=1
  # )

  # strech_stiffness = props.FloatProperty(
  #   name="Strech Stiffness",
  #   default=1
  # )