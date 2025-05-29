# FlashQuiz

FlashQuiz is a web-based flashcard application that helps users learn and memorize information through interactive flashcards. It supports both learners and content creators, allowing creators to make custom flashcard decks and learners to study them.

## Features

- User authentication (login/register)
- Create, edit, and delete flashcard decks
- Interactive flashcard study sessions
- Progress tracking for learners
- Analytics for content creators
- Explore public flashcard decks

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git

## Installation

1. Clone the repository:
```bash
git clone https://github.com/JulianoMI/ProjectPAS-FlashQuiz.git
cd ProjectPAS-FlashQuiz
```

2. Create a virtual environment:
```bash
python -m venv .venv
```

3. Activate the virtual environment:
- On Windows:
```bash
.venv\Scripts\activate
```
- On macOS/Linux:
```bash
source .venv/bin/activate
```

4. Install the required packages:
```bash
pip install -r requirements.txt
```

## Configuration

1. Create a `.env` file in the project root with the following content:
```
FLASK_APP=run.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/flashquiz.db
```

Replace `your-secret-key-here` with a secure secret key.

## Database Setup

The database will be automatically created when you first run the application, but you can manually initialize it with:

```bash
flask db init
flask db migrate
flask db upgrade
```

## Running the Application

1. Make sure your virtual environment is activated
2. Run the development server:
```bash
flask run
```
3. Open your web browser and navigate to `http://localhost:5000`

## User Roles

The application supports two types of users:
- **Learners**: Can study flashcard decks and track their progress
- **Creators**: Can create and manage flashcard decks, view analytics

## Project Structure

```
PROJECTPAS/
├── app/
│   ├── controllers/
│   │   ├── auth_controller.py
│   │   └── views_controller.py
│   ├── models/
│   │   └── models.py
│   ├── templates/
│   │   ├── auth/
│   │   └── *.html
│   ├── static/
│   └── __init__.py
├── instance/
├── .env
├── config.py
├── requirements.txt
├── README.md
└── run.py
```

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 