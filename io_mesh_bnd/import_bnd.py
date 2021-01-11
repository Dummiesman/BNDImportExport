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

import io_mesh_bnd.common_helpers as helper

######################################################
# IMPORT MAIN FILES
######################################################
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
        ob.data.materials.append(helper.create_material(cmps[1]))
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

    # start reading our bnd file
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
