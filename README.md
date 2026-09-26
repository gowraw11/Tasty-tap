# 🌴 TASTY TAP — AI-Powered Multi-Vendor Food Marketplace

> **Tap. Taste. Delivered.**
> *Every region has a story. Every business has a taste. Every craving is one TAP away.*

---

## 📌 1. Project Overview

**TASTY TAP** is a full-stack, production-style **Multi-Vendor Local Food Marketplace**, **Regional Indian Food Discovery Platform**, **AI Food Recommendation System**, **Restaurant & Small Business Management System**, and **Delivery Management Platform** built using **Django** and **Django REST Framework**.

TASTY TAP connects four major participants:

### 👤 Customers

Customers can:

* Discover regional Indian food
* Explore food from 12+ Indian states
* Search restaurants, hotels, cafés, bakeries, and local food businesses
* Customize food items
* Add food to cart
* Apply coupons
* Redeem Tasty Points
* Build complete meals using Smart Meal Builder
* Chat with TAP AI
* Receive personalized food recommendations
* Place and track orders
* View order history
* Download PDF invoices
* Submit verified reviews
* Save favorite foods and businesses

### 🏪 Business Partners

Local businesses can join TASTY TAP with:

> **₹0 Joining Cost & ₹0 Registration Fee**

Supported business types include:

* Small Hotels
* Restaurants
* Cafés
* Bakeries
* Juice Shops
* Cloud Kitchens
* Tiffin Services
* Home Food Businesses

Partners receive their own digital storefront and dashboard to:

* Manage business profile
* Manage food items
* Manage prices
* Manage inventory
* Accept orders
* Update order preparation status
* Create offers
* Launch festival promotions
* View customer reviews
* Track revenue
* View business analytics
* Manage their own storefront

### 🛵 Delivery Partners

Delivery partners can:

* View available deliveries
* Accept delivery assignments
* View pickup information
* Update delivery status
* Track active deliveries
* View daily earnings
* View lifetime earnings

Delivery status:

```text
Accepted
   ↓
Picked Up
   ↓
Out for Delivery
   ↓
Delivered
```

### 🛡️ Platform Administrators

Administrators can:

* Review business applications
* Approve businesses
* Reject applications
* Request changes
* Suspend businesses
* Manage users
* Manage regional content
* Manage regional themes
* Manage festival campaigns
* Monitor marketplace activity
* View platform analytics

---

## 💰 2. ₹0 Joining Cost Partner Program

TASTY TAP provides a dedicated onboarding program for local food businesses.

### Partner Registration

Businesses can register without upfront registration charges.

```text
₹0 Joining Cost
₹0 Registration Fee
```

The free registration feature is separate from any future:

* GST/statutory taxes
* Payment gateway processing charges
* Delivery charges
* Applicable business costs
* Optional subscription plans

Possible future subscription tiers:

```text
Free
Growth
Premium
```

The platform should clearly distinguish **free registration** from any future transaction, delivery, payment, tax, or subscription charges.

---

# 🌏 3. Tasty Tap Regions

One of TASTY TAP's signature features is **Tasty Tap Regions**.

The platform provides a dynamic regional food discovery experience.

### Supported Regions

The initial system supports:

1. Karnataka
2. Kerala
3. Goa
4. Tamil Nadu
5. Andhra Pradesh
6. Telangana
7. Maharashtra
8. Rajasthan
9. Gujarat
10. Punjab
11. West Bengal
12. Uttar Pradesh

---

## 🎨 4. Dynamic Regional Experience

When a customer changes their selected food region, the platform dynamically changes:

* Regional greeting
* Color palette
* Food categories
* Popular dishes
* Local businesses
* Regional imagery
* Festival campaigns
* Food recommendations
* Regional offers
* Discovery content

Example greetings:

```text
Namaskara Karnataka 👋
Namaskaram Kerala 🌴
Vanakkam Tamil Nadu 👋
Flavors of the Indian Coast 🌊
```

### Immersive Region Transition

Changing regions triggers an animated transition using CSS/GSAP.

Example:

```text
Current Region
      ↓
Immersive Transition
      ↓
New Regional Theme
      ↓
New Food + Businesses + Recommendations
```

---

## 📍 5. Region vs Delivery Location

The selected food region and physical delivery location are treated as separate concepts.

For example:

```text
Food Region:
Kerala

Delivery Location:
Mangaluru
```

A customer can explore Kerala food while maintaining Mangaluru as their delivery location.

The system can display appropriate cross-region delivery advisories when required.

---

# 🍛 6. Regional Food Examples

### Karnataka

Popular dishes include:

