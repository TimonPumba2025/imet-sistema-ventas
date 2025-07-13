from django import forms
from django.forms import modelformset_factory

from entidad.models import *
from decimal import Decimal

class ProductoForm(forms.ModelForm):
    proveedores = forms.ModelMultipleChoiceField(
    queryset=ProveedorProducto.objects.filter(activo=True),
    widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check'}),
    required=False
    )
    class Meta:
        model = Producto
        fields = ('codigo','nombre','marca','precio','cantidad','descripcion','proveedores','unidad_medida')
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-styling'}), 
            'nombre': forms.TextInput(attrs={'class': 'form-styling'}),
            'marca': forms.TextInput(attrs={'class': 'form-styling'}),
            'precio': forms.NumberInput(attrs={'class': 'form-styling'}),
            'unidad_medida': forms.Select(attrs={'class': 'form-styling'}),

            
            'cantidad': forms.NumberInput(attrs={'class': 'form-styling'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-styling', 'rows': 3, 'cols': 40}),

        }
        


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields= ('nombre',)

import re
from django import forms
from django.core.exceptions import ValidationError

class ProveedorProductoForm(forms.ModelForm):
    telefono = forms.CharField(
        max_length=15, 
        min_length=8,
        widget=forms.TextInput(attrs={
            'pattern': '[0-9+\-\s\(\)]*',
            'maxlength': '15',
            'placeholder': 'Ej: +54 381 123-4567',
            'class': 'form-control',
            'oninput': '''
                // Permitir solo números, espacios, guiones, paréntesis y el signo +
                this.value = this.value.replace(/[^0-9+\-\s\(\)]/g, '');
                // Limitar longitud
                if(this.value.length > 15) this.value = this.value.slice(0, 15);
            ''',
            'onkeypress': '''
                // Prevenir entrada de letras y caracteres especiales no permitidos
                const charCode = event.which || event.keyCode;
                const char = String.fromCharCode(charCode);
                const allowedChars = /[0-9+\-\s\(\)]/;
                if (!allowedChars.test(char) && charCode !== 8 && charCode !== 9) {
                    event.preventDefault();
                    return false;
                }
            ''',
            'onpaste': '''
                // Limpiar contenido pegado
                setTimeout(() => {
                    this.value = this.value.replace(/[^0-9+\-\s\(\)]/g, '');
                    if(this.value.length > 15) this.value = this.value.slice(0, 15);
                }, 1);
            '''
        }), 
        label='Teléfono',
        help_text='Solo números, espacios, guiones y paréntesis. Ej: +54 381 123-4567'
    )
    
    nombre = forms.CharField(
        max_length=100,
        min_length=2,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: Distribuidora San Martín',
            'class': 'form-control',
            'maxlength': '100',
            'oninput': '''
                // Permitir solo letras, números, espacios y algunos caracteres especiales
                this.value = this.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s\.\-&]/g, '');
                // Capitalizar primera letra de cada palabra
                this.value = this.value.replace(/\b\w/g, l => l.toUpperCase());
                // Limitar longitud
                if(this.value.length > 100) this.value = this.value.slice(0, 100);
            ''',
            'onkeypress': '''
                // Prevenir entrada de caracteres no permitidos
                const charCode = event.which || event.keyCode;
                const char = String.fromCharCode(charCode);
                const allowedChars = /[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s\.\-&]/;
                if (!allowedChars.test(char) && charCode !== 8 && charCode !== 9) {
                    event.preventDefault();
                    return false;
                }
            ''',
            'onpaste': '''
                // Limpiar contenido pegado
                setTimeout(() => {
                    this.value = this.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s\.\-&]/g, '');
                    this.value = this.value.replace(/\b\w/g, l => l.toUpperCase());
                    if(this.value.length > 100) this.value = this.value.slice(0, 100);
                }, 1);
            '''
        }),
        label='Nombre del Proveedor',
        help_text='Solo letras, números y caracteres básicos (. - &)'
    )
    
    class Meta:
        model = ProveedorProducto
        fields = ('nombre', 'telefono')
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '')
        
        # Remover espacios y caracteres de formato para validación
        telefono_limpio = re.sub(r'[^0-9]', '', telefono)
        
        # Validar que tenga al menos 8 dígitos
        if len(telefono_limpio) < 8:
            raise ValidationError('El teléfono debe tener al menos 8 dígitos.')
        
        # Validar que no tenga más de 15 dígitos
        if len(telefono_limpio) > 15:
            raise ValidationError('El teléfono no puede tener más de 15 dígitos.')
        
        # Validar que solo contenga números y caracteres permitidos
        if not re.match(r'^[0-9+\-\s\(\)]+$', telefono):
            raise ValidationError('El teléfono solo puede contener números, espacios, guiones y paréntesis.')
        
        return telefono.strip()
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre', '')
        
        # Validar que no esté vacío después de strip
        if not nombre.strip():
            raise ValidationError('El nombre del proveedor es obligatorio.')
        
        # Validar longitud mínima
        if len(nombre.strip()) < 2:
            raise ValidationError('El nombre debe tener al menos 2 caracteres.')
        
        # Validar que no sean solo números
        if nombre.strip().isdigit():
            raise ValidationError('El nombre no puede ser solo números.')
        
        # Validar caracteres permitidos
        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ0-9\s\.\-&]+$', nombre):
            raise ValidationError('El nombre solo puede contener letras, números y caracteres básicos (. - &).')
        
        # Validar que no tenga espacios múltiples
        if '  ' in nombre:
            raise ValidationError('El nombre no puede tener espacios múltiples.')
        
        return nombre.strip().upper()
    
    def clean(self):
        cleaned_data = super().clean()
        nombre = cleaned_data.get('nombre')
        telefono = cleaned_data.get('telefono')
        
        # Validaciones adicionales entre campos si es necesario
        if nombre and telefono:
            # Evitar que el nombre sea igual al teléfono
            if nombre.replace(' ', '') == re.sub(r'[^0-9]', '', telefono):
                raise ValidationError('El nombre y el teléfono no pueden ser iguales.')
        
        return cleaned_data

