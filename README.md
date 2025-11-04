# FastAPI + PostgreSQL Migration

This backend has been migrated from Flask + Firebase to FastAPI + PostgreSQL.

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Environment variables configured in `.env` file

## Environment Variables

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=postgresql://username:password@host:port/database

# Admin
ADMIN_PASSWORD=your_admin_password_base64
ADMIN_PORTAL=/admin

# OTP Service
OTP_AUTH_TOKEN=your_otp_auth_token

# Testing
TEST_PHONE_NUMBER=7777777777
TEST_OTP=123456

# Server
PORT=8000
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Initialize the database:
```bash
python init_db.py
```

To drop and recreate all tables (WARNING: This will delete all data):
```bash
python init_db.py --drop
```

## Running the Application

### Development
```bash
uvicorn app:app --reload --port 8000
```

### Production
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Or use the main script:
```bash
python app.py
```

## API Endpoints

### Authentication
- `POST /phone/auth` - Send verification code
- `POST /phone/verify_code` - Verify OTP code
- `POST /phone/add_user` - Create user after verification
- `POST /user/by_email` - Search user by email
- `POST /user/by_phone` - Search user by phone

### Users
- `POST /user/add` - Add new user
- `PUT /user/update` - Update user profile
- `DELETE /user/delete` - Delete user profile
- `GET /user/profile/{unique_id}` - Get user profile

### Credits
- `POST /points/allocate` - Allocate points to user
- `POST /points/redeem` - Redeem points
- `POST /transactions/history` - Get transaction history
- `GET /leaderboard?limit=10` - Get leaderboard

### Admin (Requires TOKEN header)
- `GET /admin/users?sort=ascending` - Get all users
- `PUT /admin/points/update` - Update user points
- `POST /admin/users/add` - Add user (admin)
- `DELETE /admin/users/{user_id}` - Remove user
- `PUT /admin/users/role` - Change user role

### Data
- `GET /schedule` - Get schedule data
- `GET /items` - Get items data
- `GET /events` - Get events data

### Website (Admin Portal)
- `GET {ADMIN_PORTAL}/` - Home page with user list
- `GET {ADMIN_PORTAL}/user/add` - Add user form
- `POST {ADMIN_PORTAL}/user/add` - Submit new user
- `GET {ADMIN_PORTAL}/user/{user_id}` - User details page
- `POST {ADMIN_PORTAL}/user/points/update` - Update user points
- `POST {ADMIN_PORTAL}/user/balance/update` - Update user balance
- `POST {ADMIN_PORTAL}/user/role/update` - Update user role
- `POST {ADMIN_PORTAL}/user/delete` - Delete user
- `GET {ADMIN_PORTAL}/user/{user_id}/transactions` - Get user transactions

## Database Schema

### Users Table
- `unique_id` (PK) - User unique identifier
- `first_name` - User first name
- `last_name` - User last name
- `email` - User email (unique)
- `phone_number` - User phone number (unique)
- `role` - User role (USER, SALES, ADMIN)
- `credits` - User credit points
- `balance` - User balance (for SALES role)
- `referral_code` - Unique referral code
- `referred_by` - Array of referrer IDs
- `referrals` - Array of referred user IDs
- `transaction_history` - JSON array of transactions
- `created_at` - Timestamp
- `updated_at` - Timestamp

### PhoneAuth Table
- `verification_id` (PK) - Verification identifier
- `phone_number` - Phone number
- `otp` - One-time password
- `verified` - Verification status
- `attempts` - Number of attempts
- `created_at` - Timestamp
- `expires_at` - Expiration timestamp
- `verified_at` - Verification timestamp
- `token` - Verification token

### Cache Table
- `key` (PK) - Cache key
- `value` - JSON cache value
- `last_updated` - Last update timestamp
- `created_at` - Creation timestamp

## Migration Notes

### Key Changes
1. **Database**: Firebase Firestore → PostgreSQL
2. **Framework**: Flask → FastAPI
3. **ORM**: Firebase Admin SDK → SQLAlchemy
4. **Request Handling**: Flask request object → FastAPI dependency injection
5. **Response**: Flask jsonify → FastAPI automatic JSON serialization
6. **Templates**: Flask render_template → FastAPI Jinja2Templates
7. **Routing**: Flask Blueprints → FastAPI APIRouter

### Removed Dependencies
- Flask and flask-cors
- Firebase Admin SDK
- All Google Cloud libraries
- Werkzeug, blinker, etc.

### Added Dependencies
- FastAPI and uvicorn
- SQLAlchemy
- psycopg2-binary
- Pydantic

## Testing

The application includes test phone number support:
- Test phone: Set via `TEST_PHONE_NUMBER` env variable (default: 7777777777)
- Test OTP: Set via `TEST_OTP` env variable (default: 123456)

Use these for testing without sending actual SMS messages.

## Deployment

Update your deployment configuration to:
1. Use `uvicorn` instead of Flask's built-in server
2. Set DATABASE_URL environment variable
3. Run database initialization before first deployment
4. Update any reverse proxy configurations for ASGI instead of WSGI
