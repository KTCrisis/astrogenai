/*
 * =============================================================================
 * ASTRO GENERATOR - JavaScript Frontend
 *
 * Auteur: AstroGenAI
 * Version: 2.0 (Refactorisée)
 * Description: Ce script gère toute la logique de l'interface Astro Generator,
 * y compris la navigation, les appels API au backend Flask, et l'affichage
 * dynamique des résultats pour la génération d'horoscopes, de vidéos et le chat.
 * =============================================================================
 */

/**
 * =============================================================================
 * I. ÉTAT DE L'APPLICATION ET CONFIGURATION GLOBALE
 *
 * Centralise les variables d'état et les données constantes de l'application
 * pour une gestion plus simple et prévisible.
 * =============================================================================
 */

// Objet pour stocker l'état global de l'application.
const appState = {
    currentSection: 'individual', // Section actuellement visible
    chatMessages: [],             // Historique des messages du chat
    selectedModel: 'llama3.1:8b-instruct-q8_0', // Modèle Ollama sélectionné par défaut
    availableModels: [],          // Liste des modèles disponibles, chargée au démarrage
    currentVideoProject: null,    // Données du dernier projet vidéo généré
    batchResults: null,           // Résultats de la dernière génération en lot
};

// Données constantes pour les signes astrologiques.
const signSymbols = { 'aries': '♈', 'taurus': '♉', 'gemini': '♊', 'cancer': '♋', 'leo': '♌', 'virgo': '♍', 'libra': '♎', 'scorpio': '♏', 'sagittarius': '♐', 'capricorn': '♑', 'aquarius': '♒', 'pisces': '♓' };
const signNames = { 'aries': 'Bélier', 'taurus': 'Taureau', 'gemini': 'Gémeaux', 'cancer': 'Cancer', 'leo': 'Lion', 'virgo': 'Vierge', 'libra': 'Balance', 'scorpio': 'Scorpion', 'sagittarius': 'Sagittaire', 'capricorn': 'Capricorne', 'aquarius': 'Verseau', 'pisces': 'Poissons' };

/**
 * =============================================================================
 * II. FONCTIONS UTILITAIRES GÉNÉRALES
 * =============================================================================
 */

/**
 * Effectue un appel API standardisé vers le backend Flask.
 * Gère automatiquement les états de chargement et l'affichage des erreurs.
 * ✅ NOUVEAU : Garantit une durée d'affichage minimale pour l'animation de chargement.
 * @param {string} endpoint - L'URL de l'API à appeler.
 * @param {object} options - Les options pour l'appel `fetch`.
 * @param {string} loadingId - L'ID de l'élément DOM du spinner de chargement.
 * @param {string} resultId - L'ID de l'élément DOM où afficher le résultat ou l'erreur.
 * @returns {Promise<object|null>} Les données JSON en cas de succès, sinon null.
 */
async function makeApiRequest(endpoint, options, loadingId, resultId) {
    const loadingElement = document.getElementById(loadingId);
    const resultElement = document.getElementById(resultId);
    
    // ✅ DÉBUT DE LA MODIFICATION : On prépare une promesse pour le délai minimum.
    const minimumLoadingTime = new Promise(resolve => setTimeout(resolve, 500)); // 500ms = 0.5 seconde
    const apiCallPromise = fetch(endpoint, options);

    if (loadingElement) loadingElement.classList.add('active');
    if (resultElement) resultElement.innerHTML = '';

    try {
        // ✅ On attend que l'appel API ET le délai minimum soient tous les deux terminés.
        const [apiResponse] = await Promise.all([apiCallPromise, minimumLoadingTime]);

        const data = await apiResponse.json();
        if (!apiResponse.ok || !data.success) {
            throw new Error(data.error || `Erreur HTTP ${apiResponse.status}`);
        }
        return data;
    } catch (error) {
        console.error(`Erreur API pour ${endpoint}:`, error);
        if (resultElement) showError(resultElement, error.message);
        return null;
    } finally {
        if (loadingElement) loadingElement.classList.remove('active');
    }
}

