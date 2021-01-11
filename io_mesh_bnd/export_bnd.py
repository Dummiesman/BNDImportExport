# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Copyright (C) Dummiesman, 2016
#
# ##### END LICENSE BLOCK #####

import os, time, struct, math, sys
import os.path as path

import bpy, bmesh, mathutils

# globals
global apply_modifiers_G
apply_modifiers_G = True

######################################################
# EXPORT HELPERS
######################################################
def bounds(obj):

    local_coords = obj.bound_box[:]
    om = obj.matrix_world
    coords = [p[:] for p in local_coords]

    rotated = zip(*coords[::-1])

    push_axis = []
    for (axis, _list) in zip('xyz', rotated):
        info = lambda: None
        info.max = max(_list)
        info.min = min(_list)
        info.distance = info.max - info.min
        push_axis.append(info)

    import collections

    originals = dict(zip(['x', 'y', 'z'], push_axis))

    o_details = collections.namedtuple('object_details', 'x y z')
    return o_details(**originals)

def get_undupe_name(name):
    nidx = name.find('.')
    return name[:nidx] if nidx != -1 else name


def find_object_ci(name):
    for obj in bpy.data.objects:
        if obj.name.lower() == name.lower() and obj.type == 'MESH':
            return obj
    return None

def write_char_array(file, w_str, length):
    file.write(bytes(w_str, 'utf-8'))
    file.write(bytes('\x00' * (length - len(w_str )), 'utf-8'))

def lerp(fr,to,t):
   return fr + (to - fr) * t

def vec_distance(v1, v2):
  nx = v2[0] - v1[0]
  ny = v2[1] - v1[1]
  return math.sqrt(nx * nx + ny * ny )
   
def poly_overlap_test(pl1, otl, ttc):
  #calculate center of otl
  otl_centerx = 0
  otl_centery = 0
  for p in otl:
    otl_centerx += p[0]
    otl_centery += p[1]
  otl_centerx /= len(otl)
  otl_centery /= len(otl)
  
  pl1.append(pl1[len(pl1) - 1])  
  for p1 in range(len(pl1) - 1):
    edge = (pl1[p1], pl1[p1+1])
    for et in range(11):
      et_prcnt = et/10
      lx = lerp(edge[0][0], edge[1][0], et_prcnt)
      ly = lerp(edge[0][1], edge[1][1], et_prcnt)
      if vec_distance((lx,ly), (otl_centerx, otl_centery)) < ttc:
        return True
  return False
  
def point_in_box(point, box):
  if box[0][0] <= point[0] and point[0] <= box[2][0] and box[0][1] <= point[1] and point[1] <= box[2][1]:
    return True
  return False
  
