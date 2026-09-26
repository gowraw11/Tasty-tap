# 🌴 TASTY TAP — AI-Powered Multi-Vendor Food Ordering & Regional Local Food Marketplace

> **"Tap. Taste. Delivered."**
> *Every region has a story. Every business has a taste. Every craving is one TAP away.*

---

## 1. Project Overview

**TASTY TAP** is a full-stack, production-grade **Multi-Vendor Local Food Marketplace**, **Regional Indian Food Discovery Platform ("Tasty Tap Regions")**, **AI Food Recommendation Engine**, **Restaurant & Small Business Management System**, and **Real-Time Delivery Tracking Platform** built with **Django** and **Django REST Framework**.

It connects four core ecosystem participants:
1. **Customers** — Discover regional dishes across 12+ Indian states, customize food, build 5-course meals within a budget, chat with **TAP AI**, earn **Tasty Points**, track orders live on a map, and download PDF tax invoices.
2. **Business Partners** (Small Hotels, Restaurants, Cafes, Bakeries, Juice Shops, Cloud Kitchens, Tiffin Services, Home Food Businesses) — Join with **₹0 Joining Cost & ₹0 Registration Fee**, create a customized digital storefront (`/store/<slug>/`), manage independent inventory & pricing, accept/prepare orders, launch festival & lunch offers, and track revenue analytics.
3. **Delivery Partners** — View available deliveries, accept pickups, update live delivery status (`Accepted` → `Picked Up` → `Out for Delivery` → `Delivered`), and track daily & lifetime earnings.
4. **Platform Admins** — Review and verify business applications (`Approve`, `Reject`, `Request Changes`, `Suspend`), manage dynamic **Regional Themes & Festival Campaigns**, and monitor marketplace analytics.

> **Important Platform Notice on ₹0 Joining Cost:**
> The **₹0 Joining Cost / ₹0 Registration Fee** is a core onboarding feature allowing local food businesses to register and launch their digital storefront without upfront registration charges. It is explicitly separated from applicable statutory taxes (GST), payment gateway processing charges, delivery partner fees, or optional future subscription tiers (`Free`, `Growth`, `Premium`).

---

## 2. Signature Features

### 🌏 Tasty Tap Regions — Dynamic Regional Food Experience
- **12+ Data-Driven Indian Culinary Regions**: Karnataka, Kerala, Goa, Tamil Nadu, Andhra Pradesh, Telangana, Maharashtra, Rajasthan, Gujarat, Punjab, West Bengal, and Uttar Pradesh.
- **Immersive Region Transition**: Switching regions triggers an animated transition and dynamically updates the color palette (`RegionTheme`), greetings (*"Namaskara Karnataka 👋"*, *"Namaskaram Kerala 🌴"*, *"Flavors of the Indian Coast 🌊"*, *"Vanakkam Tamil Nadu 👋"*), categories, local businesses, popular dishes, festival offers, and AI recommendations.
- **Region vs. Delivery Location Separation**: Customers can explore food from any Indian region (e.g., Kerala or Goa) while keeping their physical delivery location (e.g., Mangaluru or Bengaluru) separate, with automatic cross-region delivery advisories.

### 🏪 ₹0 Joining Cost Partner Program & Multi-Tenant Dashboard
- **Dedicated Partner Onboarding (`/partner/` & `/partner/register/`)**: 5-step registration wizard (Business Info & Region → Location & Map Pin → Cuisine, Hours & Dietary Type → Logo, Cover & Story → Verification Submission).
- **Strict Multi-Tenant Isolation**: Business Partner A can only view and manage their own products, orders, promotions, reviews, and analytics.
- **Store Onboarding Checklist & Growth Center**: Dynamic 7-step completion progress bar and analytics-backed growth suggestions.

### 🛒 Multi-Vendor Smart Cart & Dynamic Food Customization
- **Single-Business Per Order Protection**: Prevents accidentally mixing kitchens with different preparation times. Adding an item from another business triggers the **"You're ordering from another business"** modal with `[Create Separate Order]` and `[Continue Shopping]`.
- **Sticky Quick Order Cart**: Live quantity steppers, Free Delivery progress bar (*"Add ₹80 more for FREE Delivery"*), coupon validation, and Tasty Points redemption.
- **Dynamic Food Customization**: Size (`Regular` / `Large`), Spice Level (`Mild` / `Medium` / `Hot` / `Extreme`), and Add-ons (`Extra Cheese +₹30`, `Extra Portion +₹60`, `Jalapeno +₹20`, `Pure Ghee +₹15`) with live price updates.

### 🤖 Tasty AI Recommendations, TAP AI Assistant & Smart Meal Builder
- **Tasty AI Recommendations**: Hybrid scoring engine factoring in selected region, order history (*"Because you ordered Chicken Biryani..."*), time of day, dietary preference, and ratings.
- **TAP AI Floating Concierge**: Region-aware conversational assistant answering *"What should I eat?"*, *"Find food under ₹200"*, *"Show nearby vegetarian food"*, *"I want something spicy"*, *"Find a small local hotel"*, and *"Recommend dinner for 2 people"*.
- **Smart Meal Builder**: Generates a complete 5-course meal (**Starter, Main Course, Side, Drink, Dessert**) scaled to budget and headcount with 1-click **Add Full Meal to Cart**.

