import logging
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import update_session_auth_hash
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import CustomUser
from .serializers import CustomUserSerializer, RegisterSerializer, ChangePasswordSerializer, CustomTokenObtainPairSerializer

logger = logging.getLogger(__name__)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        logger.info(f"Received registration data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            logger.info(f"User registered successfully: {serializer.validated_data['username']}")
            return Response(
                {"message": "User registered successfully"},
                status=status.HTTP_201_CREATED
            )
        logger.error(f"Registration failed. Errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(generics.RetrieveUpdateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = CustomUserSerializer

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)

class ChangePasswordView(generics.UpdateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            if not user.check_password(serializer.validated_data['old_password']):
                return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            update_session_auth_hash(request, user)

            return Response({"message": "Password updated successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            email = request.data.get('email')
            print(f"\n=== Iniciando proceso de reset de contraseña ===")
            print(f"Email solicitado: {email}")
            print(f"Usando correo remitente: {settings.EMAIL_HOST_USER}")

            if not email:
                return Response(
                    {"error": "Se requiere un correo electrónico"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = CustomUser.objects.filter(email=email).first()
            if not user:
                return Response(
                    {"message": "Si existe una cuenta con este correo, recibirá las instrucciones."}, 
                    status=status.HTTP_200_OK
                )

            # Genera el token y la URL
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"

            try:
                # Renderiza el template
                context = {
                    'user': user,
                    'reset_url': reset_url,
                }
                email_html_message = render_to_string('password_reset_email.html', context)

                # Configuración explícita del correo
                subject = 'Restablecer tu contraseña - TaskMaster'
                from_email = settings.EMAIL_HOST_USER
                recipient_list = [email]

                print("\nEnviando correo con la siguiente configuración:")
                print(f"From: {from_email}")
                print(f"To: {recipient_list}")
                print(f"Subject: {subject}")

                # Intenta enviar el correo
                send_mail(
                    subject=subject,
                    message='',  # Versión texto plano
                    html_message=email_html_message,
                    from_email=from_email,
                    recipient_list=recipient_list,
                    fail_silently=False,
                )
                
                print("✓ Correo enviado exitosamente")
                return Response(
                    {"message": "Se ha enviado un correo con las instrucciones"}, 
                    status=status.HTTP_200_OK
                )
            
            except Exception as mail_error:
                print(f"\n✗ Error al enviar el correo:")
                print(f"Tipo de error: {type(mail_error).__name__}")
                print(f"Mensaje de error: {str(mail_error)}")
                print(f"Configuración de correo:")
                print(f"BACKEND: {settings.EMAIL_BACKEND}")
                print(f"HOST: {settings.EMAIL_HOST}")
                print(f"PORT: {settings.EMAIL_PORT}")
                print(f"TLS: {settings.EMAIL_USE_TLS}")
                print(f"USER: {settings.EMAIL_HOST_USER}")
                return Response(
                    {"error": "Error al enviar el correo. Por favor, intente más tarde."}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            print(f"\n✗ Error general:")
            print(f"Tipo: {type(e).__name__}")
            print(f"Mensaje: {str(e)}")
            return Response(
                {"error": "Error interno del servidor"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
class PasswordResetConfirmView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            new_password = request.data.get('new_password')
            if new_password:
                user.set_password(new_password)
                user.save()
                return Response({"message": "Password has been reset"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "New password is required"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "Invalid reset link"}, status=status.HTTP_400_BAD_REQUEST)