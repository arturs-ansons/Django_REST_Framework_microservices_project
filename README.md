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

### Testing

- Comprehensive **unit tests** cover:
  - Admin vs. normal user
  - Success vs. failure scenarios
  - External service failures
- **Mocking** used for **Order Service**, **Product Service**, and **RabbitMQ** for isolated tests

---

## 📈 Architecture & Flow

### User Flow

```mermaid
flowchart TD
    A["User Registration"] --> B["Login"]
    B --> C{"Check is_admin?"}
    C -- No --> U1["View Products/Orders"]
    U1 --> U2["Create Order via OrderViewSet"]
    U2 --> U3["Validate Product & Price via Product Service"]
    U3 --> U4["Order Created Successfully"]
    U4 --> RU1["Appoint Order → Create Shipment"]
    RU1 --> RU2["View My Shipments"]
    RU2 --> RU3["Pay for Shipment"]
    C -- Yes --> AU1["View All Shipments"]
    AU1 --> AU2["Ship a Shipment"]
    RU3 --> EndRU["Shipment Paid"]
    AU2 --> EndAU["Shipment Shipped"]





