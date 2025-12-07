// Configuration API
const API_URL = 'http://localhost:8000';

// Vérification d'authentification
// ⚠️ CORRECTION: Utiliser 'token' au lieu de 'access_token' pour correspondre au Login.html
function checkAuth() {
    const token = sessionStorage.getItem('token');
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
        
        if (!response.ok) {
            console.error('Failed to load user info');
            return null;
        }
        
        const data = await response.json();
        
        // Stocker dans sessionStorage
        sessionStorage.setItem('username', data.username);
        sessionStorage.setItem('fullName', data.full_name);
        sessionStorage.setItem('studentId', data.student_id);
        sessionStorage.setItem('email', data.email);
        sessionStorage.setItem('role', data.role);
        
        // Mettre à jour l'affichage
        updateUserDisplay(data);
        
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
            ? userData.full_name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2)
            : userData.username.substring(0, 2).toUpperCase();
        userAvatarElement.textContent = initials;
    }
}

// Fonction de déconnexion
function logout() {
    sessionStorage.clear();
    window.location.href = 'Login.html';
}

// Charger les données médicales
async function loadMedicalRecords() {
    try {
        const response = await authenticatedFetch(`${API_URL}/medical-records`);
        if (!response || !response.ok) return null;
        return await response.json();
    } catch (error) {
        console.error('Error loading medical records:', error);
        return null;
    }
}

// Charger les rendez-vous
async function loadAppointments() {
    try {
        const response = await authenticatedFetch(`${API_URL}/appointments`);
        if (!response || !response.ok) return [];
        return await response.json();
    } catch (error) {
        console.error('Error loading appointments:', error);
        return [];
    }
}

// Charger l'historique des visites
async function loadVisitHistory() {
    try {
        const response = await authenticatedFetch(`${API_URL}/visits/all`);
        if (!response || !response.ok) return null;
        return await response.json();
    } catch (error) {
        console.error('Error loading visit history:', error);
        return null;
    }
}

// Créer un rendez-vous
async function createAppointment(appointmentData) {
    try {
        const response = await authenticatedFetch(`${API_URL}/appointments`, {
            method: 'POST',
            body: JSON.stringify(appointmentData)
        });
        
        if (!response) return null;
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to create appointment');
        }
        
        return data;
    } catch (error) {
        console.error('Error creating appointment:', error);
        throw error;
    }
}

// Annuler un rendez-vous
async function cancelAppointment(appointmentId) {
    try {
        const response = await authenticatedFetch(`${API_URL}/appointments/${appointmentId}`, {
            method: 'DELETE'
        });
        
        if (!response) return null;
        return await response.json();
    } catch (error) {
        console.error('Error cancelling appointment:', error);
        throw error;
    }
}

// Ajouter une entrée médicale
async function addMedicalEntry(entryData) {
    try {
        const response = await authenticatedFetch(`${API_URL}/medical-records/entry`, {
            method: 'POST',
            body: JSON.stringify(entryData)
        });
        
        if (!response) return null;
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to add entry');
        }
        
        return data;
    } catch (error) {
        console.error('Error adding medical entry:', error);
        throw error;
    }
}

// Supprimer une entrée médicale
async function deleteMedicalEntry(entryId) {
    try {
        const response = await authenticatedFetch(`${API_URL}/medical-records/${entryId}`, {
            method: 'DELETE'
        });
        
        if (!response) return null;
        return await response.json();
    } catch (error) {
        console.error('Error deleting medical entry:', error);
        throw error;
    }
}

// Mettre à jour le profil
async function updateProfile(profileData) {
    try {
        const response = await authenticatedFetch(`${API_URL}/profile/update`, {
            method: 'PUT',
            body: JSON.stringify(profileData)
        });
        
        if (!response) return null;
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to update profile');
        }
        
        return data;
    } catch (error) {
        console.error('Error updating profile:', error);
        throw error;
    }
}

// Mettre à jour le contact d'urgence
async function updateEmergencyContact(contactData) {
    try {
        const response = await authenticatedFetch(`${API_URL}/profile/emergency-contact`, {
            method: 'PUT',
            body: JSON.stringify(contactData)
        });
        
        if (!response) return null;
        return await response.json();
    } catch (error) {
        console.error('Error updating emergency contact:', error);
        throw error;
    }
}

// Initialisation automatique au chargement de la page
document.addEventListener('DOMContentLoaded', async function() {
    // Ne pas vérifier l'auth sur les pages Login et Registration
    const currentPage = window.location.pathname.split('/').pop();
    const publicPages = ['Login.html', 'Registration.html', 'index.html', ''];
    
    if (!publicPages.includes(currentPage)) {
        const token = sessionStorage.getItem('token');
        if (!token) {
            window.location.href = 'Login.html';
            return;
        }
        
        // Charger les infos utilisateur
        await loadUserInfo();
    }
});