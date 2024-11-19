"""

------------------------
Author: Benjamin Gutierrez Serafin
Date: 2024-11-19
"""
from http import HTTPStatus
from flask import current_app, request
from flask_restful import Resource
from flask_jwt_extended import get_jwt_identity, jwt_required

from marshmallow import ValidationError

from app.routes.api.schemas.device import DeviceSchema

from app.routes.api.models.device import Device
from app.routes.api.models.user import User



class DeviceResource(Resource):
    
    """
    TODO
    """

    def __init__(self, **kwargs):
        self.logger = current_app.logger

    @jwt_required()
    def get(self, device_serial=None):
        """
        
        """

        current_user = User.get_by_id(id=get_jwt_identity())

        if current_user.is_superuser or current_user.is_admin:
            if device_serial:
                device = Device.get_by_serial(serial=device_serial)

                if device is None:
                    return {'message': 'User not found'}, HTTPStatus.NOT_FOUND
                
                data = DeviceSchema().dump(device)

            else:
                all_devices = Device.get_all_devices()
                data = DeviceSchema(many=True).dump(all_devices)

            return data
        else:
            return {"message":"You are not allowed to see this information"}, HTTPStatus.FORBIDDEN



    @jwt_required()
    def post(self):
        """
        TODO
        """

        json_data = request.get_json()

        current_user = User.get_by_id(id=get_jwt_identity())

        if current_user.is_superuser or current_user.is_admin:

            try:
                data = DeviceSchema().load(json_data)
            except ValidationError as errors:
                return {'message': 'Validation errors', 'errors':errors.messages}, HTTPStatus.BAD_REQUEST

            if Device.get_by_serial(serial=data.get('serial_number')):
                return {'message': 'This device has already been created'}, HTTPStatus.BAD_REQUEST

            device = Device(**data)
            device.user_id = current_user.id
            device.save()

            device_created = DeviceSchema().dump(device)

            self.logger.debug(f"User {current_user.email} has created device {device.device_name} with serial number {device.serial_number}")

            return device_created, HTTPStatus.CREATED
        else:
            return {"message":"You are not allowed to register a device"}, HTTPStatus.FORBIDDEN
    