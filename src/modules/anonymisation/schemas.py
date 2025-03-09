from marshmallow import Schema, fields, validate, ValidationError

class MetricSchema(Schema):
    """Schema for serializing and validating MetricModel with error handling."""
    
    id = fields.Int(
        dump_only=True,
        error_messages={"invalid": "Metric ID must be an integer."}
    )
    
    name = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=32),
        error_messages={
            "required": "Metric name is required.",
            "null": "Metric name cannot be null.",
            "validator_failed": "Metric name must be between 3 and 32 characters."
        }
    )

    parameters = fields.Str(
        missing="{}",
        error_messages={
            "invalid": "Parameters must be a valid JSON object."
        }
    )

    is_selected = fields.Bool(
        default=False,
        error_messages={
            "invalid": "Activation status must be true or false."
        }
    )