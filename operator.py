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

# TODO: move from particle seperation to particle list

class Particle(object):

  def __init__(self, particle, uv_layer, inv_mass, mass):
    self.pos = list(particle.co)
    self.predicted_pos = list(particle.co)
    self.veloctiy = [0, 0, 0]
    self.inv_mass = inv_mass
    self.mass = mass
    self.idx = particle.index
    self.phase = 0

    self.uv_layer = uv_layer
    self.uv = list(particle.link_loops[0][uv_layer].uv);

  def __lt__(self, other):
    return self.idx < other.idx

  def __gt__(self, other):
    return self.idx > other.idx

  def to_dict(self):
    final_dict = dict()

    final_dict["pos"] = self.pos
    final_dict["predictedPos"] = self.predicted_pos
    final_dict["veloctiy"] = self.veloctiy
    final_dict["invMass"] = self.inv_mass
    final_dict["mass"] = self.mass
    final_dict["idx"] = self.idx
    final_dict["phase"] = self.phase
    final_dict["uv"] = self.uv

    return final_dict

class Edge(object):

  def __init__(self, edge):
    self.p = [v.index for v in edge.verts]
    self.restLength = (edge.verts[0].co - edge.verts[1].co).length

    self.neighbors = list()
    for vert in edge.verts:
      for link_edge in vert.link_edges:
        if link_edge != edge:
          self.neighbors.append(link_edge.index)

    self.idx = edge.index

  def __lt__(self, other):
    return self.idx < other.idx

  def __gt__(self, other):
    return self.idx > other.idx

  def has_particle(self, particle):
    return particle.idx in self.p

  def to_dict(self):
    final_dict = dict()

    final_dict["p"] = self.p
    final_dict["neighbors"] = self.neighbors
    final_dict["idx"] = self.idx
    final_dict["restLength"] = self.restLength

    return final_dict

class Triangle(object):

  def __init__(self, triangle):
    self.p = [v.index for v in triangle.verts]

    self.neighbors = list()
    for vert in triangle.verts:
      for link_triangle in vert.link_faces:
        if link_triangle != triangle:
          self.neighbors.append(link_triangle.index)

    self.idx = triangle.index

  def __lt__(self, other):
    return self.idx < other.idx
  
  def __gt__(self, other):
    return self.idx > other.idx
  
  def has_edge(self, edge):
    return edge.p0 in self.triangle_idx and edge.p1 in self.triangle_idx

  def has_particle(self, particle):
    return particle.idx in self.p

  def to_dict(self):
    final_dict = dict()

    final_dict["p"] = self.p
    final_dict["neighbors"] = self.neighbors
    final_dict["idx"] = self.idx

    return final_dict

class NeighborTriangles(object):

  def __init__(self, edge, edge2neighbor_triangle):
    triangles = edge.link_faces
    verts = edge.verts
    t1 = list(triangles[0].verts)
    t2 = list(triangles[1].verts)

    for p in verts:
      t1.remove(p)
      t2.remove(p)

    p0 = t1[0]
    p1 = t2[0]
    p2 = verts[0]
    p3 = verts[1]

    n1 = (p2.co - p0.co).cross(p3.co - p0.co)
    n1 /= n1.dot(n1)
    n2 = (p3.co - p1.co).cross(p2.co - p1.co)
    n2 /= n2.dot(n2)

    n1.normalize()
    n2.normalize()

    try:
      self.rest_angle = math.acos(n1.dot(n2))
    except Exception as e:
      print(e)
      self.rest_angle = 0.0

    _p = [p0, p1, p2, p3]
    self.p = [p.index for p in _p]

    self.neighbors = list()
    for vert in verts:
      for link_edge in vert.link_edges:
        if len(link_edge.link_faces) == 2 and link_edge != edge:
          self.neighbors.append(edge2neighbor_triangle[link_edge.index])

    self.idx = edge2neighbor_triangle[edge.index]

  def __lt__(self, other):
    return self.idx < other.idx
  
  def __gt__(self, other):
    return self.idx > other.idx

  def to_dict(self):
    final_dict = dict()

    final_dict["p"] = self.p
    final_dict["neighbors"] = self.neighbors
    final_dict["idx"] = self.idx
    final_dict["restAngle"] = self.rest_angle

    return final_dict

class ClothExporter_OT_Transform(bpy.types.Operator):
  bl_idname = "cloth_exporter.transform"
  bl_label = "Cloth Exporter"
  bl_description = "Transform mesh into a structure that is easy to simulate"
  bl_info = "v0.0.2"

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
    sequence_length = []

    uv_layer = mesh.loops.layers.uv.active

    # particles
    for p in mesh.verts:
      i = p.index
      particles[i] = Particle(p, uv_layer, prop_ClothExp.inv_mass, prop_ClothExp.mass).to_dict()

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

    # edge to neighbor triangle index
    edge2neighbor_triangle = dict()
    for e in mesh.edges:
      if len(e.link_faces) == 2:
        edge2neighbor_triangle[e.index] = len(edge2neighbor_triangle)

    # neighbor triangles
    for e in mesh.edges:
      if len(e.link_faces) == 2:
        neighbor_triangles.append(NeighborTriangles(e, edge2neighbor_triangle).to_dict())

    # sequence
    for p in mesh.verts:
      sequence_length.append(len(p.link_faces))
      for f in p.link_faces:
        for pp in f.verts:
          sequence.append(pp.index)

    for i in range(1, len(sequence_length)):
      sequence_length[i] += sequence_length[i-1]

    # save to filepath based on filename and current selected directory
    filepath = os.path.join(prop_ClothExp.directory, "%s.json" % prop_ClothExp.filename)
    filepath = bpy.path.abspath(filepath)

    # edge_cliques = self.create_cliques(edges)
    # triangle_cliques = self.create_cliques(triangles)
    # neighbor_triangle_cliques = self.create_cliques(neighbor_triangles)

    json.dump(
      {
        "particles": particles,
        "edges": edges,
        "triangles": triangles,
        "neighborTriangles": neighbor_triangles,
        "sequence": sequence,
        "sequenceLength": sequence_length,
        # "edgeCliques": edge_cliques,
        # "triCliques": triangle_cliques,
        # "neighborTriCliques": neighbor_triangle_cliques
      },
      open(filepath, "w"),
      indent=2
    )

    self.report({"INFO"}, f"Exported to Unity format in Json, {total_verts} vertices, {total_edges} edges, {total_triangles} triangles, {len(neighbor_triangles)} neighbor trianlges.")
    return {"FINISHED"}

  def draw(self, context):
    layout = self.layout
    layout.prop(self, "mass")

  @classmethod
  def bron_kerbosch1(self, clique, candidates, excluded, constraints, output_clique):
    # Naive Bron–Kerbosch algorithm
    if not candidates and not excluded:
      output_clique.append(clique)
      return

    for v in list(candidates):
      candidates.remove(v)
      new_candidates = candidates.intersection(constraints[v]["neighbors"])
      new_excluded = excluded.intersection(constraints[v]["neighbors"])
      self.bron_kerbosch1(clique + [v], new_candidates, new_excluded, constraints, output_clique)
      excluded.add(v)

  @classmethod
  def create_cliques(self, constraints):
    nodes = set(range(len(constraints)))
    output_cliques = []
    self.bron_kerbosch1([], nodes, set(), constraints, output_cliques)
    output_cliques.sort(key=len, reverse=True)

    return output_cliques