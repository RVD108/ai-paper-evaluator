from fastapi import FastAPI, Form, File, UploadFile, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from pydantic import BaseModel  # <-- Importing BaseModel for Pydantic
import shutil

# Initialize FastAPI app
app = FastAPI()

# Database setup (SQLite in this case)
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Models for SQLAlchemy
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

# Create the tables in the database
Base.metadata.create_all(bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic model for user data (optional if needed for validation)
class UserCreate(BaseModel):
    username: str
    password: str

# Function to hash passwords
def hash_password(password: str):
    return pwd_context.hash(password)

# Function to verify passwords
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# Route to display the form for username, password, and PDF upload
@app.get("/", response_class=HTMLResponse)
async def form():
    return """
        <html>
            <head>
                <title>Exam Evaluation Portal</title>
                <style>
                    body {
                        font-family: Arial, sans-serif;
                        background-color: #f4f7fa;
                        margin: 0;
                        padding: 0;
                    }
                    .container {
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        text-align: center;
                    }
                    .form-container {
                        background-color: #ffffff;
                        padding: 40px;
                        border-radius: 8px;
                        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                        width: 400px;
                    }
                    h2 {
                        color: #333;
                        margin-bottom: 20px;
                    }
                    input[type="text"], input[type="password"], input[type="file"] {
                        margin-bottom: 20px;
                        padding: 10px;
                        font-size: 16px;
                    }
                    input[type="submit"] {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        padding: 15px 32px;
                        font-size: 16px;
                        cursor: pointer;
                        border-radius: 5px;
                    }
                    input[type="submit"]:hover {
                        background-color: #45a049;
                    }
                    .footer {
                        position: fixed;
                        bottom: 10px;
                        left: 50%;
                        transform: translateX(-50%);
                        color: #888;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="form-container">
                        <h2>Student Exam Evaluation Upload</h2>
                        <form action="/register/" method="post" enctype="multipart/form-data">
                            <input type="text" name="username" placeholder="Username" required><br>
                            <input type="password" name="password" placeholder="Password" required><br>
                            <input type="file" name="pdf_file" accept="application/pdf" required><br><br>
                            <input type="submit" value="Register and Upload">
                        </form>
                    </div>
                </div>
                <div class="footer">
                    <p>&copy; 2024 Exam Evaluation Portal</p>
                </div>
            </body>
        </html>
    """

# Route to handle user registration and file upload
@app.post("/register/")
async def register_user(
    username: str = Form(...), 
    password: str = Form(...), 
    pdf_file: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    # Check if the username already exists
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Hash the password before saving it to the database
    hashed_password = hash_password(password)

    # Create the new user in the database
    new_user = User(username=username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Save the uploaded PDF file
    file_location = f"uploads/{pdf_file.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(pdf_file.file, buffer)

    return {"message": "User registered and file uploaded successfully!", "user_id": new_user.id, "file_location": file_location}
