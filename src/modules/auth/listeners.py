from blinker import Namespace
from src.modules.auth import tasks
auth_signals = Namespace()

user_register = auth_signals.signal("user-register")

@user_register.connect
def send_activation_email_task(sender, user_email):
    tasks.send_activation_email_task.delay(user_email)

