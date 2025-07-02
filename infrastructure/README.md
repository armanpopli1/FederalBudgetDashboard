# Federal Budget Dashboard - Infrastructure Setup

This directory contains scripts and configuration for setting up the AWS infrastructure for the Federal Budget Dashboard.

## 🏗️ Infrastructure Overview

- **RDS PostgreSQL**: Database for budget data and bill changes
- **VPC**: Private network with proper security groups
- **Secrets Manager**: Secure storage of database credentials
- **Lambda**: Will host the FastAPI backend (deployed later)

## 📋 Prerequisites

### AWS Account Setup
1. **AWS Account** with programmatic access
2. **AWS CLI** installed and configured
3. **Appropriate IAM permissions** (see below)

### Required IAM Permissions
Your AWS user/role needs these permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:*",
                "rds:*",
                "secretsmanager:*"
            ],
            "Resource": "*"
        }
    ]
}
```

## 🚀 Setup Process

### Step 1: Configure AWS CLI
```bash
# Install AWS CLI if not already installed
curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
sudo installer -pkg AWSCLIV2.pkg -target /

# Configure with your credentials
aws configure
```

**You'll need to provide:**
- AWS Access Key ID
- AWS Secret Access Key  
- Default region: `us-east-1`
- Default output format: `json`

### Step 2: Run RDS Setup Script
```bash
# Make the script executable
chmod +x setup-rds.sh

# Run the setup (takes 10-15 minutes)
./setup-rds.sh
```

This script will:
1. ✅ Create VPC and subnets
2. ✅ Set up security groups
3. ✅ Create RDS PostgreSQL instance
4. ✅ Store credentials in Secrets Manager
5. ✅ Output configuration for serverless.yml

### Step 3: Test Database Connection
```bash
# Set the DATABASE_URL from script output
export DATABASE_URL='postgresql://budgetuser:PASSWORD@ENDPOINT:5432/federal_budget'

# Test the connection
python test-connection.py
```

## 📊 Cost Breakdown

| Service | Configuration | Monthly Cost |
|---------|---------------|--------------|
| RDS t3.micro | 20GB storage | ~$13-15 |
| VPC | Basic setup | Free |
| Secrets Manager | 1 secret | ~$0.40 |
| **Total** | | **~$13-16/month** |

## 🔧 Configuration Files Updated

After running the setup script, update these files:

### backend/serverless.yml
Replace the placeholder VPC configuration:
```yaml
vpc:
  securityGroupIds:
    - sg-XXXXXXXXX  # Lambda security group ID from script output
  subnetIds:
    - subnet-XXXXXXXX  # Private subnet IDs from script output
    - subnet-YYYYYYYY
```

### Local Development (.env)
Create `backend/.env`:
```bash
DATABASE_URL=postgresql://budgetuser:PASSWORD@ENDPOINT:5432/federal_budget
CORS_ORIGINS=http://localhost:3000
DATABASE_DEBUG=false
```

## 🧪 Testing & Validation

### 1. Connection Test
```bash
cd ../backend
python infrastructure/test-connection.py
```

### 2. Seed Database
```bash
python scripts/seed_database.py
```

### 3. Run Local Server
```bash
python run_local.py
```

### 4. Test API Endpoints
```bash
python test_api.py
```

## 🔒 Security Features

- ✅ **RDS in private subnets** - not publicly accessible
- ✅ **Security groups** restrict access to Lambda only
- ✅ **Secrets Manager** for credential storage
- ✅ **VPC isolation** from internet
- ✅ **Encrypted storage** (RDS default)

## 🚨 Troubleshooting

### Common Issues

**❌ AWS CLI not configured**
```bash
aws configure list
# Should show your access key and region
```

**❌ Permission denied**
- Check your IAM user has EC2, RDS, and Secrets Manager permissions
- Try: `aws sts get-caller-identity` to verify credentials

**❌ RDS creation failed**
- Check region has enough capacity for t3.micro
- Verify subnet group was created successfully

**❌ Connection test fails**
- Ensure DATABASE_URL environment variable is set
- Check RDS instance is in "available" state
- Verify security groups allow connections

### Cleanup Commands
```bash
# Delete RDS instance
aws rds delete-db-instance \
    --db-instance-identifier federal-budget-db \
    --skip-final-snapshot \
    --region us-east-1

# Delete VPC resources (run after RDS is deleted)
aws ec2 delete-vpc --vpc-id vpc-XXXXXXXX --region us-east-1
```

## 📞 Next Steps

After successful RDS setup:

1. ✅ **Update serverless.yml** with VPC configuration
2. ✅ **Test database connection** locally
3. ✅ **Seed database** with sample data
4. ✅ **Deploy Lambda backend** with Serverless Framework
5. ✅ **Build React frontend** 

---

**💡 Tip**: Save the script output! It contains important IDs and connection strings you'll need for deployment. 