from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, TestCase
from businesses.models import Business
from core.models import Region
from menu.models import FoodItem
from orders.models import Order


class TastyTapMarketplaceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command('seed_data')

    def setUp(self):
        self.client = Client()

    def test_homepage_and_regional_switching(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'TASTY TAP')
        self.assertContains(resp, 'Quick Order Cart')

        # Switch region to Kerala
        resp_kl = self.client.get('/?region=kerala')
        self.assertEqual(resp_kl.status_code, 200)
        self.assertContains(resp_kl, 'Namaskaram Kerala')

        # Switch region via API
        api_resp = self.client.post(
            '/api/regions/',
            data={'region_slug': 'tamil-nadu'},
            content_type='application/json'
        )
        self.assertEqual(api_resp.status_code, 200)
        self.assertEqual(api_resp.json()['region']['name'], 'Tamil Nadu')

    def test_multi_vendor_cart_conflict_and_resolution(self):
        tasty_bites = Business.objects.get(slug='tasty-bites')
        sri_krishna = Business.objects.get(slug='sri-krishna-hotel')
        food_a = FoodItem.objects.filter(business=tasty_bites).first()
        food_b = FoodItem.objects.filter(business=sri_krishna).first()

        # Add item from Business A
        r1 = self.client.post(
            '/api/cart/',
            data={'action': 'add', 'food_id': food_a.id, 'quantity': 1},
            content_type='application/json'
        )
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json()['cart']['item_count'], 1)

        # Adding item from Business B without force_separate must return 409 Conflict (Section 9)
        r2 = self.client.post(
            '/api/cart/',
            data={'action': 'add', 'food_id': food_b.id, 'quantity': 1},
            content_type='application/json'
        )
        self.assertEqual(r2.status_code, 409)
        self.assertTrue(r2.json()['conflict'])
        self.assertIn("ordering from another business", r2.json()['message'])

        # Resolving with force_separate=True starts a separate order for Business B
        r3 = self.client.post(
            '/api/cart/',
            data={'action': 'add', 'food_id': food_b.id, 'quantity': 2, 'force_separate': True},
            content_type='application/json'
        )
        self.assertEqual(r3.status_code, 200)
        self.assertEqual(r3.json()['cart']['business_name'], sri_krishna.name)
        self.assertEqual(r3.json()['cart']['item_count'], 2)

    def test_partner_zero_joining_cost_registration_and_admin_approval(self):
        resp = self.client.get('/partner/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, '₹0')

        reg_resp = self.client.post('/partner/register/', data={
            'business_name': 'Coastal Tiffin Center',
            'owner_name': 'Suresh Nayak',
            'email': 'suresh@coastaltiffin.in',
            'phone': '+91 9845099111',
            'business_type': 'SMALL_HOTEL',
            'region_slug': 'karnataka',
            'address': 'Car Street',
            'area': 'Car Street',
            'city': 'Mangaluru',
            'state': 'Karnataka',
            'pincode': '575001',
            'cuisine': 'Mangalorean Tiffins',
            'dietary_type': 'VEG',
            'delivery_fee': '15',
            'description': 'Fresh morning idlis and buns.',
        })
        self.assertEqual(reg_resp.status_code, 302)
        new_biz = Business.objects.get(name='Coastal Tiffin Center')
        self.assertEqual(new_biz.status, 'PENDING')
        self.assertEqual(float(new_biz.joining_cost_inr), 0.0)

        # Admin approves the business
        admin_user = User.objects.get(username='admin')
        self.client.force_login(admin_user)
        approve_resp = self.client.post('/dashboard/admin/', data={
            'action': 'verify_business',
            'business_id': new_biz.id,
            'decision': 'APPROVED',
            'admin_remarks': 'Verified and approved!',
        })
        self.assertEqual(approve_resp.status_code, 302)
        new_biz.refresh_from_db()
        self.assertEqual(new_biz.status, 'APPROVED')

    def test_smart_meal_builder_and_tap_ai_assistant(self):
        meal_resp = self.client.post(
            '/api/recommendations/',
            data={'mode': 'meal_builder', 'budget': 500, 'people': 2, 'veg_type': 'ANY'},
            content_type='application/json'
        )
        self.assertEqual(meal_resp.status_code, 200)
        self.assertGreaterEqual(len(meal_resp.json()['courses']), 3)

        ai_resp = self.client.post(
            '/api/recommendations/',
            data={'mode': 'tap_ai', 'query': 'Find food under ₹200'},
            content_type='application/json'
        )
        self.assertEqual(ai_resp.status_code, 200)
        self.assertIn('reply', ai_resp.json())

    def test_order_tracking_and_pdf_invoice(self):
        track_resp = self.client.get('/orders/TT1024/track/')
        self.assertEqual(track_resp.status_code, 200)
        self.assertContains(track_resp, 'TT1024')

        pdf_resp = self.client.get('/orders/TT1024/invoice/')
        self.assertEqual(pdf_resp.status_code, 200)
        self.assertEqual(pdf_resp['Content-Type'], 'application/pdf')
        self.assertTrue(pdf_resp.content.startswith(b'%PDF'))

    def test_rest_api_endpoints(self):
        endpoints = [
            '/api/businesses/',
            '/api/foods/',
            '/api/categories/',
            '/api/offers/',
            '/api/reviews/',
            '/api/recommendations/',
            '/api/delivery/',
            '/api/search/?q=Biryani',
        ]
        for ep in endpoints:
            r = self.client.get(ep)
            self.assertEqual(r.status_code, 200, f"Endpoint failed: {ep}")

    def test_map_tile_proxy_and_api_key(self):
        tile_resp = self.client.get('/api/map-tiles/11/1449/952.png?style=street')
        self.assertEqual(tile_resp.status_code, 200)
        self.assertEqual(tile_resp['Content-Type'], 'image/png')
        self.assertGreater(len(tile_resp.content), 50)

        explore_resp = self.client.get('/explore/')
        self.assertEqual(explore_resp.status_code, 200)
        self.assertContains(explore_resp, 'TASTY_TAP_MAPS_API_KEY')
        self.assertContains(explore_resp, 'Maps API Key Active')

