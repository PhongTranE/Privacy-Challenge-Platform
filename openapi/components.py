pagination_parameters = [
    {
        "name": "page",
        "in": "query",
        "description": "Page number (default is 1)",
        "required": False,
        "schema": {"type": "integer", "default": 1}
    },
    {
        "name": "per_page",
        "in": "query",
        "description": "Number of items per page (default is 10)",
        "required": False,
        "schema": {"type": "integer", "default": 10}
    },
    {
        "name": "count",
        "in": "query",
        "description": "Include the total count of items in the response metadata. Set to 'true' to execute a count query, which may impact performance on large datasets; set to 'false' to omit the total count. Default is 'true'.",
        "required": False,
        "schema": {"type": "boolean", "default": True}
    }
]

pagination_metadata = {
    "type": "object",
    "properties": {
        "total_items": {"type": "integer", "nullable": True},
        "total_pages": {"type": "integer", "nullable": True},
        "current_page": {"type": "integer"},
        "per_page": {"type": "integer"},
        "has_next": {"type": "boolean"},
        "has_prev": {"type": "boolean"}
    }
}
