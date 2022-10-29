from django.core.mail import send_mail

send_mail(
    'Тема письма',
    'Текст письма.',
    'from@example.com',
    ['to@example.com'],
    fail_silently=False,
)
