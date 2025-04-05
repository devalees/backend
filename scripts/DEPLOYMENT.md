# Deployment Guide for Django Project on Amazon EC2

## Prerequisites

1. AWS Account with appropriate permissions
2. Domain name (optional but recommended)
3. AWS CLI configured on your local machine
4. SSH key pair for EC2 access

## Step 1: Launch EC2 Instance

1. Go to AWS Console > EC2 > Launch Instance
2. Choose Ubuntu 22.04 LTS AMI
3. Select instance type (t2.micro for testing, t2.medium for production)
4. Configure instance details:
   - VPC: Default or your custom VPC
   - Auto-assign Public IP: Enable
5. Add storage (minimum 8GB)
6. Configure security group:
   - SSH (port 22)
   - HTTP (port 80)
   - HTTPS (port 443)
   - Custom TCP (port 8000 for development)
7. Review and launch
8. Select your SSH key pair

## Step 2: Set Up AWS Services

### RDS Setup
1. Create PostgreSQL database
2. Note down database endpoint, username, and password
3. Update security group to allow EC2 instance access

### S3 Setup
1. Create S3 bucket for media files
2. Configure CORS policy
3. Create IAM user with S3 access
4. Note down access key and secret

### Elasticache Setup (Optional)
1. Create Redis cluster
2. Note down endpoint and port
3. Update security group to allow EC2 instance access

## Step 3: Deploy Application

1. SSH into your EC2 instance:
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-public-ip
   ```

2. Clone your repository:
   ```bash
   git clone https://github.com/your-repo.git /var/www/project
   ```

3. Make the deployment script executable:
   ```bash
   chmod +x scripts/deploy.sh
   ```

4. Run the deployment script:
   ```bash
   ./scripts/deploy.sh
   ```

5. Update environment variables in `/var/www/project/.env`:
   - Replace `your_secret_key_here` with a secure secret key
   - Update database credentials
   - Add AWS credentials
   - Set your domain name in ALLOWED_HOSTS

## Step 4: SSL Configuration (Optional but Recommended)

1. Install Certbot:
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   ```

2. Obtain SSL certificate:
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```

3. Configure automatic renewal:
   ```bash
   sudo certbot renew --dry-run
   ```

## Step 5: Monitoring and Maintenance

1. Set up CloudWatch for monitoring
2. Configure log rotation
3. Set up automated backups
4. Configure auto-scaling if needed

## Troubleshooting

1. Check Nginx logs:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

2. Check application logs:
   ```bash
   sudo tail -f /var/log/project.err.log
   sudo tail -f /var/log/project.out.log
   ```

3. Check supervisor status:
   ```bash
   sudo supervisorctl status
   ```

## Security Considerations

1. Regularly update system packages
2. Use strong passwords and keys
3. Implement proper backup strategy
4. Monitor for security vulnerabilities
5. Use AWS WAF for additional protection
6. Implement proper IAM roles and policies

## Scaling Considerations

1. Use AWS Auto Scaling Groups
2. Implement database read replicas
3. Use Elastic Load Balancer
4. Configure CloudFront for CDN
5. Implement proper caching strategy

## Backup and Recovery

1. Set up automated database backups
2. Configure S3 versioning for media files
3. Document recovery procedures
4. Test backup restoration regularly

## Maintenance

1. Schedule regular security updates
2. Monitor resource usage
3. Review and rotate credentials
4. Update dependencies regularly
5. Monitor application performance 