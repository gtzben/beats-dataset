"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-21
"""

from marshmallow import Schema, fields, validates, ValidationError

class LinkSchema(Schema):

    """
    TODO
    """
    class Meta:
        ordered = True

    serial_number = fields.String()
    account_email = fields.String()

    @validates
    def validate_at_least_one(self, data):
        """
        Ensures at least one field (device_serial or participant_pid) is provided.
        """
        if not data.get("serial_number") and not data.get("account_email"):
            raise ValidationError("At least one of 'device_serial' or 'participant_pid' must be provided.")