# forms.py
from django import forms
from .models import Producto, ProductoImagen, Categoria, ProductoTalla, Contacto, Profile, OpinionCliente
from django.db.models import Min, Max
from django.contrib.auth.forms import SetPasswordForm,UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['marca', 'nombre', 'precio', 'descripcion','activo','categoria']  # No es necesario incluir 'imagen' aquí

    categoria = forms.ModelChoiceField(queryset=Categoria.objects.all(), required=False)  # Si quieres que sea un campo de selección
    
   
class ProductoTallaForm(forms.ModelForm):
    class Meta:
        model = ProductoTalla
        fields = ['talla', 'cantidad']

    def __init__(self, *args, **kwargs):
        self.producto = kwargs.pop('producto', None)  # Recuperamos el producto del kwargs
        super(ProductoTallaForm, self).__init__(*args, **kwargs)

        if self.producto:
            # Filtramos las tallas según la categoría del producto
            if self.producto.categoria.nombre == 'Zapatos':
                self.fields['talla'].choices = [('37', '37'), ('38', '38'), ('39', '39')]
            elif self.producto.categoria.nombre == 'Pantalones y Jeans':
                self.fields['talla'].choices = [('40', '40'), ('41', '41'), ('42', '42'), ('43', '43'), ('44', '44')]
            else:
                self.fields['talla'].choices = [('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL')]

    def clean_talla(self):
        talla = self.cleaned_data['talla']
        if ProductoTalla.objects.filter(producto=self.producto, talla=talla).exists():
            raise forms.ValidationError(f'La talla {talla} ya ha sido agregada para este producto.')
        return talla
    
    
class ProductoImagenForm(forms.ModelForm):
    class Meta:
        model = ProductoImagen
        fields = ['imagen']

    def __init__(self, *args, **kwargs):
        super(ProductoImagenForm, self).__init__(*args, **kwargs)
        producto = kwargs.get('instance').producto if 'instance' in kwargs else None
        if producto:
            self.fields['producto'].initial = producto
        
class ProductoFilterForm(forms.Form):
    categoria = forms.ModelChoiceField(queryset=Categoria.objects.all(), required=False, label='Categoría', empty_label='Selecciona una categoría' )
    min_precio = forms.DecimalField(required=False, label='Precio Mínimo', min_value=0)
    max_precio = forms.DecimalField(required=False, label='Precio Máximo', min_value=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Cambiar las opciones de categoría si es necesario
        self.fields['categoria'].queryset = Categoria.objects.all()

        # Establecer el rango de precios mínimo y máximo dinámicamente
        self.fields['min_precio'].initial = Producto.objects.all().aggregate(Min('precio'))['precio__min']
        self.fields['max_precio'].initial = Producto.objects.all().aggregate(Max('precio'))['precio__max']

    def clean(self):
        cleaned_data = super().clean()

        categoria = cleaned_data.get('categoria')
        if categoria:
            # Si se selecciona una categoría, solo mostrar productos de esa categoría en los rangos de precios
            productos_categoria = Producto.objects.filter(categoria=categoria)
            min_precio = productos_categoria.aggregate(Min('precio'))['precio__min']
            max_precio = productos_categoria.aggregate(Max('precio'))['precio__max']
            self.fields['min_precio'].initial = min_precio
            self.fields['max_precio'].initial = max_precio

        return cleaned_data
   
class ContactoForm(forms.ModelForm):
    class Meta:
        model = Contacto
        fields = ['customer_name', 'customer_email', 'message']
        labels = {
            'customer_name': 'Nombre:',
            'customer_email': 'Correo Electrónico:',
            'message': 'Mensaje:',
        }
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',  # Clase de Bootstrap
                'placeholder': 'Ingresa tu nombre',  # Placeholder
            }),
            'customer_email': forms.EmailInput(attrs={
                'class': 'form-control',  # Clase de Bootstrap
                'placeholder': 'Ingresa tu correo electrónico',  # Placeholder
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',  # Clase de Bootstrap
                'cols': 30,
                'rows': 3,
                'placeholder': 'Escribe tu mensaje aquí...',  # Placeholder
            }),
        }

class CustomPasswordResetConfirmForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="Nueva Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Ingresa tu nueva contraseña'}),
    )
    new_password2 = forms.CharField(
        label="Confirmar Nueva Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirma tu nueva contraseña'}),
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        if new_password1 and new_password2 and new_password1 != new_password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
    
    
class CustomEmailForm(forms.Form):
    email = forms.EmailField(
        label="Correo Electrónico",
        max_length=254,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ingresa tu correo electrónico'}),
    )
    
class LoginForm(forms.Form):
    username = forms.CharField(
        label='Nombre de usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',  # Clase de Bootstrap
            'placeholder': 'Ingresa tu correo',  # Placeholder
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',  # Clase de Bootstrap
            'placeholder': 'Ingresa tu contraseña',  # Placeholder
        })
    )
# Formulario para crear un usuario con campos adicionales
# Formulario para crear un usuario con campos adicionales
class CustomUserCreationForm(UserCreationForm):
    nombre = forms.CharField(max_length=30, required=True)
    apellido = forms.CharField(max_length=30, required=True)
    rut = forms.CharField(max_length=12, required=True)
    telefono = forms.CharField(max_length=15, required=True)
    direccion = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'cols': 40}), required=True)

    class Meta:
        model = User
        fields = ['nombre', 'apellido', 'email', 'password1', 'password2', 'rut', 'telefono', 'direccion']
        
    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        if Profile.objects.filter(rut=rut).exists():
            raise ValidationError("Este correo rut ya está registrado.")
        return rut

    # Validación personalizada para asegurarse de que el correo y el teléfono sean únicos
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este correo electrónico ya está registrado.")
        return email
    # Validaciones de las contraseñas
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        # Aquí puedes agregar reglas personalizadas si lo deseas
        if password and len(password) < 8:
            raise ValidationError("La contraseña debe tener al menos 8 caracteres.")
        
        # No permitir contraseñas completamente numéricas
        if password and password.isdigit():
            raise ValidationError("La contraseña no puede ser completamente numérica.")
       
        # Validacion de Contraseñas
        if password == password2:
            raise ValidationError("La contraseña tiene que ser Iguales.")
        
        return password

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if Profile.objects.filter(telefono=telefono).exists():
            raise ValidationError("Este número de teléfono ya está registrado.")
        return telefono

    def save(self, commit=True):
        # Guardar el usuario
        user = super().save(commit=False)

        # Asignar el correo como el username
        user.username = self.cleaned_data['email']
        
        if commit:
            user.save()

        # Crear el perfil del usuario
        profile = Profile.objects.create(
            user=user,
            rut=self.cleaned_data['rut'],
            telefono=self.cleaned_data['telefono'],
            direccion=self.cleaned_data['direccion']
        )
        return user

# Formulario para crear o actualizar el perfil del usuario
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['rut', 'telefono', 'direccion']
        
        
class OpinionClienteForm(forms.ModelForm):
    class Meta:
        model = OpinionCliente
        fields = ['opinion', 'valoracion']
        widgets = {
            'opinion': forms.Textarea(attrs={'rows': 3, 'cols': 50}),
        }
        
   