/**
 * Affiche un message d'erreur formaté dans un conteneur spécifié.
 * @param {HTMLElement} container - L'élément DOM où afficher l'erreur.
 * @param {string} message - Le message d'erreur à afficher.
 */
function showError(container, message) {
    container.innerHTML = `
        <div class="horoscope-result" style="border-color: #ff4444;">
            <div class="horoscope-text" style="color: #ff4444;">
                <strong>❌ Erreur:</strong> ${message}
            </div>
        </div>
    `;
}

/**
 * Copie un texte dans le presse-papiers avec une méthode de secours.
 * @param {string} text - Le texte à copier.
 * @returns {Promise<boolean>} Vrai si la copie a réussi.
 */
async function copyTextWithFallback(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            console.error('Erreur clipboard API:', err);
        }
    }
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);
        return successful;
    } catch (err) {
        document.body.removeChild(textArea);
        return false;
    }
}

/**
 * Formate une taille de fichier en B, KB, ou MB.
 * @param {number} bytes - La taille en octets.
 * @returns {string} La taille formatée.
 */
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
}

/**
 * Vérifie l'état général du backend.
 * @returns {Promise<boolean>} Vrai si le backend est sain.
 */
async function checkSystemHealth() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        return data.status === 'healthy';
    } catch (error) {
        console.error('Erreur lors de la vérification système:', error);
        return false;
    }
}

/**
 * =============================================================================
 * III. NAVIGATION ET GESTION DE L'INTERFACE
 * =============================================================================
 */

/**
 * Affiche une section spécifique de l'application et masque les autres.
 * @param {string} sectionName - Le nom de la section à afficher (ex: 'individual', 'daily').
 */
function showSection(sectionName) {
    document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    
    document.getElementById(`${sectionName}-section`)?.classList.add('active');
    document.getElementById(`nav-${sectionName}`)?.classList.add('active');
    
    appState.currentSection = sectionName;
    updatePageTitle(sectionName);
    
    // Ferme la sidebar sur mobile après un clic
    if (window.innerWidth <= 768) {
        document.getElementById('sidebar')?.classList.remove('open');
    }
}

/**
 * Met à jour le titre et le sous-titre de la page en fonction de la section active.
 * @param {string} sectionName - Le nom de la section.
 */
function updatePageTitle(sectionName) {
    const titles = {
        'individual': { title: 'Horoscope Individuel', subtitle: 'Générez votre horoscope personnel avec l\'IA' },
        'daily': { title: 'Horoscopes Quotidiens', subtitle: 'Tous les horoscopes du jour en un clic' },
        'context': { title: 'Contexte Astral', subtitle: 'Découvrez les influences cosmiques du moment' },
        'astrochart': { title: 'Carte du Ciel', subtitle: 'Visualisez les positions planétaires à une date donnée' },
        'chat': { title: 'Chat IA', subtitle: 'Discutez avec votre assistant astral' },
        'video': { title: 'Générateur Vidéo', subtitle: 'Créez du contenu vidéo pour vos réseaux sociaux' }
    };
    const titleInfo = titles[sectionName];
    if (titleInfo) {
        document.getElementById('pageTitle').textContent = titleInfo.title;
        document.getElementById('pageSubtitle').textContent = titleInfo.subtitle;
    }
}

/**
 * Bascule l'affichage de la sidebar sur les écrans mobiles.
 */
function toggleSidebar() {
    document.getElementById('sidebar')?.classList.toggle('open');
}

/**
 * Configure les gestionnaires pour le design responsive.
 */
function setupResponsiveHandlers() {
    function checkResponsive() {
        const menuToggle = document.querySelector('.menu-toggle');
        if (window.innerWidth <= 768) {
            if (menuToggle) menuToggle.style.display = 'block';
        } else {
            if (menuToggle) menuToggle.style.display = 'none';
            document.getElementById('sidebar')?.classList.remove('open');
        }
    }
    checkResponsive();
    window.addEventListener('resize', checkResponsive);
}


/**
 * =============================================================================
 * IV. GESTION DES MODÈLES OLLAMA
 * =============================================================================
 */

/**
 * Charge la liste des modèles Ollama disponibles depuis le backend.
 */
