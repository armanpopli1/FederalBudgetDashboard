# Federal Budget Dashboard

A scalable, AWS-hosted, public-facing dashboard that visualizes the U.S. federal budget with interactive comparisons to proposed legislation changes.

## 🎯 Project Vision

**Phase 1 Goal**: Display current U.S. federal budget with interactive comparisons to the "Big Beautiful Bill" (BBB) proposed changes. Provide policy-curious citizens and Washington professionals a clear view of government spending and legislative impact.

**Future Phases**: User budget simulations, real-time legislative tracking, state-by-state impact analysis.

## 🏗️ Architecture Overview

### Tech Stack
- **Frontend**: React + Recharts/D3.js + TailwindCSS (deployed to Vercel)
- **Backend**: FastAPI + Mangum (deployed to AWS Lambda via Serverless Framework)
- **Database**: PostgreSQL on Amazon RDS (us-east-1)
- **API**: AWS API Gateway with CORS configuration
- **Secrets**: AWS Secrets Manager for database credentials

### AWS Infrastructure
- **Lambda Functions**: FastAPI app with VPC configuration for RDS access
- **RDS PostgreSQL**: t3.micro instance in private subnet
- **VPC + Security Groups**: Lambda → RDS connectivity (port 5432)
- **API Gateway**: RESTful API exposure with CORS
- **Secrets Manager**: Database connection strings

## 📊 Data Sources & Structure

### Primary Data
- **OMB Public Budget Database**: Latest available fiscal year (FY 2024/2025)
- **Budget Focus**: Outlays (actual spending) vs budget authority
- **Granularity**: Agency-level and functional categories with drilldown support

### Big Beautiful Bill (BBB)
- **Format**: Manually provided JSON/CSV with delta values
- **Structure**: `{"function": "Defense", "change": -10000000000}`
- **Metadata**: Title, purpose, sponsor, date (stubbed for Phase 1)

### Database Schema
```sql
-- Budget data table
budget_data (
  id, category, subcategory, agency, 
  amount, fiscal_year, data_type
)

-- BBB changes table  
bbb_changes (
  id, category, change_amount, 
  change_type, metadata
)

-- Bill metadata table
bills (
  id, title, sponsor, purpose, 
  date_introduced, status
)
```

## 🔌 API Endpoints

### Core Endpoints
- `GET /api/budget` - Returns current federal budget data
- `GET /api/bill/bbb` - Returns BBB proposed changes
- `GET /api/compare` - Returns merged current + BBB comparison view

### Response Format
```json
{
  "category": "Defense",
  "current_amount": 800000000000,
  "proposed_change": -10000000000,
  "new_amount": 790000000000,
  "change_percentage": -1.25
}
```

## 🖥️ Frontend Features

### Core Visualizations
- **Primary View**: Interactive pie chart of federal budget categories
- **Comparison Toggle**: "Current Budget" vs "Current + BBB Changes"
- **Drilldown Support**: Category → Agency → Program navigation
- **Change Display**: Absolute dollars, percentages, and new totals

### BBB Information Panel
- Bill summary, sponsor, purpose
- Key changes highlight
- Link to full legislation text

## 🚀 Development Workflow

### Setup Order
1. **AWS RDS Setup**: PostgreSQL instance with VPC/security groups
2. **Local Development**: FastAPI app connecting to AWS RDS
3. **Lambda Emulation**: SAM CLI for local testing
4. **Backend Deployment**: Serverless Framework to Lambda + API Gateway
5. **Frontend Development**: React app consuming deployed API
6. **Frontend Deployment**: Vercel hosting

### Environment Management
- **Single Environment**: Dev environment in AWS (Phase 1)
- **Local Development**: Connect directly to AWS RDS
- **Secrets**: Database credentials via AWS Secrets Manager

## 📁 Project Structure

```
FederalBudgetDashboard/
│
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app with Mangum
│   │   ├── models/              # SQLAlchemy models
│   │   ├── routers/             # API route handlers
│   │   └── database.py          # DB connection & config
│   ├── scripts/
│   │   ├── fetch_omb_data.py    # OMB data scraping
│   │   └── seed_database.py     # Database population
│   ├── serverless.yml           # AWS deployment config
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── views/               # Page components
│   │   ├── api/                 # API client functions
│   │   └── utils/               # Chart helpers
│   ├── public/
│   └── package.json
│
└── infrastructure/
    └── vpc-setup.yml            # VPC/RDS CloudFormation
```

## 🔒 Security Considerations

### Lambda VPC Configuration
```python
# VPC CONFIGURATION NEEDED:
# - Lambda must be in same VPC as RDS
# - Security group allows outbound 5432 to RDS security group  
# - VPC endpoints for internet access (or NAT Gateway)

# ENVIRONMENT VARIABLES NEEDED:
# - DATABASE_URL (from AWS Secrets Manager)
# - CORS_ORIGINS (for frontend domain)
```

### Database Security
- RDS in private subnet only
- Security groups restrict access to Lambda only
- SSL connections enforced
- Credentials via Secrets Manager rotation

## 💰 Cost Management

### Target: <$30/month
- **RDS t3.micro**: ~$13-15/month
- **Lambda**: Free tier covers expected usage
- **API Gateway**: Free tier for development traffic
- **Secrets Manager**: ~$1/month
- **Data Transfer**: Minimal costs expected

### Cost Monitoring
- AWS billing alerts configured
- Query optimization for RDS efficiency
- CloudFront caching for API responses

## 🧪 Phase 1 Scope (Current)

### ✅ Include
- Static federal budget visualization
- BBB comparison functionality  
- Agency/functional category drilldowns
- Responsive web interface
- AWS-hosted backend infrastructure

### ❌ Exclude (Future Phases)
- User accounts or authentication
- Budget simulation tools
- Real-time legislative tracking
- State-by-state impact analysis
- Mobile applications

## 🔄 Next Steps

1. **Infrastructure Setup**: RDS + VPC configuration
2. **Backend Development**: FastAPI app with database models
3. **Data Pipeline**: OMB data fetching and seeding scripts
4. **API Implementation**: Budget and comparison endpoints
5. **Frontend Scaffolding**: React app with chart components
6. **Integration Testing**: End-to-end functionality
7. **Deployment**: Lambda + Vercel hosting setup

---

**Ready to build**: Confirm this README captures your vision, then we'll start with infrastructure setup and backend development.
