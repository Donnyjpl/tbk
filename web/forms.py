# forms.py
from django import forms
from .models import Producto, ProductoImagen,Categoria,ProductoTalla,Contacto
from django.db.models import Min, Max

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
        producto = kwargs.pop('producto', None)  # Eliminamos el producto del kwargs
        super(ProductoTallaForm, self).__init__(*args, **kwargs)

        if producto:
            # Filtramos las tallas según la categoría del producto
            if producto.categoria.nombre == 'Zapatos':
                self.fields['talla'].choices = [('37', '37'), ('38', '38'), ('39', '39')]
            elif producto.categoria.nombre == 'Pantalones y Jeans':
                self.fields['talla'].choices = [('40', '40'), ('41', '41'), ('42', '42'), ('43', '43'), ('44', '44')]
            else:
                self.fields['talla'].choices = [('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL')]
    
class ProductoImagenForm(forms.ModelForm):
    class Meta:
        model = ProductoImagen
        fields = ['producto', 'imagen']

    def __init__(self, *args, **kwargs):
        super(ProductoImagenForm, self).__init__(*args, **kwargs)
        producto = kwargs.get('instance').producto if 'instance' in kwargs else None
        if producto:
            self.fields['producto'].initial = producto
        
class ProductoFilterForm(forms.Form):
    categoria = forms.ModelChoiceField(queryset=Categoria.objects.all(), required=False, label='Categoría')
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