async function loadAvailableModels() {
    const statusDot = document.getElementById('model-status-dot');
    const statusText = document.getElementById('model-status-text');
    const modelSelect = document.getElementById('global-model-select');
    
    try {
        const response = await fetch('/api/ollama/models');
        const data = await response.json();

        if (data.success && data.models && data.models.length > 0) {
            appState.availableModels = data.models;
            modelSelect.innerHTML = '';
            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.name;
                option.textContent = model.name;
                modelSelect.appendChild(option);
            });
            
            const savedModel = localStorage.getItem('selectedModel') || appState.selectedModel;
            if (data.models.some(m => m.name === savedModel)) {
                modelSelect.value = savedModel;
                appState.selectedModel = savedModel;
            } else {
                appState.selectedModel = data.models[0].name;
                modelSelect.value = appState.selectedModel;
            }
            
            statusDot.className = 'status-dot connected';
            statusText.textContent = `${data.models.length} modèles`;
        } else {
            throw new Error(data.error || 'Aucun modèle trouvé');
        }
    } catch (error) {
        console.error('Erreur chargement modèles:', error);
        statusDot.className = 'status-dot error';
        statusText.textContent = 'Ollama offline';
    }
}

/**
 * Met à jour le modèle sélectionné et le sauvegarde.
 */
async function changeModel() {
    const modelSelect = document.getElementById('global-model-select');
    appState.selectedModel = modelSelect.value;
    localStorage.setItem('selectedModel', appState.selectedModel);
    
    const statusDot = document.getElementById('model-status-dot');
    const statusText = document.getElementById('model-status-text');
    statusDot.className = 'status-dot connected confirming';
    statusText.textContent = `Activé : ${appState.selectedModel.split(':')[0]}`;

    setTimeout(() => {
        statusDot.classList.remove('confirming');
        statusText.textContent = `${appState.availableModels.length} modèles`;
    }, 1500);
}

/**
 * =============================================================================
 * V. GÉNÉRATION D'HOROSCOPES ET CRÉATION DE HTML
 * =============================================================================
 */

/**
 * Génère un horoscope pour un signe et une date spécifiques.
 */
async function generateIndividualHoroscope() {
    const sign = document.getElementById('sign-select').value;
    const date = document.getElementById('date-input').value;

    if (!sign) {
        alert('Veuillez sélectionner un signe astrologique.');
        return;
    }

    const response = await makeApiRequest(
        '/api/generate_single_horoscope',
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sign, date })
        },
        'individual-loading',
        'individual-result'
    );

    if (response) {
        document.getElementById('individual-result').innerHTML = createHoroscopeResultHTML(response.result);
    }
}

/**
 * Génère les horoscopes pour les 12 signes pour une date donnée.
 */
async function generateDailyHoroscopes() {
    const date = document.getElementById('daily-date-input').value;
    const resultDiv = document.getElementById('daily-results');

    const response = await makeApiRequest(
        '/api/generate_daily_horoscopes',
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ date })
        },
        'daily-loading',
        'daily-results'
    );

    if (response) {
        const horoscopes = response.result.horoscopes;
        resultDiv.innerHTML = ''; // Vider le conteneur
        for (const [signKey, horoscope] of Object.entries(horoscopes)) {
            const cardHTML = horoscope.error 
                ? createErrorCard(signKey, horoscope.error) 
                : createHoroscopeCard(signKey, horoscope);
            resultDiv.innerHTML += cardHTML;
        }
    }
}

/**
 * Récupère et affiche le contexte astral pour une date donnée.
 */
async function getAstralContext() {
    const date = document.getElementById('context-date-input').value;
    const resultDiv = document.getElementById('context-result');

    const response = await makeApiRequest(
        '/api/get_astral_context',
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ date })
        },
        'context-loading',
        'context-result'
    );

    if (response) {
        const context = response.result;
        const planetsHtml = context.influential_planets.map(p => `<li><strong>${p.name}</strong> (${p.state}): ${p.influence}</li>`).join('');
        resultDiv.innerHTML = `
            <div class="horoscope-result">
                <div class="horoscope-header">
                    <div class="sign-icon">🌌</div>
                    <div class="horoscope-meta"><h3>Contexte Astral du ${context.date}</h3></div>
                </div>
                <div class="horoscope-text">
                    <h4>🌙 Phase Lunaire</h4><p>${context.lunar_phase}</p>
                    <h4>🍂 Saison</h4><p>${context.season} - ${context.seasonal_energy}</p>
                    <h4>🪐 Planètes Influentes</h4><ul>${planetsHtml}</ul>
                </div>
            </div>`;
    }
}

