#!/bin/bash

# Federal Budget Dashboard - RDS Setup Script
# This script creates a PostgreSQL RDS instance with proper VPC configuration

set -e  # Exit on any error

echo "🏗️  Setting up PostgreSQL RDS for Federal Budget Dashboard"
echo "========================================================"

# Configuration variables
DB_NAME="federal_budget"
DB_USERNAME="budgetuser"
DB_INSTANCE_ID="federal-budget-db"
DB_INSTANCE_CLASS="db.t3.micro"
ALLOCATED_STORAGE="20"
REGION="us-east-1"
STAGE="dev"

# Generate a random password
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)

echo "Configuration:"
echo "  Database Name: $DB_NAME"
echo "  Username: $DB_USERNAME"
echo "  Instance ID: $DB_INSTANCE_ID"
echo "  Instance Class: $DB_INSTANCE_CLASS"
echo "  Storage: ${ALLOCATED_STORAGE}GB"
echo "  Region: $REGION"
echo ""

# Step 1: Create VPC (if not exists)
echo "1️⃣  Setting up VPC..."

VPC_ID=$(aws ec2 describe-vpcs \
    --filters "Name=tag:Name,Values=federal-budget-vpc" \
    --query "Vpcs[0].VpcId" \
    --output text \
    --region $REGION 2>/dev/null || echo "None")

if [ "$VPC_ID" = "None" ]; then
    echo "Creating new VPC..."
    VPC_ID=$(aws ec2 create-vpc \
        --cidr-block 10.0.0.0/16 \
        --query "Vpc.VpcId" \
        --output text \
        --region $REGION)
    
    aws ec2 create-tags \
        --resources $VPC_ID \
        --tags Key=Name,Value=federal-budget-vpc \
        --region $REGION
    
    echo "Created VPC: $VPC_ID"
else
    echo "Using existing VPC: $VPC_ID"
fi

# Step 2: Create Internet Gateway
echo "2️⃣  Setting up Internet Gateway..."

IGW_ID=$(aws ec2 describe-internet-gateways \
    --filters "Name=tag:Name,Values=federal-budget-igw" \
    --query "InternetGateways[0].InternetGatewayId" \
    --output text \
    --region $REGION 2>/dev/null || echo "None")

if [ "$IGW_ID" = "None" ]; then
    IGW_ID=$(aws ec2 create-internet-gateway \
        --query "InternetGateway.InternetGatewayId" \
        --output text \
        --region $REGION)
    
    aws ec2 create-tags \
        --resources $IGW_ID \
        --tags Key=Name,Value=federal-budget-igw \
        --region $REGION
    
    aws ec2 attach-internet-gateway \
        --internet-gateway-id $IGW_ID \
        --vpc-id $VPC_ID \
        --region $REGION
    
    echo "Created Internet Gateway: $IGW_ID"
else
    echo "Using existing Internet Gateway: $IGW_ID"
fi

# Step 3: Create Subnets (Private for RDS, Public for NAT)
echo "3️⃣  Setting up Subnets..."

# Private subnet 1 (for RDS)
PRIVATE_SUBNET_1_ID=$(aws ec2 describe-subnets \
    --filters "Name=tag:Name,Values=federal-budget-private-1" \
    --query "Subnets[0].SubnetId" \
    --output text \
    --region $REGION 2>/dev/null || echo "None")

if [ "$PRIVATE_SUBNET_1_ID" = "None" ]; then
    PRIVATE_SUBNET_1_ID=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block 10.0.1.0/24 \
        --availability-zone ${REGION}a \
        --query "Subnet.SubnetId" \
        --output text \
        --region $REGION)
    
    aws ec2 create-tags \
        --resources $PRIVATE_SUBNET_1_ID \
        --tags Key=Name,Value=federal-budget-private-1 \
        --region $REGION
    
    echo "Created Private Subnet 1: $PRIVATE_SUBNET_1_ID"
else
    echo "Using existing Private Subnet 1: $PRIVATE_SUBNET_1_ID"
fi