---

## 3. Project Folder Structure

```text
tasty_tap/
├── accounts/           # UserProfile (4 roles), Address, PointsTransaction, Auth views
├── businesses/         # Business, BusinessProfile, BusinessVerification, Partner & Admin dashboards
├── restaurants/        # Restaurant kitchen & hygiene metadata
├── menu/               # FoodCategory, FoodItem, FoodCustomization
├── cart/               # Multi-vendor Cart, CartItem, Wishlist
├── orders/             # Order, OrderItem, PDF Invoice generator (ReportLab), Live Tracking
├── payments/           # PCI-safe mock Payment gateway (UPI, Card, Net Banking, COD)
├── delivery/           # DeliveryPartner, Delivery tracking & Rider Dashboard
├── reviews/            # Verified Order Reviews & Business Owner replies
├── offers/             # Coupon & Promotional Offers
├── recommendations/    # UserPreference, Recommendation, Tasty AI, TAP AI & Smart Meal Builder
├── notifications/      # Role-targeted Notification system
├── analytics/          # BusinessAnalytics daily revenue & customer insights
├── core/               # Region, RegionTheme, RegionalFood, REST APIs, seed_data command
├── templates/          # Responsive HTML5 templates with dark mode & regional theming
├── static/             # CSS, JS (Three.js, GSAP/CSS transitions, Leaflet maps, Chart.js)
├── media/              # Uploaded business logos, covers, food & review photos
├── requirements.txt
├── .env.example
├── README.md
└── manage.py
```

---

## 4. Installation & Quick Start

### Step 1: Create & Activate Virtual Environment (Optional)
```bash
python -m venv venv
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 4: Seed Realistic Demo Data
```bash
python manage.py seed_data
```

### Step 5: Run the Application Server
```bash
python manage.py runserver
```
Open **`http://127.0.0.1:8000/`** in your browser!

---

## 5. Demo Accounts (1-Click Login Available at `/accounts/login/`)

| Role | Username | Password | Dashboard / Access URL |
| :--- | :--- | :--- | :--- |
| **Customer** | `customer_demo` | `Customer@123` | `/` & `/accounts/profile/` |
| **Business Partner** | `rahul_tastybites` | `Partner@123` | `/dashboard/business/` |
| **Delivery Partner** | `kiran_rider` | `Delivery@123` | `/dashboard/delivery/` |
| **Platform Admin** | `admin` | `Admin@123` | `/dashboard/admin/` & `/django-admin/` |

---

## 6. REST API Documentation

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/auth/` | `GET`, `POST` | Session auth status, login & logout |
| `/api/regions/` | `GET`, `POST` | List all dynamic Indian regions & switch active region theme |
| `/api/businesses/` | `GET` | List approved local businesses (filter by `region`, `type`, `diet`, `q`) |
| `/api/businesses/<id>/` | `GET` | Storefront profile & full menu for a business |
| `/api/foods/` | `GET` | List food items (filter by `region`, `category`, `veg`, `max_price`, `q`) |
| `/api/categories/` | `GET` | List food categories |
| `/api/cart/` | `GET`, `POST` | Smart Cart CRUD, multi-vendor conflict check, coupons & Tasty Points |
| `/api/orders/` | `GET` | Customer orders & live order timeline |
| `/api/payments/` | `GET` | Customer payment transaction history |
| `/api/reviews/` | `GET` | Verified customer reviews |
| `/api/offers/` | `GET` | Active regional offers & discount coupons |
| `/api/recommendations/` | `GET`, `POST` | Tasty AI recommendations, TAP AI chat (`mode="tap_ai"`), Smart Meal Builder (`mode="meal_builder"`) |
| `/api/delivery/` | `GET` | Live delivery assignments & coordinates |
| `/api/notifications/` | `GET`, `POST` | User notifications & mark-as-read |
| `/api/search/` | `GET` | Live AJAX search prioritizing current region with `all_india` toggle |
| `/api/wishlist/` | `POST` | Toggle saved food items & businesses |

---

## 7. Running Automated Tests

```bash
python manage.py test
```

---

## 8. Production Deployment Checklist

1. Copy `.env.example` to `.env` and set a strong `SECRET_KEY` and `DEBUG=False`.
2. Configure PostgreSQL in `DATABASES` via environment variables.
3. Run `python manage.py collectstatic --noinput`.
4. Serve with Gunicorn / Uvicorn behind Nginx or deploy to Render / Railway / AWS Elastic Beanstalk.

---

## 9. Author & Contact

- **Author:** Gowrav H L
- **GitHub:** [@gowraw11](https://github.com/gowraw11)
- **Email:** [gowravhadikallu@gmail.com](mailto:gowravhadikallu@gmail.com)
- **Phone:** +91 8431939226

&copy; 2026 **TASTY TAP** — All Rights Reserved.

#   T a s t y - t a p  
 