/**
 * Crée le HTML pour un résultat d'horoscope individuel.
 * @param {object} horoscope - L'objet horoscope retourné par l'API.
 * @returns {string} La chaîne de caractères HTML.
 */
function createHoroscopeResultHTML(horoscope) {
    const signKey = Object.keys(signNames).find(key => signNames[key] === horoscope.sign);
    return `
        <div class="horoscope-result">
            <div class="horoscope-header">
                <div class="sign-icon">${signSymbols[signKey] || '✨'}</div>
                <div class="horoscope-meta">
                    <h3>${horoscope.sign}</h3>
                    <p>📅 ${horoscope.date}</p>
                </div>
            </div>
            <div class="horoscope-text">${horoscope.horoscope}</div>
        </div>
    `;
}

/**
 * Crée le HTML pour une carte d'horoscope dans la grille quotidienne.
 * @param {string} signKey - La clé du signe (ex: 'aries').
 * @param {object} horoscope - L'objet horoscope.
 * @returns {string} La chaîne de caractères HTML.
 */
function createHoroscopeCard(signKey, horoscope) {
    return `
        <div class="horoscope-card">
            <div class="card-header">
                <div class="card-icon">${signSymbols[signKey] || '✨'}</div>
                <div>
                    <div class="card-title">${horoscope.sign}</div>
                    <div class="card-dates">${horoscope.word_count} mots</div>
                </div>
            </div>
            <div class="card-content">${horoscope.horoscope}</div>
        </div>
    `;
}

/**
 * Crée le HTML pour une carte d'erreur dans la grille.
 * @param {string} signKey - La clé du signe.
 * @param {string} error - Le message d'erreur.
 * @returns {string} La chaîne de caractères HTML.
 */
function createErrorCard(signKey, error) {
    return `
        <div class="horoscope-card error">
            <div class="card-header">
                <div class="card-icon">${signSymbols[signKey] || '❌'}</div>
                <div>
                    <div class="card-title">${signNames[signKey]}</div>
                    <div class="card-dates">Erreur</div>
                </div>
            </div>
            <div class="card-content">${error}</div>
        </div>
    `;
}

/**
 * =============================================================================
 * VI. ASTROCHART
 * =============================================================================
 */
/**
/**
 * Appelle l'API pour générer une image de la carte du ciel et l'affiche.
 */
async function generateAstroChartImage() {
    const date = document.getElementById('astrochart-date-input').value;
    const resultDiv = document.getElementById('astrochart-result');

    const response = await makeApiRequest(
        '/api/astrochart/generate_image',
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ date })
        },
        'astrochart-loading',
        'astrochart-result'
    );

    if (response) {
        // ✅ CORRECTION : Utiliser "chart_image_path" au lieu de "image_url"
        const imageUrl = response.chart_image_path;

        resultDiv.innerHTML = `
            <h3 style="color: #FFD700; margin-bottom: 20px;">Carte du Ciel pour le ${date}</h3>
            <img src="${imageUrl}?t=${new Date().getTime()}" alt="Carte du Ciel" class="astrochart-image" />
        `;
        // Le ?t=... force le navigateur à recharger l'image et à ne pas utiliser le cache
    }
}


/**
 * =============================================================================
 * VI. CHAT IA
 * =============================================================================
 */
/**
 * Ajoute un message à l'interface du chat.
 * @param {string} content - Le contenu du message.
 * @param {boolean} isUser - Vrai si le message vient de l'utilisateur.
 */
