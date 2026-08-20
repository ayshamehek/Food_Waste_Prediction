# Food Waste Prediction

## Project Overview

**Food Waste Prediction** is a Flask-based web application designed to help users track and manage their food inventory to reduce food waste. The application predicts the waste risk level of stored food items and provides useful insights into inventory status.

## Core Features

### 1. User Management

- User registration and login functionality
- Secure password storage using SHA-256 hashing
- Session-based user authentication
- Pre-configured demo account:
  - **Username:** `demo`
  - **Password:** `demo123`

### 2. Food Inventory Tracking

Users can add and manage food items with the following details:

- Food name
- Category
- Storage location
- Quantity
- Unit of measurement
- Purchase date
- Expiry date

#### Food Categories

- Vegetables
- Fruits
- Dairy
- Meat
- Bakery
- Grains
- Prepared Meals
- Other

#### Storage Locations

- Fridge
- Freezer
- Pantry
- Counter

### 3. Waste Risk Prediction

The application automatically calculates the waste risk level based on the number of days remaining until expiry.

| Condition | Risk Level |
|---|---|
| 2 days or less until expiry | High Risk |
| 3–5 days until expiry | Medium Risk |
| More than 5 days until expiry | Low Risk |

Additional category and storage logic is applied:

- Vegetables and fruits stored on counters or in pantries may be classified as **Medium Risk**.

### 4. Dashboard

The dashboard provides a real-time view of the user's food inventory.

#### Features

- Inventory sorted by expiry date
- Search items by name
- Filter by risk level
- View inventory statistics

#### Summary Statistics

- Total number of items
- Items by risk level
- Items expiring soon

### 5. Item Status Tracking

Each food item is automatically assigned a status based on its expiry date.

| Status | Condition |
|---|---|
| Fresh | More than 3 days until expiry |
| Expiring Soon | 0–3 days until expiry |
| Expired | Past expiry date |

### 6. Reporting System

The application includes an analytics dashboard with visual reports for:

- Total inventory items
- Category distribution
- Risk-level breakdown
- Status distribution
  - Fresh
  - Expiring Soon
  - Expired

### 7. Item Management

Users can:

- Add food items
- View food items
- Search and filter items
- Delete consumed or expired items
- Automatically update item status as expiry dates change

## Technical Stack

| Component | Technology |
|---|---|
| Backend Framework | Flask 3.1.3 |
| Programming Language | Python |
| Database | SQLite3 |
| Frontend | HTML, CSS, JavaScript |
| Web Server | Gunicorn 23.0.0 |
| Testing Framework | Pytest 9.1.1 |

### Language Composition

- HTML — 53.3%
- Python — 30%
- CSS — 13.8%
- JavaScript — 2.9%

## Database Schema

### Users Table

| Column | Description |
|---|---|
| `id` | Unique user ID |
| `username` | User's username |
| `email` | User's email address |
| `password_hash` | Hashed password |
| `created_at` | Account creation date |

### Food Items Table

| Column | Description |
|---|---|
| `id` | Unique food item ID |
| `user_id` | ID of the associated user |
| `name` | Food item name |
| `category` | Food category |
| `storage_location` | Storage location |
| `quantity` | Quantity of food |
| `unit` | Unit of measurement |
| `purchase_date` | Purchase date |
| `expiry_date` | Expiry date |
| `risk_level` | Calculated waste risk |
| `status` | Current food status |
| `created_at` | Record creation date |

## Project Structure

```text
Food_Waste_Prediction/
│
├── app.py
├── requirements.txt
├── food_waste.db
├── render.yaml
├── run.txt
│
├── templates/
│
├── static/
│
├── models/
│
├── tests/
│
└── __pycache__/
