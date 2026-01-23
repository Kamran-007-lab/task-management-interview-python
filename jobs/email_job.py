import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from celery import Celery
from datetime import datetime
from models.user import User
from config.database import SessionLocal

celery_app = Celery(
    'email_queue',
    broker=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/0",
    backend=f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}/0"
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    result_expires=300,
    worker_prefetch_multiplier=1,
)

@celery_app.task(
    name='send-email',
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3},
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True
)
def send_email_task(self, job_data):
    db = SessionLocal()
    try:
        user_id = job_data.get('userId')
        task_id = job_data.get('taskId')
        task_title = job_data.get('taskTitle')
        email_type = job_data.get('type')

        print(f'Processing email job for user {user_id}')
        print(f"Sending email to: {job_data.get('email')}")

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise Exception('User not found')

        if email_type == 'task_completion':
            subject = f'Task Completed: {task_title}'
            html_content = f'''
        <h2>Task Completed!</h2>
        <p>Hi {user.username},</p>
        <p>Your task "<strong>{task_title}</strong>" has been marked as completed.</p>
        <p>Task ID: {task_id}</p>
        <p>Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <br>
        <p>Best regards,<br>Task Management System</p>
      '''
        else:
            subject = 'Task Notification'
            html_content = f'<p>Hi {user.username}, you have a task notification.</p>'

        msg = MIMEMultipart('alternative')
        msg['From'] = os.getenv('SMTP_USER')
        msg['To'] = job_data.get('email')
        msg['Subject'] = subject

        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)

        smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        smtp_user = os.getenv('SMTP_USER')
        smtp_password = os.getenv('SMTP_PASSWORD')

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        print(f'Email sent successfully to {job_data.get("email")}')
        return {'success': True, 'messageId': self.request.id}

    except Exception as error:
        print(f'Email job failed: {error}')
        db.close()
        raise error
    finally:
        db.close()

async def add_email_job(job_data: dict):
    try:
        job = send_email_task.apply_async(
            args=[job_data],
            retry=True,
            retry_policy={
                'max_retries': 3,
                'interval_start': 5,
                'interval_step': 5,
                'interval_max': 15,
            }
        )

        print(f'Email job added to queue: {job.id}')
        return job
    except Exception as error:
        print(f'Failed to add email job: {error}')
        raise error

async def init_job_queue():
    print('Email job queue initialized')
    return celery_app

async def close_job_queue():
    celery_app.control.shutdown()
    print('Email job queue closed')