function addChatMessage(content, isUser = false) {
    const messagesDiv = document.getElementById('chat-messages');
    if (!messagesDiv) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
    messageDiv.innerHTML = `<div class="message-content">${content.replace(/\n/g, '<br>')}</div>`;
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    appState.chatMessages.push({ content, isUser, timestamp: new Date().toISOString() });
}

/**
 * Envoie un message au backend et affiche la réponse.
 */
async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input?.value.trim();
    if (!message) return;

    addChatMessage(message, true);
    input.value = '';

    const messagesDiv = document.getElementById('chat-messages');
    const loadingId = 'loading-' + Date.now();
    messagesDiv.innerHTML += `<div class="message assistant" id="${loadingId}"><div class="message-content"><div class="loading-dots"><div class="loading-dot"></div><div class="loading-dot"></div><div class="loading-dot"></div></div></div></div>`;
    messagesDiv.scrollTop = messagesDiv.scrollHeight;

    try {
        const response = await fetch('/api/ollama/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, model: appState.selectedModel })
        });
        const data = await response.json();
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Erreur de l\'API Chat.');
        }
        addChatMessage(data.response, false);
    } catch (error) {
        addChatMessage(`❌ Erreur de connexion: ${error.message}`, false);
    } finally {
        document.getElementById(loadingId)?.remove();
    }
}

/**
 * =============================================================================
 * VIII. GESTIONNAIRES D'ÉVÉNEMENTS (Centralisés)
 * =============================================================================
 */

/**
 * Configure tous les écouteurs d'événements de la page.
 * Cette fonction est appelée une seule fois au chargement.
 */
function initializeEventListeners() {
    // Bouton pour ouvrir/fermer la sidebar sur mobile
    document.getElementById('btn-menu-toggle')?.addEventListener('click', toggleSidebar);

    // Liens de navigation dans la sidebar
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const section = link.id.replace('nav-', '');
            showSection(section);
        });
    });
    
    // Sélecteur de modèle IA
    document.getElementById('global-model-select')?.addEventListener('change', changeModel);

    // Formulaire pour l'horoscope individuel (écoute l'événement 'submit')
    document.getElementById('individual-form')?.addEventListener('submit', (e) => {
        e.preventDefault();
        generateIndividualHoroscope();
    });

    // Boutons des autres sections
    document.getElementById('btn-generate-daily')?.addEventListener('click', generateDailyHoroscopes);
    document.getElementById('btn-get-context')?.addEventListener('click', getAstralContext);

    // Section AstroChart
    document.getElementById('nav-astrochart')?.addEventListener('click', (e) => { e.preventDefault(); showSection('astrochart'); });
    // Bouton pour générer la carte
    document.getElementById('btn-generate-astrochart')?.addEventListener('click', generateAstroChartImage);

    // Section Chat
    document.getElementById('btn-send-chat')?.addEventListener('click', sendChatMessage);
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') { e.preventDefault(); sendChatMessage(); }
        });
    }

    // Ajoute dynamiquement les boutons de la section vidéo et leurs écouteurs
    addVideoButtonsAndListeners();
}

/**
 * Crée et attache les boutons d'action de la section vidéo.
 */