class AperturaCajaForm(forms.Form):
    monto_inicial = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        max_value=Decimal('999999.00'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00',
            'step': '0.01',
            'min': '0.01',
            'max': '999999.00'
        }),
        label='Monto Inicial',
        help_text='Ingrese el monto con el que iniciará la caja'
    )
    
    def clean_monto_inicial(self):
        monto = self.cleaned_data['monto_inicial']
        if monto <= 0:
            raise forms.ValidationError('El monto debe ser mayor a 0')
        if monto > 999999:
            raise forms.ValidationError('El monto no puede exceder $999,999.00')
        return monto
    

class IngresarDineroForm(forms.Form):
    tipo = forms.ChoiceField(choices=[('INGRESO', 'Ingreso')])
    cantidad=forms.DecimalField(max_digits=10,decimal_places=2, min_value=0, required=True)
    descripcion = forms.CharField(widget=forms.Textarea, required=False, label="Descripción")

class RetirarDineroForm(forms.Form):
    tipo = forms.ChoiceField(choices=[('RETIRO', 'Retiro')])
    cantidad=forms.DecimalField(max_digits=10,decimal_places=2, min_value=0, required=True)
    descripcion = forms.CharField(widget=forms.Textarea, required=False, label="Descripción")

class ClienteForm(forms.ModelForm):
    dni = forms.CharField(max_length=8, widget= forms.NumberInput(attrs={'max_length': '8', 'oninput': "this.value=this.value.slice(0,8)", 'placeholder': 'Ingrese su DNI'}), label='DNI')
    telefono = forms.CharField(max_length=10, widget= forms.NumberInput(attrs={'max_length': '10', 'oninput': "this.value=this.value.slice(0,10)" , 'placeholder':'Ingrese Teléfono'}), label='Teléfono')
    nombre = forms.CharField(widget=forms.TextInput(attrs={'oninput': "this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ\\s]/g, '')",'placeholder': 'Ingrese su nombre'}),label='Nombre')
    apellido = forms.CharField(widget=forms.TextInput(attrs={'oninput': "this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ\\s]/g, '')",'placeholder': 'Ingrese su apellido'}),label='apellido')
    correo = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Ingrese su correo electrónico'} ), label='Correo Electrónico' )
    class Meta:
        model= Cliente
        fields= ("dni","nombre","apellido","correo","telefono")

#probando formulario de registro

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'oninput': "this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ\\s]/g, '')",'placeholder': 'Ingrese su nombre'}),label='Nombre', required=True)
    last_name = forms.CharField(widget=forms.TextInput(attrs={'oninput': "this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ\\s]/g, '')",'placeholder': 'Ingrese su apellido'}),label='Apellido', required= True)
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'Ingrese su correo electrónico'} ), label='Correo Electrónico', required=True)
    group = forms.ModelChoiceField(label='Tipo de usuario', queryset=Group.objects.all(), required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'group',)
class UserModifyForm(forms.ModelForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'oninput': "this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ\\s]/g, '')",'placeholder': 'Ingrese su nombre'}),label='Nombre', required=True)
    last_name = forms.CharField(widget=forms.TextInput(attrs={'oninput': "this.value=this.value.replace(/[^A-Za-zÁÉÍÓÚáéíóúÑñ\\s]/g, '')",'placeholder': 'Ingrese su apellido'}),label='apellido', required= True)
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'Ingrese su correo electrónico'} ), label='Correo Electrónico', required=True)
    group = forms.ModelChoiceField(label='Tipo de usuario', queryset=Group.objects.all(), required=True)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'group','is_active',)

