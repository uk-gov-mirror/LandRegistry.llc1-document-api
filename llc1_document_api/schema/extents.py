PAYLOAD_SCHEMA = {
    "type": "object",
    "required": ["extents", "source"],
    "properties": {
        "description": {
            "type": "string"
        },
        "extents": {
            "$ref": "#/definitions/feature_collection"
        },
        "source": {
            "type": "string"
        },
        "language": {
            "type": ["string", "null"]
        },
        "contact_id": {
            "type": ["string", "null"]
        },
        "parent_search_id": {
            "type": "number"
        },
        "charges": {
            "type": "array"
        },
        "format": {
            "type": "string"
        }
    },

    "definitions": {

        "feature_collection": {
            "type": "object",
            "required": ["type", "features"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["FeatureCollection"]
                },
                "features": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/feature"
                    }
                }
            }
        },

        "feature": {
            "type": "object",
            "required": ["type", "geometry", "properties"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["Feature"]
                },
                "geometry": {
                    "type": "object",
                    "oneOf": [
                        {
                            "$ref": "#/definitions/polygon"
                        },
                        {
                            "$ref": "#/definitions/multi_polygon"
                        },
                        {
                            "$ref": "#/definitions/line_string"
                        },
                        {
                            "$ref": "#/definitions/multi_line_string"
                        },
                        {
                            "$ref": "#/definitions/point_geometry"
                        },
                        {
                            "$ref": "#/definitions/multi_point_geometry"
                        },
                        {
                            "$ref": "#/definitions/geometry_collection"
                        }
                    ]
                },
                "properties": {
                    "oneOf": [
                        {
                            "type": "object"
                        },
                        {
                            "type": "null"
                        }
                    ]
                },
            }
        },

        "point": {
            "type": "array",
            "minItems": 2,
            "maxItems": 2,
            "items": {
                "type": "number"
            }
        },

        "point_geometry": {
            "type": "object",
            "required": ["coordinates", "type"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["Point"]
                },
                "coordinates": {
                    "$ref": "#/definitions/point"
                }
            }
        },

        "multi_point_geometry": {
            "type": "object",
            "required": ["coordinates", "type"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["MultiPoint"]
                },
                "coordinates": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/point"
                    }
                }
            }
        },

        "polygon": {
            "type": "object",
            "required": ["coordinates", "type"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["Polygon"]
                },
                "coordinates": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {
                            "$ref": "#/definitions/point"
                        }
                    }
                }
            }
        },

        "multi_polygon": {
            "type": "object",
            "required": ["coordinates", "type"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["MultiPolygon"]
                },
                "coordinates": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {
                                "$ref": "#/definitions/point"
                            }
                        }
                    }
                }
            }
        },

        "line_string": {
            "type": "object",
            "required": ["coordinates", "type"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["LineString"]
                },
                "coordinates": {
                    "type": "array",
                    "items": {
                        "$ref": "#/definitions/point"
                    }
                }
            }
        },

        "multi_line_string": {
            "type": "object",
            "required": ["coordinates", "type"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["MultiLineString"]
                },
                "coordinates": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {
                            "$ref": "#/definitions/point"
                        }
                    }
                }
            }
        },

        "geometry_collection": {
            "type": "object",
            "required": ["geometries", "type"],
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["GeometryCollection"]
                },
                "geometries": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "oneOf": [
                            {
                                "$ref": "#/definitions/polygon"
                            },
                            {
                                "$ref": "#/definitions/multi_polygon"
                            },
                            {
                                "$ref": "#/definitions/line_string"
                            },
                            {
                                "$ref": "#/definitions/multi_line_string"
                            },
                            {
                                "$ref": "#/definitions/point_geometry"
                            },
                            {
                                "$ref": "#/definitions/multi_point_geometry"
                            }
                        ]
                    }
                }
            }
        }
    }
}
