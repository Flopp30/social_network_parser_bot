from user.models import User


async def check_bot_context(update, context, force_update: bool = False):
    if not context.user_data.get('user') or force_update:
        user, _ = await User.objects.aget_or_create(
            chat_id=update.effective_chat.id,
            defaults={
                'username': update.effective_chat.username
            }
        )
        context.user_data['user'] = user
