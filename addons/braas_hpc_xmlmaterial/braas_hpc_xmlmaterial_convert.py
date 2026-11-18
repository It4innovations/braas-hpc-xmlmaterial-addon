#####################################################################################################################
# Copyright(C) 2011-2025 IT4Innovations National Supercomputing Center, VSB - Technical University of Ostrava
#
# This program is free software : you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#####################################################################################################################
"""
Export of Blender shader node trees to the CyclesPhi XML shader format.

The conversion follows intern/cycles/blender/shader.cpp (add_node, add_nodes, set_default_value,
node_find_input_by_name, node_find_output_by_name, sync_materials, sync_world, sync_lights).

The output is read by CyclesPhi (src/app/cycles_xml_bin.cpp, src/graph/node_xml_bin.cpp):

    <shader name="Material">
      <socket name="volume_step_rate" ui_name="Volume Step Rate" value="1"/>
      <principled_bsdf name="Principled BSDF">
        <socket name="base_color" ui_name="Base Color" value="0.8 0.8 0.8 0"/>
      </principled_bsdf>
      <connect from_node="Principled BSDF" from_socket="BSDF" from_socket_ui="BSDF"
               to_node="output" to_socket="surface" to_socket_ui="Surface"/>
    </shader>

Sockets are written with both the Cycles socket name and UI name. The reader requires both to
match, which keeps sockets with the same UI name apart (e.g. texture mapping "Scale" and the
"Scale" input of a noise texture).
"""

import bpy
import math
import struct
import xml.etree.ElementTree as ET
from collections import defaultdict

from . import braas_hpc_xmlmaterial_map as node_map
from .braas_hpc_xmlmaterial_sockets import CYCLES_NODES

try:
    import numpy as np
except ImportError:  # pragma: no cover
    np = None

RAMP_TABLE_SIZE = 256
FLT_MAX = 3.4028234663852886e38

# Name of the graph output node, the XML reader maps it to ShaderGraph::output().
OUTPUT_NODE_NAME = "output"
# Shader name the XML reader assigns to Scene::default_background.
WORLD_SHADER_NAME = "default_background"


def report(message):
    print(f"BRaaS-HPC-XMLMaterial: {message}")

#########################################################################################
# Cycles node types


class CyclesSocket:
    __slots__ = ("name", "ui_name", "type", "linkable")

    def __init__(self, name, ui_name, socket_type, linkable=True):
        self.name = name
        self.ui_name = ui_name
        self.type = socket_type
        self.linkable = linkable


class CyclesNodeType:
    def __init__(self, xml_type, class_name, inputs, outputs):
        self.xml_type = xml_type
        self.class_name = class_name
        # All node sockets by name (linkable inputs and parameters).
        self.params = {}
        for s in inputs:
            self.params.setdefault(s.name, s)
        # ShaderNode::inputs only contains the linkable sockets.
        self.inputs = [s for s in inputs if s.linkable]
        self.outputs = outputs

    # ShaderNode::input() / ShaderNode::output() compare against the UI name.
    def input(self, ui_name):
        for s in self.inputs:
            if s.ui_name == ui_name:
                return s
        return None

    def output(self, ui_name):
        for s in self.outputs:
            if s.ui_name == ui_name:
                return s
        return None


_node_types = {}


def cycles_node_type(xml_type):
    node_type = _node_types.get(xml_type)
    if node_type is None:
        entry = CYCLES_NODES.get(xml_type)
        if entry is None:
            return None
        class_name, inputs, outputs = entry
        node_type = CyclesNodeType(xml_type,
                                   class_name,
                                   [CyclesSocket(*s) for s in inputs],
                                   [CyclesSocket(*s) for s in outputs])
        _node_types[xml_type] = node_type
    return node_type


def proxy_node_type(socket_type):
    """ConvertNode with the same input and output type, used as a proxy (SHADER_SPECIAL_TYPE_PROXY)."""
    xml_type = f"convert_{socket_type}_to_{socket_type}"
    node_type = _node_types.get(xml_type)
    if node_type is None:
        value = f"value_{socket_type}"
        node_type = CyclesNodeType(xml_type,
                                   "ConvertNode",
                                   [CyclesSocket(value, value, socket_type)],
                                   [CyclesSocket(value, value, socket_type)])
        _node_types[xml_type] = node_type
    return node_type


def convert_socket_type(b_socket):
    """convert_socket_type() in shader.cpp"""
    return {
        'VALUE': "float",
        'BOOLEAN': "int",
        'INT': "int",
        'VECTOR': "vector",
        'RGBA': "color",
        'STRING': "string",
        'SHADER': "closure",
    }.get(b_socket.type)

#########################################################################################
# Value formatting


def fmt_float(value):
    value = float(value)
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    if math.isnan(value):
        return "nan"
    if np is not None:
        # Shortest representation of the float32 value Cycles will use.
        return str(np.float32(value))
    return f"{value:.9g}"


def is_scalar(value):
    return isinstance(value, (bool, int, float))


def as_floats(value, size):
    if is_scalar(value):
        values = [float(value)] * size
    else:
        values = [float(v) for v in value][:size]
        values += [0.0] * (size - len(values))
    return values


def transform_rows(matrix):
    """get_transform() in blender/util.h: first three rows of the 4x4 matrix, row major."""
    return [float(matrix[row][col]) for row in range(3) for col in range(4)]


