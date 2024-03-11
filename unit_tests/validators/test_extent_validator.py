from unittest import TestCase

import simplejson as json
from llc1_document_api.validators.payload_validator import PayloadValidator


class TestExtentValidator(TestCase):

    VALID_POLYGON = {
        "source": "Unit Tests",
        "description": "example description",
        "extents":
            {
                "type": "FeatureCollection",
                "features":
                    [
                        {
                            "type": "Feature",
                            "geometry":
                                {
                                    "type": "Polygon",
                                    "coordinates":
                                        [
                                            [
                                                [111.111, 111.111],
                                                [111.111, 111.111],
                                                [111.111, 111.111]
                                            ]
                                        ]
                                },
                            "properties": None
                        }
                    ]
            }
    }

    VALID_MULTI_POLYGON = {
        "source": "Unit Tests",
        "description": "example description",
        "extents":
            {
                "type": "FeatureCollection",
                "features":
                    [
                        {
                            "type": "Feature",
                            "geometry":
                                {
                                    "type": "MultiPolygon",
                                    "coordinates":
                                        [
                                            [
                                                [
                                                    [222.222, 222.222],
                                                    [222.222, 222.222],
                                                    [222.222, 222.222],
                                                    [222.222, 222.222],
                                                    [222.222, 222.222]
                                                ]
                                            ],
                                            [
                                                [
                                                    [333.333, 333.333],
                                                    [333.333, 333.333],
                                                    [333.333, 333.333],
                                                    [333.333, 333.333],
                                                    [333.333, 333.333]
                                                ]
                                            ]
                                        ],
                                },
                            "properties": None
                        },
                    ]
            }
    }

    MISSING_EXTENTS = {
        "description": "example description"
    }

    MISSING_SOURCE = {
        "description": "example description",
        "extents": VALID_MULTI_POLYGON
    }

    VALID_INPUT = [
        VALID_POLYGON,
        VALID_MULTI_POLYGON
    ]

    INVALID_INPUT = [
        None,
        '',
        MISSING_EXTENTS,
        MISSING_SOURCE
    ]

    def test_validate_with_valid_input(self):
        """All valid inputs should return True."""
        for input_ in self.VALID_INPUT:
            result = PayloadValidator.validate(json.dumps(input_))
            self.assertTrue(result)

    def test_validate_with_invalid_input(self):
        """All invalid inputs should return False."""
        for input_ in self.INVALID_INPUT:
            result = PayloadValidator.validate(json.dumps(input_))
            self.assertFalse(result)
