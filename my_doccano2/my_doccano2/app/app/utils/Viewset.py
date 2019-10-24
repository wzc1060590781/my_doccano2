from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet


class ApiModelViewSet(ModelViewSet):
    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return Response({
            "status": response.status_code,
            "success": True,
            "message": "成功",
            "data": response.data
        }, status=response.status_code)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response({
            "status": response.status_code,
            "success": True,
            "message": "成功",
            "data": response.data
        }, status=response.status_code)

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return Response({
            "status": response.status_code,
            "success": True,
            "message": "成功",
            "data": response.data
        },status=response.status_code)

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return Response({
            "status": response.status_code,
            "success": True,
            "message": "成功",
            "data": response.data
        }, status=response.status_code)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response({
            "status": response.status_code,
            "success": True,
            "message": "成功",
            "data": response.data
        }, status=response.status_code)
