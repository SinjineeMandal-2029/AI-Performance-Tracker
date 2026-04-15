# 🎓 EduTrack AI — Student Performance Tracker & Predictor

A full-stack web application for tracking and predicting student academic performance.

**Color Palette:** #F2B418 · #ECF8FD · #AFCBD5 · #272838 · #815355  
**Stack:** HTML / CSS / JS  |  Python (Flask)  |  MySQL  |  AI (NumPy + Scikit-learn)

---

## 📁 Project Structure

```
edutrack/
├── index.html              ← Login / Sign Up page (first page)
├── student_dashboard.html  ← Student dashboard
├── teacher_dashboard.html  ← Teacher dashboard
├── parent_dashboard.html   ← Parent dashboard
├── admin_dashboard.html    ← Admin dashboard
├── styles.css              ← Shared dashboard styles
├── app.py                  ← Flask backend (all API routes)
├── ai_predictor.py         ← AI prediction & study suggestion engine
├── schema.sql              ← MySQL database schema + sample data
├── requirements.txt        ← Python dependencies
└── README.md
```

---

## ⚙️ Setup Instructions

### 1. MySQL Database

```bash
# Login to MySQL
mysql -u root -p

# Run the schema
mysql -u root -p < schema.sql
```

### 2. Python Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your_super_secret_key_here
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=edutrack_db
```

Then add this to the top of `app.py` (after imports):
```python
from dotenv import load_dotenv
load_dotenv()
```

### 4. Run the Application

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## 🔐 User Roles & Dashboards

| Role    | Dashboard              | Capabilities |
|---------|------------------------|--------------|
| Student | student_dashboard.html | View grades, attendance, AI predictions, assignments, study recommendations |
| Teacher | teacher_dashboard.html | Manage students, post grades, mark attendance, create assignments |
| Parent  | parent_dashboard.html  | Monitor child's performance, attendance, AI insights |
| Admin   | admin_dashboard.html   | User management, system overview, statistics |

---

## 🤖 AI Predictor

Located in `ai_predictor.py`, the AI module:

- **Predicts end-of-semester GPA** based on current scores + attendance trend
- **Generates study suggestions** with urgency levels (Critical → Minimal)
- **Recommends study hours** per subject based on current performance
- **Detects performance trends** (improving / declining / stable)

**Algorithm:**
```
predicted_score = avg_score + trend_bonus + attendance_bonus
```
- Trend bonus: ±15% weight on recent vs earlier scores
- Attendance bonus: +3 (≥90%), 0 (75–90%), -3 (60–75%), -7 (<60%)

---

## 🗃️ Key API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/signup` | Register new account |
| POST | `/api/auth/login` | Login |
| POST | `/api/auth/logout` | Logout |
| GET  | `/api/auth/me` | Get current user |

### Student
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/student/dashboard` | Full dashboard data |
| GET | `/api/student/grades` | Grade history |

### Teacher
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/teacher/students` | All students |
| POST | `/api/teacher/grades` | Add grade |
| POST | `/api/teacher/attendance` | Mark attendance |
| GET/POST | `/api/teacher/assignments` | Manage assignments |

### Parent
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/parent/children` | List children |
| GET | `/api/parent/child/<id>` | Child's dashboard |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/users` | All users |
| POST | `/api/admin/users` | Create user |
| DELETE | `/api/admin/users/<id>` | Delete user |
| GET | `/api/admin/stats` | System stats |

### AI
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/ai/predict/<student_id>` | Get AI predictions |

---

## 🚀 Next Steps / Enhancements

- Add email notifications for deadlines
- Integrate real ML model (scikit-learn Linear/Ridge Regression trained on historical data)
- Add file upload for assignment submissions
- Push notifications for parents when child is absent
- Export reports as PDF
- Add OAuth (Google login for university accounts)

---

*Built with ❤️ using EduTrack AI color palette: Gold · Ice Blue · Steel · Navy · Rose*
