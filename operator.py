import bpy, bmesh
import numpy as np
import mathutils as mt
import math
import json
import os


global original_mesh
global cloth_mesh

original_mesh = None
cloth_mesh = None


class Particle(object):

  def __init__(self, particle, inv_mass, mass):
    self.pos = list(particle.co)
    self.predicted_pos = list(particle.co)
    self.veloctiy = [0, 0, 0]
    self.inv_mass = inv_mass
    self.mass = mass
    self.idx = particle.index
    self.phase = 0

  def __lt__(self, other):
    return self.idx < other.idx

  def __gt__(self, other):
    return self.idx > other.idx

  def to_dict(self):
    final_dict = dict()

    final_dict["pos"] = self.pos
    final_dict["predictedPos"] = self.predicted_pos
    final_dict["invMass"] = self.inv_mass
    final_dict["mass"] = self.mass
    final_dict["idx"] = self.idx
    final_dict["phase"] = self.phase
    final_dict["veloctiy"] = self.veloctiy

    return final_dict

class Edge(object):

  def __init__(self, edge):
    e = []

    for p in edge.verts:
      e.append(p)

    self.restLength = (e[0].co - e[1].co).length
    e = [e.index for e in e]
    self.p0 = min(e)
    self.p1 = max(e)

    assert self.p0 != self.p1

    self.edge_idx = [self.p0, self.p1]
    self.idx = edge.index

  def __lt__(self, other):
    return self.idx < other.idx

  def __gt__(self, other):
    return self.idx > other.idx

  def has_particle(self, particle):
    return particle.idx in self.edge_idx

  def has_idx(self, idx):
    return idx in self.edge_idx

  def to_dict(self):
    final_dict = dict()

    final_dict["p0"] = self.p0
    final_dict["p1"] = self.p1
    final_dict["restLength"] = self.restLength
    final_dict["idx"] = self.idx

    return final_dict

class Triangle(object):

  def __init__(self, triangle):
    t = []
    for p in triangle.verts:
      t.append(p.index)

    self.p0 = min(t)
    t.remove(self.p0)
    self.p2 = max(t)
    t.remove(self.p2)
    self.p1 = t[0]

    assert self.p0 != self.p1
    assert self.p1 != self.p2
    assert self.p2 != self.p0

    self.triangle_idx = [self.p0, self.p1, self.p2]
    self.idx = triangle.index

  def __lt__(self, other):
    return self.idx < other.idx
  
  def __gt__(self, other):
    return self.idx > other.idx
  
  def has_edge(self, edge):
    return edge.p0 in self.triangle_idx and edge.p1 in self.triangle_idx

  def has_particle(self, particle):
    return particle.idx in self.triangle_idx

  def has_idx(self, idx):
    return idx in self.triangle_idx

  def to_dict(self):
    final_dict = dict()

    final_dict["p0"] = self.p0
    final_dict["p1"] = self.p1
    final_dict["p2"] = self.p2
    final_dict["idx"] = self.idx

    return final_dict

class NeighborTriangles(object):

  def __init__(self, triangles, edge, idx):
    t1 = list(triangles[0].verts)
    t2 = list(triangles[1].verts)

    for p in edge:
      t1.remove(p)
      t2.remove(p)

    p0 = t1[0]
    p1 = t2[0]
    p2 = edge[0]
    p3 = edge[1]

    n1 = (p2.co - p0.co).cross(p3.co - p0.co)
    n1 /= n1.dot(n1)
    n2 = (p3.co - p1.co).cross(p2.co - p1.co)
    n2 /= n2.dot(n2)

    n1.normalize()
    n2.normalize()
    self.rest_angle = math.acos(n1.dot(n2))

    self.p0 = p0.index
    self.p1 = p1.index
    self.p2 = p2.index
    self.p3 = p3.index

    assert self.p0 != self.p1
    assert self.p0 != self.p2
    assert self.p0 != self.p3
    assert self.p1 != self.p2
    assert self.p1 != self.p3
    assert self.p2 != self.p3

    self.neighbor_triangle_idx = [self.p0, self.p1, self.p2, self.p3]
    self.idx = idx

  def __lt__(self, other):
    return self.idx < other.idx
  
  def __gt__(self, other):
    return self.idx > other.idx

  def to_dict(self):
    final_dict = dict()

    final_dict["p0"] = self.p0
    final_dict["p1"] = self.p1
    final_dict["p2"] = self.p2
    final_dict["p3"] = self.p3
    final_dict["restAngle"] = self.rest_angle
    final_dict["idx"] = self.idx

    return final_dict

