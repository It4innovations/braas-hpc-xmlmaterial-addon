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

import bpy

#   EnumName                      StructName                UIName                        Cycles Node Class             XML Node
blender_cycles_shader_map = [
    ["ADD_SHADER",               "AddShader",               "Add Shader",               [["AddClosureNode",             "add_closure"]]],
    ["AMBIENT_OCCLUSION",        "AmbientOcclusion",        "Ambient Occlusion",        [["AmbientOcclusionNode",       "ambient_occlusion"]]],
    ["ATTRIBUTE",                "Attribute",               "Attribute",                [["AttributeNode",              "attribute"]]],
    ["BACKGROUND",               "Background",              "Background",               [["BackgroundNode",             "background_shader"]]],
    ["BEVEL",                    "Bevel",                   "Bevel",                    [["BevelNode",                  "bevel"]]],
    ["BLACKBODY",                "Blackbody",               "Blackbody",                [["BlackbodyNode",              "blackbody"]]],
    ["BRIGHTCONTRAST",           "BrightContrast",          "Brightness/Contrast",      [["BrightContrastNode",         "brightness_contrast"]]],
    ["BSDF_DIFFUSE",             "BsdfDiffuse",             "Diffuse BSDF",             [["DiffuseBsdfNode",            "diffuse_bsdf"]]],
    ["BSDF_GLASS",               "BsdfGlass",               "Glass BSDF",               [["GlassBsdfNode",              "glass_bsdf"]]],
    ["BSDF_GLOSSY",              "BsdfAnisotropic",         "Glossy BSDF",              [["GlossyBsdfNode",             "glossy_bsdf"]]],
    ["BSDF_HAIR",                "BsdfHair",                "Hair BSDF",                [["HairBsdfNode",               "hair_bsdf"]]],
    ["BSDF_HAIR_PRINCIPLED",     "BsdfHairPrincipled",      "Principled Hair BSDF",     [["PrincipledHairBsdfNode",     "principled_hair_bsdf"]]],
    ["BSDF_PRINCIPLED",          "BsdfPrincipled",          "Principled BSDF",          [["PrincipledBsdfNode",         "principled_bsdf"]]],
    ["BSDF_RAY_PORTAL",          "BsdfRayPortal",           "Ray Portal BSDF",          [["RayPortalBsdfNode",          "ray_portal_bsdf"]]],
    ["BSDF_REFRACTION",          "BsdfRefraction",          "Refraction BSDF",          [["RefractionBsdfNode",         "refraction_bsdf"]]],
    ["BSDF_SHEEN",               "BsdfSheen",               "Sheen BSDF",               [["SheenBsdfNode",              "sheen_bsdf"]]],
    ["BSDF_TOON",                "BsdfToon",                "Toon BSDF",                [["ToonBsdfNode",               "toon_bsdf"]]],
    ["BSDF_TRANSLUCENT",         "BsdfTranslucent",         "Translucent BSDF",         [["TranslucentBsdfNode",        "translucent_bsdf"]]],
    ["BSDF_TRANSPARENT",         "BsdfTransparent",         "Transparent BSDF",         [["TransparentBsdfNode",        "transparent_bsdf"]]],
    ["BUMP",                     "Bump",                    "Bump",                     [["BumpNode",                   "bump"]]],
    ["CAMERA",                   "CameraData",              "Camera Data",              [["CameraNode",                 "camera_info"]]],
    ["CLAMP",                    "Clamp",                   "Clamp",                    [["ClampNode",                  "clamp"]]],
    ["COMBHSV",                  "CombineHSV",              "Combine HSV",              [["CombineHSVNode",             "combine_hsv"]]],
    ["COMBINE_COLOR",            "CombineColor",            "Combine Color",            [["CombineColorNode",           "combine_color"]]],
    ["COMBRGB",                  "CombineRGB",              "Combine RGB",              [["CombineRGBNode",             "combine_rgb"]]],
    ["COMBXYZ",                  "CombineXYZ",              "Combine XYZ",              [["CombineXYZNode",             "combine_xyz"]]],
    ["CURVE_FLOAT",              "FloatCurve",              "Float Curve",              [["FloatCurveNode",             "float_curve"]]],
    ["CURVE_RGB",                "RGBCurve",                "RGB Curves",               [["RGBCurvesNode",              "rgb_curves"]]],
    ["CURVE_VEC",                "VectorCurve",             "Vector Curves",            [["VectorCurvesNode",           "vector_curves"]]],
    ["DISPLACEMENT",             "Displacement",            "Displacement",             [["DisplacementNode",           "displacement"]]],
    ["EMISSION",                 "Emission",                "Emission",                 [["EmissionNode",               "emission"]]],
    ["FRESNEL",                  "Fresnel",                 "Fresnel",                  [["FresnelNode",                "fresnel"]]],
    ["GAMMA",                    "Gamma",                   "Gamma",                    [["GammaNode",                  "gamma"]]],
    ["HAIR_INFO",                "HairInfo",                "Curves Info",              [["HairInfoNode",               "hair_info"]]],
    ["HOLDOUT",                  "Holdout",                 "Holdout",                  [["HoldoutNode",                "holdout"]]],
    ["HUE_SAT",                  "HueSaturation",           "Hue/Saturation/Value",     [["HSVNode",                    "hsv"]]],
    ["INVERT",                   "Invert",                  "Invert Color",             [["InvertNode",                 "invert"]]],
    ["LAYER_WEIGHT",             "LayerWeight",             "Layer Weight",             [["LayerWeightNode",            "layer_weight"]]],
    ["LIGHT_FALLOFF",            "LightFalloff",            "Light Falloff",            [["LightFalloffNode",           "light_falloff"]]],
    ["LIGHT_PATH",               "LightPath",               "Light Path",               [["LightPathNode",              "light_path"]]],
    ["MAPPING",                  "Mapping",                 "Mapping",                  [["MappingNode",                "mapping"]]],
    ["MATH",                     "Math",                    "Math",                     [["MathNode",                   "math"]]],
    ["MIX_RGB",                  "MixRGB",                  "MixRGB",                   [["MixNode",                    "mix"]]],
    ["MIX_SHADER",               "MixShader",               "Mix Shader",               [["MixClosureNode",             "mix_closure"]]],
    ["NEW_GEOMETRY",             "NewGeometry",             "Geometry",                 [["GeometryNode",               "geometry"]]],
    ["NORMAL",                   "Normal",                  "Normal",                   [["NormalNode",                 "normal_map"]]],
    ["NORMAL_MAP",               "NormalMap",               "Normal Map",               [["NormalMapNode",              "normal"]]],
    ["OBJECT_INFO",              "ObjectInfo",              "Object Info",              [["ObjectInfoNode",             "object_info"]]],
    ["OUTPUT_AOV",               "OutputAOV",               "AOV Output",               [["OutputAOVNode",              "aov_output"]]],
    ["PARTICLE_INFO",            "ParticleInfo",            "Particle Info",            [["ParticleInfoNode",           "particle_info"]]],
    ["POINT_INFO",               "PointInfo",               "Point Info",               [["PointInfoNode",              "point_info"]]],
    ["PRINCIPLED_VOLUME",        "VolumePrincipled",        "Principled Volume",        [["PrincipledVolumeNode",       "principled_volume"]]],
    ["RGB",                      "RGB",                     "RGB",                      [["ColorNode",                  "color"]]],
    ["RGBTOBW",                  "RGBToBW",                 "RGB to BW",                [["RGBToBWNode",                "rgb_to_bw"]]],
    ["SEPARATE_COLOR",           "SeparateColor",           "Separate Color",           [["SeparateColorNode",          "separate_color"]]],
    ["SEPHSV",                   "SeparateHSV",             "Separate HSV",             [["SeparateHSVNode",            "separate_hsv"]]],
    ["SEPRGB",                   "SeparateRGB",             "Separate RGB",             [["SeparateRGBNode",            "separate_rgb"]]],
    ["SEPXYZ",                   "SeparateXYZ",             "Separate XYZ",             [["SeparateXYZNode",            "separate_xyz"]]],
    ["SUBSURFACE_SCATTERING",    "SubsurfaceScattering",    "Subsurface Scattering",    [["SubsurfaceScatteringNode",   "subsurface_scattering"]]],
    ["TANGENT",                  "Tangent",                 "Tangent",                  [["TangentNode",                "tangent"]]],
    ["TEX_BRICK",                "TexBrick",                "Brick Texture",            [["BrickTextureNode",           "brick_texture"]]],
    ["TEX_CHECKER",              "TexChecker",              "Checker Texture",          [["CheckerTextureNode",         "checker_texture"]]],
    ["TEX_COORD",                "TexCoord",                "Texture Coordinate",       [["TextureCoordinateNode",      "texture_coordinate"]]],
    ["TEX_ENVIRONMENT",          "TexEnvironment",          "Environment Texture",      [["EnvironmentTextureNode",     "environment_texture"]]],
    ["TEX_GRADIENT",             "TexGradient",             "Gradient Texture",         [["GradientTextureNode",        "gradient_texture"]]],
    ["TEX_IES",                  "TexIES",                  "IES Texture",              [["IESLightNode",               "ies_light"]]],
    ["TEX_IMAGE",                "TexImage",                "Image Texture",            [["ImageTextureNode",           "image_texture"]]],
    ["TEX_MAGIC",                "TexMagic",                "Magic Texture",            [["MagicTextureNode",           "magic_texture"]]],
    ["TEX_NOISE",                "TexNoise",                "Noise Texture",            [["NoiseTextureNode",           "noise_texture"]]],
    ["TEX_POINTDENSITY",         "TexPointDensity",         "Point Density",            [["PointDensityTextureNode",    "point_density_texture"]]],
    ["TEX_SKY",                  "TexSky",                  "Sky Texture",              [["SkyTextureNode",             "sky_texture"]]],
    ["TEX_VORONOI",              "TexVoronoi",              "Voronoi Texture",          [["VoronoiTextureNode",         "voronoi_texture"]]],
    ["TEX_WAVE",                 "TexWave",                 "Wave Texture",             [["WaveTextureNode",            "wave_texture"]]],
    ["TEX_WHITE_NOISE",          "TexWhiteNoise",           "White Noise Texture",      [["WhiteNoiseTextureNode",      "white_noise_texture"]]],
    ["UVMAP",                    "UVMap",                   "UV Map",                   [["UVMapNode",                  "uvmap"]]],
    ["VALTORGB",                 "ValToRGB",                "Color Ramp",               [["RGBRampNode",                "rgb_ramp"]]],
    ["VALUE",                    "Value",                   "Value",                    [["ValueNode",                  "value"]]],

    ["VECT_MATH",                 "VectorMath",             "Vector Math",              [["VectorMathNode",             "vector_math"]]],
    ["VECT_TRANSFORM",            "VectorTransform",        "Vector Transform",         [["VectorTransformNode",        "vector_transform"]]],
    ["VECTOR_DISPLACEMENT",       "VectorDisplacement",     "Vector Displacement",      [["VectorDisplacementNode",     "vector_displacement"]]],
    ["VECTOR_ROTATE",             "VectorRotate",           "Vector Rotate",            [["VectorRotateNode",           "vector_rotate"]]],
    ["VERTEX_COLOR",              "VertexColor",            "Color Attribute",          [["VertexColorNode",            "vertex_color"]]],
    ["VOLUME_ABSORPTION",         "VolumeAbsorption",       "Volume Absorption",        [["AbsorptionVolumeNode",       "absorption_volume"]]],
    ["VOLUME_INFO",               "VolumeInfo",             "Volume Info",              [["VolumeInfoNode",             "volume_info"]]],
    ["VOLUME_SCATTER",            "VolumeScatter",          "Volume Scatter",           [["ScatterVolumeNode",          "scatter_volume"]]],
    ["WAVELENGTH",                "Wavelength",             "Wavelength",               [["WavelengthNode",             "wavelength"]]],
    ["WIREFRAME",                 "Wireframe",              "Wireframe",                [["WireframeNode",              "wireframe"]]],

    ["MIX",                      "Mix",                     "Mix",                      [["MixVectorNode",              "mix_vector"],
                                                                                         ["MixVectorNonUniformNode",    "mix_vector_non_uniform"],
                                                                                         ["MixColorNode",               "mix_color"],
                                                                                         ["MixFloatNode",               "mix_float"]]],

    ["MAP_RANGE",                "MapRange",                "Map Range",                [["VectorMapRangeNode",         "vector_map_range"],
                                                                                         ["MapRangeNode",               "map_range"]]],
]

EnumName = 0
StructName = 1
UIName = 2
CyclesNode = 3

CyclesNodeClass = 0
CyclesNodeXml = 1

def find_by_enum_type(enum_type: str):
    for m in blender_cycles_shader_map:
        if m[EnumName] == enum_type:
            return m
    
    raise Exception("enum_type not found: %s" % enum_type)

def find_by_struct_name(struct_name: str):
    for m in blender_cycles_shader_map:
        if m[StructName] == struct_name:
            return m
    
    raise Exception("struct_name not found: %s" % struct_name)

def enum_to_xml_type(enum_type: str) -> str:
    m = find_by_enum_type(enum_type)

    return m[CyclesNode][0][CyclesNodeXml]


def struct_name_to_xml_type(struct_name: str) -> str:
    m = find_by_struct_name(struct_name)

    return m[CyclesNode][0][CyclesNodeXml]