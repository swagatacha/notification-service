from handlers.email_handler import Email
from handlers.sms_handler import Sms
from handlers.push_handler import Push

def process_message(message):
    """
    Process the message and send notifications accordingly.
    """
    print(message)
    # notification_type = message.get("type")
    # recipient = message.get("recipient")
    # data = message.get("data")
    
    # # Fetch template from MongoDB
    # template = get_template(notification_type)

    # # Route message to appropriate handler
    # if notification_type == "email":
    #     send_email(recipient, template, data)
    # elif notification_type == "sms":
    #     send_sms(recipient, template, data)
    # elif notification_type == "push":
    #     send_push(recipient, template, data)
    # elif notification_type == "whatsapp":
    #     send_whatsapp(recipient, template, data)
    # else:
    #     print(f"Unknown notification type: {notification_type}")
