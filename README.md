---

# 🛡️ Privacy Challenge Platform

---

## ⚙️ Prerequisites

- 🐍 Python 3.10 or newer  
- 🐘 PostgreSQL (or SQLite for local testing)  
- 🐳 Redis (for Celery tasks)  

---

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/PhongTranE/Privacy-Challenge-Platform.git
   cd Privacy-Challenge-Platform
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - 📄 Copy `.env.example` to `.env` and update values as needed.
   - Or set variables directly in your shell.

5. **Start the development server:**
   ```bash
   ./infrastructure/scripts/run.sh dev
   ```

6. **Run database migrations:**
   ```bash
   ./infrastructure/scripts/run.sh exec
   1
   bash
   flask db init
   flask db migrate
   flask db upgrade
   flask seed
   ```

---

## 📝 Environment Variables

- `FLASK_ENV` — Environment (development/production)
- `DATABASE_URL` — Database connection string
- `SECRET_KEY` — Flask secret key
- `JWT_SECRET_KEY` — JWT signing key
- `GCS_BUCKET_NAME` — Google Cloud Storage bucket (if used)
- `REDIS_URL` — Redis connection string (for Celery)
- ...and others as needed (see `config/`)

---

## 🧪 Unit Testing

- Run all unit tests using [Pytest](https://docs.pytest.org/):
  ```bash
  pytest
  ```

---

## 🚦 Performance Testing

- Performance/load testing is done using [k6](https://k6.io/).
- Example command to run a k6 test script:
  ```bash
  k6 run path/to/your_test_script.js
  ```
- See the `Test/` directory for sample k6 scripts and usage.

---

## 📬 Contact

For questions, suggestions, or support, please contact:

- **Project Maintainer:** [Phong Tran](mailto:phongtranhk20@gmail.com)
- **Repository:** [https://github.com/PhongTranE/Privacy-Challenge-Platform](https://github.com/PhongTranE/Privacy-Challenge-Platform)

---

*© 2025 Privacy Challenge Platform. All rights reserved.*
Beta
0 / 0
used queries
1
