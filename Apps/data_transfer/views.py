from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import DataTransfer, DataTransferItem
from .serializers import DataTransferSerializer, DataTransferItemSerializer

class DataTransferViewSet(viewsets.ModelViewSet):
    """ViewSet for DataTransfer model"""
    queryset = DataTransfer.objects.all()
    serializer_class = DataTransferSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter data transfers by source or destination organization"""
        source_org = self.request.query_params.get('source_organization', None)
        dest_org = self.request.query_params.get('destination_organization', None)
        queryset = DataTransfer.objects.all()

        if source_org:
            queryset = queryset.filter(source_organization_id=source_org)
        if dest_org:
            queryset = queryset.filter(destination_organization_id=dest_org)

        return queryset

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a data transfer"""
        transfer = self.get_object()
        try:
            transfer.approve()
            return Response({'status': 'transfer approved'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a data transfer"""
        transfer = self.get_object()
        try:
            transfer.reject()
            return Response({'status': 'transfer rejected'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete a data transfer"""
        transfer = self.get_object()
        try:
            transfer.complete()
            return Response({'status': 'transfer completed'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DataTransferItemViewSet(viewsets.ModelViewSet):
    """ViewSet for DataTransferItem model"""
    queryset = DataTransferItem.objects.all()
    serializer_class = DataTransferItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter transfer items by data transfer"""
        transfer_id = self.request.query_params.get('data_transfer', None)
        if transfer_id:
            return DataTransferItem.objects.filter(data_transfer_id=transfer_id)
        return DataTransferItem.objects.all() 