function addVideoButtonsAndListeners() {
    const container = document.getElementById('video-buttons-container');
    if (!container) return;

    // Vider le conteneur avant d'ajouter les nouveaux boutons
    container.innerHTML = `
        <div class="action-group">
            <h4 class="action-group-title">Génération & Montage</h4>
            <div class="button-wrapper" id="group-main-actions"></div>
        </div>
        <div class="action-group">
            <h4 class="action-group-title">Actions en Lot & Upload</h4>
            <div class="button-wrapper" id="group-batch-actions"></div>
        </div>
        <div class="action-group">
            <h4 class="action-group-title">Utilitaires & Statut</h4>
            <div class="button-wrapper" id="group-utility-actions"></div>
        </div>
    `;

    // Définition des boutons et de leur groupe cible
    const buttons = [
        // Groupe 1: Actions Principales
        { group: 'group-main-actions', text: '🎬 Générer Clip Vidéo', action: generateComfyUIVideo, class: 'button-primary' },
        { group: 'group-main-actions', text: '🎞️ Montage pour ce Signe', action: generateSingleSignMontage, class: 'button-primary' },
        
        // Groupe 2: Actions en Lot
        { group: 'group-batch-actions', text: '🚀 Générer le Montage Complet', action: generateFullMontage, class: 'button-special' },
        { group: 'group-batch-actions', text: '🚀 Batch Clips Vidéo', action: generateComfyUIBatchVideos, class: 'button-secondary' },
        { group: 'group-batch-actions', text: '📤 Upload ce Signe', action: uploadCurrentSignToYouTube, class: 'button-youtube' },
        { group: 'group-batch-actions', text: '📺 Upload Batch YouTube', action: uploadBatchToYouTube, class: 'button-youtube' },
        { group: 'group-batch-actions', text: '🎵 Upload ce Signe (TikTok)', action: uploadCurrentSignToTikTok, class: 'button-tiktok' },

        // Groupe 3: Utilitaires
        { group: 'group-utility-actions', text: '🔍 Statut ComfyUI', action: checkComfyUIStatus, class: 'button-secondary' },
        { group: 'group-utility-actions', text: '📡 Statut YouTube', action: checkYouTubeStatus, class: 'button-secondary' }
    ];

    // Création et ajout des boutons dans leurs groupes respectifs
    buttons.forEach(btnInfo => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = `astro-button ${btnInfo.class}`; // Utilise la nouvelle classe de style
        button.textContent = btnInfo.text;
        button.addEventListener('click', btnInfo.action);
        
        document.getElementById(btnInfo.group).appendChild(button);
    });
}

/**
 * =============================================================================
 * VII. WORKFLOW DE GÉNÉRATION VIDÉO (ComfyUI, Montage, YouTube)
 *
 * Contient toutes les fonctions liées à la création, au montage et à l'upload
 * de contenu vidéo.
 * =============================================================================
 */

/**
 * Lance la génération d'une vidéo de constellation seule via ComfyUI.
 */
async function generateComfyUIVideo() {
    const sign = document.getElementById('video-sign').value;
    const format = document.getElementById('video-format').value;
    const customPrompt = document.getElementById('custom-prompt').value;
    const seed = document.getElementById('seed-input').value;

    if (!sign) {
        alert('Veuillez sélectionner un signe astrologique.');
        return;
    }

    const resultDiv = document.getElementById('video-result');
    const response = await makeApiRequest(
        '/api/comfyui/generate_video',
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sign,
                format,
                custom_prompt: customPrompt || null,
                seed: seed ? parseInt(seed) : null
            })
        },
        'video-loading',
        'video-result'
    );

    if (response) {
        resultDiv.innerHTML = createComfyUIVideoResultHTML(response.result);
    }
}

/**
 * Lance la génération en lot de vidéos de constellations pour tous les signes.
 */
async function generateComfyUIBatchVideos() {
    if (!confirm('Lancer la génération en lot pour les 12 signes ?\nLe processus peut prendre plus de 20 minutes.')) {
        return;
    }

    const format = document.getElementById('video-format').value;
    const resultDiv = document.getElementById('video-result');
    const response = await makeApiRequest(
        '/api/comfyui/generate_batch',
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ format })
        },
        'video-loading',
        'video-result'
    );

    if (response) {
        resultDiv.innerHTML = createComfyUIBatchResultHTML(response);
    }
}

/**
 * Lance le workflow complet (horoscope, audio, vidéo, montage) pour un seul signe.
 */
async function generateSingleSignMontage() {
    const sign = document.getElementById('video-sign').value;
    if (!sign) {
        alert("Veuillez d'abord sélectionner un signe astrologique.");
        return;
    }
    if (!confirm(`Lancer le workflow complet pour ${signNames[sign]} ?\nCela peut prendre quelques minutes.`)) return;
    
    const resultDiv = document.getElementById('video-result');
    const response = await makeApiRequest(
        '/api/workflow/complete_sign_generation',
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                sign: sign,
                format: document.getElementById('video-format').value || 'test',
                add_music: true
            })
        },
        'video-loading',
        'video-result'
    );

    if (response) {
        const finalResult = response.workflow_results?.synchronized_video;
        resultDiv.innerHTML = `
            <div class="horoscope-result">
                <h3 style="color: #00ff41;">✅ Workflow pour ${signNames[sign]} terminé !</h3>
                <p><strong>Chemin :</strong> ${finalResult.video_path}</p>
                <p><strong>Durée :</strong> ${finalResult.transcription.duration.toFixed(1)}s</p>
                <p><strong>Taille :</strong> ${formatFileSize(finalResult.file_size)}</p>
            </div>`;
    }
}