* Bisi Bele Bath
* Mysore Masala Dosa
* Maddur Vada
* Ragi Mudde
* Neer Dosa
* Kori Rotti
* Mangaluru Buns
* Udupi Idli
* Dharwad Peda
* Mysore Pak

Regional categories:

* Udupi Hotels
* Mangaluru Restaurants
* Bengaluru Cafés
* Mysuru Restaurants
* Coastal Food
* Local Hotels

---

### Kerala

Popular dishes include:

* Appam
* Puttu
* Kadala Curry
* Kerala Parotta
* Fish Curry
* Malabar Biryani
* Beef Fry
* Idiyappam
* Pazham Pori
* Payasam

---

### Tamil Nadu

Popular dishes include:

* Idli
* Dosa
* Pongal
* Vada
* Parotta
* Chettinad Chicken
* Kothu Parotta
* Sambar
* Filter Coffee
* Murukku

---

### Andhra Pradesh

Examples:

* Andhra Meals
* Gongura
* Pulihora
* Chicken Curry
* Pesarattu
* Biryani
* Regional Pickles

---

### Telangana

Examples:

* Hyderabadi Biryani
* Haleem
* Double Ka Meetha
* Osmania Biscuits
* Mirchi Ka Salan

---

### Maharashtra

Examples:

* Vada Pav
* Misal Pav
* Pav Bhaji
* Poha
* Puran Poli
* Sabudana Khichdi
* Bombay Sandwich

---

### Goa

Examples:

* Goan Fish Curry
* Prawn Curry
* Xacuti
* Pork Vindaloo
* Bebinca
* Poi

---

# 🏪 7. Multi-Vendor Marketplace

Every approved business receives an independent digital storefront.

Example:

```text
/store/<business-slug>/
```

Each business manages only its own:

* Products
* Prices
* Inventory
* Orders
* Promotions
* Reviews
* Analytics

### Multi-Tenant Isolation

Business Partner A cannot access or modify:

```text
Business Partner B
```

data.

All business-related queries should be filtered by the authenticated business owner.

---

# 📝 8. Partner Onboarding

The partner registration process contains five major steps:

```text
1. Business Information & Region
          ↓
2. Location & Map Pin
          ↓
3. Cuisine, Hours & Dietary Type
          ↓
4. Logo, Cover & Business Story
          ↓
5. Verification Submission
```

Possible application states:

```text
Pending
Under Review
Approved
Rejected
Changes Requested
Suspended
```

---

# 🛒 9. Smart Multi-Vendor Cart

TASTY TAP prevents customers from accidentally combining incompatible orders from different businesses.

Example:

```text
Business A
    +
Business B
```

When a customer attempts to add food from another business, the system displays:

> **You're ordering from another business**

Options:

```text
[ Create Separate Order ]
[ Continue Shopping ]
```

The recommended checkout model is to maintain separate orders for different businesses.

### Quick Cart Features

* Live quantity controls
* Item removal
* Price calculation
* Coupon validation
* Tasty Points redemption
* Delivery fee calculation
* Free-delivery progress indicator

Example:

> Add ₹80 more for FREE Delivery

---

# 🍕 10. Dynamic Food Customization

Customers can customize supported food items.

### Size

```text
Regular
Large
```

### Spice Level

```text
Mild
Medium
Hot
Extreme
```

### Add-ons

```text
Extra Cheese +₹30
Extra Portion +₹60
Jalapeno +₹20
Pure Ghee +₹15
```

Prices update dynamically based on selected options.

---

# 🤖 11. Tasty AI Recommendation System

Tasty AI provides personalized food recommendations.

The recommendation engine can consider:

* Selected region
* Previous orders
* Food preferences
* Time of day
* Dietary preferences
* Food category
* Ratings
* Price/budget
* Spice preference

Example:

> Because you ordered Chicken Biryani recently, you may also like Thalassery Biryani.

The system should provide a rule-based fallback when an external AI service is unavailable.

---

# 💬 12. TAP AI Assistant

TAP AI is a floating food discovery assistant.

Example queries:

```text
What should I eat?

Find food under ₹200.

Show nearby vegetarian food.

I want something spicy.

Find a small local hotel.

Recommend dinner for 2 people.

Show me Karnataka special food.
```

TAP AI uses the customer's:

* Selected region
* Budget
* Preferences
* Food history
* Dietary choices
* Time of day

to provide relevant recommendations.

---

# 🍽️ 13. Smart Meal Builder

Smart Meal Builder generates a complete five-course meal:

```text
Starter
   ↓
Main Course
   ↓
Side
   ↓
Drink
   ↓
Dessert
```

The meal can be generated based on:

