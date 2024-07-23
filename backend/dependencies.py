from containers import container


def get_session_manager():
    return container.session_manager()


async def get_message_processor():
    return container.message_processor()
