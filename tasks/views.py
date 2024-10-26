from rest_framework import viewsets, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Task
from .serializers import TaskSerializer

class TaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet para operaciones CRUD en tareas.
    Solo permite a los usuarios ver y modificar sus propias tareas.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        """
        Retorna solo las tareas que pertenecen al usuario autenticado,
        ordenadas por fecha de creación descendente.
        """
        return Task.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        """
        Al crear una nueva tarea, asigna automáticamente el usuario actual
        como propietario.
        """
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        """
        Sobreescribe el método list para añadir logging y debugging
        """
        queryset = self.get_queryset()
        print(f"TaskViewSet.list - Usuario: {request.user.id}")
        print(f"TaskViewSet.list - Tareas encontradas: {queryset.count()}")
        return super().list(request, *args, **kwargs)