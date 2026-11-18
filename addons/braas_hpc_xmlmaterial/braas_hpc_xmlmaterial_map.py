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
Mapping of Blender shader nodes to Cycles shader nodes.

Follows add_node() in intern/cycles/blender/shader.cpp. The XML element name of a Cycles node is
looked up by its class name in the table generated from the CyclesPhi sources
(braas_hpc_xmlmaterial_sockets.py), so it always matches what the CyclesPhi XML reader expects.
"""

from .braas_hpc_xmlmaterial_sockets import CYCLES_NODES

# Blender nodes whose Cycles node has a fixed type. Nodes that pick the Cycles type from their
# settings (Mix, Map Range) are resolved in braas_hpc_xmlmaterial_convert.py.
BLENDER_TO_CYCLES_CLASS = {
    # Curves, ramps and constants
    "ShaderNodeRGBCurve":               "RGBCurvesNode",
    "ShaderNodeVectorCurve":            "VectorCurvesNode",
    "ShaderNodeFloatCurve":             "FloatCurveNode",
    "ShaderNodeValToRGB":               "RGBRampNode",
    "ShaderNodeRGB":                    "ColorNode",
    "FunctionNodeInputVector":          "ColorNode",
    "ShaderNodeValue":                  "ValueNode",
    "FunctionNodeInputBool":            "ValueNode",
    "FunctionNodeInputInt":             "ValueNode",
    # Color
    "ShaderNodeCameraData":             "CameraNode",
    "ShaderNodeInvert":                 "InvertNode",
    "ShaderNodeGamma":                  "GammaNode",
    "ShaderNodeBrightContrast":         "BrightContrastNode",
    "ShaderNodeMixRGB":                 "MixNode",
    "ShaderNodeSeparateColor":          "SeparateColorNode",
    "ShaderNodeCombineColor":           "CombineColorNode",
    "ShaderNodeSeparateXYZ":            "SeparateXYZNode",
    "FunctionNodeGetVectorComponent":   "GetVectorComponentNode",
    "ShaderNodeCombineXYZ":             "CombineXYZNode",
    "ShaderNodeHueSaturation":          "HSVNode",
    "ShaderNodeRGBToBW":                "RGBToBWNode",
    # Converter
    "ShaderNodeClamp":                  "ClampNode",
    "ShaderNodeMath":                   "MathNode",
    "FunctionNodeBooleanMath":          "BooleanMathNode",
    "FunctionNodeIntegerMath":          "IntegerMathNode",
    "ShaderNodeVectorMath":             "VectorMathNode",
    "ShaderNodeVectorRotate":           "VectorRotateNode",
    "ShaderNodeVectorTransform":        "VectorTransformNode",
    "ShaderNodeNormal":                 "NormalNode",
    "ShaderNodeMapping":                "MappingNode",
    "ShaderNodeFresnel":                "FresnelNode",
    "ShaderNodeLayerWeight":            "LayerWeightNode",
    # Shaders
    "ShaderNodeAddShader":              "AddClosureNode",
    "ShaderNodeMixShader":              "MixClosureNode",
    "ShaderNodeAttribute":              "AttributeNode",
    "ShaderNodeBackground":             "BackgroundNode",
    "ShaderNodeHoldout":                "HoldoutNode",
    "ShaderNodeBsdfDiffuse":            "DiffuseBsdfNode",
    "ShaderNodeSubsurfaceScattering":   "SubsurfaceScatteringNode",
    "ShaderNodeBsdfMetallic":           "MetallicBsdfNode",
    "ShaderNodeBsdfAnisotropic":        "GlossyBsdfNode",
    "ShaderNodeBsdfGlass":              "GlassBsdfNode",
    "ShaderNodeBsdfRefraction":         "RefractionBsdfNode",
    "ShaderNodeBsdfToon":               "ToonBsdfNode",
    "ShaderNodeBsdfHair":               "HairBsdfNode",
    "ShaderNodeBsdfHairPrincipled":     "PrincipledHairBsdfNode",
    "ShaderNodeBsdfPrincipled":         "PrincipledBsdfNode",
    "ShaderNodeBsdfTranslucent":        "TranslucentBsdfNode",
    "ShaderNodeBsdfTransparent":        "TransparentBsdfNode",
    "ShaderNodeBsdfRayPortal":          "RayPortalBsdfNode",
    "ShaderNodeBsdfSheen":              "SheenBsdfNode",
    "ShaderNodeEmission":               "EmissionNode",
    "ShaderNodeAmbientOcclusion":       "AmbientOcclusionNode",
    "ShaderNodeVolumeScatter":          "ScatterVolumeNode",
    "ShaderNodeVolumeAbsorption":       "AbsorptionVolumeNode",
    "ShaderNodeVolumeCoefficients":     "VolumeCoefficientsNode",
    "ShaderNodeVolumePrincipled":       "PrincipledVolumeNode",
    # Input
    "ShaderNodeNewGeometry":            "GeometryNode",
    "ShaderNodeWireframe":              "WireframeNode",
    "ShaderNodeWavelength":             "WavelengthNode",
    "ShaderNodeBlackbody":              "BlackbodyNode",
    "ShaderNodeLightPath":              "LightPathNode",
    "ShaderNodeLightFalloff":           "LightFalloffNode",
    "ShaderNodeObjectInfo":             "ObjectInfoNode",
    "ShaderNodeParticleInfo":           "ParticleInfoNode",
    "ShaderNodeHairInfo":               "HairInfoNode",
    "ShaderNodePointInfo":              "PointInfoNode",
    "ShaderNodeVolumeInfo":             "VolumeInfoNode",
    "ShaderNodeVertexColor":            "VertexColorNode",
    "ShaderNodeBump":                   "BumpNode",
    "GeometryNodeInputSceneTime":       "SceneTimeNode",
    "ShaderNodeRaycast":                "RaycastNode",
    # Textures
    "ShaderNodeTexImage":               "ImageTextureNode",
    "ShaderNodeTexEnvironment":         "EnvironmentTextureNode",
    "ShaderNodeTexGradient":            "GradientTextureNode",
    "ShaderNodeTexVoronoi":             "VoronoiTextureNode",
    "ShaderNodeTexMagic":               "MagicTextureNode",
    "ShaderNodeTexWave":                "WaveTextureNode",
    "ShaderNodeTexChecker":             "CheckerTextureNode",
    "ShaderNodeTexBrick":               "BrickTextureNode",
    "ShaderNodeTexNoise":               "NoiseTextureNode",
    "ShaderNodeTexGabor":               "GaborTextureNode",
    "ShaderNodeTexCoord":               "TextureCoordinateNode",
    "ShaderNodeTexSky":                 "SkyTextureNode",
    "ShaderNodeTexIES":                 "IESLightNode",
    "ShaderNodeTexWhiteNoise":          "WhiteNoiseTextureNode",
    # Vector
    "ShaderNodeNormalMap":              "NormalMapNode",
    "ShaderNodeRadialTiling":           "RadialTilingNode",
    "ShaderNodeTangent":                "TangentNode",
    "ShaderNodeUVMap":                  "UVMapNode",
    "ShaderNodeBevel":                  "BevelNode",
    "ShaderNodeDisplacement":           "DisplacementNode",
    "ShaderNodeVectorDisplacement":     "VectorDisplacementNode",
    # Output
    "ShaderNodeOutputAOV":              "OutputAOVNode",
}

# Blender nodes that are handled by the graph traversal and never become a Cycles node.
OUTPUT_NODE_IDNAMES = {
    "ShaderNodeOutputMaterial",
    "ShaderNodeOutputWorld",
    "ShaderNodeOutputLight",
}

IGNORED_NODE_IDNAMES = {
    "NodeFrame",
    "ShaderNodeOutputLineStyle",
}

CLASS_TO_XML_TYPE = {cycles[0]: xml_type for xml_type, cycles in CYCLES_NODES.items()}


def class_to_xml_type(class_name: str):
    """XML element name of a Cycles node class, None when CyclesPhi does not know the class."""
    return CLASS_TO_XML_TYPE.get(class_name)


def blender_to_xml_type(bl_idname: str):
    class_name = BLENDER_TO_CYCLES_CLASS.get(bl_idname)
    return class_to_xml_type(class_name) if class_name else None
