"""
Utilidad simple para impresión térmica - Solo Cierre de Caja
"""

from escpos.printer import Usb, Network, File
from django.conf import settings


class ThermalPrinter:
    """Clase para manejar impresión térmica"""
    
    def __init__(self, printer_type='usb', paper_width=58, **kwargs):
        """
        Inicializar impresora
        
        Args:
            printer_type: 'usb', 'network', o 'file'
            paper_width: 58 o 80 (mm de ancho del papel)
        """
        self.printer = None
        self.width = 32 if paper_width == 58 else 48
        
        try:
            if printer_type == 'usb':
                self.printer = Usb(
                    kwargs.get('vendor_id', 0x04b8),
                    kwargs.get('product_id', 0x0e15)
                )
            elif printer_type == 'network':
                self.printer = Network(
                    kwargs.get('host', '192.168.1.100'),
                    kwargs.get('port', 9100)
                )
            elif printer_type == 'file':
                output_path = kwargs.get('output_path', '/tmp/thermal_print.bin')
                
                # Crear el directorio si no existe
                import os
                output_dir = os.path.dirname(output_path)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)
                
                # Abrir archivo en modo escritura
                self.printer = File(output_path, auto_flush=True)
        except Exception as e:
            print(f"Error al conectar con impresora: {e}")
            raise
    
    def _line(self, char="-"):
        """Crear línea divisoria"""
        return char * self.width
    
    def _format_price(self, amount):
        """Formatear precio"""
        return f"${amount:,.2f}"
    
    def print_cierre_caja(self, caja, empleado, fecha_cierre):
        """
        Imprimir cierre de caja
        """
        try:
            # ENCABEZADO
            self.printer.set(align='center', bold=True, double_width=True, double_height=True)
            self.printer.text("CIERRE DE CAJA\n")
            
            self.printer.set(align='center', bold=False, double_width=False, double_height=False)
            self.printer.text(f"{caja.sucursal.nombre}\n")
            self.printer.text(self._line() + "\n")
            
            # INFORMACIÓN
            self.printer.set(align='left')
            caja_numero = str(caja.id).zfill(6)
            fecha_str = fecha_cierre.strftime("%d/%m/%Y %H:%M")
            
            self.printer.text(f"Caja N: {caja_numero}\n")
            self.printer.text(f"Fecha Cierre: {fecha_str}\n")
            self.printer.text(f"Empleado: {empleado.first_name} {empleado.last_name}\n")
            self.printer.text(f"Usuario: {empleado.username}\n")
            self.printer.text(self._line() + "\n")
            
            # RESUMEN FINANCIERO
            self.printer.set(bold=True)
            self.printer.text("RESUMEN FINANCIERO\n")
            self.printer.set(bold=False)
            self.printer.text(self._line() + "\n")
            
            # Monto inicial
            self.printer.text(f"Monto Inicial:\n")
            self.printer.set(align='right')
            self.printer.text(f"{self._format_price(caja.monto_inicial)}\n")
            
            # Total ingresado
            self.printer.set(align='left')
            self.printer.text(f"Total Ingresado:\n")
            self.printer.set(align='right')
            self.printer.text(f"+{self._format_price(caja.total_ingresado)}\n")
            
            # Total egresado
            self.printer.set(align='left')
            self.printer.text(f"Total Egresado:\n")
            self.printer.set(align='right')
            self.printer.text(f"-{self._format_price(caja.total_egresado)}\n")
            
            self.printer.set(align='left')
            self.printer.text(self._line("=") + "\n")
            
            # SALDO TOTAL
            self.printer.set(align='center', bold=True, double_width=True, double_height=True)
            self.printer.text("SALDO TOTAL\n")
            self.printer.text(f"{self._format_price(caja.saldo_total)}\n")
            self.printer.set(bold=False, double_width=False, double_height=False)
            
            self.printer.text(self._line("=") + "\n")
            
            # FIRMAS
            self.printer.set(align='center')
            self.printer.text("\n\n\n")
            self.printer.text("_______________________\n")
            self.printer.text("Firma del Empleado\n")
            self.printer.text("\n\n\n")
            self.printer.text("_______________________\n")
            self.printer.text("Firma del Supervisor\n")
            self.printer.text("\n")
            
            # Cortar papel
            self.printer.cut()
            
            return True
            
        except Exception as e:
            print(f"Error al imprimir cierre de caja: {e}")
            return False
    
    def close(self):
        """Cerrar conexión con la impresora"""
        if self.printer:
            try:
                self.printer.close()
            except:
                pass


def get_printer_config():
    """Obtener configuración de impresora desde settings.py"""
    return getattr(settings, 'THERMAL_PRINTER', {
        'type': 'file',
        'paper_width': 58,
        'output_path': '/tmp/thermal_print.bin'
    })


def create_printer():
    """Crear instancia de impresora con la configuración de settings"""
    config = get_printer_config()
    printer_type = config.pop('type', 'file')
    paper_width = config.pop('paper_width', 58)
    return ThermalPrinter(printer_type=printer_type, paper_width=paper_width, **config)