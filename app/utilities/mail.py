from typing import Union, List, Dict
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from fastapi import BackgroundTasks, UploadFile
from os import getenv


class EmailSender:
    def __init__(self):
        self.conf = ConnectionConfig(
            MAIL_USERNAME=getenv("MAIL_USERNAME"),
            MAIL_PASSWORD=getenv("MAIL_PASSWORD"),
            MAIL_FROM=getenv("MAIL_FROM"),
            MAIL_PORT=getenv("MAIL_PORT"),
            MAIL_SERVER=getenv("MAIL_SERVER"),
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            MAIL_DEBUG=0,
            TEMPLATE_FOLDER=getenv("TEMPLATE_FOLDER"),
        )
        self.mail = FastMail(self.conf)
        self.templates = {}

    def load_template(self, template_name: str):
        temp = self.conf.template_engine()
        self.templates[template_name] = temp.get_template(template_name)

    def send_email_background(
        self,
        background_tasks: BackgroundTasks,
        email: str,
        subject: str,
        template_name: str,
        attachments: List[Union[Dict, str, UploadFile]] = [],
        **kwargs
    ):
        if template_name not in self.templates:
            self.load_template(template_name)
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            subtype="html",
            template_body=self.templates[template_name].render(**kwargs),
            attachments=attachments,
        )
        background_tasks.add_task(self.mail.send_message, message)

    async def send_email(
        self,
        email: str,
        subject: str,
        template_name: str,
        attachments: List[Union[Dict, str, UploadFile]] = [],
        **kwargs
    ):
        if template_name not in self.templates:
            self.load_template(template_name)
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            subtype="html",
            template_body=self.templates[template_name].render(**kwargs),
            attachments=attachments,
        )
        await self.mail.send_message(message)
