import requests
import paramiko
import digitalocean
import smtplib
import time
import schedule
import os
from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env.development')
load_dotenv(dotenv_path)

EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
EMAIL_HOST_SERVER = os.environ.get('EMAIL_HOST_SERVER')
EMAIL_HOST_PORT = os.environ.get('EMAIL_HOST_PORT')
DIGITAL_OCEAN_SANDBOX_SERVER_IP = os.environ.get('DIGITAL_OCEAN_SANDBOX_SERVER_IP')
DIGITAL_OCEAN_SANDBOX_SERVER_PORT = os.environ.get('DIGITAL_OCEAN_SANDBOX_SERVER_PORT')
DIGITAL_OCEAN_TOKEN = os.environ.get('DIGITAL_OCEAN_TOKEN')
DIGITAL_OCEAN_DROPLET_ID = os.environ.get('DIGITAL_OCEAN_DROPLET_ID')
SSH_USERNAME = os.environ.get('SSH_USERNAME')
SSH_KEY_FILENAME = os.environ.get('SSH_KEY_FILENAME')


def send_notification(email_msg):
    print('Sending an email...')

    with smtplib.SMTP(EMAIL_HOST_SERVER, EMAIL_HOST_PORT) as smtp:
        smtp.starttls()
        smtp.ehlo()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        message = f'Subject: Application is Down\n{email_msg}'
        smtp.sendmail(EMAIL_ADDRESS, EMAIL_ADDRESS, message)


def restart_container():
    print('Restarting the application...')

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=DIGITAL_OCEAN_SANDBOX_SERVER_IP, username=SSH_USERNAME, key_filename=SSH_KEY_FILENAME)
    ssh.exec_command('systemctl restart docker')
    stdin, stdout, stderr = ssh.exec_command("docker ps -a | grep -v IMAGE | awk '$2 ~ /nginx/ {print $1}'")
    start_container = f'docker start {stdout.read().decode()}'
    ssh.exec_command(start_container)
    ssh.close()


def restart_server_and_container():
    print("Rebooting the server...")

    manager = digitalocean.Manager(token=DIGITAL_OCEAN_TOKEN)
    nginx_server = manager.get_droplet(droplet_id=DIGITAL_OCEAN_DROPLET_ID)
    nginx_server.reboot()

    while True:
        nginx_server = manager.get_droplet(droplet_id=DIGITAL_OCEAN_DROPLET_ID)
        print(f'Nginx Server Status: {nginx_server.status}')
        if nginx_server.status == 'active':
            time.sleep(20)
            restart_container()
            break


def monitor_application():
    try:
        server_url = f'http://{DIGITAL_OCEAN_SANDBOX_SERVER_IP}:{DIGITAL_OCEAN_SANDBOX_SERVER_PORT}'
        response = requests.get(server_url)

        if response.status_code == 200:
            print('Application is running successfully!')
        else:
            print('Application is down - Please debug!')

            msg = f'Application returned status code: {response.status_code}'
            send_notification(msg)

            restart_container()

    except Exception as ex:
        print(f'Connection error happened: {ex}')

        msg = f'Application is not accessible'
        send_notification(msg)

        restart_server_and_container()


schedule.every(5).seconds.do(monitor_application)

while True:
    schedule.run_pending()