/**
 * Lance le workflow complet en lot pour les 12 signes.
 */
async function generateFullMontage() {
    if (!confirm('Lancer le workflow complet pour les 12 signes ?\nLe processus peut prendre plus de 30 minutes.')) return;

    const resultDiv = document.getElementById('video-result');
    const response = await makeApiRequest(
        '/api/workflow/batch_complete_generation',
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                format: document.getElementById('video-format').value || 'youtube_short',
                add_music: true
            })
        },
        'video-loading',
        'video-result'
    );

    if (response) {
        resultDiv.innerHTML = `<div class="horoscope-result"><h3 style="color: #00ff41;">✅ Workflow de Lot Terminé !</h3><p>${response.summary.message}</p></div>`;
    }
}

/**
 * Vérifie l'état du service ComfyUI et affiche un résumé.
 */
async function checkComfyUIStatus() {
    try {
        const response = await fetch('/api/comfyui/status');
        const data = await response.json();
        if (!data.success) throw new Error(data.error);
        
        const message = `🎬 STATUT COMFYUI\n\n` +
            `Statut: ${data.connected ? '✅ Connecté' : '❌ Déconnecté'}\n` +
            `Serveur: ${data.server}\n` +
            `Formats: ${data.available_formats.length} disponibles\n` +
            `Workflow: ${data.workflow_ready ? 'Prêt' : 'Non prêt'}`;
        alert(message);
    } catch (error) {
        alert(`❌ Erreur: ${error.message}`);
    }
}

/**
 * Vérifie l'état du service YouTube et affiche un résumé.
 */
async function checkYouTubeStatus() {
    try {
        const response = await fetch('/api/youtube/status');
        const data = await response.json();
        if (!data.success) throw new Error(data.error);
        
        const channel = data.channel_info;
        const message = `📤 STATUT YOUTUBE\n\n` +
            `Statut: ${data.youtube_connected ? '✅ Connecté' : '❌ Déconnecté'}\n` +
            `Chaîne: ${channel.title}\n` +
            `Abonnés: ${channel.subscribers}\n` +
            `Vidéos disponibles: ${data.available_videos.total_available}`;
        alert(message);
    } catch (error) {
        alert(`❌ Erreur: ${error.message}`);
    }
}

/**
 * Lance l'upload du signe actuellement sélectionné sur YouTube.
 */
async function uploadCurrentSignToYouTube() {
    const sign = document.getElementById('video-sign').value;
    if (!sign) {
        alert('Veuillez sélectionner un signe astrologique.');
        return;
    }
    if (!confirm(`Uploader la vidéo de ${signNames[sign]} sur YouTube en mode PRIVÉ ?`)) return;

    const resultDiv = document.getElementById('video-result');
    const response = await makeApiRequest(
        `/api/youtube/upload_sign/${sign}`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ privacy: 'private' })
        },
        'video-loading',
        'video-result'
    );

    if (response) {
        alert(`✅ Upload réussi !\n\nTitre: ${response.title}\nConsultez YouTube Studio pour publier la vidéo.`);
        resultDiv.innerHTML = `<div class="horoscope-result">
            <h3 style="color: #00ff41;">✅ Vidéo uploadée !</h3>
            <p><strong>Titre :</strong> ${response.title}</p>
            <p><a href="${response.video_url}" target="_blank">Voir sur YouTube</a></p>
        </div>`;
    }
}

/**
 * Lance l'upload en lot de toutes les vidéos disponibles sur YouTube.
 */