def point_in_polygon(p, vertices):
    n = len(vertices)
    inside =False

    x, y = p
    p1x,p1y = vertices[0]
    for i in range(n+1):
        p2x,p2y = vertices[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/float((p2y-p1y))+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x,p1y = p2x,p2y

    return inside


def write_binary_material(file, name):
    write_char_array(file, name, 32)
    file.write(struct.pack('ff', 0.1, 0.5))
    write_char_array(file, 'none', 32)
    write_char_array(file, 'none', 32)
    

def make_ascii_material(name):
    return "mtl " + name + " {\n\telasticity: 0.100000\n\tfriction: 0.500000\n\teffect: none\n\tsound: none\n}\n"


def point_in_bounds(bmin, bmax, p):
    return p[0] >= bmin[0] and p[1] >= bmin[1] and p[0] <= bmax[0] and p[1] <= bmax[1]

    
def edges_intersect(p1, p2, p3, p4):
    #https://stackoverflow.com/a/24392281
    #returns true if the line from (a,b)->(c,d) intersects with (p,q)->(r,s)
    a = p1[0]
    b = p1[1]
    c = p2[0]
    d = p2[1]
    p = p3[0]
    q = p3[1]
    r = p4[0]
    s = p4[1]
    
    det = (c - a) * (s - q) - (r - p) * (d - b);
    if abs(det) < 0.001:
      return False
    else:
      lmbda = ((s - q) * (r - a) + (p - r) * (s - b)) / det
      gamma = ((b - d) * (r - a) + (c - a) * (s - b)) / det
      return (0 < lmbda and lmbda < 1) and (0 < gamma and gamma < 1)
      
def bounds_intersect(amin, amax, bmin, bmax):
    return amin[0] <= bmax[0] and amax[0] >= bmin[0] and amin[1] <= bmax[1] and amax[1] >= bmin[1]


######################################################
# EXPORT MAIN FILES
######################################################
def export_terrain_bound(file, ob):
    # create temp mesh
    temp_mesh = None
    global apply_modifiers_G
    if apply_modifiers_G:
        dg = bpy.context.evaluated_depsgraph_get()
        eval_obj = ob.evaluated_get(dg)
        temp_mesh = eval_obj.to_mesh()
    else:
        temp_mesh = ob.to_mesh()
    
    # get bmesh
    bm = bmesh.new()
    bm.from_mesh(temp_mesh)
    bm.verts.ensure_lookup_table()
    bm.faces.index_update()
    
    # header
    file.write(struct.pack('f', 1.1))
    file.write(struct.pack('LLB', len(bm.faces), 0, 0))
    
    # boundbox
    bnds = bounds(ob)

    bnds_min = (bnds.x.min, bnds.y.min)
    bnds_max = (bnds.x.max, bnds.y.max)
    
    bnd_width = math.fabs(bnds.x.max - bnds.x.min)
    bnd_height = math.fabs(bnds.z.max - bnds.z.min)
    bnd_depth = math.fabs(bnds.y.max - bnds.y.min)

    file.write(struct.pack('fff', bnd_width, bnd_height, bnd_depth))
    
    # section data  
    width_sections = max(1, math.ceil(bnd_width / 10))
    depth_sections = max(1, math.ceil(bnd_depth / 10))
    height_sections = 1
    
    total_sections = width_sections * height_sections * depth_sections
    individual_section_width = (1 / width_sections) * bnd_width
    individual_section_depth = (1 / depth_sections) * bnd_depth
    
    file.write(struct.pack('LLLL', width_sections, height_sections, depth_sections, total_sections))
    
    #calculate intersecting polygons + poly indices
    poly_indices = 0
    section_groups = []
    
    for d in range(depth_sections):
      for w in reversed(range(width_sections)):
        BOUNDS_INFLATION = 0.1
        
        section_bnds_min = ((bnds_min[0] + (w * individual_section_width)) - BOUNDS_INFLATION, (bnds_min[1] + (d * individual_section_depth)) - BOUNDS_INFLATION)
        section_bnds_max = ((bnds_min[0] + ((w + 1) * individual_section_width)) + BOUNDS_INFLATION, (bnds_min[1] + ((d + 1) * individual_section_depth)) + BOUNDS_INFLATION)
        
        section_edges = []
        section_edges.append(((section_bnds_min[0], section_bnds_min[1]), (section_bnds_max[0], section_bnds_min[1])))
        section_edges.append(((section_bnds_max[0], section_bnds_min[1]), (section_bnds_max[0], section_bnds_max[1])))
        section_edges.append(((section_bnds_min[0], section_bnds_max[1]), (section_bnds_max[0], section_bnds_max[1])))
        section_edges.append(((section_bnds_min[0], section_bnds_min[1]), (section_bnds_min[0], section_bnds_max[1])))
        
        section_group = []
        section_poly = [(section_bnds_min[0], section_bnds_min[1]), (section_bnds_max[0], section_bnds_min[1]), (section_bnds_max[0], section_bnds_max[1]), (section_bnds_min[0], section_bnds_max[1])]
        
        for f in bm.faces:
          # quick bounds check
          face_2d = []
          for loop in f.loops:
            face_2d.append((loop.vert.co[0], loop.vert.co[1])) 
          
          face_min = [9999, 9999]
          face_max = [-9999, -9999]
          for pt in face_2d:
            face_min[1] = min(face_min[1], pt[1])
            face_min[0] = min(face_min[0], pt[0])
            face_max[1] = max(face_max[1], pt[1])
            face_max[0] = max(face_max[0], pt[0])
          if not bounds_intersect(face_min, face_max, section_bnds_min, section_bnds_max):
            continue
          
          # slower edges check
          isect = False
          for edge in f.edges:
            if isect:
                break
                
            v0_3d = edge.verts[0]
            v1_3d = edge.verts[1]
            v0 = (v0_3d.co[0], v0_3d.co[1])
            v1 = (v1_3d.co[0], v1_3d.co[1])
            
            isect |= point_in_bounds(section_bnds_min, section_bnds_max, v0)
            isect |= point_in_bounds(section_bnds_min, section_bnds_max, v1)
            
            # check if the face surrounds this polygon
            if not isect:
                for p in section_poly:
                    isect |= point_in_polygon(p, face_2d)
                    if isect:
                        break
            
            # more expensive edge-edge intersect testing (only if edge is not vertical)
            edge_is_vertical = v0[0] == v1[0] and v0[1] == v1[1]
            if not isect and not edge_is_vertical:
                for se in section_edges:
                    isect |= edges_intersect(se[0], se[1], v0, v1)
                    if isect:
                        break
            
          if isect:
            section_group.append(f.index)
            poly_indices += 1
        
        section_groups.append(section_group)
        
    # continue writing more binary information about boxes and stuff
    file.write(struct.pack('L', poly_indices))
    
    if bnd_width == 0:
      file.write(struct.pack('f', float('Inf')))
    else:
      file.write(struct.pack('f', width_sections / bnd_width))
      
    file.write(struct.pack('f', 1))
      
    if bnd_depth == 0:
      file.write(struct.pack('f', float('Inf')))
    else:
      file.write(struct.pack('f', depth_sections / bnd_depth))
      
    file.write(struct.pack('ffffff',  -bnds.x.max, bnds.z.min, bnds.y.min, -bnds.x.min, bnds.z.max ,bnds.y.max))
    
    # write index info
    tot_ind = 0
    for i in range(total_sections):
      file.write(struct.pack('H', tot_ind))
      tot_ind += len(section_groups[i])

    for i in range(total_sections):
      file.write(struct.pack('H', len(section_groups[i])))
      
    for i in range(total_sections):
      for j in range(len(section_groups[i])):
          file.write(struct.pack('H', section_groups[i][j]))
      
        
    # finish off
    bm.free()
    file.close()
    return
    
def export_binary_bound(file, ob):
    # create temp mesh
    temp_mesh = None
    global apply_modifiers_G
    if apply_modifiers_G:
        dg = bpy.context.evaluated_depsgraph_get()
        eval_obj = ob.evaluated_get(dg)
        temp_mesh = eval_obj.to_mesh()
    else:
        temp_mesh = ob.to_mesh()
        
    # get bmesh
    bm = bmesh.new()
    bm.from_mesh(temp_mesh)

    # header
    file.write(struct.pack('B', 1))
    file.write(struct.pack('LLL', len(bm.verts), len(ob.material_slots), len(bm.faces)))
    
    # vertices
    for v in bm.verts:
        file.write(struct.pack('fff', v.co[0] * -1, v.co[2], v.co[1]))

    # materials
    num_materials = len(ob.material_slots)
    if num_materials > 0:
        for ms in ob.material_slots:
            mat = ms.material
            write_binary_material(file, get_undupe_name(mat.name))
    else:
        write_binary_material(file, "default")

    # faces
    bm.verts.index_update()
    for fcs in bm.faces:
        material_index = max(0, fcs.material_index)
        if len(fcs.loops) == 3:
            file.write(struct.pack('HHHHH', fcs.loops[0].vert.index, fcs.loops[1].vert.index, fcs.loops[2].vert.index, 0, material_index))
        elif len(fcs.loops) == 4:
            file.write(struct.pack('HHHHH', fcs.loops[0].vert.index, fcs.loops[1].vert.index, fcs.loops[2].vert.index, fcs.loops[3].vert.index, material_index))
    
    # finish off
    bm.free()
    file.close()
    return


def export_bound(file, ob):
    # create temp mesh
    temp_mesh = None
    global apply_modifiers_G
    if apply_modifiers_G:
        dg = bpy.context.evaluated_depsgraph_get()
        eval_obj = ob.evaluated_get(dg)
        temp_mesh = eval_obj.to_mesh()
    else:
        temp_mesh = ob.to_mesh()
    
    # get bmesh
    bm = bmesh.new()
    bm.from_mesh(temp_mesh)

    # header
    bnd_file = "version: 1.01\nverts: " + str(len(bm.verts)) + "\nmaterials: " + str(len(ob.material_slots)) + "\nedges: 0\npolys: " + str(len(bm.faces)) + "\n\n"

    # vertices
    for v in bm.verts:
        bnd_file += "v " + "{0:.6f}".format(v.co[0] * -1) + " " + "{0:.6f}".format(v.co[2]) + " " + "{0:.6f}".format(v.co[1]) + "\n"

    bnd_file += "\n"

    # materials
    num_materials = len(ob.material_slots)
    if num_materials > 0:
        for ms in ob.material_slots:
            mat = ms.material
            bnd_file += make_ascii_material(get_undupe_name(mat.name))
    else:
        bnd_file += make_ascii_material("default")
        
    bnd_file += "\n"

    # faces
    bm.verts.index_update()
    for fcs in bm.faces:
        material_index = max(0, fcs.material_index)
        if len(fcs.loops) == 3:
            bnd_file += "tri " + str(fcs.loops[0].vert.index) + "  " + str(fcs.loops[1].vert.index) + "  " + str(fcs.loops[2].vert.index) + "  " + str(material_index) + "\n"
        elif len(fcs.loops) == 4:
            bnd_file += "quad " + str(fcs.loops[0].vert.index) + "  " + str(fcs.loops[1].vert.index) + "  " + str(fcs.loops[2].vert.index) + "  " + str(fcs.loops[3].vert.index) + "  " + str(material_index) + "\n"
            
    # write BOUND
    file.write(bnd_file)

    # finish off
    bm.free()
    file.close()
    return


######################################################
# EXPORT
######################################################
def save_bnd(filepath,
             export_binary,
             export_terrain,
             context):

    print("exporting BOUND: %r..." % (filepath))

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    time1 = time.clock()
    

    # find bound object
    bound_obj = find_object_ci("BOUND")
    if bound_obj is None:
      raise Exception('No BOUND object in scene.')
    
    # write bnd
    file = open(filepath, 'w')
    export_bound(file, bound_obj)
    
    if export_binary:
      # write BBND
      binfile = open(filepath[:-3] + "bbnd", 'wb')
      export_binary_bound(binfile, bound_obj)
    
    if export_terrain:
      # write TER
      terfile = open(filepath[:-3] + "ter", 'wb')
      export_terrain_bound(terfile, bound_obj)
      
    # bound export complete
    print(" done in %.4f sec." % (time.clock() - time1))


def save(operator,
         context,
         filepath="",
         export_binary=False,
         export_terrain=False,
         apply_modifiers=False
         ):
    
    # set object modes
    for ob in context.scene.objects:
      if ob.type == 'MESH' and ob.name.lower() == "bound":
        context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
      elif ob.name.lower() == "bound" and ob.type != 'MESH':
        raise Exception("BOUND has invalid object type, or is not visible in the scene")
    
    # set globals
    global apply_modifiers_G
    apply_modifiers_G = apply_modifiers
    
    # save BND
    save_bnd(filepath,
             export_binary,
             export_terrain,
             context,
             )

    return {'FINISHED'}