# Private subnet 2 (for RDS - different AZ)
PRIVATE_SUBNET_2_ID=$(aws ec2 describe-subnets \
    --filters "Name=tag:Name,Values=federal-budget-private-2" \
    --query "Subnets[0].SubnetId" \
    --output text \
    --region $REGION 2>/dev/null || echo "None")

if [ "$PRIVATE_SUBNET_2_ID" = "None" ]; then
    PRIVATE_SUBNET_2_ID=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block 10.0.2.0/24 \
        --availability-zone ${REGION}b \
        --query "Subnet.SubnetId" \
        --output text \
        --region $REGION)
    
    aws ec2 create-tags \
        --resources $PRIVATE_SUBNET_2_ID \
        --tags Key=Name,Value=federal-budget-private-2 \
        --region $REGION
    
    echo "Created Private Subnet 2: $PRIVATE_SUBNET_2_ID"
else
    echo "Using existing Private Subnet 2: $PRIVATE_SUBNET_2_ID"
fi

# Public subnet (for NAT Gateway)
PUBLIC_SUBNET_ID=$(aws ec2 describe-subnets \
    --filters "Name=tag:Name,Values=federal-budget-public" \
    --query "Subnets[0].SubnetId" \
    --output text \
    --region $REGION 2>/dev/null || echo "None")

if [ "$PUBLIC_SUBNET_ID" = "None" ]; then
    PUBLIC_SUBNET_ID=$(aws ec2 create-subnet \
        --vpc-id $VPC_ID \
        --cidr-block 10.0.3.0/24 \
        --availability-zone ${REGION}a \
        --query "Subnet.SubnetId" \
        --output text \
        --region $REGION)
    
    aws ec2 create-tags \
        --resources $PUBLIC_SUBNET_ID \
        --tags Key=Name,Value=federal-budget-public \
        --region $REGION
    
    aws ec2 modify-subnet-attribute \
        --subnet-id $PUBLIC_SUBNET_ID \
        --map-public-ip-on-launch \
        --region $REGION
    
    echo "Created Public Subnet: $PUBLIC_SUBNET_ID"
else
    echo "Using existing Public Subnet: $PUBLIC_SUBNET_ID"
fi

# Step 4: Create DB Subnet Group
echo "4️⃣  Creating DB Subnet Group..."

aws rds create-db-subnet-group \
    --db-subnet-group-name federal-budget-subnet-group \
    --db-subnet-group-description "Subnet group for Federal Budget Dashboard RDS" \
    --subnet-ids $PRIVATE_SUBNET_1_ID $PRIVATE_SUBNET_2_ID \
    --region $REGION 2>/dev/null || echo "DB Subnet Group already exists"

# Step 5: Create Security Groups
echo "5️⃣  Creating Security Groups..."

# RDS Security Group
RDS_SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=federal-budget-rds-sg" \
    --query "SecurityGroups[0].GroupId" \
    --output text \
    --region $REGION 2>/dev/null || echo "None")

if [ "$RDS_SG_ID" = "None" ]; then
    RDS_SG_ID=$(aws ec2 create-security-group \
        --group-name federal-budget-rds-sg \
        --description "Security group for Federal Budget RDS" \
        --vpc-id $VPC_ID \
        --query "GroupId" \
        --output text \
        --region $REGION)
    
    echo "Created RDS Security Group: $RDS_SG_ID"
else
    echo "Using existing RDS Security Group: $RDS_SG_ID"
fi

# Lambda Security Group  
LAMBDA_SG_ID=$(aws ec2 describe-security-groups \
    --filters "Name=group-name,Values=federal-budget-lambda-sg" \
    --query "SecurityGroups[0].GroupId" \
    --output text \
    --region $REGION 2>/dev/null || echo "None")

if [ "$LAMBDA_SG_ID" = "None" ]; then
    LAMBDA_SG_ID=$(aws ec2 create-security-group \
        --group-name federal-budget-lambda-sg \
        --description "Security group for Federal Budget Lambda" \
        --vpc-id $VPC_ID \
        --query "GroupId" \
        --output text \
        --region $REGION)
    
    echo "Created Lambda Security Group: $LAMBDA_SG_ID"