class ClothExporter_OT_Transform(bpy.types.Operator):
  bl_idname = "cloth_exporter.transform"
  bl_label = "Cloth Exporter"
  bl_description = "Transform mesh into a structure that is easy to simulate"
  bl_info = "v0.0.1"

  def execute(self, context):

    global original_mesh
    global cloth_mesh

    obj = bpy.context.active_object
    mesh = bmesh.from_edit_mesh(obj.data)

    original_mesh = mesh

    for f in mesh.faces:
      if len(f.verts) > 3:
        co_sum = mt.Vector((0, 0, 0))
        for v in f.verts:
          co_sum += v.co

        center = co_sum / len(f.verts)
        center_v = mesh.verts.new(center)

        for e in f.edges:
          v1 = e.verts[0]
          v2 = e.verts[1]
          
          mesh.faces.new((v1, v2, center_v))

        bmesh.ops.delete(mesh, geom=[f], context="FACES")

    cloth_mesh = mesh

    self.report({"INFO"}, "Transformed faces higher than 3 vertices into PBD mode :)")
    bmesh.update_edit_mesh(obj.data, True)

    return {"FINISHED"}

class ClothExporter_OT_Export(bpy.types.Operator):
  bl_idname = "cloth_exporter.export"
  bl_label = "Cloth Exporter"
  bl_description = "Exports cloth data in a unique format for Unity to use."
  bl_info = "v0.0.1"

  def execute(self, context):

    prop_ClothExp = context.scene.prop_ClothExp
    obj = bpy.context.active_object
    mesh = bmesh.from_edit_mesh(obj.data)

    total_verts = len(mesh.verts)
    total_edges = len(mesh.edges)
    total_triangles = len(mesh.faces)

    particles = [None for i in range(total_verts)]
    edges = [None for i in range(total_edges)]
    triangles = [None for i in range(total_triangles)]
    neighbor_triangles = []
    sequence = []

    # particles
    for p in mesh.verts:
      i = p.index
      particles[i] = Particle(p, prop_ClothExp.inv_mass, prop_ClothExp.mass).to_dict()

    assert not None in particles

    # edges
    for e in mesh.edges:
      i = e.index
      edges[i] = Edge(e).to_dict()

    assert not None in edges

    # triangles
    for f in mesh.faces:
      i = f.index
      triangles[i] = Triangle(f).to_dict()

    assert not None in triangles

    # neighbor triangles
    for e in mesh.edges:
      if len(e.link_faces) == 2:
        neighbor_triangles.append(NeighborTriangles(
          e.link_faces,
          e.verts,
          len(neighbor_triangles)).to_dict())

    # vertex sequence
    for f in mesh.faces:
      for p in f.verts:
        sequence.append(p.index)

    # print(sequence)
    # print(len(sequence))

    # save to filepath based on filename and current selected directory
    filepath = os.path.join(prop_ClothExp.directory, "%s.json" % prop_ClothExp.filename)
    filepath = bpy.path.abspath(filepath)

    json.dump(
      {
        "particles": particles,
        "edges": edges,
        "triangles": triangles,
        "neighborTriangles": neighbor_triangles,
        "sequence": sequence
      },
      open(filepath, "w")
    )

    self.report({"INFO"}, f"Exported to Unity format in Json, {total_verts} vertices, {total_edges} edges, {total_triangles} triangles, {len(neighbor_triangles)} neighbor trianlges.")
    return {"FINISHED"}

  def draw(self, context):
    layout = self.layout
    layout.prop(self, "mass")

# def my_handler(scene):
#   print("Frame Change", scene.frame_current)


# bpy.app.handlers.frame_change_pre.append(my_handler)