* Budget
* Number of people
* Region
* Dietary preference
* Spice preference

Customers can use:

> **Add Full Meal to Cart**

to add the generated meal.

---

# 🎁 14. Offers & Festival Campaigns

Businesses can create promotional offers such as:

* Lunch offers
* Weekend offers
* Regional food offers
* New customer offers
* Festival promotions
* Discount coupons

Possible regional campaigns include:

* Onam
* Pongal
* Ugadi
* Mysuru Dasara
* Vishu
* Ganesh Chaturthi
* Diwali

Festival campaigns should be controlled through the admin system.

---

# ⭐ 15. Reviews & Ratings

Customers can submit reviews after eligible orders.

Features include:

* Verified order reviews
* Food ratings
* Business ratings
* Review comments
* Business owner replies

---

# 🪙 16. Tasty Points

Customers can earn platform loyalty points.

Example:

```text
Order Food
    ↓
Earn Tasty Points
    ↓
Redeem Points
    ↓
Receive Eligible Discount
```

The system maintains a points transaction history.

---

# 🔔 17. Notifications

Role-based notifications are supported for:

### Customers

* Order confirmation
* Order status
* Delivery updates
* Offers
* Recommendations

### Business Partners

* New order
* Order cancellation
* Review received
* Business verification update

### Delivery Partners

* New delivery
* Pickup reminder
* Delivery status

### Admins

* New business application
* Verification request
* Platform notifications

---

# 🗺️ 18. Delivery Tracking

The delivery module provides order tracking.

Example:

```text
Order Confirmed
      ↓
Preparing
      ↓
Accepted by Rider
      ↓
Picked Up
      ↓
Out for Delivery
      ↓
Delivered
```

Map-based tracking can use:

* Leaflet
* OpenStreetMap

---

# 📊 19. Analytics

Business partners can monitor:

* Daily revenue
* Order count
* Popular foods
* Customer activity
* Reviews
* Business performance

The platform admin can monitor marketplace-level analytics.

Chart.js can be used for dashboard visualizations.

---

# 🏗️ 20. Project Architecture

```text
tasty_tap/
│
├── accounts/
│   ├── UserProfile
│   ├── Address
│   ├── PointsTransaction
│   └── Authentication
│
├── businesses/
│   ├── Business
│   ├── BusinessProfile
│   ├── BusinessVerification
│   ├── Partner Dashboard
│   └── Admin Dashboard
│
├── restaurants/
│   └── Restaurant & Kitchen Metadata
│
├── menu/
│   ├── FoodCategory
│   ├── FoodItem
│   └── FoodCustomization
│
├── cart/
│   ├── Cart
│   ├── CartItem
│   └── Wishlist
│
├── orders/
│   ├── Order
│   ├── OrderItem
│   ├── Invoice
│   └── Order Tracking
│
├── payments/
│   └── Payment Processing
│
├── delivery/
│   ├── DeliveryPartner
│   ├── Delivery
│   └── Tracking
│
├── reviews/
│   └── Verified Reviews
│
├── offers/
│   ├── Coupons
│   └── Promotions
│
├── recommendations/
│   ├── UserPreference
│   ├── Recommendation Engine
│   ├── Tasty AI
│   ├── TAP AI
│   └── Smart Meal Builder
│
├── notifications/
│   └── Role-based Notifications
│
├── analytics/
│   └── Business Analytics
│
├── core/
│   ├── Region
│   ├── RegionTheme
│   ├── RegionalFood
│   ├── API
│   └── Seed Data
│
├── templates/
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── media/
│
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── manage.py
```

---

# 💻 21. Technology Stack

### Backend

* Python
* Django
* Django REST Framework

### Frontend

* HTML5
* CSS3
* JavaScript
* Responsive UI
* GSAP
* Three.js

### Database

Development:

```text
SQLite
```

Production:

```text
PostgreSQL
```

### Maps

```text
Leaflet
OpenStreetMap
```

### Data Visualization

```text
Chart.js
```

### PDF

```text
ReportLab
```

### Deployment

Possible deployment platforms:

* Render
* Railway
* AWS

---

# 📁 22. Installation & Quick Start

## Step 1 — Clone the Repository

```bash
git clone https://github.com/gowraw11/Tasty-tap.git
cd Tasty-tap
```

---

## Step 2 — Create Virtual Environment

### Windows

```powershell
python -m venv venv
```

Activate:

