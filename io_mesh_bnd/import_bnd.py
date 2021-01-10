# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Created by Dummiesman, 2016-2020
#
# ##### END LICENSE BLOCK #####

import bpy, bmesh
import time

# material color list
material_colors = {
                    'grass': (0, 0.507, 0.005, 1.0),
                    'cobblestone': (0.040, 0.040, 0.040, 1.0),
                    'default': (1, 1, 1, 1.0),
                    'wood': (0.545, 0.27, 0.074, 1.0),
                    'dirt': (0.545, 0.35, 0.168, 1.0),
                    'mud': (0.345, 0.25, 0.068, 1.0),
                    'sand': (1, 0.78, 0.427, 1.0),
                    'water': (0.20, 0.458, 0.509, 1.0),
                    'deepwater': (0.15, 0.408, 0.459, 1.0),
                  }

######################################################
# IMPORT MAIN FILES
######################################################
def create_material(name):
    name_l = name.lower()
    
    # get color
    material_color = (1,1,1)
    if name_l in material_colors:
      material_color = material_colors[name_l]
      
    # setup material
    mtl = bpy.data.materials.new(name=name_l)
    mtl.diffuse_color = material_color
    mtl.specular_intensity = 0
    
    mtl.use_nodes = True
    mtl.use_backface_culling = True
    
    # get output node
    output_node = None
    for node in mtl.node_tree.nodes:
        if node.type == "OUTPUT_MATERIAL":
            output_node = node
            break
    
    # clear principled, put diffuse in it's place
    bsdf = mtl.node_tree.nodes["Principled BSDF"]
    mtl.node_tree.nodes.remove(bsdf)
    
    bsdf = mtl.node_tree.nodes.new(type='ShaderNodeBsdfDiffuse')
    mtl.node_tree.links.new( bsdf.outputs['BSDF'], output_node.inputs['Surface'] )
    
    # setup bsdf
    bsdf.inputs["Color"].default_value = material_color
    
    return mtl
    
def read_bnd_file(file):
    scn = bpy.context.scene
    # add a mesh and link it to the scene
    me = bpy.data.meshes.new('BoundMesh')
    ob = bpy.data.objects.new('BOUND', me)

    bm = bmesh.new()
    bm.from_mesh(me)
    
    scn.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    
    # read in BND file!
    for raw_line in file.readlines():
      # get line components
      cmps = raw_line.lower().split()
      
      # empty line?
      if len(cmps) < 2:
        continue
      
      # not an empty line, read it!
      if cmps[0] == "v":
        # vertex
        bm.verts.new((float(cmps[1]) * -1, float(cmps[3]), float(cmps[2])))
        bm.verts.ensure_lookup_table()
      elif cmps[0] == "mtl":
        # material
        ob.data.materials.append(create_material(cmps[1]))
      elif cmps[0] == "quad" or cmps[0] == "tri":
        face = None
        num_indices = 4 if cmps[0] == "quad" else 3
        
        # create face
        if num_indices == 4:
          try:
            face = bm.faces.new((bm.verts[int(cmps[1])], bm.verts[int(cmps[2])], bm.verts[int(cmps[3])], bm.verts[int(cmps[4])]))
          except Exception as e:
            print(str(e))
        if num_indices == 3:
          try:
            face = bm.faces.new((bm.verts[int(cmps[1])], bm.verts[int(cmps[2])], bm.verts[int(cmps[3])]))
          except Exception as e:
            print(str(e))
        
        # set smooth/material
        if face is not None:
          face.material_index = int(cmps[num_indices+1])
          face.smooth = True
    
    # calculate normals
    bm.normal_update()
    
    # free resources
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    bm.to_mesh(me)
    bm.free()
      

######################################################
# IMPORT
######################################################
def load_bnd(filepath,
             context):

    print("importing BND: %r..." % (filepath))

    if bpy.ops.object.select_all.poll():
        bpy.ops.object.select_all(action='DESELECT')

    time1 = time.clock()
    file = open(filepath, 'r')

    # start reading our pkg file
    read_bnd_file(file)

    print(" done in %.4f sec." % (time.clock() - time1))
    file.close()


def load(operator,
         context,
         filepath="",
         ):

    load_bnd(filepath,
             context,
             )

    return {'FINISHED'}
