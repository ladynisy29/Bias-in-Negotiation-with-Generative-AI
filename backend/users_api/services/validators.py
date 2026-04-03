from rest_framework.exceptions import ValidationError


def validate_positive_number(value: float, field_name: str) -> None:
    if value is None:
        raise ValidationError({field_name: "This field is required."})
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        raise ValidationError({field_name: "Must be a numeric value."})

    if numeric <= 0:
        raise ValidationError({field_name: "Must be greater than zero."})


def validate_message(value: str) -> None:
    if not value or not value.strip():
        raise ValidationError({"message": "Message cannot be empty."})
    if len(value) > 2000:
        raise ValidationError({"message": "Message must be 2000 characters or fewer."})
