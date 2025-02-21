# docs/invite_key_docs.py

from http import HTTPStatus
from docs.components import pagination_parameters, pagination_metadata
from src.modules.admin.schemas import InviteKeySchema

invite_key_list_doc = {
    "description": "Retrieve a paginated list of invite keys.",
    "parameters": pagination_parameters,
    "responses": {
        HTTPStatus.OK.value: {
            "description": "A paginated list of invite keys.",
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "array",
                                "items": InviteKeySchema
                            },
                            "meta": pagination_metadata
                        }
                    }
                }
            }
        }
    }
}
