from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Task
from datetime import date

User = get_user_model()

class TaskTests(APITestCase):
    def setUp(self):
        """
        Configuración inicial para cada test.
        Crea usuarios y una tarea de prueba.
        """
        # Limpiar datos existentes
        Task.objects.all().delete()
        User.objects.all().delete()
        
        # Crear usuarios de prueba
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!'
        )
        
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='TestPass123!'
        )
        
        # Configurar cliente con autenticación
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Datos para crear una tarea
        self.task_data = {
            'title': 'Test Task',
            'description': 'Test Description',
            'due_date': '2024-12-31',
            'priority': 'high',
            'status': 'pending'
        }
        
        # Crear tarea de prueba
        self.test_task = Task.objects.create(
            user=self.user,
            title='Existing Task',
            description='Existing Description',
            due_date=date(2024, 12, 31),
            priority='medium',
            status='pending'
        )

    def tearDown(self):
        """Limpieza después de cada test"""
        Task.objects.all().delete()
        User.objects.all().delete()

    def test_create_task(self):
        """Test crear una nueva tarea"""
        url = reverse('tasks-list')
        response = self.client.post(url, self.task_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.filter(user=self.user).count(), 2)
        self.assertEqual(response.data['title'], 'Test Task')
        self.assertEqual(response.data['user'], self.user.id)

    def test_list_tasks(self):
        """Test listar tareas del usuario"""
        # Asegurar que solo existe una tarea
        Task.objects.filter(user=self.user).exclude(id=self.test_task.id).delete()
        
        url = reverse('tasks-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Existing Task')
        self.assertEqual(response.data['results'][0]['user'], self.user.id)

    def test_retrieve_task(self):
        """Test recuperar una tarea específica"""
        url = reverse('tasks-detail', args=[self.test_task.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Existing Task')
        self.assertEqual(response.data['user'], self.user.id)

    def test_update_task(self):
        """Test actualizar una tarea"""
        url = reverse('tasks-detail', args=[self.test_task.id])
        update_data = {
            'title': 'Updated Task',
            'status': 'in_progress'
        }
        response = self.client.patch(url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Task')
        self.assertEqual(response.data['status'], 'in_progress')
        self.assertEqual(response.data['description'], 'Existing Description')
        self.assertEqual(response.data['priority'], 'medium')

    def test_delete_task(self):
        """Test eliminar una tarea"""
        url = reverse('tasks-detail', args=[self.test_task.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Task.objects.filter(user=self.user).count(), 0)

    def test_task_user_isolation(self):
        """Test que los usuarios solo pueden acceder a sus propias tareas"""
        # Crear tarea para otro usuario
        other_task = Task.objects.create(
            user=self.other_user,
            title='Other User Task',
            description='Other Description',
            priority='low',
            status='pending'
        )
        
        # Intentar acceder a la tarea del otro usuario
        url = reverse('tasks-detail', args=[other_task.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Verificar listado de tareas
        url = reverse('tasks-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Existing Task')

    def test_create_task_with_invalid_data(self):
        """Test crear una tarea con datos inválidos"""
        url = reverse('tasks-list')
        invalid_data = {
            'title': '',
            'priority': 'invalid_priority'
        }
        response = self.client.post(url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_task_without_authentication(self):
        """Test crear una tarea sin autenticación"""
        self.client.credentials()  # Remover credenciales
        
        url = reverse('tasks-list')
        response = self.client.post(url, self.task_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_nonexistent_task(self):
        """Test actualizar una tarea que no existe"""
        url = reverse('tasks-detail', args=[999])
        update_data = {
            'title': 'Updated Task'
        }
        response = self.client.patch(url, update_data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_nonexistent_task(self):
        """Test eliminar una tarea que no existe"""
        url = reverse('tasks-detail', args=[999])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)