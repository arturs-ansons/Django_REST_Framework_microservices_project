Order Service

    The Order Service is a Django REST Framework (DRF) microservice responsible for managing orders in the eCommerce platform.
    It communicates with the User Service and Product Service to validate users and products.

🚀 Features

    Create orders (pending by default).

    Validate users and products through service-to-service API calls.

    Calculate total price using product price × quantity.


📦 Tech Stack

    Django + Django REST Framework

    mySQL (via Django ORM)

    Docker + docker-compose

⚙️ Environment Variables

    USER_SERVICE_URL	http://user_service:8000/api/users/	Base URL of the User Service
    PRODUCT_SERVICE_URL	http://product_service:8000/api/products/	Base URL of the Product Service
    DATABASE_URL	postgres://user:password@db:5432/order_db	Postgres connection string

🐳 Running with Docker

docker compose up --build

docker compose exec order_service python manage.py migrate


🔑 API Endpoints

    POST	/api/orders/	Create a new order (status: pending).
    GET	/api/orders/	List all orders.
    GET	/api/orders/{id}/	Retrieve a specific order.


🧪 Testing Connectivity

    Quick script to check if dependent services (user + product) are reachable:

    docker compose exec order_service python tests/test_connect.py

📂 Project Structure

order_service/
├── order_service/         # Django project settings
├── orders/                # App containing views, models, serializers
│   ├── views.py           # OrderViewSet with /pay endpoint
│   ├── models.py          # Order model
│   ├── serializers.py     # DRF serializer
│ 
├── tests/                 # Integration & unit tests
├── Dockerfile
├── requirements.txt
└── README.md

🔮 Next Steps

Move payment logic into a Payment Service.

Extend order lifecycle with refunds & cancellations.