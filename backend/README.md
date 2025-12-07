# CareConnect - Health Center Management System

Un système complet de gestion de centre de santé avec backend FastAPI et chatbot IA intégré.

## 🚀 Fonctionnalités

- **Authentification & Autorisation** : JWT tokens, bcrypt password hashing
- **Gestion des Rendez-vous** : Planification, modification, annulation
- **Dossiers Médicaux** : Allergies, médicaments, conditions médicales
- **Chatbot IA** : Assistant santé multilingue (English, Français, العربية)
- **Demandes d'Urgence** : Système d'alerte et de réponse rapide
- **Profils Étudiants** : Informations personnelles et académiques

## 📋 Prérequis

- Python 3.9+
- pip
- PostgreSQL (optionnel, SQLite par défaut)
- OpenAI API Key

## 🛠️ Installation

### 1. Cloner le projet

```bash
git clone <votre-repo>
cd careconnect-backend
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Configuration des variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
OPENAI_API_KEY=votre_cle_api_openai
SECRET_KEY=votre_cle_secrete_jwt
DATABASE_URL=sqlite:///./careconnect.db
```

### 5. Initialiser la base de données

```bash
python database.py
```

Cela créera les tables et insérera des données de test.

## 🚀 Lancement

### Démarrer le serveur backend

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Le serveur sera accessible sur : `http://localhost:8000`

### Documentation API

- Swagger UI : `http://localhost:8000/docs`
- ReDoc : `http://localhost:8000/redoc`

## 📁 Structure du Projet

```
careconnect-backend/
├── main.py                 # Application FastAPI principale
├── chatbot.py             # Service chatbot avec OpenAI
├── models.py              # Modèles SQLAlchemy
├── database.py            # Configuration base de données
├── routes/
│   └── chatbot_routes.py  # Routes du chatbot
├── requirements.txt       # Dépendances Python
├── .env                   # Variables d'environnement
├── .gitignore            # Fichiers à ignorer
└── README.md             # Cette documentation
```

## 🔐 Authentification

### Créer un compte

```bash
POST /auth/register
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123",
  "full_name": "John Doe",
  "student_id": "S2024001",
  "institution": "University Name",
  "program": "Computer Science"
}
```

### Se connecter

```bash
POST /auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "SecurePass123"
}
```

Réponse :
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "username": "john_doe",
    "full_name": "John Doe",
    "role": "student"
  }
}
```

### Utiliser le token

Pour les requêtes protégées, ajoutez le header :

```
Authorization: Bearer <votre_token>
```

## 💬 Chatbot API

### Envoyer un message

```bash
POST /chat/
Content-Type: application/json
Authorization: Bearer <token>

{
  "message": "J'ai mal à la tête, que dois-je faire?",
  "conversation_id": "optional-conversation-id",
  "user_context": {
    "name": "John Doe",
    "student_id": "S2024001"
  }
}
```

Réponse :
```json
{
  "reply": "Pour un mal de tête, voici quelques conseils...",
  "conversation_id": "uuid-generated",
  "tokens_used": 150
}
```

### Vérification de symptômes

```bash
POST /chat/symptom-check
Content-Type: application/json

{
  "symptom": "fever and cough"
}
```

## 📅 Rendez-vous

### Créer un rendez-vous

```bash
POST /appointments
Content-Type: application/json
Authorization: Bearer <token>

{
  "doctor_id": "dr_chen",
  "date": "2024-10-15",
  "time": "10:00 AM",
  "type": "General Consultation"
}
```

### Obtenir mes rendez-vous

```bash
GET /appointments
Authorization: Bearer <token>
```

### Annuler un rendez-vous

```bash
DELETE /appointments/{appointment_id}
Authorization: Bearer <token>
```

## 🏥 Dossiers Médicaux

### Obtenir mon dossier médical

```bash
GET /medical-records
Authorization: Bearer <token>
```

### Ajouter une entrée médicale

```bash
POST /medical-records/entry
Content-Type: application/json
Authorization: Bearer <token>

{
  "type": "allergy",
  "name": "Peanuts",
  "description": "Severe allergic reaction"
}
```

Types disponibles : `allergy`, `medication`, `condition`

## 🚨 Urgences

### Créer une demande d'urgence

```bash
POST /emergency
Content-Type: application/json
Authorization: Bearer <token>

{
  "type": "medical",
  "description": "Chest pain",
  "location": "Campus Building A, Room 201"
}
```

## 🎨 Intégration Frontend

### Ajouter le widget chatbot

Copiez le fichier `ChatbotWidget.html` et ajoutez ces lignes avant `</body>` :

```html
<!-- Widget Chatbot -->
<div id="chatbot-widget">
    <!-- Contenu du widget -->
</div>

<script src="chatbot-widget.js"></script>
```

### Configuration CORS

Le backend est configuré pour accepter les requêtes de tous les domaines. En production, modifiez `main.py` :

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://votre-domaine.com"],  # Domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🧪 Tests

### Comptes de test

```
Username: alexandra
Password: password123
Role: student

Username: admin
Password: admin123
Role: admin
```

### Tester le chatbot

```bash
curl -X POST http://localhost:8000/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, I need help"}'
```

## 🔧 Configuration Avancée

### Utiliser PostgreSQL

1. Installez PostgreSQL
2. Créez une base de données :

```sql
CREATE DATABASE careconnect_db;
```

3. Modifiez `.env` :

```env
DATABASE_URL=postgresql://username:password@localhost:5432/careconnect_db
```

### Utiliser Redis pour les sessions

1. Installez Redis
2. Ajoutez à `.env` :

```env
REDIS_URL=redis://localhost:6379/0
```

## 📊 Monitoring

Le backend expose des métriques Prometheus sur `/metrics`

## 🐛 Debugging

### Logs

Les logs sont affichés dans la console. Pour les sauvegarder :

```bash
uvicorn main:app --log-config logging.conf
```

### Mode Debug

Dans `.env` :

```env
DEBUG=True
```

## 🚀 Déploiement

### Production avec Gunicorn

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker

```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🤝 Contribution

1. Fork le projet
2. Créez une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push sur la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📝 License

Ce projet est sous licence MIT.

## 📧 Support

Pour toute question : support@careconnect.com

## 🙏 Remerciements

- FastAPI
- OpenAI
- SQLAlchemy
- Tous les contributeurs