## 1. Problem Statement
The objective is to build a Centralized License Service for group.one to act as a unified "Source of Truth" for license lifecycles across multiple brands (e.g., WP Rocket, RankMath). Currently, brand-specific systems manage their own payments and users, but we need a central authority to provision, validate, and manage entitlements to ensure a seamless ecosystem for both the brands and the end-users.   


## 2. Architecture & Design Decisions
### Centralized vs. Distributed Licenses
For this system, a centralized architecture was chosen over a distributed one for several key reasons:

- Single Source of Truth: It prevents data fragmentation. When a user buys an add-on from a different brand, we can associate it with an existing key immediately because all data lives in one place.   
- Operational Simplicity: Managing security updates, API versioning, and observability is significantly easier in one service than across five or six different brand platforms.   
- Cross-Brand Visibility: It allows for features like "Listing all licenses by customer email across all brands" (US6), which would be highly complex and slow in a distributed environment.   

### Multi-Tenancy Strategy
We are implementing Logical Multi-tenancy using a brand_id foreign key on all core entities.

- Isolation: Every API request must be authenticated with a Brand-specific credential.  
- Data Integrity: Queries are scoped at the database level to ensure Brand A can never access Brand B's data.   


## 3. Tech Stack: Why Django?
For the implementation, Django (Python) is the chosen framework. It is ideal for this use case because:   

- Robust ORM: The complexity of the "License Key as a Container" (one key to many licenses) is easily handled by Django’s ORM, allowing for clean relationships and easy migrations.   
- Built-in Security: Django provides out-of-the-box protection against common vulnerabilities like SQL Injection and Cross-Site Request Forgery (CSRF), which is critical for a "Source of Truth" system.   
- Admin Interface: While no user-facing GUI is required, Django's auto-generated admin panel is a "free" benefit that allows internal staff to monitor and manage licenses during the initial phase.   
- Scalability & Ecosystem: Django's mature ecosystem (e.g., Django REST Framework) allows us to quickly build the "brand-integrable APIs" required by the assessment.