async function uploadBatchToYouTube() {
    if (!confirm('Uploader TOUTES les vidéos disponibles sur YouTube en mode PRIVÉ ?')) return;

    const resultDiv = document.getElementById('video-result');
    const response = await makeApiRequest(
        '/api/youtube/upload_batch',
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ privacy: 'private' })
        },
        'video-loading',
        'video-result'
    );

    if (response) {
        alert(`Batch Upload terminé: ${response.summary}`);
        // Afficher les résultats détaillés
        let resultsHtml = `<div class="horoscope-result"><h3>Résultats de l'Upload Batch</h3>`;
        response.details.forEach(res => {
            resultsHtml += `<p>${res.success ? '✅' : '❌'} ${signNames[res.sign]}: ${res.success ? 'OK' : res.error}</p>`;
        });
        resultsHtml += `</div>`;
        resultDiv.innerHTML = resultsHtml;
    }
}

async function uploadCurrentSignToTikTok() {
    const sign = document.getElementById('video-sign').value;
    if (!sign) {
        alert('Veuillez sélectionner un signe astrologique.');
        return;
    }
    if (!confirm(`Uploader la vidéo de ${signNames[sign]} sur TikTok ?`)) return;

    const resultDiv = document.getElementById('video-result');
    const response = await makeApiRequest(
        `/api/tiktok/upload_sign/${sign}`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        },
        'video-loading',
        'video-result'
    );

    if (response) {
        alert(`✅ Upload TikTok réussi !\nTitre: ${response.title}`);
        resultDiv.innerHTML = `<div class="horoscope-result">
            <h3 style="color: #00ff41;">✅ Vidéo uploadée sur TikTok !</h3>
            <p><strong>Titre :</strong> ${response.title}</p>
        </div>`;
    }
}

/**
 * Helper pour créer le HTML du résultat d'une génération ComfyUI.
 * @param {object} result - L'objet résultat de l'API.
 * @returns {string} Le code HTML à afficher.
 */
function createComfyUIVideoResultHTML(result) {
    return `
        <div class="video-preview">
            <h3 style="color: #FFD700;">🎬 Vidéo générée avec ComfyUI !</h3>
            <p><strong>Signe:</strong> ${result.sign_name} ${signSymbols[result.sign]}</p>
            <p><strong>Chemin:</strong> ${result.video_path}</p>
            <p><strong>Taille:</strong> ${formatFileSize(result.file_size)}</p>
            <div class="video-actions">
                <a href="/api/comfyui/download_video/${result.video_path.split('/').pop()}" download class="astro-button">📥 Télécharger</a>
            </div>
        </div>`;
}

/**
 * Helper pour créer le HTML du résultat d'un batch ComfyUI.
 * @param {object} data - L'objet de données complet de l'API.
 * @returns {string} Le code HTML à afficher.
 */
function createComfyUIBatchResultHTML(data) {
    let resultsList = data.results.map(res => 
        `<li class="${res.success ? 'success' : 'error'}">
            <strong>${signNames[res.sign]}:</strong> 
            ${res.success ? `Réussi (${formatFileSize(res.result.file_size)})` : `Échoué - ${res.error}`}
        </li>`
    ).join('');

    return `
        <div class="horoscope-result">
            <h3 style="color: #00ff41;">Batch ComfyUI Terminé !</h3>
            <p>${data.message}</p>
            <ul class="batch-results-list">${resultsList}</ul>
        </div>`;
}



/**
 * =============================================================================
 * IX. INITIALISATION DE L'APPLICATION
 *
 * Point d'entrée du script, s'exécute quand le document est prêt.
 * =============================================================================
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('🌟 Initialisation de l\'application Astro Generator...');
    
    // Applique la date du jour aux champs de date
    const today = new Date().toISOString().split('T')[0];
    ['date-input', 'daily-date-input', 'context-date-input', 'astrochart-date-input', 'video-date'].forEach(id => {
        const input = document.getElementById(id);
        if (input) input.value = today;
    });

    // Lance les initialisations
    loadAvailableModels();
    initializeEventListeners();
    setupResponsiveHandlers();
    checkSystemHealth().then(isHealthy => {
        console.log(`🩺 Bilan de santé du système: ${isHealthy ? 'OK' : 'Dégradé'}`);
    });

    console.log('✅ Application initialisée et prête.');
});