```powershell
.\venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Step 4 — Configure Environment

Create a `.env` file using `.env.example` as the template.

Configure values such as:

```text
SECRET_KEY
DEBUG
DATABASE_URL
```

Do not commit the actual `.env` file to GitHub.

---

## Step 5 — Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## Step 6 — Seed Demo Data

```bash
python manage.py seed_data
```

---

## Step 7 — Run the Development Server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

---

# 👤 23. Demo Accounts

| Role             | Username           | Password       | Dashboard              |
| ---------------- | ------------------ | -------------- | ---------------------- |
| Customer         | `customer_demo`    | `Customer@123` | `/`                    |
| Business Partner | `rahul_tastybites` | `Partner@123`  | `/dashboard/business/` |
| Delivery Partner | `kiran_rider`      | `Delivery@123` | `/dashboard/delivery/` |
| Platform Admin   | `admin`            | `Admin@123`    | `/dashboard/admin/`    |

> **Security:** Demo passwords should never be used in a production deployment. Change or remove demo credentials before deploying publicly.

---

# 🔌 24. REST API

| Endpoint                | Method    | Description                             |
| ----------------------- | --------- | --------------------------------------- |
| `/api/auth/`            | GET, POST | Authentication status, login and logout |
| `/api/regions/`         | GET, POST | Regional data and region selection      |
| `/api/businesses/`      | GET       | Approved businesses                     |
| `/api/businesses/<id>/` | GET       | Business storefront and menu            |
| `/api/foods/`           | GET       | Food discovery and filtering            |
| `/api/categories/`      | GET       | Food categories                         |
| `/api/cart/`            | GET, POST | Cart management                         |
| `/api/orders/`          | GET       | Customer orders                         |
| `/api/payments/`        | GET       | Payment history                         |
| `/api/reviews/`         | GET       | Verified reviews                        |
| `/api/offers/`          | GET       | Active offers                           |
| `/api/recommendations/` | GET, POST | AI recommendations                      |
| `/api/delivery/`        | GET       | Delivery information                    |
| `/api/notifications/`   | GET, POST | Notifications                           |
| `/api/search/`          | GET       | Food and business search                |
| `/api/wishlist/`        | POST      | Wishlist management                     |

### Recommendation API Modes

```text
mode=tasty_ai
mode=tap_ai
mode=meal_builder
```

---

# 🧪 25. Running Tests

Run the Django test suite:

```bash
python manage.py test
```

---

# 🚀 26. Production Deployment

Before deployment:

### Environment

```text
DEBUG=False
```

Configure a secure:

```text
SECRET_KEY
```

### Database

Configure PostgreSQL using environment variables.

### Static Files

```bash
python manage.py collectstatic --noinput
```

### Production Server

Possible deployment stack:

```text
Django
   ↓
Gunicorn / Uvicorn
   ↓
Nginx
   ↓
PostgreSQL
```

Possible hosting platforms:

```text
Render
Railway
AWS
```

---

# 🔐 27. Security

Production deployments should include:

* Strong secret key
* `DEBUG=False`
* Environment variables
* CSRF protection
* Secure authentication
* Role-based authorization
* Multi-tenant access control
* Input validation
* Secure password handling
* HTTPS
* Secure cookies
* Database access restrictions
* API permission controls

Payment integrations should use PCI-compliant external payment providers rather than storing sensitive card information directly.

---

# 🔮 28. Future Enhancements

Possible future improvements include:

* Real payment gateway integration
* Advanced AI/LLM integration
* Real-time WebSocket delivery tracking
* Push notifications
* Advanced recommendation models
* Food image recognition
* Voice-based TAP AI
* Multi-language support
* Advanced business analytics
* Customer referral system
* Subscription memberships
* Restaurant POS integration
* Mobile application
* Automated delivery assignment
* Demand forecasting
* Personalized regional food journeys

---

# 🎯 29. Project Objectives

The main objectives of TASTY TAP are:

1. Build a scalable multi-vendor food marketplace.
2. Help local food businesses establish a digital presence.
3. Provide regional Indian food discovery.
4. Personalize food discovery using AI-based recommendations.
5. Provide efficient business and order management.
6. Provide delivery tracking.
7. Support customer loyalty through Tasty Points.
8. Provide data-driven business analytics.
9. Maintain secure role-based access.
10. Create a modern, responsive and production-style food platform.

---

# 👨‍💻 30. Author

**Gowrav H L**

### GitHub

https://github.com/gowraw11

### Email

[gowravhadikallu@gmail.com](mailto:gowravhadikallu@gmail.com)

---

# 📄 31. License

This project is developed as an academic/project portfolio application.

© 2026 **TASTY TAP** — All Rights Reserved.

---

## 🌴 TASTY TAP

> **Tap. Taste. Delivered.**

> *Every region has a story. Every business has a taste. Every craving is one TAP away.*