else
    echo "Using existing Lambda Security Group: $LAMBDA_SG_ID"
fi

# Configure security group rules
echo "Configuring security group rules..."

# Allow Lambda to connect to RDS (port 5432)
aws ec2 authorize-security-group-ingress \
    --group-id $RDS_SG_ID \
    --protocol tcp \
    --port 5432 \
    --source-group $LAMBDA_SG_ID \
    --region $REGION 2>/dev/null || echo "RDS ingress rule already exists"

# Allow Lambda outbound to RDS
aws ec2 authorize-security-group-egress \
    --group-id $LAMBDA_SG_ID \
    --protocol tcp \
    --port 5432 \
    --source-group $RDS_SG_ID \
    --region $REGION 2>/dev/null || echo "Lambda egress rule already exists"

# Step 6: Create RDS Instance
echo "6️⃣  Creating RDS Instance..."

aws rds create-db-instance \
    --db-instance-identifier $DB_INSTANCE_ID \
    --db-instance-class $DB_INSTANCE_CLASS \
    --engine postgres \
    --engine-version 15.4 \
    --master-username $DB_USERNAME \
    --master-user-password "$DB_PASSWORD" \
    --allocated-storage $ALLOCATED_STORAGE \
    --storage-type gp2 \
    --vpc-security-group-ids $RDS_SG_ID \
    --db-subnet-group-name federal-budget-subnet-group \
    --backup-retention-period 7 \
    --no-deletion-protection \
    --no-publicly-accessible \
    --region $REGION \
    --db-name $DB_NAME

echo "🔄 RDS instance creation initiated. This will take 5-10 minutes..."

# Step 7: Wait for RDS to be available
echo "7️⃣  Waiting for RDS instance to be available..."

aws rds wait db-instance-available \
    --db-instance-identifier $DB_INSTANCE_ID \
    --region $REGION

# Get RDS endpoint
RDS_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier $DB_INSTANCE_ID \
    --query "DBInstances[0].Endpoint.Address" \
    --output text \
    --region $REGION)

echo "✅ RDS instance is ready!"
echo "   Endpoint: $RDS_ENDPOINT"

# Step 8: Create Secrets Manager secret
echo "8️⃣  Creating Secrets Manager secret..."

SECRET_VALUE="{\"username\":\"$DB_USERNAME\",\"password\":\"$DB_PASSWORD\",\"host\":\"$RDS_ENDPOINT\",\"port\":5432,\"dbname\":\"$DB_NAME\"}"

aws secretsmanager create-secret \
    --name "federal-budget-db-credentials-$STAGE" \
    --description "Database credentials for Federal Budget Dashboard" \
    --secret-string "$SECRET_VALUE" \
    --region $REGION 2>/dev/null || \
aws secretsmanager update-secret \
    --secret-id "federal-budget-db-credentials-$STAGE" \
    --secret-string "$SECRET_VALUE" \
    --region $REGION

echo "✅ Secrets Manager secret created/updated"

# Output configuration for serverless.yml
echo ""
echo "🎉 RDS Setup Complete!"
echo "======================"
echo ""
echo "📝 Update your serverless.yml with these values:"
echo ""
echo "  vpc:"
echo "    securityGroupIds:"
echo "      - $LAMBDA_SG_ID"
echo "    subnetIds:"
echo "      - $PRIVATE_SUBNET_1_ID"
echo "      - $PRIVATE_SUBNET_2_ID"
echo ""
echo "📝 Environment variables for local development:"
echo ""
echo "export DATABASE_URL='postgresql://$DB_USERNAME:$DB_PASSWORD@$RDS_ENDPOINT:5432/$DB_NAME'"
echo ""
echo "💰 Estimated monthly cost: ~\$13-15 (db.t3.micro)"
echo ""
echo "🔄 Next steps:"
echo "1. Update serverless.yml with the VPC configuration above"
echo "2. Set your local DATABASE_URL environment variable"
echo "3. Run: python scripts/seed_database.py"
echo "4. Test locally: python run_local.py" 