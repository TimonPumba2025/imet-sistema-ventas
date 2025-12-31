"""
UTILIDADES PARA WHATSAPP - VERSION GRATUITA
Genera enlaces directos de WhatsApp (Click to Chat)
No requiere API ni costos
"""

from urllib.parse import quote


class WhatsAppLink:
    """Genera enlaces directos de WhatsApp"""
    
    @staticmethod
    def generar_link(telefono, mensaje):
        """
        Genera enlace de WhatsApp con mensaje pre-escrito
        
        Args:
            telefono (str): Número (ej: "3874123456")
            mensaje (str): Mensaje a enviar
            
        Returns:
            str: URL de WhatsApp
        """
        # Limpiar número
        telefono_limpio = ''.join(filter(str.isdigit, telefono))
        
        # Agregar código de país (Argentina)
        if not telefono_limpio.startswith('54'):
            telefono_limpio = '54' + telefono_limpio
        
        # Codificar mensaje para URL
        mensaje_codificado = quote(mensaje)
        
        # Generar link: https://wa.me/5493874123456?text=Mensaje
        return f"https://wa.me/{telefono_limpio}?text={mensaje_codificado}"
    
    @staticmethod
    def mensaje_puntos_ganados(cliente, puntos_ganados, total_puntos, monto_compra=None):
        """Genera link con mensaje de puntos ganados"""
        if monto_compra:
            mensaje = (
                f"¡Hola {cliente.nombre}! 🎉\n\n"
                f"Has ganado *{puntos_ganados} puntos* en tu compra de ${monto_compra}.\n\n"
                f"Ahora tienes *{total_puntos} puntos* acumulados.\n\n"
                f"¡Gracias por tu preferencia! 🛍️"
            )
        else:
            mensaje = (
                f"¡Hola {cliente.nombre}! 🎉\n\n"
                f"Has ganado *{puntos_ganados} puntos*.\n\n"
                f"Total: *{total_puntos} puntos*\n\n"
                f"¡Gracias!"
            )
        
        return WhatsAppLink.generar_link(cliente.telefono, mensaje)
    
    @staticmethod
    def mensaje_consulta_puntos(cliente):
        """Genera link para enviar consulta de puntos"""
        mensaje = (
            f"¡Hola {cliente.nombre}!\n\n"
            f"Tienes *{cliente.puntos_actuales} puntos* disponibles.\n\n"
            f"¡Ven a canjearlos!"
        )
        return WhatsAppLink.generar_link(cliente.telefono, mensaje)
    
    @staticmethod
    def mensaje_personalizado(cliente, texto):
        """Genera link con mensaje personalizado"""
        # Reemplazar variables
        mensaje = texto.replace('{nombre}', cliente.nombre)
        mensaje = mensaje.replace('{puntos}', str(cliente.puntos_actuales))
        
        return WhatsAppLink.generar_link(cliente.telefono, mensaje)


def procesar_puntos_venta(venta, empleado=None):
    """
    Procesa puntos de una venta y genera link de WhatsApp
    
    Args:
        venta: Objeto Venta
        empleado: Usuario que procesa (opcional)
        
    Returns:
        dict: Información del procesamiento + link WhatsApp
    """
    try:
        # Validar que tenga cliente
        if not venta.cliente:
            return {
                'success': False,
                'message': 'La venta no tiene cliente asociado',
                'puntos_otorgados': 0,
                'whatsapp_link': None
            }
        
        # Calcular puntos
        from .models import RangoPuntos
        puntos = RangoPuntos.calcular_puntos(venta.total)
        
        if puntos == 0:
            return {
                'success': True,
                'message': 'El monto no califica para puntos',
                'puntos_otorgados': 0,
                'whatsapp_link': None
            }
        
        # Agregar puntos al cliente
        venta.cliente.agregar_puntos(
            cantidad=puntos,
            descripcion=f"Compra - Ticket #{venta.id} - ${venta.total}",
            empleado=empleado
        )
        
        # Actualizar venta
        venta.puntos_otorgados = puntos
        venta.save()
        
        # Generar link de WhatsApp
        whatsapp_link = WhatsAppLink.mensaje_puntos_ganados(
            cliente=venta.cliente,
            puntos_ganados=puntos,
            total_puntos=venta.cliente.puntos_actuales,
            monto_compra=venta.total
        )
        
        return {
            'success': True,
            'message': 'Puntos procesados correctamente',
            'puntos_otorgados': puntos,
            'total_puntos': venta.cliente.puntos_actuales,
            'whatsapp_link': whatsapp_link,
            'cliente_nombre': venta.cliente.nombre
        }
        
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Error en procesar_puntos_venta: {str(e)}")
        return {
            'success': False,
            'message': f"Error: {str(e)}",
            'puntos_otorgados': 0,
            'whatsapp_link': None
        }