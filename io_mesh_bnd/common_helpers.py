import bpy

def get_material_color(name):
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
  
  return material_colors[name] if name in material_colors else material_colors["default"]


def create_material(name):
  name_l = name.lower()
  
  # get color
  material_color = get_material_color(name_l)
    
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