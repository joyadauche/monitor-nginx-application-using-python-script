# Pre-requisites
- Set up a digital ocean droplet running that runs nginx docker container
- Ensure you can log in over the network via SSH
- Create a digital ocean token
- Set up an email password for this application. For example, if your email host server is gmail, set it up via https://myaccount.google.com/apppasswords

# Run application
- Run `pip install -r requirements.txt`
- Create a .env.development with appropriate values using the .env.development.template file
- Run `python main.py`