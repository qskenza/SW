// Configuration API
const API_URL = 'http://localhost:8000';

// Vérification d'authentification
function checkAuth() {
    const token = sessionStorage.getItem('access_token');
    if (!token) {
        window.location.href = 'Login.html';
        return null;
    }
    return token;
}

// Fonction pour faire des requêtes authentifiées
async function authenticatedFetch(url, options = {}) {
    const token = checkAuth();
    if (!token) return null;
    
    const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers
    };
    
    try {
        const response = await fetch(url, { ...options, headers });
        
        if (response.status === 401) {
            // Token expiré
            sessionStorage.clear();
            window.location.href = 'Login.html';
            return null;
        }
        
        return response;
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}

// Charger les informations utilisateur
async function loadUserInfo() {
    try {
        const response = await authenticatedFetch(`${API_URL}/profile`);
        if (!response) return null;
        
        const data = await response.json();
        
        // Stocker dans sessionStorage
        sessionStorage.setItem('username', data.username);
        sessionStorage.setItem('fullName', data.full_name);
        sessionStorage.setItem('studentId', data.student_id);
        
        return data;
    } catch (error) {
        console.error('Error loading user info:', error);
        return null;
    }
}

// Mettre à jour l'affichage utilisateur dans le header
function updateUserDisplay(userData) {
    const userNameElement = document.querySelector('.user-info span');
    const userAvatarElement = document.querySelector('.user-avatar');
    
    if (userNameElement && userData) {
        userNameElement.textContent = userData.full_name || userData.username;
    }
    
    if (userAvatarElement && userData) {
        const initials = userData.full_name
            ? userData.full_name.split(' ').map(n => n[0]).join('').toUpperCase()
            : userData.username.substring(0, 2).toUpperCase();
        userAvatarElement.textContent = initials;
    }
}

// Fonction de déconnexion
function logout() {
    sessionStorage.clear();
    window.location.href = 'Login.html';
}