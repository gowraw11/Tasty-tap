from datetime import date, time, timedelta
from decimal import Decimal
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Address, PointsTransaction, UserProfile
from analytics.models import BusinessAnalytics
from businesses.models import Business, BusinessCategory, BusinessProfile, BusinessVerification
from core.models import (
    PlatformSetting, Region, RegionTheme, RegionalBusiness,
    RegionalCategory, RegionalCuisine, RegionalFood, RegionalOffer
)
from delivery.models import Delivery, DeliveryPartner
from menu.models import FoodCategory, FoodCustomization, FoodItem
from notifications.models import Notification
from offers.models import Coupon, Offer
from orders.models import Order, OrderItem
from payments.models import Payment
from recommendations.models import Recommendation, UserPreference
from restaurants.models import Restaurant
from reviews.models import Review


class Command(BaseCommand):
    help = "Seeds Tasty Tap with complete Regional Food Experience, Local Businesses, Products, Orders, Offers, and Demo Accounts."

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING("Seeding TASTY TAP Multi-Vendor & Regional Food Marketplace..."))

        # 1. Platform Settings
        settings_seed = [
            ('JOINING_COST_INR', '0', '₹0 Joining Cost for local food businesses'),
            ('REGISTRATION_FEE_INR', '0', '₹0 Registration Fee'),
            ('POINTS_PER_100_INR', '10', 'Tasty Points earned per ₹100 spent'),
            ('FREE_DELIVERY_THRESHOLD', '199', 'Order value for Free Delivery'),
        ]
        for k, v, desc in settings_seed:
            PlatformSetting.objects.update_or_create(key=k, defaults={'value': v, 'description': desc})

        # 2. Create Demo Users for all 4 Roles
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={'email': 'admin@tastytap.in', 'first_name': 'Aarav', 'last_name': 'Admin', 'is_staff': True, 'is_superuser': True}
        )
        admin_user.set_password('Admin@123')
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

        partner_user, _ = User.objects.get_or_create(
            username='rahul_tastybites',
            defaults={'email': 'rahul@tastybites.in', 'first_name': 'Rahul', 'last_name': 'Shetty'}
        )
        partner_user.set_password('Partner@123')
        partner_user.save()

        customer_user, _ = User.objects.get_or_create(
            username='customer_demo',
            defaults={'email': 'ananya@tastytap.in', 'first_name': 'Ananya', 'last_name': 'Rao'}
        )
        customer_user.set_password('Customer@123')
        customer_user.save()

        rider_user, _ = User.objects.get_or_create(
            username='kiran_rider',
            defaults={'email': 'kiran@tastytap.in', 'first_name': 'Kiran', 'last_name': 'Kumar'}
        )
        rider_user.set_password('Delivery@123')
        rider_user.save()

        # 3. Seed 12 Indian Culinary Regions & Themes (Sections 69-98)
        regions_data = [
            {
                'name': 'Karnataka',
                'slug': 'karnataka',
                'code': 'KA',
                'emoji': '🇮🇳',
                'greeting': 'Namaskara Karnataka 👋',
                'subheading': 'Discover the flavors of Karnataka — from Coastal Mangaluru Gassi to Heritage Udupi & Mysuru Tiffins.',
                'tagline': 'Flavors of Coastal & Heritage Karnataka',
                'city': 'Mangaluru',
                'lat': 12.9141,
                'lng': 74.8560,
                'order': 1,
                'popular': 'Bisi Bele Bath, Mysore Masala Dosa, Neer Dosa, Mangaluru Buns, Kori Rotti, Ragi Mudde, Maddur Vada, Dharwad Peda',
                'specialties': ['Mangaluru Specials', 'Udupi Heritage Tiffins', 'Mysuru Royal Sweets', 'Bengaluru Favorites'],
                'card_img': 'https://images.unsplash.com/photo-1630383249896-424e482df921?w=800&auto=format&fit=crop&q=80',
                'theme': {
                    'primary': '#B8532A',
                    'secondary': '#1A5F72',
                    'accent': '#E69F38',
                    'bg': '#FDF8F2',
                    'gradient': 'linear-gradient(135deg, #9E421B 0%, #C66B37 50%, #7C3112 100%)',
                    'wave': '#1A5F72',
                    'hero_img': 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=900&auto=format&fit=crop&q=80',
                    'hero_sec': 'https://images.unsplash.com/photo-1593693397690-362cb9666fc2?w=700&auto=format&fit=crop&q=80',
                    'anim': 'coastal_wave',
                    'cats': ['Udupi Hotels', 'Mangaluru Restaurants', 'Bengaluru Cafes', 'Mysuru Restaurants', 'Coastal Food', 'Local Hotels'],
                }
            },
            {
                'name': 'Kerala',
                'slug': 'kerala',
                'code': 'KL',
                'emoji': '🌴',
                'greeting': 'Namaskaram Kerala 🌴',
                'subheading': "Explore the flavors of God's Own Country — Earthen Meen Curry, Lace Appams & Malabar Biryanis.",
                'tagline': 'Flavors of the Malabar Coast & Backwaters',
                'city': 'Kochi',
                'lat': 9.9312,
                'lng': 76.2673,
                'order': 2,
                'popular': 'Appam, Puttu, Kadala Curry, Kerala Parotta, Kerala Meen Curry, Malabar Biryani, Idiyappam, Pazham Pori, Payasam',
                'specialties': ['Malabar Specials', 'Backwater Seafood', 'Traditional Kerala Sadhya', 'Chaya Kada Snacks'],
                'card_img': 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=800&auto=format&fit=crop&q=80',
                'theme': {
                    'primary': '#1E5E3A',
                    'secondary': '#0F4C5C',
                    'accent': '#D99B26',
                    'bg': '#F4FAF5',
                    'gradient': 'linear-gradient(135deg, #164A2E 0%, #2B7A4B 52%, #0F3822 100%)',
                    'wave': '#0F4C5C',
                    'hero_img': 'https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=900&auto=format&fit=crop&q=80',
                    'hero_sec': 'https://images.unsplash.com/photo-1602216056096-3b40cc0c9944?w=700&auto=format&fit=crop&q=80',
                    'anim': 'coconut_breeze',
                    'cats': ['Kerala Restaurants', 'Malabar Restaurants', 'Seafood', 'Tea Shops', 'Local Hotels', 'Home Food'],
                }
            },
            {
                'name': 'Goa',
                'slug': 'goa',
                'code': 'GA',
                'emoji': '🌿',
                'greeting': 'Flavors of the Indian Coast 🌊',
                'subheading': 'High-quality coastal seafood, Konkan Fry, Creamy Coconut Prawn Curries & Traditional Bebinca.',
                'tagline': 'Flavors of the Indian Coast',
                'city': 'Panaji',
                'lat': 15.4909,
                'lng': 73.8278,
                'order': 3,
                'popular': 'Goan Prawn Curry, Konkani Bangda Fry, Goan Fish Curry, Xacuti, Bebinca, Poi Bread',
                'specialties': ['Goan Curries', 'Konkan Fry', 'Coastal Desserts', 'Beachside Shacks'],
                'card_img': 'https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=800&auto=format&fit=crop&q=80',
                'theme': {
                    'primary': '#AD4F24',
                    'secondary': '#185C70',
                    'accent': '#E49836',
                    'bg': '#FCF7EE',
                    'gradient': 'linear-gradient(135deg, #9A411B 0%, #C66C38 50%, #833414 100%)',
                    'wave': '#185C70',
                    'hero_img': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=900&auto=format&fit=crop&q=80',
                    'hero_sec': 'https://images.unsplash.com/photo-1593693397690-362cb9666fc2?w=700&auto=format&fit=crop&q=80',
                    'anim': 'coastal_wave',
                    'cats': ['Malabar Special', 'Goan Curries', 'Mangalorean Tandoor', 'Konkan Fry', 'Coastal Desserts'],
                }
            },
            {
                'name': 'Tamil Nadu',
                'slug': 'tamil-nadu',
                'code': 'TN',
                'emoji': '🌶️',
                'greeting': 'Vanakkam Tamil Nadu 👋',
                'subheading': 'Discover authentic Tamil flavors — Roasted Chettinad Masala, Kothu Parotta & Brass-Davara Filter Coffee.',
                'tagline': 'Heritage Tiffins & Fiery Chettinad',
                'city': 'Chennai',
                'lat': 13.0827,
                'lng': 80.2707,
                'order': 4,
                'popular': 'Idli, Dosa, Ghee Pongal, Vada, Chettinad Chicken, Kothu Parotta, Sambar, Filter Coffee, Murukku',
                'specialties': ['Chettinad Kitchens', 'Madurai Mess Specials', 'Chennai Tiffin Centers', 'Kumbakonam Coffee'],
                'card_img': 'https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?w=800&auto=format&fit=crop&q=80',
                'theme': {
                    'primary': '#9C2B23',
                    'secondary': '#7A4918',
                    'accent': '#E8A838',
                    'bg': '#FDF6F0',
                    'gradient': 'linear-gradient(135deg, #8A2019 0%, #B84028 52%, #631610 100%)',
                    'wave': '#5C3A1E',
                    'hero_img': 'https://images.unsplash.com/photo-1610192244261-3f33de3f55e4?w=900&auto=format&fit=crop&q=80',
                    'hero_sec': 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=700&auto=format&fit=crop&q=80',
                    'anim': 'temple_glow',
                    'cats': ['Tamil Restaurants', 'Chettinad', 'Tiffin Centers', 'Street Food', 'Filter Coffee Shops', 'Local Hotels'],
                }
            },
            {
                'name': 'Andhra Pradesh',
                'slug': 'andhra-pradesh',
                'code': 'AP',
                'emoji': '🌊',
                'greeting': 'Namaskaram Andhra Pradesh 🌶️',
                'subheading': 'Experience fiery Guntur chilies, tangy Gongura delicacies, Pesarattu & Banana Leaf Andhra Meals.',
                'tagline': 'Bold Spice & Banana Leaf Feasts',
                'city': 'Vijayawada',
                'lat': 16.5062,
                'lng': 80.6480,
                'order': 5,
                'popular': 'Andhra Meals, Gongura Chicken, Pulihora, Pesarattu, Kodi Pulao, Spicy Avakaya Pickles',
                'specialties': ['Guntur Spice Specials', 'Banana Leaf Meals', 'Godavari Coastal Curries'],
                'card_img': 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=800&auto=format&fit=crop&q=80',
                'theme': {
                    'primary': '#B3261E',
                    'secondary': '#2D5A27',
                    'accent': '#F29900',
                    'bg': '#FFF7F5',
                    'gradient': 'linear-gradient(135deg, #9E1C15 0%, #CC3B28 52%, #75120D 100%)',
                    'wave': '#2D5A27',
                    'hero_img': 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=900&auto=format&fit=crop&q=80',
                    'hero_sec': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=700&auto=format&fit=crop&q=80',
                    'anim': 'spice_burst',
                    'cats': ['Andhra Mess', 'Gongura Specials', 'Spicy Biryanis', 'Tiffin Centers'],
                }
            },
            {
                'name': 'Telangana',
                'slug': 'telangana',
                'code': 'TS',
                'emoji': '🍚',
                'greeting': 'Welcome to Telangana 👋',
                'subheading': 'Savor royal Hyderabadi Kachchi Dum Biryani, slow-cooked Haleem, Irani Chai & Osmania Biscuits.',
                'tagline': 'Royal Nizami Dastarkhwan',
                'city': 'Hyderabad',
                'lat': 17.3850,
                'lng': 78.4867,
                'order': 6,
                'popular': 'Hyderabadi Biryani, Haleem, Double Ka Meetha, Osmania Biscuits, Mirchi Ka Salan',
                'specialties': ['Charminar Biryani Houses', 'Irani Cafes', 'Nizami Desserts'],
                'card_img': 'https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=800&auto=format&fit=crop&q=80',
                'theme': {
                    'primary': '#6B3FA0',
                    'secondary': '#9E421B',
                    'accent': '#E5A93C',
                    'bg': '#FAF7FC',
                    'gradient': 'linear-gradient(135deg, #4E2A7A 0%, #7C4BB8 52%, #391D5C 100%)',
                    'wave': '#9E421B',
                    'hero_img': 'https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=900&auto=format&fit=crop&q=80',
                    'hero_sec': 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=700&auto=format&fit=crop&q=80',
                    'anim': 'royal_marigold',
                    'cats': ['Biryani Houses', 'Irani Cafes', 'Kebab Grills', 'Sweet Shops'],
                }
            },
            {
                'name': 'Maharashtra',
                'slug': 'maharashtra',
                'code': 'MH',
                'emoji': '🌸',
                'greeting': 'Namaskar Maharashtra 👋',
                'subheading': 'From Mumbai Vada Pav & Pav Bhaji to Puneri Misal, Puran Poli & Coastal Malvani Thalis.',
                'tagline': 'Street Icons & Sahyadri Flavors',
                'city': 'Mumbai',
                'lat': 19.0760,
                'lng': 72.8777,
                'order': 7,
                'popular': 'Vada Pav, Misal Pav, Pav Bhaji, Kanda Poha, Puran Poli, Sabudana Khichdi, Bombay Sandwich',
                'specialties': ['Mumbai Street Favorites', 'Puneri Misal Joints', 'Malvani Seafood'],
                'card_img': 'https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=800&auto=format&fit=crop&q=80',
                'theme': {
                    'primary': '#C85A17',
                    'secondary': '#1E4D6B',
                    'accent': '#F4A261',
                    'bg': '#FFF9F4',
                    'gradient': 'linear-gradient(135deg, #A8440C 0%, #D96B27 52%, #7D3107 100%)',
                    'wave': '#1E4D6B',
                    'hero_img': 'https://images.unsplash.com/photo-1606491956689-2ea866880c84?w=900&auto=format&fit=crop&q=80',
                    'hero_sec': 'https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=700&auto=format&fit=crop&q=80',
                    'anim': 'spice_burst',
                    'cats': ['Mumbai Chaat', 'Misal Houses', 'Malvani Kitchens', 'Local Bakeries'],
                }
            },
            {
                'name': 'Rajasthan',
                'slug': 'rajasthan',
                'code': 'RJ',
                'emoji': '🏰',
                'greeting': 'Khamma Ghani Rajasthan 🏰',
                'subheading': 'Indulge in royal Dal Baati Churma, fiery Laal Maas, crispy Pyaaz Kachori & Honeycomb Ghevar.',
                'tagline': 'Royal Heritage Kitchens',
                'city': 'Jaipur',
                'lat': 26.9124,
                'lng': 75.7873,
                'order': 8,
                'popular': 'Dal Baati Churma, Laal Maas, Gatte Ki Sabzi, Pyaaz Kachori, Mirchi Bada, Ghevar',
                'specialties': ['Jaipur Royal Thalis', 'Jodhpuri Kachori & Sweets', 'Marwari Bhojanalayas'],
                'card_img': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=800&auto=format&fit=crop&q=80',
                'theme': {
                    'primary': '#B5385A',
                    'secondary': '#8C4A1D',
                    'accent': '#E5A93C',
                    'bg': '#FFF7F9',
                    'gradient': 'linear-gradient(135deg, #8F2442 0%, #C44569 52%, #69182F 100%)',
                    'wave': '#8C4A1D',
                    'hero_img': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=900&auto=format&fit=crop&q=80',
                    'hero_sec': 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=700&auto=format&fit=crop&q=80',
                    'anim': 'royal_marigold',
                    'cats': ['Royal Thali', 'Sweet & Namkeen', 'Rajasthani Bhojanalaya'],
                }
            },
            {
                'name': 'Gujarat',
                'slug': 'gujarat',
                'code': 'GJ',
                'emoji': '🥘',
                'greeting': 'Kem Cho Gujarat 👋',
                'subheading': 'Fluffy Khaman Dhokla, festive Undhiyu, Methi Thepla & unlimited Gujarati Thalis.',
                'tagline': 'Farsan, Thalis & Sweet Hospitality',
                'city': 'Ahmedabad',
                'lat': 23.0225,
                'lng': 72.5714,
                'order': 9,
                'popular': 'Khaman Dhokla, Gujarati Thali, Undhiyu, Methi Thepla, Khandvi, Fafda Jalebi',
                'specialties': ['Ahmedabad Farsan Corners', 'Kathiyawadi Dhaba', 'Surti Snacks'],
                'card_img': 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=800&auto=format&fit=crop&q=80',
                'theme': {
                    'primary': '#C46210',
                    'secondary': '#2B6CB0',
                    'accent': '#ECC94B',
                    'bg': '#FFFDF7',
                    'gradient': 'linear-gradient(135deg, #9C4A08 0%, #D67418 52%, #783705 100%)',
                    'wave': '#2B6CB0',
                    'hero_img': 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=900&auto=format&fit=crop&q=80',
                    'hero_sec': 'https://images.unsplash.com/photo-1601050690597-df0568f70950?w=700&auto=format&fit=crop&q=80',
                    'anim': 'royal_marigold',
                    'cats': ['Farsan & Snacks', 'Gujarati Thali', 'Sweet Marts'],
                }
            },
            {
                'name': 'Punjab',
                'slug': 'punjab',
                'code': 'PB',
                'emoji': '🍛',
                'greeting': 'Sat Sri Akal Punjab 🌾',
                'subheading': 'Smoky Tandoori Kulchas, Sarson Da Saag with white makhan, Dal Makhani & tall glasses of Lassi.',
                'tagline': 'Hearty Dhaba & Tandoor Classics',
                'city': 'Amritsar',
                'lat': 31.6340,
                'lng': 74.8723,
                'order': 10,
                'popular': 'Amritsari Kulcha, Butter Chicken, Sarson Da Saag, Makki Di Roti, Dal Makhani, Patiala Lassi',
                'specialties': ['Amritsari Kulcha Dhabas', 'Punjabi Tandoor Grills', 'Lassi & Sweet Houses'],
                'card_img': 'https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=800&auto=format&fit=crop&q=80',
                'theme': {
                    'primary': '#B84B18',
                    'secondary': '#2C5E2E',
                    'accent': '#F2B705',
                    'bg': '#FFF9F0',
                    'gradient': 'linear-gradient(135deg, #96380D 0%, #CC5A22 52%, #732A08 100%)',
                    'wave': '#2C5E2E',
                    'hero_img': 'https://images.unsplash.com/photo-1603894584373-5ac82b2ae398?w=900&auto=format&fit=crop&q=80',
                    'hero_sec': 'https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=700&auto=format&fit=crop&q=80',
                    'anim': 'spice_burst',
                    'cats': ['Punjabi Dhabas', 'Tandoori Grills', 'Lassi Bars'],
                }
            },
            {
                'name': 'West Bengal',
                'slug': 'west-bengal',
                'code': 'WB',
                'emoji': '🐟',
                'greeting': 'Nomoshkar West Bengal 🌺',
                'subheading': 'Delicate Shorshe Ilish, aromatic Kolkata Biryani with potato, Kathi Rolls & warm Rosogolla.',
                'tagline': 'Mustard Coast & Mishti Heritage',
                'city': 'Kolkata',
                'lat': 22.5726,
                'lng': 88.3639,
                'order': 11,
                'popular': 'Shorshe Ilish, Kosha Mangsho, Kolkata Biryani, Egg Kathi Roll, Luchi Aloor Dom, Mishti Doi, Rosogolla',
                'specialties': ['Kolkata Biryani & Rolls', 'Bengali Pice Hotels', 'Traditional Mishti Shops'],
                'card_img': 'https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=800&auto=format&fit=crop&q=80',
                'theme': {
                    'primary': '#A62B2B',
                    'secondary': '#1D5B6E',
                    'accent': '#E59F32',
                    'bg': '#FFF8F6',
                    'gradient': 'linear-gradient(135deg, #871F1F 0%, #BD3A3A 52%, #631515 100%)',
                    'wave': '#1D5B6E',
                    'hero_img': 'https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=900&auto=format&fit=crop&q=80',
                    'hero_sec': 'https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=700&auto=format&fit=crop&q=80',
                    'anim': 'coastal_wave',
                    'cats': ['Pice Hotels', 'Mishti & Sweets', 'Kolkata Street Rolls'],
                }
            },
            {
                'name': 'Uttar Pradesh',
                'slug': 'uttar-pradesh',
                'code': 'UP',
                'emoji': '🍲',
                'greeting': 'Adaab & Pranam Uttar Pradesh ✨',
                'subheading': 'Melt-in-mouth Lucknowi Kebabs, Banarasi Kachori Sabzi, Tehri & Creamy Malai Kulfi.',
                'tagline': 'Awadhi Dastarkhwan & Banarasi Ghats',
                'city': 'Lucknow',
                'lat': 26.8467,
                'lng': 80.9462,
                'order': 12,
                'popular': 'Galouti Kebab, Awadhi Biryani, Banarasi Tamatar Chaat, Bedmi Poori, Malai Makhan',
                'specialties': ['Lucknowi Kebab Kitchens', 'Banarasi Chaat & Sweets', 'Purani Dilli & Awadh'],
                'card_img': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=800&auto=format&fit=crop&q=80',
                'theme': {
                    'primary': '#8E4121',
                    'secondary': '#234E52',
                    'accent': '#D69E2E',
                    'bg': '#FDF9F3',
                    'gradient': 'linear-gradient(135deg, #703016 0%, #A8522B 52%, #52210E 100%)',
                    'wave': '#234E52',
                    'hero_img': 'https://images.unsplash.com/photo-1544025162-d76694265947?w=900&auto=format&fit=crop&q=80',
                    'hero_sec': 'https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=700&auto=format&fit=crop&q=80',
                    'anim': 'royal_marigold',
                    'cats': ['Awadhi Kebabs', 'Chaat Corners', 'Halwai & Sweets'],
                }
            },
        ]

        region_map = {}
        for rdata in regions_data:
            reg, _ = Region.objects.update_or_create(
                slug=rdata['slug'],
                defaults={
                    'name': rdata['name'],
                    'code': rdata['code'],
                    'emoji_flag': rdata['emoji'],
                    'greeting': rdata['greeting'],
                    'subheading': rdata['subheading'],
                    'tagline': rdata['tagline'],
                    'short_description': rdata['subheading'],
                    'default_city': rdata['city'],
                    'latitude': rdata['lat'],
                    'longitude': rdata['lng'],
                    'card_image_url': rdata['card_img'],
                    'popular_dishes_preview': rdata['popular'],
                    'specialties_sections': rdata['specialties'],
                    'display_order': rdata['order'],
                    'is_active': True,
                }
            )
            t = rdata['theme']
            RegionTheme.objects.update_or_create(
                region=reg,
                defaults={
                    'primary_color': t['primary'],
                    'secondary_color': t['secondary'],
                    'accent_color': t['accent'],
                    'background': t['bg'],
                    'hero_gradient': t['gradient'],
                    'wave_color': t['wave'],
                    'hero_image': t['hero_img'],
                    'hero_secondary_image': t['hero_sec'],
                    'animation_style': t['anim'],
                    'food_categories': t['cats'],
                    'popular_foods': [x.strip() for x in rdata['popular'].split(',')],
                    'description': rdata['subheading'],
                }
            )
            for idx, cname in enumerate(t['cats'], start=1):
                RegionalCategory.objects.update_or_create(
                    region=reg,
                    name=cname,
                    defaults={
                        'icon': ['🍛', '🥥', '🔥', '🐟', '🍮', '☕'][idx % 6],
                        'display_order': idx,
                    }
                )
            region_map[reg.slug] = reg

        # Set user profiles & delivery rider
        UserProfile.objects.update_or_create(
            user=admin_user,
            defaults={'role': 'ADMIN', 'phone': '+91 9845000001', 'selected_region': region_map['karnataka'], 'has_chosen_region': True}
        )
        UserProfile.objects.update_or_create(
            user=partner_user,
            defaults={'role': 'BUSINESS_PARTNER', 'phone': '+91 9845099887', 'selected_region': region_map['karnataka'], 'has_chosen_region': True}
        )
        UserProfile.objects.update_or_create(
            user=customer_user,
            defaults={
                'role': 'CUSTOMER',
                'phone': '+91 9845011223',
                'selected_region': region_map['karnataka'],
                'has_chosen_region': True,
                'tasty_points': 240,
            }
        )
        UserProfile.objects.update_or_create(
            user=rider_user,
            defaults={'role': 'DELIVERY_PARTNER', 'phone': '+91 9845055667', 'selected_region': region_map['karnataka'], 'has_chosen_region': True}
        )

        rider_partner, _ = DeliveryPartner.objects.update_or_create(
            user=rider_user,
            defaults={
                'full_name': 'Kiran Kumar',
                'phone': '+91 9845055667',
                'vehicle_type': 'EV_SCOOTER',
                'vehicle_number': 'KA-19-EV-4022',
                'city': 'Mangaluru',
                'current_area': 'MG Road',
                'is_available': True,
                'is_verified': True,
            }
        )

        Address.objects.update_or_create(
            user=customer_user,
            label='Home',
            defaults={
                'recipient_name': 'Ananya Rao',
                'phone': '+91 9845011223',
                'address_line': 'Flat 302, Palm Grove Apartments, MG Road',
                'area': 'MG Road',
                'city': 'Mangaluru',
                'state': 'Karnataka',
                'pincode': '575003',
                'latitude': 12.9185,
                'longitude': 74.8595,
                'is_default': True,
            }
        )
        UserPreference.objects.update_or_create(
            user=customer_user,
            defaults={
                'preferred_region': region_map['karnataka'],
                'favorite_cuisines': 'Coastal Seafood, South Indian, Mangalorean, Biryani',
                'dietary_preference': 'ANY',
                'spice_preference': 'MEDIUM',
                'preferred_budget': Decimal('250.00'),
            }
        )

        # 4. Business Categories & Food Categories (matching Coastal + All-India categories)
        biz_cats = [
            ('Small Hotel', '🏨'),
            ('Restaurant', '🍴'),
            ('Cafe', '☕'),
            ('Bakery', '🥐'),
            ('Juice Shop', '🥤'),
            ('Cloud Kitchen', '🍱'),
            ('Home Food', '🏠'),
            ('Sweet Shop', '🍬'),
        ]
        biz_cat_map = {}
        for name, icon in biz_cats:
            bc, _ = BusinessCategory.objects.update_or_create(name=name, defaults={'icon': icon})
            biz_cat_map[name] = bc

        food_cats = [
            ('Malabar Special', '🥥', 1, '/static/images/foods/meen_curry.jpg'),
            ('Goan Curries', '🍲', 2, '/static/images/foods/prawn_curry.jpg'),
            ('Mangalorean Tandoor', '🍗', 3, '/static/images/foods/kori_rotti.jpg'),
            ('Konkan Fry', '🐟', 4, '/static/images/foods/bangda_fry.jpg'),
            ('Coastal Desserts', '🍮', 5, '/static/images/foods/bebinca.jpg'),
            ('South Indian', '🥞', 6, '/static/images/foods/masala_dosa.jpg'),
            ('North Indian', '🍛', 7, '/static/images/foods/paneer_butter_masala.jpg'),
            ('Biryani & Pulao', '🍚', 8, '/static/images/foods/chicken_biryani.jpg'),
            ('Fast Food', '🍔', 9, '/static/images/foods/chicken_burger.jpg'),
            ('Bakery & Desserts', '🧁', 10, '/static/images/foods/mysore_pak.jpg'),
            ('Cafe & Beverages', '☕', 11, '/static/images/foods/filter_coffee.jpg'),
            ('Home Food & Healthy', '🥗', 12, '/static/images/foods/ragi_mudde.jpg'),
        ]
        fcat_map = {}
        for name, icon, order, img in food_cats:
            fc, _ = FoodCategory.objects.update_or_create(
                name=name,
                defaults={'icon': icon, 'display_order': order, 'image_url': img, 'is_active': True}
            )
            fcat_map[name] = fc

        # 5. Seed Local Businesses across Regions (Sections 44, 58, 81)
        businesses_seed = [
            {
                'name': 'Tasty Bites',
                'slug': 'tasty-bites',
                'owner_name': 'Rahul Shetty',
                'type': 'SMALL_HOTEL',
                'region': 'karnataka',
                'city': 'Mangaluru',
                'area': 'Hampankatta',
                'lat': 12.8714,
                'lng': 74.8426,
                'cuisine': 'South Indian • Mangalorean • Chinese',
                'diet': 'BOTH',
                'price_range': '₹₹',
                'del_time': '22–30 min',
                'del_mins': 24,
                'del_fee': Decimal('15.00'),
                'rating': Decimal('4.9'),
                'status': 'APPROVED',
                'featured': True,
                'local_fav': True,
                'cover': '/static/images/foods/kori_rotti.jpg',
                'desc': 'Beloved Mangaluru neighborhood hotel serving crispy Neer Dosa, Kori Rotti, Fish Gassi, Chicken 65, and aromatic Biryanis.',
            },
            {
                'name': 'Samudra Ras Coastal Kitchen',
                'slug': 'samudra-ras-coastal',
                'owner_name': 'Capt. DSilva & Nayak',
                'type': 'RESTAURANT',
                'region': 'goa',
                'city': 'Panaji',
                'area': 'Fontainhas Coast',
                'lat': 15.4950,
                'lng': 73.8310,
                'cuisine': 'Coastal Indian • Goan • Konkani • Malabar',
                'diet': 'BOTH',
                'price_range': '₹₹',
                'del_time': '20–25 min',
                'del_mins': 22,
                'del_fee': Decimal('18.00'),
                'rating': Decimal('4.9'),
                'status': 'APPROVED',
                'featured': True,
                'local_fav': True,
                'cover': '/static/images/foods/prawn_curry.jpg',
                'desc': 'Signature coastal Indian seafood kitchen celebrating earthen Meen Curry, Goan Prawn Curry, Mangalorean Gassi & Konkani Bangda Fry.',
            },
            {
                'name': 'Sri Krishna Hotel',
                'slug': 'sri-krishna-hotel',
                'owner_name': 'Vidya Pai',
                'type': 'SMALL_HOTEL',
                'region': 'karnataka',
                'city': 'Udupi',
                'area': 'Car Street',
                'lat': 13.3409,
                'lng': 74.7421,
                'cuisine': 'Pure Udupi • South Indian Tiffin • Filter Coffee',
                'diet': 'VEG',
                'price_range': '₹',
                'del_time': '18–25 min',
                'del_mins': 20,
                'del_fee': Decimal('12.00'),
                'rating': Decimal('4.8'),
                'status': 'APPROVED',
                'featured': True,
                'local_fav': True,
                'cover': '/static/images/foods/masala_dosa.jpg',
                'desc': 'Authentic Udupi vegetarian tiffins — golden Masala Dosa, fluffy Idli Vada, Bisi Bele Bath, and brass-davara Filter Coffee.',
            },
            {
                'name': 'Malabar Backwater Kitchen',
                'slug': 'malabar-backwater-kitchen',
                'owner_name': 'Fathima & Nair',
                'type': 'RESTAURANT',
                'region': 'kerala',
                'city': 'Kochi',
                'area': 'Fort Kochi',
                'lat': 9.9658,
                'lng': 76.2421,
                'cuisine': 'Kerala • Malabar • Backwater Seafood',
                'diet': 'BOTH',
                'price_range': '₹₹',
                'del_time': '25–32 min',
                'del_mins': 26,
                'del_fee': Decimal('20.00'),
                'rating': Decimal('4.9'),
                'status': 'APPROVED',
                'featured': True,
                'local_fav': True,
                'cover': '/static/images/foods/meen_curry.jpg',
                'desc': 'Traditional Kerala earthen-pot curries, lace Appams, Puttu Kadala, and Thalassery Dum Biryani.',
            },
            {
                'name': 'Madurai Chettinad Mess',
                'slug': 'madurai-chettinad-mess',
                'owner_name': 'Senthil Murugan',
                'type': 'SMALL_HOTEL',
                'region': 'tamil-nadu',
                'city': 'Chennai',
                'area': 'Mylapore',
                'lat': 13.0368,
                'lng': 80.2676,
                'cuisine': 'Tamil • Chettinad • Madurai Tiffin',
                'diet': 'BOTH',
                'price_range': '₹',
                'del_time': '20–28 min',
                'del_mins': 24,
                'del_fee': Decimal('15.00'),
                'rating': Decimal('4.8'),
                'status': 'APPROVED',
                'featured': False,
                'local_fav': True,
                'cover': '/static/images/foods/chettinad_chicken.jpg',
                'desc': 'Stone-ground Chettinad spices, iron-tawa Kothu Parotta, Ghee Pongal, and frothy degree coffee.',
            },
            {
                'name': 'Local Cafe',
                'slug': 'local-cafe',
                'owner_name': 'Rohan & Meera',
                'type': 'CAFE',
                'region': 'karnataka',
                'city': 'Bengaluru',
                'area': 'Indiranagar',
                'lat': 12.9784,
                'lng': 77.6408,
                'cuisine': 'Artisan Cafe • Burgers • Cold Brews • Desserts',
                'diet': 'BOTH',
                'price_range': '₹₹',
                'del_time': '20–25 min',
                'del_mins': 22,
                'del_fee': Decimal('20.00'),
                'rating': Decimal('4.7'),
                'status': 'APPROVED',
                'featured': False,
                'hidden_gem': True,
                'cover': '/static/images/foods/chicken_burger.jpg',
                'desc': 'Cozy neighborhood cafe crafting thick Cold Coffee, gourmet burgers, peri-peri fries, and warm brownies.',
            },
            {
                'name': 'Spice Junction',
                'slug': 'spice-junction',
                'owner_name': 'Mirza Baig',
                'type': 'RESTAURANT',
                'region': 'telangana',
                'city': 'Hyderabad',
                'area': 'Banjara Hills',
                'lat': 17.4156,
                'lng': 78.4347,
                'cuisine': 'Hyderabadi • North Indian • Mughlai',
                'diet': 'BOTH',
                'price_range': '₹₹',
                'del_time': '28–35 min',
                'del_mins': 30,
                'del_fee': Decimal('22.00'),
                'rating': Decimal('4.8'),
                'status': 'APPROVED',
                'featured': True,
                'local_fav': True,
                'cover': '/static/images/foods/chicken_biryani.jpg',
                'desc': 'Saffron-infused Hyderabadi Dum Biryani, rich Paneer Butter Masala, garlic naans, and Double Ka Meetha.',
            },
            {
                'name': 'Biryani House & Andhra Mess',
                'slug': 'biryani-house',
                'owner_name': 'Venkat Reddy',
                'type': 'CLOUD_KITCHEN',
                'region': 'andhra-pradesh',
                'city': 'Vijayawada',
                'area': 'Benz Circle',
                'lat': 16.4971,
                'lng': 80.6534,
                'cuisine': 'Andhra Meals • Gongura Biryani • Spicy Curries',
                'diet': 'BOTH',
                'price_range': '₹₹',
                'del_time': '24–30 min',
                'del_mins': 26,
                'del_fee': Decimal('15.00'),
                'rating': Decimal('4.7'),
                'status': 'APPROVED',
                'hidden_gem': True,
                'cover': '/static/images/foods/veg_biryani.jpg',
                'desc': 'Authentic Guntur & Bezawada spice trails with tangy Gongura Biryani and full Andhra banana-leaf meals.',
            },
            {
                'name': 'Urban Cravings',
                'slug': 'urban-cravings',
                'owner_name': 'Siddharth Joshi',
                'type': 'FAST_FOOD',
                'region': 'maharashtra',
                'city': 'Mumbai',
                'area': 'Dadar West',
                'lat': 19.0178,
                'lng': 72.8478,
                'cuisine': 'Mumbai Street Food • Woodfired Pizza • Burgers',
                'diet': 'VEG',
                'price_range': '₹₹',
                'del_time': '20–28 min',
                'del_mins': 23,
                'del_fee': Decimal('18.00'),
                'rating': Decimal('4.7'),
                'status': 'APPROVED',
                'local_fav': True,
                'cover': '/static/images/foods/vada_pav.jpg',
                'desc': 'Crispy Mumbai Vada Pav, Puneri Misal Pav, buttery Pav Bhaji, and hand-stretched Margherita & Paneer pizzas.',
            },
            {
                'name': 'Home Kitchen — Ammas Dabba',
                'slug': 'home-kitchen',
                'owner_name': 'Lakshmi Amma',
                'type': 'HOME_FOOD',
                'region': 'karnataka',
                'city': 'Mysuru',
                'area': 'VV Mohalla',
                'lat': 12.3262,
                'lng': 76.6290,
                'cuisine': 'Home Food • Healthy Millet Meals • Traditional Sweets',
                'diet': 'VEG',
                'price_range': '₹',
                'del_time': '25–30 min',
                'del_mins': 26,
                'del_fee': Decimal('10.00'),
                'rating': Decimal('4.9'),
                'status': 'APPROVED',
                'hidden_gem': True,
                'local_fav': True,
                'cover': '/static/images/foods/ragi_mudde.jpg',
                'desc': '100% homestyle meals cooked in small batches with organic millets, cold-pressed oils, and zero preservatives.',
            },
            {
                'name': 'Fresh Juice Corner',
                'slug': 'fresh-juice-corner',
                'owner_name': 'Harish & Sons',
                'type': 'JUICE_SHOP',
                'region': 'karnataka',
                'city': 'Mangaluru',
                'area': 'Balmatta',
                'lat': 12.8745,
                'lng': 74.8512,
                'cuisine': 'Fresh Fruit Juices • Coastal Coolers • Milkshakes',
                'diet': 'VEG',
                'price_range': '₹',
                'del_time': '15–20 min',
                'del_mins': 17,
                'del_fee': Decimal('10.00'),
                'rating': Decimal('4.8'),
                'status': 'APPROVED',
                'hidden_gem': True,
                'cover': '/static/images/foods/lime_soda.jpg',
                'desc': 'Chilled Fresh Lime Soda, Tender Coconut Elaneer Punch, Gadbad Ice Cream, and seasonal fruit bowls.',
            },
            {
                'name': 'Sweet Treats Bakery',
                'slug': 'sweet-treats',
                'owner_name': 'Divya Hegde',
                'type': 'BAKERY',
                'region': 'karnataka',
                'city': 'Mysuru',
                'area': 'Devaraja Market',
                'lat': 12.3105,
                'lng': 76.6525,
                'cuisine': 'Bakery • Mysore Pak • Dharwad Peda • Pastries',
                'diet': 'VEG',
                'price_range': '₹',
                'del_time': '20–25 min',
                'del_mins': 21,
                'del_fee': Decimal('15.00'),
                'rating': Decimal('4.8'),
                'status': 'APPROVED',
                'local_fav': True,
                'cover': '/static/images/foods/mysore_pak.jpg',
                'desc': 'Artisanal bakery & heritage sweet house crafting melt-in-mouth Ghee Mysore Pak, Dharwad Peda, and Chocolate Brownies.',
            },
            {
                'name': 'The Food Hub (Pending Verification)',
                'slug': 'the-food-hub',
                'owner_name': 'Nikhil Kamath',
                'type': 'TIFFIN_SERVICE',
                'region': 'karnataka',
                'city': 'Mangaluru',
                'area': 'Bejai',
                'lat': 12.8891,
                'lng': 74.8442,
                'cuisine': 'Daily Tiffins • Coastal Thalis • Evening Snacks',
                'diet': 'BOTH',
                'price_range': '₹',
                'del_time': '25–30 min',
                'del_mins': 25,
                'del_fee': Decimal('15.00'),
                'rating': Decimal('4.6'),
                'status': 'PENDING',
                'cover': '/static/images/foods/idli_vada.jpg',
                'desc': 'New local tiffin center applying via Tasty Tap ₹0 Joining Program.',
            },
        ]

        biz_map = {}
        for bdata in businesses_seed:
            reg = region_map.get(bdata['region'])
            biz, _ = Business.objects.update_or_create(
                slug=bdata['slug'],
                defaults={
                    'owner': partner_user,
                    'name': bdata['name'],
                    'owner_name': bdata['owner_name'],
                    'email': f"contact@{bdata['slug'].replace('-', '')}.in",
                    'phone': '+91 9845099887',
                    'business_type': bdata['type'],
                    'region': reg,
                    'address': f"12 Heritage Street, {bdata['area']}",
                    'area': bdata['area'],
                    'city': bdata['city'],
                    'state': reg.name if reg else 'Karnataka',
                    'pincode': '575001',
                    'latitude': bdata['lat'],
                    'longitude': bdata['lng'],
                    'cuisine': bdata['cuisine'],
                    'dietary_type': bdata['diet'],
                    'price_range': bdata['price_range'],
                    'estimated_delivery_time': bdata['del_time'],
                    'delivery_mins_numeric': bdata['del_mins'],
                    'delivery_fee': bdata['del_fee'],
                    'free_delivery_threshold': Decimal('199.00'),
                    'rating': bdata['rating'],
                    'status': bdata['status'],
                    'joining_cost_inr': Decimal('0.00'),
                    'is_featured': bdata.get('featured', False),
                    'is_hidden_gem': bdata.get('hidden_gem', False),
                    'is_local_favorite': bdata.get('local_fav', False),
                    'is_open_now': True,
                    'is_demo_business': True,
                }
            )
            BusinessProfile.objects.update_or_create(
                business=biz,
                defaults={
                    'cover_image_url': bdata['cover'],
                    'logo_url': bdata['cover'],
                    'description': bdata['desc'],
                    'heritage_story': f"Founded by {bdata['owner_name']} in {bdata['city']}, {bdata['name']} brings authentic regional flavors online with ₹0 joining cost.",
                }
            )
            BusinessVerification.objects.update_or_create(
                business=biz,
                defaults={
                    'optional_license_ref': f"TT-REG-{biz.id:04d}",
                    'document_notes': 'Verified local partner store on Tasty Tap.',
                }
            )
            Restaurant.objects.update_or_create(business=biz)
            biz_map[biz.slug] = biz

        # 6. Seed Comprehensive Food Items with Authentic Dish-Specific Photos
        foods_seed = [
            # Samudra Ras Coastal Favorites
            ('samudra-ras-coastal', 'Malabar Special', 'kerala', 'Kerala Meen Curry', '49.00', 'NON_VEG', 'HOT', 'MAIN', 25, True, True,
             'Spicy red fish curry slow-simmered with Kodampuli (Malabar tamarind) and coconut oil in a traditional earthen chatti.',
             'Originated in coastal Toddy shops and homes along Alappuzha and Kochi backwaters.',
             '/static/images/foods/meen_curry.jpg'),

            ('samudra-ras-coastal', 'Goan Curries', 'goa', 'Goan Prawn Curry', '65.00', 'NON_VEG', 'MEDIUM', 'MAIN', 25, True, True,
             'Creamy golden coconut curry with fresh coastal prawns, kokum petals, and stone-ground Kashmiri chilies.',
             'A timeless staple of Goan Catholic and Saraswat households served over steamed red rice.',
             '/static/images/foods/prawn_curry.jpg'),

            ('samudra-ras-coastal', 'Mangalorean Tandoor', 'karnataka', 'Mangalorean Fish Gassi', '59.00', 'NON_VEG', 'HOT', 'MAIN', 22, True, True,
             'Creamy, spicy roasted Byadagi chili & coconut fish curry paired with soft lace Neer Dosa.',
             'Celebrated across Tulunadu coastal homes from Mangaluru to Kundapura.',
             '/static/images/foods/fish_gassi.jpg'),

            ('samudra-ras-coastal', 'Konkan Fry', 'goa', 'Konkani Bangda Fry', '48.00', 'NON_VEG', 'HOT', 'STARTER', 18, True, True,
             'Crispy rava-crusted pan-fried mackerel marinated in kokum, garlic, and Konkan coastal masala with solkadi.',
             'Iconic coastal starter from Karwar, Sindhudurg, and Panaji.',
             '/static/images/foods/bangda_fry.jpg'),

            ('samudra-ras-coastal', 'Coastal Desserts', 'goa', 'Traditional Goan Bebinca', '55.00', 'VEG', 'MILD', 'DESSERT', 15, False, True,
             'Seven-layered caramelized coconut milk and nutmeg coastal pudding served warm.',
             'Known as the Queen of Goan Desserts, traditionally baked layer by layer in clay ovens.',
             '/static/images/foods/bebinca.jpg'),

            # Tasty Bites (Mangaluru, Karnataka)
            ('tasty-bites', 'Biryani & Pulao', 'karnataka', 'Chicken Biryani', '180.00', 'NON_VEG', 'MEDIUM', 'MAIN', 25, True, False,
             'Fragrant seeraga samba & basmati dum biryani layered with succulent spiced chicken, caramelized onions, and mint raita.',
             'House signature recipe slow-sealed on dum at Tasty Bites Mangaluru.',
             '/static/images/foods/chicken_biryani.jpg'),

            ('tasty-bites', 'Mangalorean Tandoor', 'karnataka', 'Chicken 65', '150.00', 'NON_VEG', 'HOT', 'STARTER', 18, True, False,
             'Crispy tempered chicken bites tossed with curry leaves, crushed garlic, green chilies, and yogurt spice glaze.',
             'South India’s most loved crispy starter.',
             '/static/images/foods/chicken_65.jpg'),

            ('tasty-bites', 'North Indian', 'karnataka', 'Paneer Butter Masala', '160.00', 'VEG', 'MILD', 'MAIN', 20, True, False,
             'Soft cottage cheese cubes simmered in velvety tomato-cashew makhani gravy finished with kasuri methi.',
             'Creamy North Indian favorite loved across Karnataka family restaurants.',
             '/static/images/foods/paneer_butter_masala.jpg'),

            ('tasty-bites', 'North Indian', 'karnataka', 'Butter Naan', '40.00', 'VEG', 'MILD', 'SIDE', 10, False, False,
             'Pillowy clay-tandoor leavened flatbread brushed generously with melted farm butter.',
             'Freshly baked to order in clay tandoor.',
             '/static/images/foods/butter_naan.jpg'),

            ('tasty-bites', 'South Indian', 'karnataka', 'Neer Dosa & Coconut Chutney', '35.00', 'VEG', 'MILD', 'BREAKFAST', 12, True, True,
             'Feather-light lacy rice crepes from Tulunadu served with fresh grated coconut-jaggery & spicy chutney.',
             'A beloved Mangalorean delicacy meaning "Water Crepe" in Tulu.',
             '/static/images/foods/neer_dosa.jpg'),

            ('tasty-bites', 'Mangalorean Tandoor', 'karnataka', 'Kori Rotti (Mangalorean Chicken & Crisp Wafers)', '145.00', 'NON_VEG', 'HOT', 'MAIN', 22, True, True,
             'Crispy sun-dried boiled-rice wafers drenched in rich, aromatic Kundapura coconut chicken curry.',
             'The crown jewel of Tulunadu cuisine.',
             '/static/images/foods/kori_rotti.jpg'),

            # Sri Krishna Hotel (Udupi / Karnataka)
            ('sri-krishna-hotel', 'South Indian', 'karnataka', 'Mysore Masala Dosa', '60.00', 'VEG', 'MEDIUM', 'BREAKFAST', 15, True, False,
             'Crispy golden fermented crepe smeared with fiery red garlic chutney, stuffed with spiced potato palya & pure ghee.',
             'Born in royal Mysuru and perfected in Udupi tiffin halls.',
             '/static/images/foods/masala_dosa.jpg'),

            ('sri-krishna-hotel', 'South Indian', 'karnataka', 'Idli Vada Sambar Dip', '50.00', 'VEG', 'MILD', 'BREAKFAST', 10, True, False,
             'Two cloud-soft Udupi mallige idlis and one crispy medu vada served with temple-style sambar and coconut chutney.',
             'Wholesome steamed South Indian breakfast classic.',
             '/static/images/foods/idli_vada.jpg'),

            ('sri-krishna-hotel', 'South Indian', 'karnataka', 'Poori Saagu', '70.00', 'VEG', 'MILD', 'BREAKFAST', 14, False, False,
             'Three puffed golden wheat pooris served with aromatic Karnataka potato-onion saagu and coconut chutney.',
             'Traditional Sunday morning favorite.',
             '/static/images/foods/poori_saagu.jpg'),

            ('sri-krishna-hotel', 'South Indian', 'karnataka', 'Royal Bisi Bele Bath', '65.00', 'VEG', 'MEDIUM', 'MAIN', 15, True, False,
             'Hot lentil, rice, and garden vegetable mash slow-cooked with 18-spice Karnataka masala, tamarind, and ghee cashews.',
             'Signature one-pot comfort meal of Old Mysore.',
             '/static/images/foods/bisi_bele_bath.jpg'),

            ('sri-krishna-hotel', 'Cafe & Beverages', 'karnataka', 'Udupi Filter Coffee', '25.00', 'VEG', 'MILD', 'DRINK', 8, True, False,
             'Freshly brewed Chikmagalur Peaberry & Arabica decoction frothed with creamy farm milk in a brass davara-tumbler.',
             'Brewed from shade-grown Western Ghats coffee estates.',
             '/static/images/foods/filter_coffee.jpg'),

            # Malabar Backwater Kitchen (Kerala)
            ('malabar-backwater-kitchen', 'Malabar Special', 'kerala', 'Lace Appam with Vegetable Stew', '65.00', 'VEG', 'MILD', 'BREAKFAST', 16, True, True,
             'Fermented coconut-milk hoppers with crisp lacy edges and soft centers paired with fragrant cardamom coconut stew.',
             'Traditional Syrian Christian and Malabar breakfast delicacy.',
             '/static/images/foods/appam_stew.jpg'),

            ('malabar-backwater-kitchen', 'Malabar Special', 'kerala', 'Puttu & Kadala Curry', '60.00', 'VEG', 'MEDIUM', 'BREAKFAST', 15, True, True,
             'Steamed cylinders of ground rice layered with fresh coconut, served alongside roasted coconut black chickpea gravy.',
             'Iconic power breakfast across Kerala from Kozhikode to Trivandrum.',
             '/static/images/foods/puttu_kadala.jpg'),

            ('malabar-backwater-kitchen', 'Biryani & Pulao', 'kerala', 'Thalassery Malabar Biryani', '160.00', 'NON_VEG', 'MEDIUM', 'MAIN', 25, True, True,
             'Short-grain Khyma rice cooked in ghee with Wayanad spices, tender chicken, fried cashews, and Malabar raisins.',
             'Crafted along the historic spice coast of North Kerala.',
             '/static/images/foods/thalassery_biryani.jpg'),

            ('malabar-backwater-kitchen', 'Malabar Special', 'kerala', 'Flaky Kerala Parotta (2 Pcs)', '35.00', 'VEG', 'MILD', 'SIDE', 10, True, True,
             'Multi-layered ribbon-flaky Malabar flatbread griddled golden brown.',
             'Hand-fanned dough folded into crispy golden layers.',
             '/static/images/foods/kerala_parotta.jpg'),

            ('malabar-backwater-kitchen', 'Coastal Desserts', 'kerala', 'Ada Pradhaman Payasam', '55.00', 'VEG', 'MILD', 'DESSERT', 12, True, True,
             'Rich Onam Sadhya dessert made with rice ada, Marayoor jaggery, coconut milk, and ghee-roasted cashews.',
             'Essential finale of the traditional 26-dish Kerala Sadhya.',
             '/static/images/foods/payasam.jpg'),

            # Madurai Chettinad Mess (Tamil Nadu)
            ('madurai-chettinad-mess', 'South Indian', 'tamil-nadu', 'Chettinad Pepper Chicken', '155.00', 'NON_VEG', 'HOT', 'MAIN', 22, True, False,
             'Slow-roasted chicken in freshly ground kalpasi, star anise, Tellicherry black pepper, and Karaikudi masala.',
             'Heirloom recipe from the Chettiar mansions of Karaikudi.',
             '/static/images/foods/chettinad_chicken.jpg'),

            ('madurai-chettinad-mess', 'South Indian', 'tamil-nadu', 'Madurai Kothu Parotta', '95.00', 'VEG', 'HOT', 'MAIN', 16, True, False,
             'Rhythmically shredded flaky parotta tossed on a hot iron tawa with spicy salna, onions, and curry leaves.',
             'Famous late-evening street delicacy of Madurai.',
             '/static/images/foods/kothu_parotta.jpg'),

            ('madurai-chettinad-mess', 'South Indian', 'tamil-nadu', 'Ven Pongal & Medu Vada', '55.00', 'VEG', 'MILD', 'BREAKFAST', 12, True, False,
             'Creamy rice and moong dal tempered with whole black pepper, cumin, ginger, and cashews in pure cow ghee.',
             'Traditional harvest & temple offering across Tamil Nadu.',
             '/static/images/foods/ven_pongal.jpg'),

            # Local Cafe
            ('local-cafe', 'Cafe & Beverages', 'karnataka', 'Classic Cold Coffee', '80.00', 'VEG', 'MILD', 'DRINK', 10, True, False,
             'Chilled espresso blended with creamy milk, Belgian cocoa, and vanilla ice cream float.',
             'Roasted with Coorg Arabica beans.',
             '/static/images/foods/cold_coffee.jpg'),

            ('local-cafe', 'Fast Food', 'karnataka', 'Crispy Chicken Burger', '120.00', 'NON_VEG', 'MEDIUM', 'MAIN', 18, True, False,
             'Brioche bun stacked with herb-crisp chicken fillet, aged cheddar, pickled jalapenos, and chipotle aioli.',
             'Hand-crafted gourmet burger with dynamic size & add-on customization.',
             '/static/images/foods/chicken_burger.jpg'),

            ('local-cafe', 'Fast Food', 'karnataka', 'Crunchy Veg Burger', '95.00', 'VEG', 'MEDIUM', 'MAIN', 15, False, False,
             'Golden herb-potato & green pea patty with crisp lettuce, melted cheese slice, and tangy house sauce.',
             '100% vegetarian cafe favorite.',
             '/static/images/foods/veg_burger.jpg'),

            ('local-cafe', 'Fast Food', 'karnataka', 'Peri-Peri French Fries', '90.00', 'VEG', 'MEDIUM', 'STARTER', 12, True, False,
             'Double-cooked skin-on potato fries dusted with smoky peri-peri spice and served with cheesy dip.',
             'Crispy outside, fluffy inside.',
             '/static/images/foods/french_fries.jpg'),

            # Spice Junction (Telangana)
            ('spice-junction', 'Biryani & Pulao', 'telangana', 'Veg Dum Biryani', '140.00', 'VEG', 'MEDIUM', 'MAIN', 22, True, False,
             'Long-grain basmati rice layered with spiced seasonal vegetables, paneer, saffron milk, and burani raita.',
             'Cooked in sealed handis with aromatic Nizami potli masala.',
             '/static/images/foods/veg_biryani.jpg'),

            # Urban Cravings (Maharashtra)
            ('urban-cravings', 'Fast Food', 'maharashtra', 'Margherita Pizza', '159.00', 'VEG', 'MILD', 'MAIN', 20, True, False,
             'Hand-stretched sourdough crust topped with San Marzano tomato sauce, fresh mozzarella, and sweet basil.',
             'Stone-baked for a blistered, airy crust.',
             '/static/images/foods/margherita_pizza.jpg'),

            ('urban-cravings', 'Fast Food', 'maharashtra', 'Tandoori Paneer Pizza', '189.00', 'VEG', 'MEDIUM', 'MAIN', 22, True, False,
             'Loaded with smoky tandoori paneer cubes, crisp capsicum, red paprika, and molten mozzarella.',
             'Fusion Indian-Italian bestseller.',
             '/static/images/foods/paneer_pizza.jpg'),

            ('urban-cravings', 'Fast Food', 'maharashtra', 'Mumbai Special Vada Pav (2 Pcs)', '45.00', 'VEG', 'HOT', 'SNACK', 10, True, False,
             'Pillow-soft ladi pav stuffed with hot batata vada, dry fiery garlic chutney, and fried green chilies.',
             'The heartbeat of Mumbai street food.',
             '/static/images/foods/vada_pav.jpg'),

            # Fresh Juice Corner & Sweet Treats & Home Kitchen
            ('fresh-juice-corner', 'Cafe & Beverages', 'karnataka', 'Fresh Lime Soda (Sweet & Salt)', '30.00', 'VEG', 'MILD', 'DRINK', 6, True, True,
             'Sparkling coastal cooler made with freshly squeezed lime, mint leaves, and black rock salt.',
             'Refreshing companion to spicy biryanis and coastal curries.',
             '/static/images/foods/lime_soda.jpg'),

            ('sweet-treats', 'Bakery & Desserts', 'karnataka', 'Warm Chocolate Walnut Brownie', '85.00', 'VEG', 'MILD', 'DESSERT', 10, True, False,
             'Fudgy dark chocolate brownie studded with roasted walnuts and drizzled with warm ganache.',
             'Baked fresh every morning.',
             '/static/images/foods/brownie.jpg'),

            ('sweet-treats', 'Bakery & Desserts', 'karnataka', 'Royal Ghee Mysore Pak', '60.00', 'VEG', 'MILD', 'DESSERT', 8, True, False,
             'Melt-in-mouth gram flour fudge cooked in pure aromatic cow ghee and cardamom.',
             'Created in the royal kitchens of Mysuru Palace.',
             '/static/images/foods/mysore_pak.jpg'),

            ('home-kitchen', 'Home Food & Healthy', 'karnataka', 'Mangaluru Banana Buns (2 Pcs)', '50.00', 'VEG', 'MILD', 'BREAKFAST', 14, True, True,
             'Fluffy, golden-fried sweet banana sourdough puris served with spicy coconut chutney and sambar.',
             'Unique Tulunadu sweet-savory breakfast specialty.',
             '/static/images/foods/mangalore_buns.jpg'),

            ('home-kitchen', 'Home Food & Healthy', 'karnataka', 'Wholesome Ragi Mudde & Soppu Saaru', '75.00', 'VEG', 'MEDIUM', 'MAIN', 18, True, False,
             'Calcium-rich steamed finger-millet balls served with nutritious greens & lentil saaru and farm ghee.',
             'Traditional healthy superfood of rural & urban Karnataka.',
             '/static/images/foods/ragi_mudde.jpg'),
        ]

        created_foods = []
        for b_slug, c_name, r_slug, fname, price_str, veg, spice, course, prep, best, coastal, desc, story, img in foods_seed:
            biz = biz_map[b_slug]
            cat = fcat_map.get(c_name)
            reg = region_map.get(r_slug)
            price_dec = Decimal(price_str)

            food, _ = FoodItem.objects.update_or_create(
                business=biz,
                name=fname,
                defaults={
                    'category': cat,
                    'region': reg,
                    'description': desc,
                    'price': price_dec,
                    'veg_type': veg,
                    'spice_level': spice,
                    'meal_course': course,
                    'preparation_time': prep,
                    'calories': 320 if veg == 'VEG' else 460,
                    'origin_story': story,
                    'preparation_style': 'Slow-cooked in small batches with fresh regional spices',
                    'regional_significance': f"Signature specialty of {reg.name if reg else 'Coastal India'}",
                    'image_url': img,
                    'stock_quantity': 60,
                    'is_available': True,
                    'is_bestseller': best,
                    'is_coastal_favorite': coastal,
                    'is_healthy': course in ('BREAKFAST', 'DRINK') or 'Ragi' in fname or 'Idli' in fname,
                    'rating': Decimal('4.9'),
                    'order_count': 48 if best else 22,
                }
            )
            # Ensure customizations exist (Section 36)
            if not food.customizations.exists():
                FoodCustomization.objects.create(food_item=food, group_type='SIZE', option_name='Regular', price_delta=Decimal('0.00'), is_default=True)
                FoodCustomization.objects.create(food_item=food, group_type='SIZE', option_name='Large', price_delta=Decimal('35.00'))
                if 'Burger' in fname or 'Pizza' in fname:
                    FoodCustomization.objects.create(food_item=food, group_type='ADDON', option_name='Cheese', price_delta=Decimal('30.00'))
                    FoodCustomization.objects.create(food_item=food, group_type='ADDON', option_name='Extra Patty / Topping', price_delta=Decimal('60.00'))
                    FoodCustomization.objects.create(food_item=food, group_type='ADDON', option_name='Jalapeno', price_delta=Decimal('20.00'))
                else:
                    FoodCustomization.objects.create(food_item=food, group_type='ADDON', option_name='Extra Ghee / Coconut Chutney', price_delta=Decimal('15.00'))
                    FoodCustomization.objects.create(food_item=food, group_type='ADDON', option_name='Papad & Pickle Side', price_delta=Decimal('10.00'))

            created_foods.append(food)

            # Also seed RegionalFood showcase entry
            if reg and (best or coastal):
                RegionalFood.objects.update_or_create(
                    region=reg,
                    name=fname,
                    defaults={
                        'description': desc,
                        'typical_price': price_dec,
                        'veg_type': veg,
                        'spice_level': spice,
                        'popular_in_cities': biz.city,
                        'origin_story': story,
                        'preparation_style': 'Traditional stone-ground spices & earthen cookware',
                        'regional_significance': f"Iconic dish of {reg.name}",
                        'image_url': img,
                    }
                )

        # 7. Seed Coupons, Business Offers & Festival Campaigns (Sections 13, 27, 90)
        coupons_seed = [
            ('TASTY20', '20% OFF on Lunch & Dinner', 'Save 20% up to ₹100 on any local food store', 'PERCENT', '20.00', '149.00'),
            ('FREEDEL', 'FREE DELIVERY above ₹199', 'Zero delivery fee on eligible local orders', 'FREE_DELIVERY', '0.00', '199.00'),
            ('COASTAL50', 'Flat ₹50 OFF Coastal Feast', 'Valid on Coastal & Regional specialties above ₹249', 'FLAT', '50.00', '249.00'),
            ('WELCOME30', '30% OFF First Regional Order', 'Explore any Indian state cuisine with 30% savings', 'PERCENT', '30.00', '129.00'),
        ]
        for code, title, desc, dtype, val, min_ord in coupons_seed:
            Coupon.objects.update_or_create(
                code=code,
                defaults={
                    'title': title,
                    'description': desc,
                    'discount_type': dtype,
                    'discount_value': Decimal(val),
                    'min_order_amount': Decimal(min_ord),
                    'max_discount': Decimal('100.00'),
                    'is_active': True,
                }
            )

        offers_seed = [
            (biz_map['tasty-bites'], region_map['karnataka'], '20% OFF on Lunch', 'Use code TASTY20 between 12 PM – 4 PM on Biryanis & Meals', 'LUNCH', 'TASTY20', 20, '149.00', 'Mysuru Dasara'),
            (biz_map['samudra-ras-coastal'], region_map['goa'], 'FREE DELIVERY above ₹199', 'Freshly caught coastal curries delivered piping hot', 'FREE_DELIVERY', 'FREEDEL', 100, '199.00', 'Coastal Fest'),
            (biz_map['malabar-backwater-kitchen'], region_map['kerala'], 'Onam Sadhya & Malabar Feast 25% OFF', 'Celebrate with Appam, Meen Curry & Ada Payasam', 'FESTIVAL', 'TASTY20', 25, '199.00', 'Onam Special'),
            (biz_map['sri-krishna-hotel'], region_map['karnataka'], 'Buy 2 Get 1 on Filter Coffee & Vada', 'Morning tiffin combo offer from 7:30 AM – 11:00 AM', 'BOGO', 'WELCOME30', 30, '120.00', 'Ugadi Special'),
        ]
        for biz, reg, title, sub, ptype, code, pct, min_v, fest in offers_seed:
            Offer.objects.update_or_create(
                business=biz,
                title=title,
                defaults={
                    'region': reg,
                    'subtitle': sub,
                    'promo_type': ptype,
                    'coupon_code': code,
                    'discount_percentage': pct,
                    'min_order_value': Decimal(min_v),
                    'festival_tag': fest,
                    'badge_text': fest.upper(),
                    'is_approved': True,
                    'is_active': True,
                }
            )
            RegionalOffer.objects.update_or_create(
                region=reg,
                title=title,
                defaults={
                    'business': biz,
                    'festival_name': fest,
                    'subtitle': sub,
                    'coupon_code': code,
                    'discount_percentage': pct,
                    'is_approved': True,
                    'is_active': True,
                }
            )

        # 8. Seed Sample Order #TT1024 + Delivery + Invoice + Analytics + Reviews (Sections 16, 25, 28, 30)
        tasty_bites = biz_map['tasty-bites']
        biryani_item = FoodItem.objects.filter(business=tasty_bites, name='Chicken Biryani').first()
        ch65_item = FoodItem.objects.filter(business=tasty_bites, name='Chicken 65').first()

        sample_order, created_ord = Order.objects.update_or_create(
            order_number='TT1024',
            defaults={
                'customer': customer_user,
                'business': tasty_bites,
                'region': region_map['karnataka'],
                'customer_name': 'Ananya Rao',
                'customer_phone': '+91 9845011223',
                'delivery_address': 'Flat 302, Palm Grove Apartments, MG Road',
                'delivery_area': 'MG Road',
                'delivery_city': 'Mangaluru',
                'delivery_lat': 12.8820,
                'delivery_lng': 74.8510,
                'subtotal': Decimal('510.00'),
                'discount_amount': Decimal('50.00'),
                'points_discount': Decimal('0.00'),
                'tax_amount': Decimal('23.00'),
                'delivery_fee': Decimal('0.00'),
                'total_amount': Decimal('483.00'),
                'coupon_code': 'TASTY20',
                'status': 'PREPARING',
                'payment_method': 'UPI',
                'payment_status': 'PAID',
                'estimated_delivery_mins': 24,
                'points_earned': 48,
                'accepted_at': timezone.now() - timedelta(minutes=8),
            }
        )
        if created_ord or not sample_order.items.exists():
            sample_order.items.all().delete()
            if biryani_item:
                OrderItem.objects.create(
                    order=sample_order,
                    food_item=biryani_item,
                    food_name='Chicken Biryani',
                    unit_price=Decimal('180.00'),
                    quantity=2,
                    customization_details='Size: Regular • Spice: Medium',
                    line_total=Decimal('360.00'),
                )
            if ch65_item:
                OrderItem.objects.create(
                    order=sample_order,
                    food_item=ch65_item,
                    food_name='Chicken 65',
                    unit_price=Decimal('150.00'),
                    quantity=1,
                    customization_details='Spice: Hot',
                    line_total=Decimal('150.00'),
                )

        Payment.objects.update_or_create(
            order=sample_order,
            defaults={
                'user': customer_user,
                'transaction_id': 'TXN-TT1024DEMO',
                'gateway': 'TASTY_TAP_MOCK_GATEWAY',
                'payment_method': 'UPI',
                'amount': Decimal('483.00'),
                'status': 'SUCCESS',
                'masked_instrument': 'ananya@okicici',
            }
        )
        Delivery.objects.update_or_create(
            order=sample_order,
            defaults={
                'partner': rider_partner,
                'status': 'ASSIGNED',
                'pickup_address': f"{tasty_bites.name}, {tasty_bites.area}, {tasty_bites.city}",
                'drop_address': 'Flat 302, Palm Grove Apartments, MG Road, Mangaluru',
                'distance_km': Decimal('2.1'),
                'estimated_mins': 22,
                'delivery_earning': Decimal('40.00'),
                'rider_lat': 12.8760,
                'rider_lng': 74.8465,
            }
        )

        # Seed 7 days of BusinessAnalytics for Tasty Bites & Samudra Ras
        today_d = date.today()
        rev_series = [2450, 2890, 3120, 2780, 3650, 4120, 3890]
        ord_series = [16, 19, 22, 18, 26, 31, 28]
        for i in range(7):
            d = today_d - timedelta(days=6 - i)
            BusinessAnalytics.objects.update_or_create(
                business=tasty_bites,
                date=d,
                defaults={
                    'daily_orders': ord_series[i],
                    'daily_revenue': Decimal(str(rev_series[i])),
                    'new_customers': 6 + (i % 4),
                    'returning_customers': 10 + i,
                    'average_order_value': Decimal('165.00'),
                    'top_product_name': 'Chicken Biryani',
                    'peak_hour': '1:00 PM - 2:30 PM',
                    'store_views': 140 + i * 18,
                }
            )

        # Seed Verified Customer Reviews
        reviews_seed = [
            (tasty_bites, biryani_item, 5, 5, 'Authentic Mangalorean flavors! The Chicken Biryani and Chicken 65 arrived piping hot in 22 minutes.', 'Thank you Ananya! Delighted you loved our signature dum biryani.'),
            (biz_map['samudra-ras-coastal'], None, 5, 5, 'The Kerala Meen Curry and Konkani Bangda Fry taste just like a traditional coastal home meal. Highly recommended!', 'Warm coastal greetings! Glad you enjoyed the earthen-pot Meen Curry.'),
            (biz_map['sri-krishna-hotel'], None, 5, 5, 'Crispy Mysore Masala Dosa and authentic brass-davara Filter Coffee for just ₹85 total. Best local tiffin store!', 'Namaskara! Happy to serve fresh Udupi tiffins every morning.'),
        ]
        for biz, fitem, br, fr, comment, reply in reviews_seed:
            Review.objects.update_or_create(
                user=customer_user,
                business=biz,
                comment=comment,
                defaults={
                    'food_item': fitem,
                    'order': sample_order if biz == tasty_bites else None,
                    'business_rating': br,
                    'food_rating': fr,
                    'is_verified_order': True,
                    'business_reply': reply,
                    'replied_at': timezone.now(),
                }
            )

        # Seed Notifications
        Notification.objects.get_or_create(
            recipient=partner_user,
            title='New Order Received! Order #TT1024',
            defaults={
                'target_role': 'BUSINESS_PARTNER',
                'notification_type': 'ORDER',
                'message': 'Customer ordered Chicken Biryani ×2, Chicken 65 ×1. Status: Preparing.',
                'link_url': '/dashboard/business/',
            }
        )
        Notification.objects.get_or_create(
            recipient=customer_user,
            title='Order #TT1024 is Being Prepared 🔥',
            defaults={
                'target_role': 'CUSTOMER',
                'notification_type': 'ORDER',
                'message': 'Tasty Bites accepted your order and is preparing your fresh meal!',
                'link_url': '/orders/TT1024/track/',
            }
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded TASTY TAP with 12 Regions, 13 Local Businesses, 26+ Regional Dishes, Offers, Analytics & Demo Accounts!"))
