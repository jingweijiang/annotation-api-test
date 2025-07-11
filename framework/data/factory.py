"""
Data Factory for generating test data.

Provides utilities for creating realistic test data using Faker and Factory Boy.
"""

import json
import random
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import faker
from faker import Faker

from framework.utils.logger import get_logger


class DataFactory:
    """
    Factory for generating test data with realistic values.
    
    Features:
    - User data generation
    - Product data generation
    - Custom data templates
    - Localization support
    - Data persistence and loading
    """
    
    def __init__(self, config_manager=None, locale: str = 'en_US'):
        """
        Initialize data factory.
        
        Args:
            config_manager: Configuration manager instance
            locale: Locale for data generation
        """
        self.config = config_manager
        self.fake = Faker(locale)
        self.logger = get_logger(self.__class__.__name__)
        
        # Seed for reproducible data
        Faker.seed(42)
        random.seed(42)
        
        # Data templates directory
        self.templates_dir = Path('data/fixtures')
        
    def create_user(self, **overrides) -> Dict[str, Any]:
        """
        Create user test data.
        
        Args:
            **overrides: Fields to override in generated data
            
        Returns:
            User data dictionary
        """
        user_data = {
            'id': self.fake.uuid4(),
            'username': self.fake.user_name(),
            'email': self.fake.email(),
            'first_name': self.fake.first_name(),
            'last_name': self.fake.last_name(),
            'full_name': None,  # Will be computed
            'phone': self.fake.phone_number(),
            'date_of_birth': self.fake.date_of_birth(minimum_age=18, maximum_age=80).isoformat(),
            'address': {
                'street': self.fake.street_address(),
                'city': self.fake.city(),
                'state': self.fake.state(),
                'postal_code': self.fake.postcode(),
                'country': self.fake.country_code()
            },
            'profile': {
                'bio': self.fake.text(max_nb_chars=200),
                'avatar_url': self.fake.image_url(),
                'website': self.fake.url(),
                'social_media': {
                    'twitter': f"@{self.fake.user_name()}",
                    'linkedin': self.fake.url(),
                    'github': f"https://github.com/{self.fake.user_name()}"
                }
            },
            'preferences': {
                'language': self.fake.language_code(),
                'timezone': self.fake.timezone(),
                'notifications': {
                    'email': self.fake.boolean(),
                    'sms': self.fake.boolean(),
                    'push': self.fake.boolean()
                }
            },
            'status': random.choice(['active', 'inactive', 'pending']),
            'role': random.choice(['user', 'admin', 'moderator']),
            'created_at': self.fake.date_time_between(start_date='-2y', end_date='now').isoformat(),
            'updated_at': datetime.now().isoformat(),
            'last_login': self.fake.date_time_between(start_date='-30d', end_date='now').isoformat()
        }
        
        # Compute full name
        user_data['full_name'] = f"{user_data['first_name']} {user_data['last_name']}"
        
        # Apply overrides
        user_data.update(overrides)
        
        return user_data
        
    def create_product(self, **overrides) -> Dict[str, Any]:
        """
        Create product test data.
        
        Args:
            **overrides: Fields to override in generated data
            
        Returns:
            Product data dictionary
        """
        categories = ['Electronics', 'Clothing', 'Books', 'Home & Garden', 'Sports', 'Toys']
        
        product_data = {
            'id': self.fake.uuid4(),
            'sku': self.fake.ean13(),
            'name': self.fake.catch_phrase(),
            'description': self.fake.text(max_nb_chars=500),
            'short_description': self.fake.text(max_nb_chars=100),
            'category': random.choice(categories),
            'brand': self.fake.company(),
            'price': {
                'amount': round(random.uniform(10.0, 1000.0), 2),
                'currency': 'USD',
                'discount_percentage': random.randint(0, 50) if random.random() > 0.7 else 0
            },
            'inventory': {
                'stock_quantity': random.randint(0, 1000),
                'reserved_quantity': random.randint(0, 50),
                'available_quantity': None,  # Will be computed
                'warehouse_location': self.fake.city()
            },
            'dimensions': {
                'length': round(random.uniform(1.0, 100.0), 2),
                'width': round(random.uniform(1.0, 100.0), 2),
                'height': round(random.uniform(1.0, 100.0), 2),
                'weight': round(random.uniform(0.1, 50.0), 2),
                'unit': 'cm'
            },
            'images': [
                self.fake.image_url(width=800, height=600),
                self.fake.image_url(width=800, height=600),
                self.fake.image_url(width=800, height=600)
            ],
            'attributes': {
                'color': self.fake.color_name(),
                'material': random.choice(['Cotton', 'Plastic', 'Metal', 'Wood', 'Glass']),
                'size': random.choice(['XS', 'S', 'M', 'L', 'XL', 'XXL']),
                'warranty_months': random.choice([6, 12, 24, 36])
            },
            'ratings': {
                'average_rating': round(random.uniform(1.0, 5.0), 1),
                'total_reviews': random.randint(0, 1000),
                'rating_distribution': {
                    '5': random.randint(0, 100),
                    '4': random.randint(0, 100),
                    '3': random.randint(0, 100),
                    '2': random.randint(0, 100),
                    '1': random.randint(0, 100)
                }
            },
            'seo': {
                'meta_title': self.fake.sentence(nb_words=6),
                'meta_description': self.fake.text(max_nb_chars=160),
                'keywords': [self.fake.word() for _ in range(5)],
                'slug': self.fake.slug()
            },
            'status': random.choice(['active', 'inactive', 'draft', 'discontinued']),
            'featured': self.fake.boolean(chance_of_getting_true=20),
            'created_at': self.fake.date_time_between(start_date='-1y', end_date='now').isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Compute available quantity
        inventory = product_data['inventory']
        inventory['available_quantity'] = max(0, inventory['stock_quantity'] - inventory['reserved_quantity'])
        
        # Apply overrides
        product_data.update(overrides)
        
        return product_data
        
    def create_order(self, user_id: str = None, products: List[Dict] = None, **overrides) -> Dict[str, Any]:
        """
        Create order test data.
        
        Args:
            user_id: User ID for the order
            products: List of products in the order
            **overrides: Fields to override in generated data
            
        Returns:
            Order data dictionary
        """
        if not user_id:
            user_id = self.fake.uuid4()
            
        if not products:
            # Generate random products
            products = [
                {
                    'product_id': self.fake.uuid4(),
                    'quantity': random.randint(1, 5),
                    'unit_price': round(random.uniform(10.0, 200.0), 2)
                }
                for _ in range(random.randint(1, 5))
            ]
            
        # Calculate totals
        subtotal = sum(p['quantity'] * p['unit_price'] for p in products)
        tax_rate = 0.08
        tax_amount = round(subtotal * tax_rate, 2)
        shipping_cost = round(random.uniform(5.0, 25.0), 2)
        total_amount = subtotal + tax_amount + shipping_cost
        
        order_data = {
            'id': self.fake.uuid4(),
            'order_number': f"ORD-{self.fake.random_number(digits=8)}",
            'user_id': user_id,
            'status': random.choice(['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']),
            'items': products,
            'pricing': {
                'subtotal': subtotal,
                'tax_amount': tax_amount,
                'tax_rate': tax_rate,
                'shipping_cost': shipping_cost,
                'discount_amount': 0.0,
                'total_amount': total_amount,
                'currency': 'USD'
            },
            'shipping_address': {
                'name': self.fake.name(),
                'street': self.fake.street_address(),
                'city': self.fake.city(),
                'state': self.fake.state(),
                'postal_code': self.fake.postcode(),
                'country': self.fake.country_code(),
                'phone': self.fake.phone_number()
            },
            'billing_address': {
                'name': self.fake.name(),
                'street': self.fake.street_address(),
                'city': self.fake.city(),
                'state': self.fake.state(),
                'postal_code': self.fake.postcode(),
                'country': self.fake.country_code()
            },
            'payment': {
                'method': random.choice(['credit_card', 'debit_card', 'paypal', 'bank_transfer']),
                'status': random.choice(['pending', 'completed', 'failed', 'refunded']),
                'transaction_id': self.fake.uuid4(),
                'processed_at': self.fake.date_time_between(start_date='-7d', end_date='now').isoformat()
            },
            'tracking': {
                'carrier': random.choice(['UPS', 'FedEx', 'DHL', 'USPS']),
                'tracking_number': self.fake.ean13(),
                'estimated_delivery': (datetime.now() + timedelta(days=random.randint(1, 7))).isoformat()
            },
            'created_at': self.fake.date_time_between(start_date='-30d', end_date='now').isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Apply overrides
        order_data.update(overrides)
        
        return order_data
        
    def create_api_key(self, **overrides) -> Dict[str, Any]:
        """
        Create API key test data.
        
        Args:
            **overrides: Fields to override in generated data
            
        Returns:
            API key data dictionary
        """
        api_key_data = {
            'id': self.fake.uuid4(),
            'key': f"ak_{self.fake.password(length=32, special_chars=False)}",
            'name': self.fake.catch_phrase(),
            'description': self.fake.text(max_nb_chars=200),
            'user_id': self.fake.uuid4(),
            'permissions': random.sample(['read', 'write', 'delete', 'admin'], k=random.randint(1, 4)),
            'rate_limit': {
                'requests_per_minute': random.choice([100, 500, 1000, 5000]),
                'requests_per_hour': random.choice([1000, 5000, 10000, 50000]),
                'requests_per_day': random.choice([10000, 50000, 100000, 500000])
            },
            'ip_whitelist': [self.fake.ipv4() for _ in range(random.randint(0, 5))],
            'status': random.choice(['active', 'inactive', 'suspended']),
            'expires_at': (datetime.now() + timedelta(days=random.randint(30, 365))).isoformat(),
            'last_used_at': self.fake.date_time_between(start_date='-7d', end_date='now').isoformat(),
            'created_at': self.fake.date_time_between(start_date='-90d', end_date='now').isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        # Apply overrides
        api_key_data.update(overrides)
        
        return api_key_data
        
    def create(self, template_name: str, **kwargs) -> Dict[str, Any]:
        """
        Create data from template.
        
        Args:
            template_name: Name of data template
            **kwargs: Additional parameters for data generation
            
        Returns:
            Generated data dictionary
        """
        # Map template names to methods
        template_methods = {
            'user': self.create_user,
            'product': self.create_product,
            'order': self.create_order,
            'api_key': self.create_api_key
        }
        
        if template_name in template_methods:
            return template_methods[template_name](**kwargs)
        else:
            # Try to load from file
            return self.load_template(template_name, **kwargs)
            
    def load_template(self, template_name: str, **kwargs) -> Dict[str, Any]:
        """
        Load data template from file.
        
        Args:
            template_name: Template file name
            **kwargs: Variables for template rendering
            
        Returns:
            Generated data from template
        """
        template_path = self.templates_dir / f"{template_name}.json"
        
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
            
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
                
            # Simple variable substitution
            template_str = json.dumps(template_data)
            for key, value in kwargs.items():
                template_str = template_str.replace(f"{{{key}}}", str(value))
                
            return json.loads(template_str)
            
        except Exception as e:
            self.logger.error(f"Failed to load template {template_name}: {e}")
            raise
            
    def create_batch(self, template_name: str, count: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Create multiple data items from template.
        
        Args:
            template_name: Template name
            count: Number of items to create
            **kwargs: Additional parameters
            
        Returns:
            List of generated data items
        """
        return [self.create(template_name, **kwargs) for _ in range(count)]