class XMLWriter:
    """Collects the Cycles nodes and connections of one exported shader graph.

    binary: optional bytearray. When set, array sockets are appended to it in the layout of
    read_array_from_binary_file() (node_xml_bin.cpp) and the socket value is the byte offset.
    The XML reader then has to be given the binary file, in which case every array socket of the
    scene has to be stored in it.
    """

    def __init__(self, binary=None):
        self.binary = binary
        self.nodes = []
        self.connections = []
        self.names = {OUTPUT_NODE_NAME}
        self.output = None

    def unique_name(self, name):
        if name not in self.names:
            self.names.add(name)
            return name
        index = 1
        while f"{name}.{index:03d}" in self.names:
            index += 1
        name = f"{name}.{index:03d}"
        self.names.add(name)
        return name

    def add_node(self, xml_type, name):
        node_type = cycles_node_type(xml_type)
        if node_type is None:
            report(f'Cycles node type "{xml_type}" is not known to CyclesPhi, node "{name}" skipped.')
            return None
        node = XMLNode(self, node_type, self.unique_name(name))
        self.nodes.append(node)
        return node

    def add_proxy(self, socket_type, name):
        node = XMLNode(self, proxy_node_type(socket_type), self.unique_name(name))
        self.nodes.append(node)
        return node

    def output_node(self):
        # The output node exists in every ShaderGraph and the reader maps the name "output" to it.
        # It is not written as an element: CyclesPhi builds before 2026-10 (389cac3dd) create a
        # second, unconnected output node for it. Its only value input, Displacement, has the same
        # default (zero) in Blender and Cycles.
        if self.output is None:
            self.output = XMLNode(self, cycles_node_type("output"), OUTPUT_NODE_NAME)
        return self.output

    def connect(self, from_socket, to_socket):
        """from_socket, to_socket: (XMLNode, CyclesSocket)"""
        self.connections.append((from_socket, to_socket))

    def array(self, fmt, values, count, text):
        if self.binary is None:
            return " ".join(text(v) for v in values)
        offset = len(self.binary)
        self.binary += struct.pack("<Q", count)
        self.binary += struct.pack(f"<{len(values)}{fmt}", *values)
        return str(offset)

    def format_value(self, socket_type, value):
        t = socket_type
        if t == "boolean":
            return "true" if value else "false"
        if t in ("int", "uint", "uint64"):
            return str(int(value))
        if t == "enum":
            return value if isinstance(value, str) else str(int(value))
        if t == "float":
            return fmt_float(value)
        if t in ("color", "vector", "point", "normal"):
            # float3 is read as 4 components (node_xml_bin.cpp, xml_read_float_array<4>).
            return " ".join(fmt_float(v) for v in as_floats(value, 3) + [0.0])
        if t == "point2":
            return " ".join(fmt_float(v) for v in as_floats(value, 2))
        if t == "string":
            return str(value)
        if t == "transform":
            return " ".join(fmt_float(v) for v in value)
        if t == "float_array":
            values = [float(v) for v in value]
            return self.array("f", values, len(values), fmt_float)
        if t == "int_array":
            values = [int(v) for v in value]
            return self.array("i", values, len(values), str)
        if t == "boolean_array":
            values = [bool(v) for v in value]
            return self.array("?", values, len(values), lambda v: "true" if v else "false")
        if t in ("color_array", "vector_array", "point_array", "normal_array"):
            # Stored as 16 byte float3.
            values = []
            for v in value:
                values += as_floats(v, 3) + [0.0]
            return self.array("f", values, len(values) // 4, fmt_float)
        if t == "point2_array":
            values = []
            for v in value:
                values += as_floats(v, 2)
            return self.array("f", values, len(values) // 2, fmt_float)
        if t == "string_array":
            return " ".join(str(v) for v in value)
        return None


class XMLNode:
    def __init__(self, writer, node_type, name):
        self.writer = writer
        self.type = node_type
        self.name = name
        self.sockets = {}

    def set(self, name, value):
        """Set a node socket (parameter or input) by its Cycles socket name."""
        socket = self.type.params.get(name)
        if socket is None:
            report(f'Cycles node "{self.type.xml_type}" has no socket "{name}" (node "{self.name}").')
            return
        self.set_socket(socket, value)

    def set_socket(self, socket, value):
        text = self.writer.format_value(socket.type, value)
        if text is None:
            report(f'Socket type "{socket.type}" of "{self.name}.{socket.name}" is not supported.')
            return
        self.sockets[socket.name] = (socket.ui_name, text)

    def write_sockets(self, xml_element):
        for name, (ui_name, value) in self.sockets.items():
            ET.SubElement(xml_element, "socket", name=name, ui_name=ui_name, value=value)

    def to_xml(self, xml_root):
        xml_node = ET.SubElement(xml_root, self.type.xml_type, name=self.name)
        self.write_sockets(xml_node)
        return xml_node

#########################################################################################
# Blender helpers


def enum_value(rna, prop):
    """Integer value of an RNA enum property (what get_enum() / DNA storage give in C++)."""
    return rna.bl_rna.properties[prop].enum_items[getattr(rna, prop)].value


def validate_enum_value(value, num_values, default_value):
    return default_value if value >= num_values else value


def socket_by_identifier(sockets, identifier):
    for socket in sockets:
        if socket.identifier == identifier:
            return socket
    return None


def socket_is_available(b_socket):
    return getattr(b_socket, "enabled", True)


def blender_absolute_path(b_id, path):
    return bpy.path.abspath(path, library=getattr(b_id, "library", None)) if path else path


OBJECT_ATTR_PREFIX = "\x01object:"
INSTANCER_ATTR_PREFIX = "\x01instancer:"
VIEW_LAYER_ATTR_PREFIX = "\x01layer:"


def blender_attribute_name_add_type(name, attr_type):
    if attr_type == 'OBJECT':
        return OBJECT_ATTR_PREFIX + name
    if attr_type == 'INSTANCER':
        return INSTANCER_ATTR_PREFIX + name
    if attr_type == 'VIEW_LAYER':
        return VIEW_LAYER_ATTR_PREFIX + name
    return name


def curvemapping_minmax(cumap, num_curves):
    min_x = FLT_MAX
    max_x = -FLT_MAX
    for i in range(num_curves):
        points = cumap.curves[i].points
        min_x = min(min_x, points[0].location[0])
        max_x = max(max_x, points[len(points) - 1].location[0])
    return min_x, max_x


def curvemapping_prepare(cumap):
    # BKE_curvemapping_changed_all() + BKE_curvemapping_init()
    cumap.update()
    cumap.initialize()


def curvemapping_float_to_array(cumap, size):
    min_x, max_x = curvemapping_minmax(cumap, 1)
    range_x = max_x - min_x
    curvemapping_prepare(cumap)
    curve = cumap.curves[0]
    return [cumap.evaluate(curve, min_x + float(i) / float(size) * range_x) for i in range(size + 1)]


def curvemapping_color_to_array(cumap, size, rgb_curve):
    min_x, max_x = curvemapping_minmax(cumap, 4 if rgb_curve else 3)
    range_x = max_x - min_x
    curvemapping_prepare(cumap)

    map_r, map_g, map_b = cumap.curves[0], cumap.curves[1], cumap.curves[2]
    data = []
    for i in range(size + 1):
        t = min_x + float(i) / float(size) * range_x
        if rgb_curve:
            map_i = cumap.curves[3]
            data.append((cumap.evaluate(map_r, cumap.evaluate(map_i, t)),
                         cumap.evaluate(map_g, cumap.evaluate(map_i, t)),
                         cumap.evaluate(map_b, cumap.evaluate(map_i, t))))
        else:
            data.append((cumap.evaluate(map_r, t), cumap.evaluate(map_g, t), cumap.evaluate(map_b, t)))
    return data


def colorramp_to_array(ramp, size):
    ramp_color = []
    ramp_alpha = []
    for i in range(size + 1):
        color = ramp.evaluate(float(i) / float(size))
        ramp_color.append((color[0], color[1], color[2]))
        ramp_alpha.append(color[3])
    return ramp_color, ramp_alpha


def get_tex_mapping(xn, b_mapping):
    if b_mapping is None:
        return
    xn.set("tex_mapping.translation", b_mapping.translation)
    xn.set("tex_mapping.rotation", b_mapping.rotation)
    xn.set("tex_mapping.scale", b_mapping.scale)
    xn.set("tex_mapping.type", enum_value(b_mapping, "vector_type"))
    xn.set("tex_mapping.x_mapping", enum_value(b_mapping, "mapping_x"))
    xn.set("tex_mapping.y_mapping", enum_value(b_mapping, "mapping_y"))
    xn.set("tex_mapping.z_mapping", enum_value(b_mapping, "mapping_z"))


def is_image_animated(b_image, b_image_user):
    return b_image.source in {'MOVIE', 'SEQUENCE'} and b_image_user.use_auto_refresh


def image_is_builtin(b_image):
    if b_image.source == 'TILED':
        for tile in b_image.tiles:
            if getattr(tile, "is_generated", False):
                return True
    return (b_image.packed_file is not None or b_image.source in {'GENERATED', 'MOVIE'} or
            b_image.is_dirty)


def image_user_file_path(b_image, b_image_user):
    filepath = b_image.filepath_from_user(image_user=b_image_user)
    return blender_absolute_path(b_image, filepath)


def set_image(xn, b_node, b_image, b_image_user, use_tiles):
    xn.set("colorspace", b_image.colorspace_settings.name)
    xn.set("animated", is_image_animated(b_image, b_image_user))
    # IMAGE_ALPHA_NUM_TYPES = 5, IMAGE_ALPHA_AUTO = 4
    xn.set("alpha_type", validate_enum_value(enum_value(b_image, "alpha_mode"), 5, 4))

    if use_tiles and b_image.source == 'TILED':
        xn.set("tiles", [tile.number for tile in b_image.tiles])

    if image_is_builtin(b_image):
        # Blender reads these from memory (BlenderImageLoader), the XML reader can only load files.
        report(f'Image "{b_image.name}" of node "{b_node.name}" is packed, generated, a movie or '
               f'modified; exporting its file path, which may not contain the current pixels.')

    xn.set("filename", image_user_file_path(b_image, b_image_user))

#########################################################################################
# Nodes, add_node() in shader.cpp

# Distribution / closure enums are written by their Cycles enum names (see shader_nodes.cpp).
GLOSSY_DISTRIBUTION = {'BECKMANN': "beckmann", 'GGX': "ggx",
                       'ASHIKHMIN_SHIRLEY': "ashikhmin_shirley", 'MULTI_GGX': "multi_ggx"}
METALLIC_DISTRIBUTION = {'BECKMANN': "beckmann", 'GGX': "ggx", 'MULTI_GGX': "multi_ggx"}
METALLIC_FRESNEL = {'PHYSICAL_CONDUCTOR': "physical_conductor", 'F82': "f82"}
GLASS_DISTRIBUTION = {'BECKMANN': "beckmann", 'GGX': "ggx", 'MULTI_GGX': "multi_ggx"}
REFRACTION_DISTRIBUTION = {'BECKMANN': "beckmann", 'GGX': "ggx"}
PRINCIPLED_DISTRIBUTION = {'GGX': "ggx", 'MULTI_GGX': "multi_ggx"}
SUBSURFACE_METHOD = {'BURLEY': "burley", 'RANDOM_WALK': "random_walk",
                     'RANDOM_WALK_SKIN': "random_walk_skin", 'RANDOM_WALK_LEGACY': "random_walk_legacy"}
TOON_COMPONENT = {'DIFFUSE': "diffuse", 'GLOSSY': "glossy"}
HAIR_COMPONENT = {'Reflection': "reflection", 'Transmission': "transmission"}
SHEEN_DISTRIBUTION = {'ASHIKHMIN': "ashikhmin", 'MICROFIBER': "microfiber"}
VOLUME_PHASE = {'HENYEY_GREENSTEIN': "Henyey-Greenstein", 'FOURNIER_FORAND': "Fournier-Forand",
                'DRAINE': "Draine", 'RAYLEIGH': "Rayleigh", 'MIE': "Mie"}


def set_mapped(xn, name, table, value):
    """Like the switch statements in add_node(): unknown values keep the Cycles default."""
    if value in table:
        xn.set(name, table[value])


def h_rgb_curve(tree, n, xn):
    xn.set("curves", curvemapping_color_to_array(n.mapping, RAMP_TABLE_SIZE, True))
    min_x, max_x = curvemapping_minmax(n.mapping, 4)
    xn.set("min_x", min_x)
    xn.set("max_x", max_x)
    xn.set("extrapolate", n.mapping.extend == 'EXTRAPOLATED')


def h_vector_curve(tree, n, xn):
    xn.set("curves", curvemapping_color_to_array(n.mapping, RAMP_TABLE_SIZE, False))
    min_x, max_x = curvemapping_minmax(n.mapping, 3)
    xn.set("min_x", min_x)
    xn.set("max_x", max_x)
    xn.set("extrapolate", n.mapping.extend == 'EXTRAPOLATED')


def h_float_curve(tree, n, xn):
    xn.set("curve", curvemapping_float_to_array(n.mapping, RAMP_TABLE_SIZE))
    min_x, max_x = curvemapping_minmax(n.mapping, 1)
    xn.set("min_x", min_x)
    xn.set("max_x", max_x)
    xn.set("extrapolate", n.mapping.extend == 'EXTRAPOLATED')


def h_color_ramp(tree, n, xn):
    ramp_values, ramp_alpha = colorramp_to_array(n.color_ramp, RAMP_TABLE_SIZE)
    xn.set("ramp", ramp_values)
    xn.set("ramp_alpha", ramp_alpha)
    xn.set("interpolate", n.color_ramp.interpolation != 'CONSTANT')


def h_rgb(tree, n, xn):
    xn.set("value", socket_by_identifier(n.outputs, "Color").default_value)


def h_input_vector(tree, n, xn):
    xn.set("value", n.vector)


def h_value(tree, n, xn):
    xn.set("value", socket_by_identifier(n.outputs, "Value").default_value)


def h_input_bool(tree, n, xn):
    xn.set("value", 1.0 if n.boolean else 0.0)


def h_input_int(tree, n, xn):
    xn.set("value", float(n.integer))


def h_mix_rgb(tree, n, xn):
    xn.set("mix_type", enum_value(n, "blend_type"))
    xn.set("use_clamp", n.use_clamp)


def h_mix(tree, n, xn):
    if xn.type.class_name == "MixColorNode":
        xn.set("blend_type", enum_value(n, "blend_type"))
        xn.set("use_clamp", n.clamp_factor)
        xn.set("use_clamp_result", n.clamp_result)
    else:
        xn.set("use_clamp", n.clamp_factor)


def h_color_type(tree, n, xn):
    xn.set("color_type", enum_value(n, "mode"))


def h_map_range(tree, n, xn):
    if xn.type.class_name == "VectorMapRangeNode":
        xn.set("use_clamp", n.clamp)
    else:
        xn.set("clamp", n.clamp)
    xn.set("range_type", enum_value(n, "interpolation_type"))


def h_clamp(tree, n, xn):
    xn.set("clamp_type", enum_value(n, "clamp_type"))


def h_math(tree, n, xn):
    xn.set("math_type", enum_value(n, "operation"))
    xn.set("use_clamp", n.use_clamp)


def h_math_type(tree, n, xn):
    xn.set("math_type", enum_value(n, "operation"))


def h_vector_rotate(tree, n, xn):
    xn.set("rotate_type", enum_value(n, "rotation_type"))
    xn.set("invert", n.invert)


def h_vector_transform(tree, n, xn):
    xn.set("transform_type", enum_value(n, "vector_type"))
    xn.set("convert_from", enum_value(n, "convert_from"))
    xn.set("convert_to", enum_value(n, "convert_to"))


def h_normal(tree, n, xn):
    xn.set("direction", socket_by_identifier(n.outputs, "Normal").default_value)


def h_mapping(tree, n, xn):
    xn.set("mapping_type", enum_value(n, "vector_type"))


def h_attribute(tree, n, xn):
    xn.set("attribute", blender_attribute_name_add_type(n.attribute_name, n.attribute_type))


def h_subsurface(tree, n, xn):
    set_mapped(xn, "method", SUBSURFACE_METHOD, n.falloff)


def h_metallic(tree, n, xn):
    set_mapped(xn, "distribution", METALLIC_DISTRIBUTION, n.distribution)
    set_mapped(xn, "fresnel_type", METALLIC_FRESNEL, n.fresnel_type)


def h_glossy(tree, n, xn):
    set_mapped(xn, "distribution", GLOSSY_DISTRIBUTION, n.distribution)


def h_glass(tree, n, xn):
    set_mapped(xn, "distribution", GLASS_DISTRIBUTION, n.distribution)


def h_refraction(tree, n, xn):
    set_mapped(xn, "distribution", REFRACTION_DISTRIBUTION, n.distribution)


def h_toon(tree, n, xn):
    set_mapped(xn, "component", TOON_COMPONENT, n.component)


def h_hair(tree, n, xn):
    set_mapped(xn, "component", HAIR_COMPONENT, n.component)


def h_principled_hair(tree, n, xn):
    # NODE_PRINCIPLED_HAIR_MODEL_NUM = 2, NODE_PRINCIPLED_HAIR_HUANG = 1
    xn.set("model", validate_enum_value(enum_value(n, "model"), 2, 1))
    # NODE_PRINCIPLED_HAIR_PARAMETRIZATION_NUM = 3, NODE_PRINCIPLED_HAIR_REFLECTANCE = 0
    xn.set("parametrization", validate_enum_value(enum_value(n, "parametrization"), 3, 0))


def h_principled(tree, n, xn):
    set_mapped(xn, "distribution", PRINCIPLED_DISTRIBUTION, n.distribution)
    set_mapped(xn, "subsurface_method", SUBSURFACE_METHOD, n.subsurface_method)


def h_sheen(tree, n, xn):
    set_mapped(xn, "distribution", SHEEN_DISTRIBUTION, n.distribution)


def h_ambient_occlusion(tree, n, xn):
    xn.set("samples", n.samples)
    xn.set("inside", n.inside)
    xn.set("only_local", n.only_local)


def h_volume_phase(tree, n, xn):
    set_mapped(xn, "phase", VOLUME_PHASE, n.phase)


def h_wireframe(tree, n, xn):
    xn.set("use_pixel_size", n.use_pixel_size)


def h_vertex_color(tree, n, xn):
    xn.set("layer_name", n.layer_name)


def h_bump(tree, n, xn):
    xn.set("invert", n.invert)


def h_image(tree, n, xn):
    # INTERPOLATION_NUM_TYPES = 4, EXTENSION_NUM_TYPES = 4, linear / repeat by default.
    xn.set("interpolation", validate_enum_value(enum_value(n, "interpolation"), 4, 0))
    xn.set("extension", validate_enum_value(enum_value(n, "extension"), 4, 0))
    xn.set("projection", enum_value(n, "projection"))
    xn.set("projection_blend", n.projection_blend)
    get_tex_mapping(xn, n.texture_mapping)
    if n.image:
        set_image(xn, n, n.image, n.image_user, use_tiles=True)


def h_environment(tree, n, xn):
    xn.set("interpolation", validate_enum_value(enum_value(n, "interpolation"), 4, 0))
    xn.set("projection", enum_value(n, "projection"))
    get_tex_mapping(xn, n.texture_mapping)
    if n.image:
        set_image(xn, n, n.image, n.image_user, use_tiles=False)


def h_gradient(tree, n, xn):
    xn.set("gradient_type", enum_value(n, "gradient_type"))
    get_tex_mapping(xn, n.texture_mapping)


def h_voronoi(tree, n, xn):
    xn.set("dimensions", enum_value(n, "voronoi_dimensions"))
    xn.set("feature", enum_value(n, "feature"))
    xn.set("metric", enum_value(n, "distance"))
    xn.set("use_normalize", n.normalize)
    get_tex_mapping(xn, n.texture_mapping)


def h_magic(tree, n, xn):
    xn.set("depth", n.turbulence_depth)
    get_tex_mapping(xn, n.texture_mapping)


def h_wave(tree, n, xn):
    xn.set("wave_type", enum_value(n, "wave_type"))
    xn.set("bands_direction", enum_value(n, "bands_direction"))
    xn.set("rings_direction", enum_value(n, "rings_direction"))
    xn.set("profile", enum_value(n, "wave_profile"))
    get_tex_mapping(xn, n.texture_mapping)


def h_checker(tree, n, xn):
    get_tex_mapping(xn, n.texture_mapping)


def h_brick(tree, n, xn):
    xn.set("offset", n.offset)
    xn.set("offset_frequency", n.offset_frequency)
    xn.set("squash", n.squash)
    xn.set("squash_frequency", n.squash_frequency)
    get_tex_mapping(xn, n.texture_mapping)


def h_noise(tree, n, xn):
    xn.set("dimensions", enum_value(n, "noise_dimensions"))
    xn.set("type", enum_value(n, "noise_type"))
    xn.set("use_normalize", n.normalize)
    get_tex_mapping(xn, n.texture_mapping)


def h_gabor(tree, n, xn):
    xn.set("type", enum_value(n, "gabor_type"))
    get_tex_mapping(xn, n.texture_mapping)


def h_tex_coord(tree, n, xn):
    xn.set("from_dupli", n.from_instancer)
    if n.object:
        xn.set("use_transform", True)
        xn.set("ob_tfm", transform_rows(n.object.matrix_world))


def h_sky(tree, n, xn):
    xn.set("sky_type", enum_value(n, "sky_type"))
    direction = [float(v) for v in n.sun_direction]
    length = math.sqrt(sum(v * v for v in direction))
    if length > 0.0:
        direction = [v / length for v in direction]
    xn.set("sun_direction", direction)
    xn.set("turbidity", n.turbidity)
    xn.set("ground_albedo", n.ground_albedo)
    xn.set("sun_disc", n.sun_disc)
    xn.set("sun_size", n.sun_size)
    xn.set("sun_intensity", n.sun_intensity)
    xn.set("sun_elevation", n.sun_elevation)
    xn.set("sun_rotation", n.sun_rotation)
    xn.set("altitude", n.altitude)
    xn.set("air_density", n.air_density)
    xn.set("aerosol_density", n.aerosol_density)
    xn.set("ozone_density", n.ozone_density)
    get_tex_mapping(xn, n.texture_mapping)


def h_ies(tree, n, xn):
    if n.mode == 'EXTERNAL':
        xn.set("filename", blender_absolute_path(tree, n.filepath))
    elif n.mode == 'INTERNAL':
        xn.set("ies", n.ies.as_string() if n.ies else "")


def h_white_noise(tree, n, xn):
    xn.set("dimensions", enum_value(n, "noise_dimensions"))


def h_normal_map(tree, n, xn):
    xn.set("space", enum_value(n, "space"))
    xn.set("attribute", n.uv_map)
    xn.set("convention", enum_value(n, "convention"))
    xn.set("base", enum_value(n, "base"))


def h_radial_tiling(tree, n, xn):
    xn.set("use_normalize", n.normalize)


def h_tangent(tree, n, xn):
    xn.set("direction_type", enum_value(n, "direction_type"))
    xn.set("axis", enum_value(n, "axis"))
    xn.set("attribute", n.uv_map)


def h_uvmap(tree, n, xn):
    xn.set("attribute", n.uv_map)
    xn.set("from_dupli", n.from_instancer)


def h_bevel(tree, n, xn):
    xn.set("samples", n.samples)


def h_displacement(tree, n, xn):
    xn.set("space", enum_value(n, "space"))


def h_vector_displacement(tree, n, xn):
    xn.set("space", enum_value(n, "space"))
    xn.set("attribute", "")


def h_aov(tree, n, xn):
    xn.set("name", n.aov_name)


def h_raycast(tree, n, xn):
    xn.set("only_local", n.only_local)


NODE_HANDLERS = {
    "ShaderNodeRGBCurve": h_rgb_curve,
    "ShaderNodeVectorCurve": h_vector_curve,
    "ShaderNodeFloatCurve": h_float_curve,
    "ShaderNodeValToRGB": h_color_ramp,
    "ShaderNodeRGB": h_rgb,
    "FunctionNodeInputVector": h_input_vector,
    "ShaderNodeValue": h_value,
    "FunctionNodeInputBool": h_input_bool,
    "FunctionNodeInputInt": h_input_int,
    "ShaderNodeMixRGB": h_mix_rgb,
    "ShaderNodeMix": h_mix,
    "ShaderNodeSeparateColor": h_color_type,
    "ShaderNodeCombineColor": h_color_type,
    "ShaderNodeMapRange": h_map_range,
    "ShaderNodeClamp": h_clamp,
    "ShaderNodeMath": h_math,
    "FunctionNodeBooleanMath": h_math_type,
    "FunctionNodeIntegerMath": h_math_type,
    "ShaderNodeVectorMath": h_math_type,
    "ShaderNodeVectorRotate": h_vector_rotate,
    "ShaderNodeVectorTransform": h_vector_transform,
    "ShaderNodeNormal": h_normal,
    "ShaderNodeMapping": h_mapping,
    "ShaderNodeAttribute": h_attribute,
    "ShaderNodeSubsurfaceScattering": h_subsurface,
    "ShaderNodeBsdfMetallic": h_metallic,
    "ShaderNodeBsdfAnisotropic": h_glossy,
    "ShaderNodeBsdfGlass": h_glass,
    "ShaderNodeBsdfRefraction": h_refraction,
    "ShaderNodeBsdfToon": h_toon,
    "ShaderNodeBsdfHair": h_hair,
    "ShaderNodeBsdfHairPrincipled": h_principled_hair,
    "ShaderNodeBsdfPrincipled": h_principled,
    "ShaderNodeBsdfSheen": h_sheen,
    "ShaderNodeAmbientOcclusion": h_ambient_occlusion,
    "ShaderNodeVolumeScatter": h_volume_phase,
    "ShaderNodeVolumeCoefficients": h_volume_phase,
    "ShaderNodeWireframe": h_wireframe,
    "ShaderNodeVertexColor": h_vertex_color,
    "ShaderNodeBump": h_bump,
    "ShaderNodeTexImage": h_image,
    "ShaderNodeTexEnvironment": h_environment,
    "ShaderNodeTexGradient": h_gradient,
    "ShaderNodeTexVoronoi": h_voronoi,
    "ShaderNodeTexMagic": h_magic,
    "ShaderNodeTexWave": h_wave,
    "ShaderNodeTexChecker": h_checker,
    "ShaderNodeTexBrick": h_brick,
    "ShaderNodeTexNoise": h_noise,
    "ShaderNodeTexGabor": h_gabor,
    "ShaderNodeTexCoord": h_tex_coord,
    "ShaderNodeTexSky": h_sky,
    "ShaderNodeTexIES": h_ies,
    "ShaderNodeTexWhiteNoise": h_white_noise,
    "ShaderNodeNormalMap": h_normal_map,
    "ShaderNodeRadialTiling": h_radial_tiling,
    "ShaderNodeTangent": h_tangent,
    "ShaderNodeUVMap": h_uvmap,
    "ShaderNodeBevel": h_bevel,
    "ShaderNodeDisplacement": h_displacement,
    "ShaderNodeVectorDisplacement": h_vector_displacement,
    "ShaderNodeOutputAOV": h_aov,
    "ShaderNodeRaycast": h_raycast,
}


def mix_class(n):
    if n.data_type == 'VECTOR':
        return "MixVectorNode" if n.factor_mode == 'UNIFORM' else "MixVectorNonUniformNode"
    if n.data_type == 'RGBA':
        return "MixColorNode"
    return "MixFloatNode"


def map_range_class(n):
    return "VectorMapRangeNode" if n.data_type == 'FLOAT_VECTOR' else "MapRangeNode"


DYNAMIC_CLASS = {
    "ShaderNodeMix": mix_class,
    "ShaderNodeMapRange": map_range_class,
}


def add_node(writer, b_ntree, b_node, prefix):
    """add_node() in shader.cpp, returns the XMLNode or None for unsupported nodes."""
    idname = b_node.bl_idname

    if idname in node_map.IGNORED_NODE_IDNAMES or idname in node_map.OUTPUT_NODE_IDNAMES:
        return None

    if idname == "ShaderNodeScript":
        report(f'Script node "{b_node.name}" skipped, the CyclesPhi XML reader has no OSL support.')
        return None

    if idname in DYNAMIC_CLASS:
        class_name = DYNAMIC_CLASS[idname](b_node)
    else:
        class_name = node_map.BLENDER_TO_CYCLES_CLASS.get(idname)

    if class_name is None:
        report(f'Node "{b_node.name}" ({idname}) is not supported by Cycles, skipped.')
        return None

    xml_type = node_map.class_to_xml_type(class_name)
    if xml_type is None:
        report(f'Node "{b_node.name}" ({idname}): {class_name} is not available in CyclesPhi, skipped.')
        return None

    xn = writer.add_node(xml_type, prefix + b_node.name)
    if xn is None:
        return None

    handler = NODE_HANDLERS.get(idname)
    if handler:
        handler(b_ntree, b_node, xn)

    if idname == "ShaderNodeRaycast" and len(b_node.outputs) > len(xn.type.outputs):
        report(f'Raycast node "{b_node.name}": sampled attribute outputs are not supported in XML.')

    return xn

#########################################################################################
# Sockets


def node_find_input_by_name(b_node, xn, b_socket):
    """node_find_input_by_name() in shader.cpp"""
    name = b_socket.identifier
    node_type = xn.type
    socket = node_type.input(name)

    if socket is None and node_type.class_name != "ConvertNode":
        # Different internal name for shader.
        if name.startswith("Shader"):
            name = name.replace("Shader", "Closure")

        # Map mix node internal name for shader.
        if b_node.bl_idname == "ShaderNodeMix":
            for suffix, replacement in (("Factor_Float", "Factor"), ("Factor_Vector", "Factor"),
                                        ("A_Float", "A"), ("B_Float", "B"),
                                        ("A_Color", "A"), ("B_Color", "B"),
                                        ("A_Vector", "A"), ("B_Vector", "B")):
                if name.endswith(suffix):
                    name = name.replace(suffix, replacement)
                    break

        socket = node_type.input(name)

        if socket is None:
            # Different internal numbering of two sockets with same name.
            if name.endswith("_001"):
                name = name.replace("_001", "2")
            elif name.endswith(".001"):
                name = name.replace(".001", "2")
            elif name.endswith("_002"):
                name = name.replace("_002", "3")
            elif name.endswith(".002"):
                name = name.replace(".002", "3")
            else:
                name += "1"
            socket = node_type.input(name)

    return socket


def node_find_output_by_name(b_node, xn, b_socket):
    """node_find_output_by_name() in shader.cpp"""
    name = b_socket.identifier
    node_type = xn.type
    socket = node_type.output(name)

    if socket is None and node_type.class_name != "ConvertNode":
        if name == "Shader":
            name = "Closure"
            socket = node_type.output(name)
        if b_node.bl_idname == "ShaderNodeMix":
            for suffix in ("Result_Float", "Result_Color", "Result_Vector"):
                if name.endswith(suffix):
                    name = name.replace(suffix, "Result")
                    socket = node_type.output(name)
                    break
        elif b_node.bl_idname == "FunctionNodeInputVector":
            # ColorNode has an output called "Color".
            if name == "Vector":
                name = "Color"
                socket = node_type.output(name)

    return socket


def set_default_value(xn, socket, b_socket, b_ntree):
    """set_default_value() in shader.cpp: copy values of the Blender socket to the Cycles input."""
    if not hasattr(b_socket, "default_value"):
        return
    value = b_socket.default_value

    if socket.type == "float":
        xn.set_socket(socket, float(value if is_scalar(value) else value[0]))
    elif socket.type == "int":
        xn.set_socket(socket, int(value if is_scalar(value) else value[0]))
    elif socket.type in ("color", "vector", "point", "normal"):
        xn.set_socket(socket, value)
    elif socket.type == "string":
        xn.set_socket(socket, blender_absolute_path(b_ntree, value))


def map_node_sockets(writer, b_ntree, b_node, xn, input_map, output_map):
    """Map the Blender sockets of a node to its Cycles sockets and copy the default values."""
    for b_input in b_node.inputs:
        if not socket_is_available(b_input):
            continue
        socket = node_find_input_by_name(b_node, xn, b_input)
        if socket is None:
            if b_input.is_linked:
                report(f'Input "{b_input.identifier}" of node "{b_node.name}" has no Cycles socket, '
                       f'link skipped.')
            continue
        if input_map is not None:
            input_map[b_input.as_pointer()].append((xn, socket))
        set_default_value(xn, socket, b_input, b_ntree)

    for b_output in b_node.outputs:
        if not socket_is_available(b_output):
            continue
        socket = node_find_output_by_name(b_node, xn, b_output)
        if socket is None:
            if b_output.is_linked:
                report(f'Output "{b_output.identifier}" of node "{b_node.name}" has no Cycles socket, '
                       f'link skipped.')
            continue
        if output_map is not None:
            output_map[b_output.as_pointer()] = (xn, socket)

#########################################################################################
# Graph, add_nodes() in shader.cpp


def find_output_node(b_ntree):
    """ntreeShaderOutputNode(ntree, SHD_OUTPUT_CYCLES)"""
    output_node = None
    for node in b_ntree.nodes:
        if node.bl_idname not in node_map.OUTPUT_NODE_IDNAMES:
            continue
        target = getattr(node, "target", 'ALL')
        current_target = getattr(output_node, "target", 'ALL')
        if target == 'ALL':
            if output_node is None:
                output_node = node
            elif current_target == 'ALL':
                if node.is_active_output and not output_node.is_active_output:
                    output_node = node
        elif target == 'CYCLES':
            if output_node is None or current_target == 'ALL':
                output_node = node
            elif node.is_active_output and not output_node.is_active_output:
                output_node = node
    return output_node


def internal_links(b_node):
    links = [(link.from_socket, link.to_socket) for link in b_node.internal_links]
    if not links and b_node.bl_idname == "NodeReroute" and b_node.inputs and b_node.outputs:
        links = [(b_node.inputs[0], b_node.outputs[0])]
    return links


def add_nodes(writer, b_ntree, prefix="", proxy_input_map=None, proxy_output_map=None):
    """Add the nodes of a tree to the graph. Node groups are inlined recursively, connected
    through proxy nodes (ConvertNode with equal input and output type) like in shader.cpp."""
    proxy_input_map = proxy_input_map or {}
    proxy_output_map = proxy_output_map or {}
    is_top_level = not prefix

    input_map = defaultdict(list)  # Blender input socket -> [(XMLNode, CyclesSocket)]
    output_map = {}                # Blender output socket -> (XMLNode, CyclesSocket)

    # Only the output node of the top level tree is used.
    output_node = find_output_node(b_ntree) if is_top_level else None

    for b_node in b_ntree.nodes:
        idname = b_node.bl_idname

        if b_node.mute or idname == "NodeReroute":
            # Replace muted node with internal links.
            for b_from, b_to in internal_links(b_node):
                socket_type = convert_socket_type(b_to)
                if socket_type is None:
                    continue
                proxy = writer.add_proxy(socket_type, f"{prefix}{b_node.name}:{b_to.identifier}")
                input_map[b_from.as_pointer()].append((proxy, proxy.type.inputs[0]))
                output_map[b_to.as_pointer()] = (proxy, proxy.type.outputs[0])

        elif idname in ("ShaderNodeGroup", "NodeCustomGroup"):
            b_group_ntree = b_node.node_tree
            group_proxy_input_map = {}
            group_proxy_output_map = {}

            # Add a proxy node for each socket, even if the node group has no internal tree,
            # so that links have something to connect to.
            for b_input in b_node.inputs:
                socket_type = convert_socket_type(b_input)
                if socket_type is None:
                    continue
                proxy = writer.add_proxy(socket_type, f"{prefix}{b_node.name}:in:{b_input.identifier}")
                group_proxy_input_map[b_input.identifier] = proxy
                input_map[b_input.as_pointer()].append((proxy, proxy.type.inputs[0]))
                set_default_value(proxy, proxy.type.inputs[0], b_input, b_ntree)

            for b_output in b_node.outputs:
                socket_type = convert_socket_type(b_output)
                if socket_type is None:
                    continue
                proxy = writer.add_proxy(socket_type, f"{prefix}{b_node.name}:out:{b_output.identifier}")
                group_proxy_output_map[b_output.identifier] = proxy
                output_map[b_output.as_pointer()] = (proxy, proxy.type.outputs[0])

            if b_group_ntree:
                add_nodes(writer, b_group_ntree, f"{prefix}{b_node.name}/",
                          group_proxy_input_map, group_proxy_output_map)

        elif idname == "NodeGroupInput":
            for b_output in b_node.outputs:
                proxy = proxy_input_map.get(b_output.identifier)
                if proxy:
                    output_map[b_output.as_pointer()] = (proxy, proxy.type.outputs[0])

        elif idname == "NodeGroupOutput":
            # Only the active group output is used.
            if b_node.is_active_output:
                for b_input in b_node.inputs:
                    proxy = proxy_output_map.get(b_input.identifier)
                    if proxy:
                        input_map[b_input.as_pointer()].append((proxy, proxy.type.inputs[0]))
                        set_default_value(proxy, proxy.type.inputs[0], b_input, b_ntree)

        else:
            if output_node is not None and b_node == output_node:
                xn = writer.output_node()
            else:
                xn = add_node(writer, b_ntree, b_node, prefix)

            if xn is not None:
                map_node_sockets(writer, b_ntree, b_node, xn, input_map, output_map)

    # Connect nodes.
    for b_link in b_ntree.links:
        # Ignore invalid links to avoid unwanted cycles created in graph.
        # Also ignore links with unavailable sockets.
        if (not b_link.is_valid or b_link.is_muted or
                not socket_is_available(b_link.from_socket) or
                not socket_is_available(b_link.to_socket)):
            continue

        # Either socket may be missing when the node was not exported, typically
        # because the node type is not supported.
        output = output_map.get(b_link.from_socket.as_pointer())
        if output is None:
            continue
        for to_input in input_map.get(b_link.to_socket.as_pointer(), ()):
            writer.connect(output, to_input)

#########################################################################################
# Shader settings, sync_materials() / sync_world() / sync_lights() in shader.cpp


def add_default_graph(writer, shader):
    """Graph used by Cycles for data-blocks without a node tree."""
    output = writer.output_node()
    if isinstance(shader, bpy.types.World):
        node = writer.add_node("background_shader", "background")
        node.set("color", shader.color)
        writer.connect((node, node.type.output("Background")), (output, output.type.input("Surface")))
    elif isinstance(shader, bpy.types.Light):
        node = writer.add_node("emission", "emission")
        node.set("color", (1.0, 1.0, 1.0))
        node.set("strength", 1.0)
        writer.connect((node, node.type.output("Emission")), (output, output.type.input("Surface")))
    else:
        node = writer.add_node("diffuse_bsdf", "diffuse")
        if shader is not None and hasattr(shader, "diffuse_color"):
            node.set("color", shader.diffuse_color)
        writer.connect((node, node.type.output("BSDF")), (output, output.type.input("Surface")))


def shader_settings(writer, shader):
    """Settings of the Cycles Shader, written as <socket> children of <shader>."""
    settings = XMLNode(writer, cycles_node_type("shader"), "shader")

    if isinstance(shader, bpy.types.Material):
        settings.set("pass_id", shader.pass_index)
        settings.set("use_transparent_shadow", shader.use_transparent_shadow)
        # DISPLACE_NUM_METHODS = 3, DISPLACE_BUMP = 0
        settings.set("displacement_method",
                     validate_enum_value(enum_value(shader, "displacement_method"), 3, 0))

        # Settings of the Cycles add-on, missing when the add-on is disabled.
        cmat = getattr(shader, "cycles", None)
        if cmat is None:
            report(f'Cycles settings of material "{shader.name}" are not available, using defaults.')
            return settings
        # EMISSION_SAMPLING_NUM = 5, EMISSION_SAMPLING_AUTO = 1
        settings.set("emission_sampling_method",
                     validate_enum_value(enum_value(cmat, "emission_sampling"), 5, 1))
        if hasattr(cmat, "use_bump_map_correction"):
            settings.set("use_bump_map_correction", cmat.use_bump_map_correction)
        # VOLUME_NUM_SAMPLING = 3, VOLUME_SAMPLING_DISTANCE = 0
        settings.set("volume_sampling_method",
                     validate_enum_value(enum_value(cmat, "volume_sampling"), 3, 0))
        # VOLUME_NUM_INTERPOLATION = 2, VOLUME_INTERPOLATION_LINEAR = 0
        settings.set("volume_interpolation_method",
                     validate_enum_value(enum_value(cmat, "volume_interpolation"), 2, 0))
        settings.set("volume_step_rate", cmat.volume_step_rate)

    elif isinstance(shader, bpy.types.World) and shader.node_tree:
        cworld = getattr(shader, "cycles", None)
        if cworld is None:
            return settings
        settings.set("volume_sampling_method",
                     validate_enum_value(enum_value(cworld, "volume_sampling"), 3, 0))
        settings.set("volume_interpolation_method",
                     validate_enum_value(enum_value(cworld, "volume_interpolation"), 2, 0))
        settings.set("volume_step_rate", cworld.volume_step_size)

    return settings


def shader_name(shader):
    if isinstance(shader, bpy.types.World):
        # sync_world() fills Scene::default_background.
        return WORLD_SHADER_NAME
    return shader.name if shader is not None else "shader"

#########################################################################################
# XML output


def xml_to_string(xml_root):
    ET.indent(xml_root, space="  ")
    text = ET.tostring(xml_root, encoding="unicode")
    # Control characters (attribute name prefixes) are not allowed raw in XML.
    for c in range(0x20):
        if chr(c) in text and c not in (0x09, 0x0A, 0x0D):
            text = text.replace(chr(c), f"&#x{c:X};")
    return '<?xml version="1.0" ?>\n' + text + "\n"


def write_xml(writer, name, settings=None):
    xml_root = ET.Element("shader", name=name)

    if settings is not None:
        settings.write_sockets(xml_root)

    for node in writer.nodes:
        node.to_xml(xml_root)

    for (from_node, from_socket), (to_node, to_socket) in writer.connections:
        ET.SubElement(xml_root, "connect",
                      from_node=from_node.name,
                      from_socket=from_socket.name,
                      from_socket_ui=from_socket.ui_name,
                      to_node=to_node.name,
                      to_socket=to_socket.name,
                      to_socket_ui=to_socket.ui_name)

    return xml_to_string(xml_root)


def export_shader(shader, node_tree, binary=None):
    """Export the shader graph of a material, world or light.

    shader: the Material / World / Light (space_data.id of the shader editor).
    node_tree: tree used when the data-block has no node tree of its own.
    binary: optional bytearray receiving the array data, see XMLWriter.
    """
    writer = XMLWriter(binary)

    # Export the whole shader even when the editor shows the inside of a node group.
    tree = getattr(shader, "node_tree", None) or node_tree

    settings = shader_settings(writer, shader)

    if tree is not None:
        add_nodes(writer, tree)
    else:
        add_default_graph(writer, shader)

    return write_xml(writer, shader_name(shader), settings)


def export_node(shader, node, binary=None):
    """Export a single node with its parameters and input values, without connections."""
    writer = XMLWriter(binary)
    tree = node.id_data

    if node.bl_idname in node_map.OUTPUT_NODE_IDNAMES:
        report(f'Output node "{node.name}" has no parameters, it maps to the graph output "output".')
        xn = None
    elif node.bl_idname in ("ShaderNodeGroup", "NodeCustomGroup", "NodeReroute",
                            "NodeGroupInput", "NodeGroupOutput"):
        report(f'Node "{node.name}" is resolved only when exporting the whole shader.')
        xn = None
    else:
        xn = add_node(writer, tree, node, "")

    if xn is not None:
        map_node_sockets(writer, tree, node, xn, None, None)

    return write_xml(writer, shader_name(shader))
