# 🎓 CampusConnect — Placement Management System

A database-driven web application designed to simplify and organize campus placement activities by connecting students, recruiting companies, and administrators through a centralized platform.

## 📌 About the Project

**CampusConnect** is a DBMS mini project developed to manage the campus recruitment process efficiently. It provides a common platform where students can explore placement opportunities and apply for jobs, companies can publish openings and manage applications, and administrators can oversee placement-related records.

The project demonstrates how database management concepts can be integrated with a web application to support structured data storage, retrieval, updates, and reporting.

## ✨ Key Features

### 👨‍🎓 Student Portal
- View student profile and placement-related information.
- Explore available placement opportunities.
- Apply for eligible job openings.
- Manage skills and academic information.
- Track application status.

### 🏢 Company Portal
- Manage company information.
- Create and update placement opportunities.
- Specify the number of available openings.
- View applicants for published opportunities.
- Review applications and record recruitment decisions.
- Manage interview-related activities.

### 🛡️ Administrator Portal
- View and manage student records.
- View and manage company records.
- Monitor placement opportunities and applications.
- Oversee recruitment and interview-related information.
- Access centralized placement management functionality.

### 🔐 Role-Based Authentication
- Common login interface with role selection.
- Separate dashboards for students, companies, and administrators.
- Role-specific access to application features.

## 🧰 Technology Stack

| Component | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Flask |
| Database | PostgreSQL |
| Database connectivity | Python PostgreSQL driver |
| Development tools | Visual Studio Code / Antigravity, pgAdmin 4 |
| Version control | Git and GitHub |

## 🗄️ Database Design

CampusConnect uses a relational PostgreSQL database to maintain structured placement-related information.

The database includes entities for:

- Users and authentication
- Students and departments
- Companies
- Placement opportunities
- Applications
- Skills and student skills

The schema uses relational constraints and relationships to maintain data consistency and support queries across related tables.

## 🧠 DBMS Concepts Demonstrated

This project provides practical implementation of core DBMS concepts, including:

- **DDL:** Creating and modifying database structures.
- **DML:** Inserting, updating, and deleting records.
- **DQL:** Retrieving data using `SELECT` queries.
- **Constraints:** Enforcing data integrity through primary keys, foreign keys, unique constraints, and other applicable constraints.
- **Joins:** Combining related records across tables.
- **Aggregate functions:** Summarizing data using functions such as `COUNT`, `AVG`, `MIN`, and `MAX`.
- **Grouping:** Using `GROUP BY` and `HAVING` for grouped analysis.
- **Subqueries:** Retrieving data using nested queries.
- **CRUD operations:** Performing Create, Read, Update, and Delete operations through the application.

## ⚙️ Getting Started

### Prerequisites

Install the following before running the application:

- Python 3
- PostgreSQL
- Git

### 1. Clone the repository

```bash
git clone https://github.com/P-G02/CampusConnect-Placement-Management-System.git
cd CampusConnect-Placement-Management-System
```

### 2. Create a virtual environment

**Windows:**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks environment activation, you can use the virtual environment's Python executable directly instead.

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure PostgreSQL

Create or use a PostgreSQL database and configure the application with the appropriate database connection settings.

Keep database credentials and secret keys in environment variables or a local `.env` file. **Do not commit real credentials to GitHub.**

Use the project's existing configuration and migration instructions when connecting the application to a database. Review migration scripts before executing them, especially when using an existing database with important data.

### 5. Run the application

```bash
python app.py
```

Open the local URL printed in the terminal, typically:

```text
http://127.0.0.1:5000
```

**Note:** The exact database configuration and initialization steps depend on the project's current setup. Use the existing database schema and migration scripts rather than recreating or resetting a populated database.

## 🧪 Testing and Demonstration

The application can be demonstrated through role-based login and placement workflows.

Suggested demonstration sequence:

1. Log in as a student and explore placement opportunities.
2. Apply for an opportunity and review application status.
3. Log in as a company and manage openings and applications.
4. Demonstrate recruitment decisions and interview-related functionality.
5. Log in as an administrator and manage student and company records.
6. Execute SQL queries in PostgreSQL or pgAdmin 4 to demonstrate database operations.
7. Show how application actions are reflected in the underlying database.

## 🎯 Project Objectives

- Apply relational database concepts to a real-world campus placement scenario.
- Simplify placement data management through a centralized web application.
- Demonstrate CRUD operations and relational queries.
- Maintain structured records for students, companies, opportunities, and applications.
- Provide role-specific functionality for different stakeholders.

## 🔮 Future Enhancements

- Email notifications for application and interview updates.
- Advanced student–opportunity matching based on skills and academic performance.
- Placement analytics and visual reports.
- Resume upload and document management.
- Cloud deployment for access outside the local development environment.

## 👥 Contributors

Developed as a team-based academic **Database Management Systems (DBMS) mini project**.

## 📄 Academic Purpose

This project was developed for educational purposes to demonstrate the practical application of database management concepts, backend development, and frontend integration.

---

⭐ If you find this project useful, consider starring the repository.

**Repository:** [CampusConnect Placement Management System](https://github.com/P-G02/CampusConnect-Placement-Management-System)
