import json
from channels.generic.websocket import AsyncWebsocketConsumer

class NotificacionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("notificaciones", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("notificaciones", self.channel_name)

    async def notificacion_pago(self, event):
        await self.send(text_data=json.dumps({
            'type': 'pago_recibido',
            'data': event['data']
        }))