from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def notify_dashboard(user_ids):
    channel_layer = get_channel_layer()
    for uid in set(user_ids):
        async_to_sync(channel_layer.group_send)(
            f"dashboard_{uid}",
            {
                "type": "dashboard_update",
                "data": {"action": "refresh"}
            }
        )


def notify_chat(thread_id, payload):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{thread_id}",
        {
            "type": "chat_message",
            "message": payload
        }
    )