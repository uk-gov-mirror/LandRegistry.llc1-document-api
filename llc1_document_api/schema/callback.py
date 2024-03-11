
CALLBACK_SCHEMA = {
    "type": "object",
    "required": ["status", "result"],
    "properties": {
        "status": {
            "type": "string"
        },
        "result": {
            "oneOf": [
                {
                    "type": "object",
                    "properties": {
                        "document_url": {
                            "type": "string"
                        },
                        "included_charges": {
                            "type": "array",
                            "items": {
                                "type": "object"
                            }
                        },
                        "external_url": {
                            "type": "string"
                        }
                    }
                },
                {
                    "type": "string"
                }
            ]
        }
    }
}
