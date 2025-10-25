# 🚚 Shipping Microservice

A **Shipping Microservice** built with **Django** and **Django REST Framework (DRF)** as part of a **microservices architecture**.  
This service manages shipments, integrates with multiple services, and demonstrates secure authentication, role-based access control, and event-driven messaging.

---

## 🛠 Built With

- Python 3.11
- Django 4.2
- Django REST Framework 3.16
- MySQL
- RabbitMQ
- Redis for caching
- JWT for authentication

---

## 🚀 Features

### REST API

- CRUD endpoints for **shipments** using `ViewSets` and `Serializers`
- Role-based **permissions** for secure access
- Follows **DRF best practices** for maintainable APIs

### Authentication & Authorization

- **JWT-based authentication**
- Custom `ServiceJWTAuthentication` extracts **roles directly from tokens**
- **Role-based access control**:
  - **Admins:** Can view/manage all shipments
  - **Users:** Can only access their own shipments

### Microservices Integration

- **Shipping Service** interacts with:
  - **Order Service** via HTTP to validate orders
  - **Product Service** (via Order Service) for product/price verification
- Publishes shipment events to **RabbitMQ** for asynchronous updates
- Designed for **independent, event-driven microservices architecture**

### Error Handling & Edge Cases

- Handles **non-pending orders**, **forbidden actions**, and **service unavailability**
- Ensures **production-ready reliability and robustness**

### Caching

- Uses **Redis** to cache shipment lists and frequently accessed data
- Improves performance for **high-traffic endpoints**

### CI/CD

- **Continuous Integration & Deployment** implemented via GitHub Actions / other CI pipeline
- Automatically:
  - Runs **unit tests** and **linting**
  - Builds Docker images
  - Deploys to staging/production environments (configurable)

### Testing

- Comprehensive **unit tests** cover:
  - Admin vs. normal user
  - Success vs. failure scenarios
  - External service failures
- **Mocking** used for **Order Service**, **Product Service**, and **RabbitMQ** for isolated tests

---

## 📈 Architecture & Flow

### User Flow

<img src="https://github.com/user-attachments/assets/5f01c270-0215-4a30-820a-116e597ee408" width="500" />

---

## 🐳 Docker Architecture

### Docker Service Flow

<img src="https://github.com/user-attachments/assets/2e66ef44-e177-4504-9433-e19995cfd30b" width="900" />
