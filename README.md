# Fuel Refund Institute - Django Application

A professional Django web application for managing fuel tax refund processes.

## 🚀 Production Deployment Guide

### Prerequisites
- Ubuntu 20.04+ VPS (Hostinger recommended)
- Domain name: `fuelrefundinstitute.com`
- SSH access to server
- Root or sudo privileges

### Quick Deployment

1. **Clone the repository:**
```bash
cd /var/www
sudo git clone https://github.com/MOCDATA-PTY/OTP-Fuel-Refund.git fuelrefund
sudo chown -R www-data:www-data fuelrefund
```

2. **Run the deployment script:**
```bash
cd fuelrefund
sudo chmod +x deploy.sh
sudo ./deploy.sh
```

3. **Configure environment variables:**
```bash
sudo nano /var/www/fuelrefund/.env
```

### Manual Deployment Steps

#### 1. System Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib redis-server supervisor certbot python3-certbot-nginx
```

#### 2. Database Setup
```bash
# Create PostgreSQL database
sudo -u postgres psql -c "CREATE DATABASE fuelrefund_db;"
sudo -u postgres psql -c "CREATE USER fuelrefund_user WITH PASSWORD 'your_secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE fuelrefund_db TO fuelrefund_user;"
```

#### 3. Application Setup
```bash
# Create virtual environment
cd /var/www/fuelrefund
sudo -u www-data python3 -m venv venv

# Install dependencies
sudo -u www-data venv/bin/pip install -r requirements.txt

# Collect static files
sudo -u www-data venv/bin/python manage.py collectstatic --noinput

# Run migrations
sudo -u www-data venv/bin/python manage.py migrate

# Create superuser
sudo -u www-data venv/bin/python manage.py createsuperuser
```

#### 4. Web Server Configuration
```bash
# Use existing Nginx configuration
# The server already has Nginx configured for fuelrefundinstitute.com
# Just ensure the application is running on port 8000

# Test Nginx configuration
sudo nginx -t
sudo systemctl restart nginx
```

#### 5. Gunicorn Setup
```bash
# Copy Gunicorn configuration
sudo cp gunicorn.conf.py /var/www/fuelrefund/

# Setup Supervisor
sudo tee /etc/supervisor/conf.d/fuelrefund.conf > /dev/null <<EOF
[program:fuelrefund]
command=/var/www/fuelrefund/venv/bin/gunicorn --config /var/www/fuelrefund/gunicorn.conf.py mysite.wsgi:application
directory=/var/www/fuelrefund
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/fuelrefund/gunicorn.log
EOF

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start fuelrefund
```

#### 6. SSL Certificate
```bash
# Obtain SSL certificate
sudo certbot --nginx -d fuelrefundinstitute.com -d www.fuelrefundinstitute.com --non-interactive --agree-tos --email fuelrefundinstitute@gmail.com
```

### Environment Variables

Create `/var/www/fuelrefund/.env` with the following:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=fuelrefundinstitute.com,www.fuelrefundinstitute.com,167.88.43.168

# Database Settings
DB_NAME=fuelrefund_db
DB_USER=fuelrefund_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Email Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=fuelrefundinstitute@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
DEFAULT_FROM_EMAIL=Fuel Refund Institute <fuelrefundinstitute@gmail.com>

# Redis Settings
REDIS_URL=redis://localhost:6379/0

# Security Settings
CSRF_TRUSTED_ORIGINS=https://fuelrefundinstitute.com,https://www.fuelrefundinstitute.com
```

### File Structure
```
/var/www/fuelrefund/
├── manage.py
├── requirements.txt
├── gunicorn.conf.py
├── .env
├── static/          # Collected static files
├── media/           # User uploads
├── venv/            # Virtual environment
└── logs/            # Application logs
```

### Management Commands

#### Restart Services
```bash
sudo /var/www/fuelrefund/restart.sh
```

#### Create Backup
```bash
sudo /var/www/fuelrefund/backup.sh
```

#### Monitor Logs
```bash
# Gunicorn logs
sudo tail -f /var/log/fuelrefund/gunicorn.log

# Nginx logs
sudo tail -f /var/log/nginx/fuelrefund_access.log
sudo tail -f /var/log/nginx/fuelrefund_error.log
```

#### Update Application
```bash
cd /var/www/fuelrefund
sudo git pull
sudo -u www-data venv/bin/pip install -r requirements.txt
sudo -u www-data venv/bin/python manage.py collectstatic --noinput
sudo -u www-data venv/bin/python manage.py migrate
sudo supervisorctl restart fuelrefund
```

### Security Checklist

- [ ] SSL certificate installed
- [ ] Firewall configured (UFW)
- [ ] Database password changed
- [ ] Django secret key updated
- [ ] Debug mode disabled
- [ ] Admin password changed
- [ ] Regular backups scheduled
- [ ] Log rotation configured

### Troubleshooting

#### Images Not Loading
1. Check file permissions: `sudo chown -R www-data:www-data /var/www/fuelrefund/media`
2. Verify Nginx configuration: `sudo nginx -t`
3. Check static files: `sudo -u www-data python manage.py collectstatic`

#### Database Connection Issues
1. Verify PostgreSQL is running: `sudo systemctl status postgresql`
2. Check database credentials in `.env`
3. Test connection: `sudo -u postgres psql -d fuelrefund_db`

#### Gunicorn Issues
1. Check logs: `sudo tail -f /var/log/fuelrefund/gunicorn.log`
2. Restart service: `sudo supervisorctl restart fuelrefund`
3. Check configuration: `sudo supervisorctl status fuelrefund`

### Support

For technical support, contact:
- Email: fuelrefundinstitute@gmail.com
- Phone: +1 (424) 222-5290

### License

This project is proprietary software owned by Magnum Opus Consultants. 