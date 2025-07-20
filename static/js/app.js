/*
 * =============================================================================
 * ASTRO GENERATOR - JavaScript Frontend
 * Interface web pour génération d'horoscopes et vidéos
 * =============================================================================
 */

// =============================================================================
// VARIABLES GLOBALES ET CONFIGURATION
// =============================================================================

// Variables d'état de l'application
let currentSection = 'individual';
let chatMessages = [];
let selectedModel = 'llama3.1:8b-instruct-q8_0';
let availableModels = [];

// Données de référence
const signSymbols = {
    'aries': '♈', 'taurus': '♉', 'gemini': '♊', 'cancer': '♋',
    'leo': '♌', 'virgo': '♍', 'libra': '♎', 'scorpio': '♏',
    'sagittarius': '♐', 'capricorn': '♑', 'aquarius': '♒', 'pisces': '♓'
};

const signNames = {
    'aries': 'Bélier', 'taurus': 'Taureau', 'gemini': 'Gémeaux', 'cancer': 'Cancer',
    'leo': 'Lion', 'virgo': 'Vierge', 'libra': 'Balance', 'scorpio': 'Scorpion',
    'sagittarius': 'Sagittaire', 'capricorn': 'Capricorne', 'aquarius': 'Verseau', 'pisces': 'Poissons'
};

const videoFormats = {
    'youtube_short': { width: 1080, height: 1920, name: 'YouTube Short' },
    'tiktok': { width: 1080, height: 1920, name: 'TikTok' },
    'instagram_reel': { width: 1080, height: 1920, name: 'Instagram Reels' },
    'square': { width: 1080, height: 1080, name: 'Format Carré' }
};

// Variables pour les projets vidéo
let currentVideoProject = null;
let batchResults = null;

// =============================================================================
// NAVIGATION ET INTERFACE
// =============================================================================

/**
 * Affiche une section spécifique de l'interface
 */
function showSection(sectionName) {
    // Masquer toutes les sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Désactiver tous les liens de navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    
    // Activer la section sélectionnée
    const targetSection = document.getElementById(sectionName + '-section');
    const targetLink = document.querySelector(`[href="#${sectionName}"]`);
    
    if (targetSection) targetSection.classList.add('active');
    if (targetLink) targetLink.classList.add('active');
    
    // Mettre à jour les titres de page
    updatePageTitle(sectionName);
    
    currentSection = sectionName;
    
    // Fermer le menu sur mobile
    if (window.innerWidth <= 768) {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) sidebar.classList.remove('open');
    }
}

/**
 * Met à jour le titre de la page selon la section
 */
function updatePageTitle(sectionName) {
    const titles = {
        'individual': { title: 'Horoscope Individuel', subtitle: 'Générez votre horoscope personnel avec l\'IA' },
        'daily': { title: 'Horoscopes Quotidiens', subtitle: 'Tous les horoscopes du jour en un clic' },
        'context': { title: 'Contexte Astral', subtitle: 'Découvrez les influences cosmiques du moment' },
        'chat': { title: 'Chat IA', subtitle: 'Discutez avec votre assistant astral' },
        'video': { title: 'Générateur Vidéo', subtitle: 'Créez du contenu vidéo pour vos réseaux sociaux' }
    };
    
    const titleInfo = titles[sectionName];
    if (titleInfo) {
        const pageTitle = document.getElementById('pageTitle');
        const pageSubtitle = document.getElementById('pageSubtitle');
        
        if (pageTitle) pageTitle.textContent = titleInfo.title;
        if (pageSubtitle) pageSubtitle.textContent = titleInfo.subtitle;
    }
}

/**
 * Bascule la sidebar sur mobile
 */
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('open');
    }
}

// =============================================================================
// GESTION DES MODÈLES OLLAMA
// =============================================================================

/**
 * Charge la liste des modèles Ollama disponibles
 */
async function loadAvailableModels() {
    const statusDot = document.getElementById('model-status-dot');
    const statusText = document.getElementById('model-status-text');
    const modelSelect = document.getElementById('global-model-select');
    
    if (!statusDot || !statusText || !modelSelect) return;
    
    statusDot.className = 'status-dot loading';
    statusText.textContent = 'Chargement...';
    
    try {
        const response = await fetch('/api/ollama/models');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Réponse non-JSON reçue');
        }
        
        const data = await response.json();
        
        if (data.success && data.models && data.models.length > 0) {
            availableModels = data.models;
            
            // Vider et remplir le sélecteur
            modelSelect.innerHTML = '';
            
            data.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.name;
                option.textContent = model.name;
                modelSelect.appendChild(option);
            });
            
            // Sélectionner le modèle par défaut
            const defaultModel = data.models.find(m => m.name === 'm llama3.1:8b-instruct-q8_0');
            if (defaultModel) {
                modelSelect.value = 'llama3.1:8b-instruct-q8_0';
                selectedModel = ' llama3.1:8b-instruct-q8_0';
            } else {
                selectedModel = data.models[0].name;
                modelSelect.value = selectedModel;
            }
            
            localStorage.setItem('selectedModel', selectedModel);
            
            statusDot.className = 'status-dot connected';
            statusText.textContent = `${data.models.length} modèles`;
        } else {
            statusDot.className = 'status-dot error';
            statusText.textContent = data.error || 'Aucun modèle';
        }
    } catch (error) {
        console.error('Erreur chargement modèles:', error);
        statusDot.className = 'status-dot error';
        statusText.textContent = 'Ollama offline';
        
        // Modèles par défaut en cas d'erreur
        modelSelect.innerHTML = `
            <option value="mistral:latest">Mistral</option>
            <option value="mistral:7b-instruct">Mistral Instruct</option>
            <option value="llama3:8b">Llama 3</option>
            <option value="llama3.1:8b-instruct-q8_0">Llama 3.1</option>
            <option value="codellama:latest">CodeLlama</option>
        `;
        selectedModel = 'llama3.1:8b-instruct-q8_0';
        localStorage.setItem('selectedModel', selectedModel);
    }
}

/**
 * Change le modèle Ollama sélectionné
 */
async function changeModel() {
    const modelSelect = document.getElementById('global-model-select');
    const statusDot = document.getElementById('model-status-dot');
    const statusText = document.getElementById('model-status-text');

    if (!modelSelect || !statusDot || !statusText) return;

    selectedModel = modelSelect.value;
    localStorage.setItem('selectedModel', selectedModel);

    statusDot.className = 'status-dot loading';
    statusText.textContent = 'Vérification...';

    try {
        const response = await fetch('/api/ollama/models');
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        const data = await response.json();

        if (data.success && data.models && data.models.length > 0) {
            availableModels = data.models;

            statusDot.className = 'status-dot connected confirming';
            statusText.textContent = `Activé : ${selectedModel.split(':')[0]}`;

            setTimeout(() => {
                statusDot.classList.remove('confirming');
                statusText.textContent = `${availableModels.length} modèles`;
            }, 1500);

        } else {
            throw new Error(data.error || 'Aucun modèle trouvé');
        }

    } catch (error) {
        console.error('Erreur lors du changement de modèle:', error);
        availableModels = [];
        statusDot.className = 'status-dot error';
        statusText.textContent = 'Ollama offline';
    }
}

// =============================================================================
// GÉNÉRATION D'HOROSCOPES
// =============================================================================

/**
 * Génère un horoscope pour un signe spécifique
 */
async function generateIndividualHoroscope(sign, date = null) {
    const loading = document.getElementById('individual-loading');
    const resultDiv = document.getElementById('individual-result');
    
    if (!loading || !resultDiv) return;
    
    loading.classList.add('active');
    resultDiv.innerHTML = '';
    
    try {
        const response = await fetch('/api/generate_single_horoscope', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sign, date })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const horoscope = data.result;
            resultDiv.innerHTML = `
                <div class="horoscope-result">
                    <div class="horoscope-header">
                        <div class="sign-icon">${signSymbols[sign] || '✨'}</div>
                        <div class="horoscope-meta">
                            <h3>${horoscope.sign}</h3>
                            <p>📅 ${horoscope.date}</p>
                            <p>🌙 Influence lunaire: ${Math.round(horoscope.lunar_influence * 100)}%</p>
                        </div>
                    </div>
                    <div class="horoscope-text">${horoscope.horoscope}</div>
                    <div style="margin-top: 15px; font-size: 0.8em; color: rgba(230, 230, 250, 0.7);">
                        <p>🌙 Phase lunaire: ${horoscope.astral_context.lunar_phase}</p>
                        <p>🍂 Saison: ${horoscope.astral_context.season}</p>
                        <p>📊 Mots: ${horoscope.word_count}</p>
                    </div>
                </div>
            `;
        } else {
            showError(resultDiv, data.error);
        }
    } catch (error) {
        showError(resultDiv, `Erreur de connexion: ${error.message}`);
    } finally {
        loading.classList.remove('active');
    }
}

/**
 * Génère tous les horoscopes quotidiens
 */
async function generateDailyHoroscopes() {
    const loading = document.getElementById('daily-loading');
    const resultDiv = document.getElementById('daily-results');
    const dateInput = document.getElementById('daily-date-input');
    
    if (!loading || !resultDiv) return;
    
    loading.classList.add('active');
    resultDiv.innerHTML = '';
    
    try {
        const response = await fetch('/api/generate_daily_horoscopes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ date: dateInput?.value || null })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const horoscopes = data.result.horoscopes;
            let html = '';
            
            for (const [signKey, horoscope] of Object.entries(horoscopes)) {
                if (horoscope.error) {
                    html += createErrorCard(signKey, horoscope.error);
                } else {
                    html += createHoroscopeCard(signKey, horoscope);
                }
            }
            
            resultDiv.innerHTML = html;
        } else {
            showError(resultDiv, data.error);
        }
    } catch (error) {
        showError(resultDiv, `Erreur de connexion: ${error.message}`);
    } finally {
        loading.classList.remove('active');
    }
}

/**
 * Obtient le contexte astral pour une date
 */
async function getAstralContext() {
    const loading = document.getElementById('context-loading');
    const resultDiv = document.getElementById('context-result');
    const dateInput = document.getElementById('context-date-input');
    
    if (!loading || !resultDiv) return;
    
    loading.classList.add('active');
    resultDiv.innerHTML = '';
    
    try {
        const response = await fetch('/api/get_astral_context', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ date: dateInput?.value || new Date().toISOString().split('T')[0] })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const context = data.result;
            const planetsHtml = context.influential_planets.map(planet => 
                `<li><strong>${planet.name}</strong> (${planet.state}): ${planet.influence}</li>`
            ).join('');
            
            resultDiv.innerHTML = `
                <div class="horoscope-result">
                    <div class="horoscope-header">
                        <div class="sign-icon">🌌</div>
                        <div class="horoscope-meta">
                            <h3>Contexte Astral</h3>
                            <p>📅 ${context.date} (${context.day_of_week})</p>
                        </div>
                    </div>
                    <div class="horoscope-text">
                        <h4>🌙 Phase Lunaire</h4>
                        <p>${context.lunar_phase}</p>
                        
                        <h4>🍂 Saison</h4>
                        <p>${context.season} - ${context.seasonal_energy}</p>
                        
                        <h4>🪐 Planètes Influentes</h4>
                        <ul>${planetsHtml}</ul>
                    </div>
                </div>
            `;
        } else {
            showError(resultDiv, data.error);
        }
    } catch (error) {
        showError(resultDiv, `Erreur de connexion: ${error.message}`);
    } finally {
        loading.classList.remove('active');
    }
}

// =============================================================================
// CHAT IA
// =============================================================================

/**
 * Envoie un message dans le chat IA
 */
async function sendChatMessage() {
    const input = document.getElementById('chat-input');
    const message = input?.value.trim();
    
    if (!message) return;
    
    const messagesDiv = document.getElementById('chat-messages');
    if (!messagesDiv) return;
    
    // Ajouter le message utilisateur
    addChatMessage(message, true);
    input.value = '';
    
    // Ajouter un indicateur de chargement
    const loadingId = 'loading-' + Date.now();
    messagesDiv.innerHTML += `
        <div class="message assistant" id="${loadingId}">
            <div class="message-content">
                <div class="loading-dots">
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                </div>
            </div>
        </div>
    `;
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    try {
        const response = await fetch('/api/ollama/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                message: message,
                model: selectedModel 
            })
        });
        
        const data = await response.json();
        
        // Supprimer l'indicateur de chargement
        const loadingElement = document.getElementById(loadingId);
        if (loadingElement) loadingElement.remove();
        
        if (data.success) {
            addChatMessage(data.response, false);
        } else {
            addChatMessage(`❌ Erreur: ${data.error}`, false);
        }
    } catch (error) {
        // Supprimer l'indicateur de chargement
        const loadingElement = document.getElementById(loadingId);
        if (loadingElement) loadingElement.remove();
        addChatMessage(`❌ Erreur de connexion: ${error.message}`, false);
    }
}

/**
 * Ajoute un message au chat
 */
function addChatMessage(content, isUser = false) {
    const messagesDiv = document.getElementById('chat-messages');
    if (!messagesDiv) return;
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;
    messageDiv.innerHTML = `<div class="message-content">${content}</div>`;
    
    messagesDiv.appendChild(messageDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    
    // Sauvegarder dans l'historique
    chatMessages.push({ content, isUser, timestamp: new Date().toISOString() });
}

// =============================================================================
// GÉNÉRATEUR VIDÉO
// =============================================================================

/**
 * Génère le contenu vidéo pour un horoscope
 */
async function generateVideoContent() {
    const loading = document.getElementById('video-loading');
    const resultDiv = document.getElementById('video-result');
    const formatSelect = document.getElementById('video-format');
    const signSelect = document.getElementById('video-sign');
    const dateInput = document.getElementById('video-date');
    const styleSelect = document.getElementById('video-style');
    
    if (!loading || !resultDiv || !formatSelect || !signSelect || !styleSelect) return;
    
    const format = formatSelect.value;
    const sign = signSelect.value;
    const date = dateInput?.value || new Date().toISOString().split('T')[0];
    const style = styleSelect.value;
    
    if (!sign) {
        alert('Veuillez sélectionner un signe astrologique');
        return;
    }
    
    loading.classList.add('active');
    resultDiv.innerHTML = '';
    
    try {
        const response = await fetch('/api/video/create_project', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sign: sign,
                date: date,
                format: format,
                style: style
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const project = data.project;
            currentVideoProject = project;
            
            resultDiv.innerHTML = createVideoPreview(project, sign, style);
        } else {
            showError(resultDiv, data.error);
        }
    } catch (error) {
        showError(resultDiv, `Erreur de connexion: ${error.message}`);
    } finally {
        loading.classList.remove('active');
    }
}

/**
 * Génère une vidéo complète
 */
async function generateFullVideo(projectId) {
    if (!currentVideoProject) {
        alert('❌ Projet vidéo non trouvé');
        return;
    }
    
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = '🎬 Génération...';
    button.disabled = true;
    
    try {
        const response = await fetch('/api/video/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                horoscope_data: {
                    sign: currentVideoProject.content.sign_name,
                    date: currentVideoProject.content.date,
                    horoscope_text: currentVideoProject.content.segments.join(' ')
                },
                format: document.getElementById('video-format')?.value,
                style: document.getElementById('video-style')?.value
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            if (data.video_path) {
                alert(`✅ Vidéo générée avec succès!\n\nChemin: ${data.video_path}\n\nVérifiez le dossier de sortie.`);
            } else {
                alert('⚠️ Projet créé mais génération vidéo non disponible.\nInstallez MoviePy pour la génération complète.');
            }
        } else {
            alert(`❌ Erreur lors de la génération: ${data.error}`);
        }
    } catch (error) {
        alert(`❌ Erreur de connexion: ${error.message}`);
    } finally {
        button.textContent = originalText;
        button.disabled = false;
    }
}

/**
 * Exporte le script vidéo
 */
async function exportVideoScript(projectId) {
    if (!currentVideoProject) {
        alert('❌ Projet vidéo non trouvé');
        return;
    }
    
    try {
        const response = await fetch('/api/video/script', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                horoscope_data: {
                    sign: currentVideoProject.content.sign_name,
                    date: currentVideoProject.content.date,
                    horoscope_text: currentVideoProject.content.segments.join(' ')
                },
                format: document.getElementById('video-format')?.value,
                style: document.getElementById('video-style')?.value
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            downloadFile(data.script, `script_${currentVideoProject.content.sign_name}_${currentVideoProject.content.date}.md`, 'text/plain');
            alert('✅ Script exporté avec succès !');
        } else {
            alert(`❌ Erreur lors de l'export: ${data.error}`);
        }
    } catch (error) {
        alert(`❌ Erreur de connexion: ${error.message}`);
    }
}

/**
 * Génère le prompt pour l'image de constellation
 */
async function generateConstellationImage(sign, style) {
    try {
        const response = await fetch('/api/video/constellation_prompt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sign: sign,
                style: style
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const alertMessage = `
🎨 Génération d'image demandée:

Signe: ${data.sign} ${signSymbols[sign] || '✨'}
Style: ${getStyleName(style)}

Prompt généré:
"${data.prompt}"

Outils recommandés:
- DALL-E 3 (OpenAI)
- Midjourney
- Stable Diffusion
- Leonardo AI

Spécifications techniques:
- Résolution: ${data.technical_specs.recommended_resolution}
- Formats: ${data.technical_specs.aspect_ratios.join(', ')}
- Type: ${data.technical_specs.file_format}

Le prompt est copié dans le presse-papiers.
            `;
            
            alert(alertMessage);
            await copyTextWithFallback(data.prompt);
            
        } else {
            alert(`❌ Erreur: ${data.error}`);
        }
    } catch (error) {
        alert(`❌ Erreur de connexion: ${error.message}`);
    }
}

/**
 * Copie le texte de la vidéo
 */
function copyVideoText(sign) {
    const textElement = document.querySelector('.text-overlay');
    if (textElement) {
        const text = textElement.textContent;
        copyTextWithFallback(text).then(() => {
            alert('✅ Texte copié dans le presse-papiers !');
        }).catch(() => {
            alert('❌ Erreur lors de la copie du texte');
        });
    }
}

/**
 * Génère des vidéos en lot pour tous les signes
 */
async function generateBatchVideos() {
    const confirmed = confirm('⚠️ Génération en lot pour tous les signes.\n\nCette opération peut prendre plusieurs minutes.\n\nContinuer ?');
    
    if (!confirmed) return;
    
    const format = document.getElementById('video-format')?.value || 'youtube_short';
    const style = document.getElementById('video-style')?.value || 'cosmic';
    const date = document.getElementById('video-date')?.value || new Date().toISOString().split('T')[0];
    
    const loading = document.getElementById('video-loading');
    const resultDiv = document.getElementById('video-result');
    
    if (!loading || !resultDiv) return;
    
    loading.classList.add('active');
    resultDiv.innerHTML = '';
    
    try {
        const response = await fetch('/api/video/batch_generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: date,
                format: format,
                style: style
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            batchResults = data;
            resultDiv.innerHTML = createBatchResultsDisplay(data, format, style, date);
        } else {
            showError(resultDiv, data.error);
        }
    } catch (error) {
        showError(resultDiv, `Erreur de connexion: ${error.message}`);
    } finally {
        loading.classList.remove('active');
    }
}

/**
 * Vérifie le statut du générateur vidéo
 */
async function checkVideoGeneratorStatus() {
    try {
        const response = await fetch('/api/video/status');
        const data = await response.json();
        
        if (data.success) {
            const status = data.status;
            const recommendations = data.recommendations;
            
            let message = `
🎬 STATUT GÉNÉRATEUR VIDÉO

✅ Statut général: ${status.video_generator ? 'Opérationnel' : 'Non disponible'}

📦 Dépendances:
• MoviePy: ${status.moviepy_available ? '✅ Disponible' : '❌ Non installé'}
• Pillow: ${status.pil_available ? '✅ Disponible' : '❌ Non installé'}

🎯 Capacités:
• Génération vidéo: ${status.capabilities.video_generation ? '✅' : '❌'}
• Génération d'images: ${status.capabilities.image_generation ? '✅' : '❌'}
• Scripts: ${status.capabilities.script_generation ? '✅' : '❌'}
• Traitement par lot: ${status.capabilities.batch_processing ? '✅' : '❌'}
• Export d'assets: ${status.capabilities.asset_export ? '✅' : '❌'}

📁 Dossier de sortie: ${status.output_directory}
🎨 Formats supportés: ${status.supported_formats.join(', ')}
🎭 Styles disponibles: ${status.supported_styles.join(', ')}
            `;
            
            if (recommendations.install_moviepy || recommendations.install_pillow) {
                message += `\n\n⚠️ Recommandations:\n${recommendations.message}`;
            }
            
            alert(message);
        } else {
            alert(`❌ Erreur: ${data.error}`);
        }
    } catch (error) {
        alert(`❌ Erreur de connexion: ${error.message}`);
    }
}

// =============================================================================
// FONCTIONS UTILITAIRES
// =============================================================================

/**
 * Affiche une erreur dans un conteneur
 */
function showError(container, message) {
    container.innerHTML = `
        <div class="horoscope-result" style="border-color: #ff4444;">
            <div class="horoscope-text" style="color: #ff4444;">
                ❌ Erreur: ${message}
            </div>
        </div>
    `;
}

/**
 * Crée une carte d'horoscope
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
            <div class="card-content">
                ${horoscope.horoscope}
            </div>
        </div>
    `;
}

/**
 * Crée une carte d'erreur
 */
function createErrorCard(signKey, error) {
    return `
        <div class="horoscope-card" style="border-color: #ff4444;">
            <div class="card-header">
                <div class="card-icon">${signSymbols[signKey] || '❌'}</div>
                <div>
                    <div class="card-title">${signKey}</div>
                    <div class="card-dates">Erreur</div>
                </div>
            </div>
            <div class="card-content" style="color: #ff4444;">
                ${error}
            </div>
        </div>
    `;
}

/**
 * Crée l'aperçu du projet vidéo
 */
function createVideoPreview(project, sign, style) {
    return `
        <div class="video-preview">
            <div class="video-specs">
                <div class="spec-item">
                    <div class="spec-label">Format</div>
                    <div class="spec-value">${project.specs.platform}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Résolution</div>
                    <div class="spec-value">${project.specs.width}x${project.specs.height}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Signe</div>
                    <div class="spec-value">${project.content.sign_name}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Date</div>
                    <div class="spec-value">${project.content.date}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Style</div>
                    <div class="spec-value">${getStyleName(style)}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Durée</div>
                    <div class="spec-value">${project.specs.duration}s</div>
                </div>
            </div>
            
            <div class="constellation-preview">
                <div class="constellation-sign">${project.content.sign_symbol}</div>
                <div class="video-text-content">
                    <h4 style="color: #FFD700; margin-bottom: 15px;">
                        ${project.content.title}
                    </h4>
                    <div class="text-overlay">
                        ${project.content.segments.join(' ')}
                    </div>
                </div>
            </div>
            
            <div class="video-actions">
                <button class="video-button" onclick="exportVideoScript('${project.id}')">
                    📝 Exporter Script
                </button>
                <button class="video-button secondary" onclick="generateConstellationImage('${sign}', '${style}')">
                    🖼️ Générer Image
                </button>
                <button class="video-button secondary" onclick="copyVideoText('${sign}')">
                    📋 Copier Texte
                </button>
                <button class="video-button secondary" onclick="generateFullVideo('${project.id}')">
                    🎬 Générer Vidéo
                </button>
                <button class="video-button secondary" onclick="exportVideoAssets('${project.id}')">
                    📦 Exporter Assets
                </button>
            </div>
        </div>
    `;
}

/**
 * Crée l'affichage des résultats de génération en lot
 */
function createBatchResultsDisplay(data, format, style, date) {
    let html = `
        <div class="video-preview">
            <h3 style="color: #FFD700; margin-bottom: 20px;">
                📊 Génération en lot terminée
            </h3>
            <div class="video-specs">
                <div class="spec-item">
                    <div class="spec-label">Total</div>
                    <div class="spec-value">${data.total}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Réussies</div>
                    <div class="spec-value" style="color: #00ff41;">${data.successful}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Échouées</div>
                    <div class="spec-value" style="color: #ff4444;">${data.failed}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Format</div>
                    <div class="spec-value">${format}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Style</div>
                    <div class="spec-value">${getStyleName(style)}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Date</div>
                    <div class="spec-value">${date}</div>
                </div>
            </div>
            
            <div class="batch-results">
                <h4 style="color: #E6E6FA; margin: 20px 0 10px 0;">Résultats détaillés:</h4>
    `;
    
    // Ajouter les résultats pour chaque signe
    data.results.forEach(result => {
        const statusColor = result.success ? '#00ff41' : '#ff4444';
        const statusIcon = result.success ? '✅' : '❌';
        const statusText = result.success ? 'Réussi' : 'Échoué';
        
        html += `
            <div class="batch-result-item" style="
                background: rgba(15, 15, 40, 0.6);
                border: 1px solid ${statusColor};
                border-radius: 8px;
                padding: 10px;
                margin: 5px 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <div>
                    <strong>${signSymbols[result.sign.toLowerCase()] || '✨'} ${result.sign}</strong>
                    ${result.video_path ? `<br><small style="color: #8A2BE2;">${result.video_path}</small>` : ''}
                    ${result.error ? `<br><small style="color: #ff4444;">${result.error}</small>` : ''}
                </div>
                <div style="color: ${statusColor};">
                    ${statusIcon} ${statusText}
                </div>
            </div>
        `;
    });
    
    html += `
            </div>
            
            <div class="video-actions" style="margin-top: 20px;">
                <button class="video-button" onclick="showBatchSummary()">
                    📋 Voir Résumé
                </button>
                <button class="video-button secondary" onclick="exportBatchAssets()">
                    📦 Exporter Tous Assets
                </button>
            </div>
        </div>
    `;
    
    return html;
}

/**
 * Retourne le nom d'un style vidéo
 */
function getStyleName(style) {
    const styleNames = {
        'cosmic': 'Cosmique',
        'constellation': 'Constellations',
        'mystical': 'Mystique',
        'elegant': 'Élégant',
        'modern': 'Moderne'
    };
    return styleNames[style] || style;
}

/**
 * Copie du texte avec méthode de fallback
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
    
    // Méthode de fallback
    try {
        const tempTextArea = document.createElement('textarea');
        tempTextArea.value = text;
        tempTextArea.style.position = 'fixed';
        tempTextArea.style.left = '-9999px';
        document.body.appendChild(tempTextArea);
        tempTextArea.select();
        tempTextArea.setSelectionRange(0, 99999);
        const successful = document.execCommand('copy');
        document.body.removeChild(tempTextArea);
        return successful;
    } catch (err) {
        console.error('Erreur fallback copy:', err);
        return false;
    }
}

/**
 * Télécharge un fichier
 */
function downloadFile(content, filename, mimeType = 'text/plain') {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Formate une date pour l'affichage
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

/**
 * Obtient le signe astrologique à partir d'une date
 */
function getSignFromDate(date) {
    const month = date.getMonth() + 1;
    const day = date.getDate();
    
    if ((month === 3 && day >= 21) || (month === 4 && day <= 19)) return 'aries';
    if ((month === 4 && day >= 20) || (month === 5 && day <= 20)) return 'taurus';
    if ((month === 5 && day >= 21) || (month === 6 && day <= 20)) return 'gemini';
    if ((month === 6 && day >= 21) || (month === 7 && day <= 22)) return 'cancer';
    if ((month === 7 && day >= 23) || (month === 8 && day <= 22)) return 'leo';
    if ((month === 8 && day >= 23) || (month === 9 && day <= 22)) return 'virgo';
    if ((month === 9 && day >= 23) || (month === 10 && day <= 22)) return 'libra';
    if ((month === 10 && day >= 23) || (month === 11 && day <= 21)) return 'scorpio';
    if ((month === 11 && day >= 22) || (month === 12 && day <= 21)) return 'sagittarius';
    if ((month === 12 && day >= 22) || (month === 1 && day <= 19)) return 'capricorn';
    if ((month === 1 && day >= 20) || (month === 2 && day <= 18)) return 'aquarius';
    if ((month === 2 && day >= 19) || (month === 3 && day <= 20)) return 'pisces';
    
    return 'aries'; // Par défaut
}

/**
 * Sauvegarde des données dans localStorage
 */
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
        console.error('Erreur lors de la sauvegarde:', error);
    }
}

/**
 * Chargement des données depuis localStorage
 */
function loadFromLocalStorage(key, defaultValue = null) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : defaultValue;
    } catch (error) {
        console.error('Erreur lors du chargement:', error);
        return defaultValue;
    }
}


// =============================================================================
// GÉNÉRATEUR VIDÉO COMFYUI
// =============================================================================

/**
 * Vérifie le statut du générateur ComfyUI
 */
async function checkComfyUIStatus() {
    try {
        const response = await fetch('/api/comfyui/status');
        const data = await response.json();
        
        if (data.success) {
            const status = data.connected ? 'connecté' : 'déconnecté';
            const statusColor = data.connected ? '#00ff41' : '#ff4444';
            
            let message = `
🎬 STATUT COMFYUI

${data.connected ? '✅' : '❌'} Statut: ${data.connected ? 'Connecté' : 'Déconnecté'}
🖥️  Serveur: ${data.server}
📁 Dossier: ${data.output_dir}
🎯 Formats: ${data.available_formats.join(', ')}
⭐ Signes: ${data.supported_signs.length} disponibles
🔧 Workflow: ${data.workflow_ready ? 'Prêt' : 'Non prêt'}
            `;
            
            alert(message);
        } else {
            alert(`❌ Erreur: ${data.error}`);
        }
    } catch (error) {
        alert(`❌ Erreur de connexion: ${error.message}`);
    }
}

/**
 * Génère une vidéo de constellation avec ComfyUI
 */
async function generateComfyUIVideo() {
    const formatSelect = document.getElementById('video-format');
    const signSelect = document.getElementById('video-sign');
    const dateInput = document.getElementById('video-date');
    const customPrompt = document.getElementById('custom-prompt');
    const seedInput = document.getElementById('seed-input');
    
    const loading = document.getElementById('video-loading');
    const resultDiv = document.getElementById('video-result');
    
    if (!formatSelect || !signSelect || !loading || !resultDiv) {
        alert('❌ Éléments d\'interface manquants');
        return;
    }
    
    const format = formatSelect.value;
    const sign = signSelect.value;
    const date = dateInput?.value || new Date().toISOString().split('T')[0];
    const prompt = customPrompt?.value || null;
    const seed = seedInput?.value ? parseInt(seedInput.value) : null;
    
    if (!sign) {
        alert('Veuillez sélectionner un signe astrologique');
        return;
    }
    
    loading.classList.add('active');
    resultDiv.innerHTML = '';
    
    try {
        const response = await fetch('/api/comfyui/generate_video', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sign: sign,
                format: format,
                custom_prompt: prompt,
                seed: seed
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const result = data.result;
            
            resultDiv.innerHTML = `
                <div class="video-preview">
                    <h3 style="color: #FFD700; margin-bottom: 20px;">
                        🎬 Vidéo générée avec ComfyUI !
                    </h3>
                    
                    <div class="video-specs">
                        <div class="spec-item">
                            <div class="spec-label">Signe</div>
                            <div class="spec-value">${result.sign_name} ${getSignSymbol(result.sign)}</div>
                        </div>
                        <div class="spec-item">
                            <div class="spec-label">Format</div>
                            <div class="spec-value">${result.specs.platform}</div>
                        </div>
                        <div class="spec-item">
                            <div class="spec-label">Résolution</div>
                            <div class="spec-value">${result.specs.width}x${result.specs.height}</div>
                        </div>
                        <div class="spec-item">
                            <div class="spec-label">Taille</div>
                            <div class="spec-value">${formatFileSize(result.file_size)}</div>
                        </div>
                        <div class="spec-item">
                            <div class="spec-label">Durée</div>
                            <div class="spec-value">${result.duration_seconds}s</div>
                        </div>
                        <div class="spec-item">
                            <div class="spec-label">FPS</div>
                            <div class="spec-value">${result.specs.fps}</div>
                        </div>
                    </div>
                    
                    <div class="constellation-preview">
                        <div class="constellation-sign">${getSignSymbol(result.sign)}</div>
                        <div class="video-text-content">
                            <h4 style="color: #FFD700; margin-bottom: 15px;">
                                Constellation ${result.sign_name}
                            </h4>
                            <p style="color: #E6E6FA; opacity: 0.8;">
                                Video Generation<br>
                                Astral theme • Fluid animation
                            </p>
                        </div>
                    </div>
                    
                    <div class="video-actions">
                        <button class="video-button" onclick="downloadComfyUIVideo('${result.video_path}')">
                            📥 Télécharger
                        </button>
                        <button class="video-button secondary" onclick="previewComfyUIPrompt('${sign}')">
                            📝 Voir Prompt
                        </button>
                        <button class="video-button secondary" onclick="copyVideoInfo('${result.video_path}')">
                            📋 Copier Infos
                        </button>
                        <button class="video-button secondary" onclick="generateComfyUIVideo()">
                            🔄 Régénérer
                        </button>
                    </div>
                    
                    <div class="video-info">
                        <p><strong>Chemin:</strong> ${result.video_path}</p>
                        <p><strong>Généré le:</strong> ${new Date(result.generation_timestamp).toLocaleString()}</p>
                    </div>
                </div>
            `;
            
        } else {
            showError(resultDiv, data.error);
        }
    } catch (error) {
        showError(resultDiv, `Erreur de connexion: ${error.message}`);
    } finally {
        loading.classList.remove('active');
    }
}

/**
 * Génère des vidéos en lot avec ComfyUI
 */
async function generateComfyUIBatchVideos() {
    const confirmed = confirm('⚠️ Génération en lot ComfyUI pour tous les signes.\n\nCette opération peut prendre 20-30 minutes.\n\nContinuer ?');
    
    if (!confirmed) return;
    
    const format = document.getElementById('video-format')?.value || 'test';
    const loading = document.getElementById('video-loading');
    const resultDiv = document.getElementById('video-result');
    
    if (!loading || !resultDiv) return;
    
    loading.classList.add('active');
    resultDiv.innerHTML = '';
    
    try {
        const response = await fetch('/api/comfyui/generate_batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                format: format
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            resultDiv.innerHTML = createComfyUIBatchResults(data, format);
        } else {
            showError(resultDiv, data.error);
        }
    } catch (error) {
        showError(resultDiv, `Erreur de connexion: ${error.message}`);
    } finally {
        loading.classList.remove('active');
    }
}

/**
 * Prévisualise le prompt ComfyUI
 */
async function previewComfyUIPrompt(sign) {
    try {
        const customPrompt = document.getElementById('custom-prompt')?.value || null;
        const seedInput = document.getElementById('seed-input');
        const seed = seedInput?.value ? parseInt(seedInput.value) : null;
        const response = await fetch('/api/comfyui/preview_prompt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sign: sign,
                seed: seed,
                custom_prompt: customPrompt
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const alertMessage = `
🎨 PROMPT COMFYUI

Signe: ${data.sign} ${data.symbol}
Seed utilisée: ${data.seed}
Durée estimée: ${data.estimated_duration}

Prompt généré:
${data.prompt}

Métadonnées:
- Élément: ${data.metadata.element}
- Couleurs: ${data.metadata.colors.join(', ')}
            `;
            
            alert(alertMessage);
            await copyTextWithFallback(data.prompt);
            
        } else {
            alert(`❌ Erreur: ${data.error}`);
        }
    } catch (error) {
        alert(`❌ Erreur de connexion: ${error.message}`);
    }
}

/**
 * Télécharge une vidéo générée
 */
function downloadComfyUIVideo(videoPath) {
    try {
        // Extraire juste le nom du fichier
        const filename = videoPath.split('/').pop();
        const downloadUrl = `/api/comfyui/download_video/${filename}`;
        
        // Créer un lien de téléchargement
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        alert('✅ Téléchargement démarré !');
    } catch (error) {
        alert(`❌ Erreur de téléchargement: ${error.message}`);
    }
}

/**
 * Copie les informations de la vidéo
 */
function copyVideoInfo(videoPath) {
    const info = `Vidéo générée avec ComfyUI: ${videoPath}`;
    copyTextWithFallback(info).then(() => {
        alert('✅ Informations copiées !');
    }).catch(() => {
        alert('❌ Erreur lors de la copie');
    });
}

/**
 * Crée l'affichage des résultats batch ComfyUI
 */
function createComfyUIBatchResults(data, format) {
    let html = `
        <div class="video-preview">
            <h3 style="color: #FFD700; margin-bottom: 20px;">
                🎬 Génération batch ComfyUI terminée
            </h3>
            <div class="video-specs">
                <div class="spec-item">
                    <div class="spec-label">Total</div>
                    <div class="spec-value">${data.total}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Réussies</div>
                    <div class="spec-value" style="color: #00ff41;">${data.successful}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Échouées</div>
                    <div class="spec-value" style="color: #ff4444;">${data.failed}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Format</div>
                    <div class="spec-value">${format}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Taux de réussite</div>
                    <div class="spec-value">${Math.round(data.successful/data.total*100)}%</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Technologie</div>
                    <div class="spec-value">ComfyUI</div>
                </div>
            </div>
            
            <div class="batch-results">
                <h4 style="color: #E6E6FA; margin: 20px 0 10px 0;">Résultats détaillés:</h4>
    `;
    
    // Ajouter les résultats pour chaque signe
    data.results.forEach(result => {
        const statusColor = result.success ? '#00ff41' : '#ff4444';
        const statusIcon = result.success ? '✅' : '❌';
        const statusText = result.success ? 'Réussi' : 'Échoué';
        
        html += `
            <div class="batch-result-item" style="
                background: rgba(15, 15, 40, 0.6);
                border: 1px solid ${statusColor};
                border-radius: 8px;
                padding: 10px;
                margin: 5px 0;
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <div>
                    <strong>${getSignSymbol(result.sign)} ${getSignName(result.sign)}</strong>
                    ${result.success ? `
                        <br><small style="color: #8A2BE2;">
                            ${formatFileSize(result.result.file_size)} - ${result.result.duration_seconds}s
                        </small>
                        <br><small style="color: #666;">
                            ${result.result.video_path}
                        </small>
                    ` : `
                        <br><small style="color: #ff4444;">${result.error}</small>
                    `}
                </div>
                <div style="color: ${statusColor};">
                    ${statusIcon} ${statusText}
                </div>
            </div>
        `;
    });
    
    html += `
            </div>
            
            <div class="video-actions" style="margin-top: 20px;">
                <button class="video-button" onclick="showComfyUIBatchSummary()">
                    📋 Résumé Détaillé
                </button>
                <button class="video-button secondary" onclick="downloadAllComfyUIVideos()">
                    📦 Télécharger Toutes
                </button>
            </div>
        </div>
    `;
    
    return html;
}

/**
 * Affiche un résumé détaillé du batch ComfyUI
 */
function showComfyUIBatchSummary() {
    const summary = `
📊 RÉSUMÉ GÉNÉRATION BATCH COMFYUI

🎯 Performance:
- Génération rapide avec ComfyUI
- Qualité vidéo optimisée
- Prompts spécialisés par signe
- Animation fluide des constellations

🚀 Prochaines étapes:
1. Ajouter la musique de fond
2. Créer les miniatures
3. Optimiser pour chaque plateforme
4. Planifier la publication

💡 Conseils:
- Utilisez le format 'test' pour les essais
- 'youtube_short' pour la production
- Personnalisez les prompts si nécessaire
- Ajustez les seeds pour la variété
    `;
    
    alert(summary);
}

/**
 * Formate la taille de fichier
 */
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
}

/**
 * Obtient le symbole d'un signe
 */
function getSignSymbol(sign) {
    return signSymbols[sign] || '✨';
}

/**
 * Obtient le nom français d'un signe
 */
function getSignName(sign) {
    return signNames[sign] || sign;
}

// Remplacer les anciennes fonctions vidéo
function generateVideoContent() {
    generateComfyUIVideo();
}

function generateBatchVideos() {
    generateComfyUIBatchVideos();
}

function checkVideoGeneratorStatus() {
    checkComfyUIStatus();
}

// Ajouter les boutons ComfyUI dans l'interface
function addComfyUIButtons() {
    const videoSection = document.getElementById('video-section');
    if (!videoSection) {
        console.log('Section vidéo non trouvée');
        return;
    }
    
    const formContainer = videoSection.querySelector('.form-container');
    if (!formContainer) {
        console.log('Conteneur de formulaire non trouvé');
        return;
    }
    
    // Vérifier si les boutons existent déjà pour éviter les doublons
    if (formContainer.querySelector('.comfyui-button')) {
        console.log('Boutons ComfyUI déjà ajoutés');
        return;
    }
    
    // Trouver le conteneur des boutons existants
    let buttonsContainer = formContainer.querySelector('.video-buttons-container');
    
    // Si le conteneur n'existe pas, le créer
    if (!buttonsContainer) {
        buttonsContainer = document.createElement('div');
        buttonsContainer.className = 'video-buttons-container';
        buttonsContainer.style.cssText = 'display: flex; gap: 10px; flex-wrap: wrap; margin-top: 20px;';
        
        // Ajouter le conteneur à la fin du formulaire
        formContainer.appendChild(buttonsContainer);
    }
    
    // Créer les boutons ComfyUI
    const generateButton = document.createElement('button');
    generateButton.type = 'button';
    generateButton.className = 'astro-button comfyui-button';
    generateButton.textContent = '🎬 Générer avec ComfyUI';
    generateButton.onclick = generateComfyUIVideo;
    
    const statusButton = document.createElement('button');
    statusButton.type = 'button';
    statusButton.className = 'astro-button comfyui-button';
    statusButton.style.background = 'linear-gradient(135deg, #4A90E2, #357ABD)';
    statusButton.textContent = '🔍 Statut ComfyUI';
    statusButton.onclick = checkComfyUIStatus;
    
    const batchButton = document.createElement('button');
    batchButton.type = 'button';
    batchButton.className = 'astro-button comfyui-button';
    batchButton.style.background = 'linear-gradient(135deg, #7B68EE, #6A5ACD)';
    batchButton.textContent = '🚀 Batch ComfyUI';
    batchButton.onclick = generateComfyUIBatchVideos;

    const singleSignButton = document.createElement('button');
    singleSignButton.type = 'button';
    singleSignButton.className = 'astro-button comfyui-button'; // Style différent pour le distinguer
    singleSignButton.style.background = 'linear-gradient(135deg, #4A90E2, #357ABD)'; // Couleur bleue
    singleSignButton.textContent = 'Montage pour ce signe';
    singleSignButton.onclick = generateSingleSignMontage; // Lier à la nouvelle fonction


    const montageButton = document.createElement('button');
    montageButton.type = 'button';
    montageButton.className = 'astro-button comfyui-button'; // Utiliser la même classe
    montageButton.style.background = 'linear-gradient(135deg, #28a745, #218838)';
    montageButton.textContent = '🎬 Générer le Montage Complet';
    montageButton.onclick = generateFullMontage;
    
    const youtubeStatusButton = document.createElement('button');
    youtubeStatusButton.type = 'button';
    youtubeStatusButton.className = 'astro-button comfyui-button';
    youtubeStatusButton.style.background = 'linear-gradient(135deg, #FF0000, #CC0000)';
    youtubeStatusButton.textContent = '📤 Statut YouTube';
    youtubeStatusButton.onclick = checkYouTubeStatus;
    
    const uploadSignButton = document.createElement('button');
    uploadSignButton.type = 'button';
    uploadSignButton.className = 'astro-button comfyui-button';
    uploadSignButton.style.background = 'linear-gradient(135deg, #FF0000, #CC0000)';
    uploadSignButton.textContent = '🚀 Upload ce Signe';
    uploadSignButton.onclick = uploadCurrentSignToYouTube;
    
    const batchUploadButton = document.createElement('button');
    batchUploadButton.type = 'button';
    batchUploadButton.className = 'astro-button comfyui-button';
    batchUploadButton.style.background = 'linear-gradient(135deg, #FF4444, #CC0000)';
    batchUploadButton.textContent = '📺 Upload Batch YouTube';
    batchUploadButton.onclick = uploadBatchToYouTube;
    

    // Ajouter les boutons au conteneur
    buttonsContainer.appendChild(generateButton);
    buttonsContainer.appendChild(statusButton);
    buttonsContainer.appendChild(batchButton);
    buttonsContainer.appendChild(singleSignButton);
    buttonsContainer.appendChild(montageButton); 
    
    buttonsContainer.appendChild(youtubeStatusButton);
    buttonsContainer.appendChild(uploadSignButton);
    buttonsContainer.appendChild(batchUploadButton);   

    console.log('✅ Boutons ComfyUI ajoutés avec succès');
}


// =============================================================================
// INTERFACE UTILISATEUR - AMÉLIORATIONS
// =============================================================================

/**
 * Ajoute un bouton de vérification du statut vidéo
 */
function addVideoStatusButton() {
    const videoSection = document.getElementById('video-section');
    if (!videoSection) return;
    
    const formContainer = videoSection.querySelector('.form-container');
    if (!formContainer) return;
    
    const statusButton = document.createElement('button');
    statusButton.type = 'button';
    statusButton.className = 'astro-button';
    statusButton.style.marginLeft = '10px';
    statusButton.textContent = '🔍 Vérifier Statut';
    statusButton.onclick = checkVideoGeneratorStatus;
    
    const generateButton = formContainer.querySelector('.astro-button');
    if (generateButton && generateButton.parentNode) {
        generateButton.parentNode.insertBefore(statusButton, generateButton.nextSibling);
    }
}

/**
 * Ajoute un bouton de génération en lot
 */
function addBatchGenerateButton() {
    const videoSection = document.getElementById('video-section');
    if (!videoSection) return;
    
    const formContainer = videoSection.querySelector('.form-container');
    if (!formContainer) return;
    
    const batchButton = document.createElement('button');
    batchButton.type = 'button';
    batchButton.className = 'astro-button';
    batchButton.style.marginLeft = '10px';
    batchButton.style.backgroundColor = '#FF1493';
    batchButton.textContent = '🚀 Génération en Lot';
    batchButton.onclick = generateBatchVideos;
    
    const generateButton = formContainer.querySelector('.astro-button');
    if (generateButton && generateButton.parentNode) {
        generateButton.parentNode.insertBefore(batchButton, generateButton.nextSibling);
    }
}

/**
 * Orchestre la génération complète du montage vidéo pour les 12 signes.
 * C'est le chef d'orchestre qui appelle tous les services dans le bon ordre.
 */
// async function generateFullMontage() {
//     const confirmed = confirm(
//         '⚠️ Vous allez lancer la génération complète pour les 12 signes.\n\n' +
//         'Cela peut prendre beaucoup de temps.\n\nContinuer ?'
//     );

//     if (!confirmed) return;

//     const loading = document.getElementById('video-loading');
//     const resultDiv = document.getElementById('video-result');
//     loading.classList.add('active');
//     resultDiv.innerHTML = '<p style="color: #E6E6FA;">Lancement de la génération complète...</p>';

//     const signs = [
//         'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo', 
//         'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
//     ];
    
//     const videoProjects = [];

//     try {
//         for (let i = 0; i < signs.length; i++) {
//             const sign = signs[i];
//             resultDiv.innerHTML = `<p style="color: #E6E6FA;">Étape ${i+1}/12 : Génération pour <strong>${sign.toUpperCase()}</strong>...</p>`;

//             // --- CORRECTION ---
//             // Étape 1 : Appelle le NOUVEL endpoint du serveur Flask (URL relative)
//             const horoscopeResponse = await fetch('/api/generate_single_horoscope_with_audio', {
//                 method: 'POST',
//                 headers: { 'Content-Type': 'application/json' },
//                 body: JSON.stringify({ sign: sign })
//             });
//             const horoscopeData = await horoscopeResponse.json();
//             if (!horoscopeData.success) throw new Error(`Erreur horoscope pour ${sign}: ${horoscopeData.error}`);
            
//             const { horoscope, audio_path, audio_duration_seconds } = horoscopeData;

//             // --- CORRECTION ---
//             // Étape 2 : Appelle l'endpoint vidéo du serveur Flask (URL relative)
//             const videoResponse = await fetch('/api/comfyui/generate_video', {
//                 method: 'POST',
//                 headers: { 'Content-Type': 'application/json' },
//                 body: JSON.stringify({ 
//                     sign: sign,
//                     format_name: 'youtube_short',
//                     duration_seconds: audio_duration_seconds 
//                 })
//             });
//             const videoData = await videoResponse.json();
//             if (!videoData.success) throw new Error(`Erreur vidéo pour ${sign}: ${videoData.error}`);

//             videoProjects.push({
//                 sign_name: horoscope.sign,
//                 horoscope_text: horoscope.horoscope_text,
//                 video_path: videoData.result.video_path,
//                 audio_path: audio_path
//             });
//         }

//         resultDiv.innerHTML = '<p style="color: #E6E6FA;">Assemblage final...</p>';
        
//         // Étape 3 : Appelle le serveur de montage qui est SÉPARÉ (URL absolue)
//         const montageResponse = await fetch('http://127.0.0.1:8002/api/create_full_horoscope_video', {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify({ video_projects: videoProjects })
//         });
//         const montageData = await montageResponse.json();
//         if (!montageData.success) throw new Error(`Erreur de montage: ${montageData.error}`);

//         resultDiv.innerHTML = `
//             <div class="horoscope-result">
//                 <h3 style="color: #00ff41;">✅ Montage terminé avec succès !</h3>
//                 <p>Vidéo finale disponible ici :</p>
//                 <p><strong>${montageData.final_video_path}</strong></p>
//             </div>
//         `;

//     } catch (error) {
//         showError(resultDiv, error.message);
//     } finally {
//         loading.classList.remove('active');
//     }
// }
// Dans app.js, remplacez l'ancienne fonction generateSingleSignMontage

/**
 * Lance le workflow complet pour un seul signe :
 * Horoscope + Audio + Vidéo de base + Montage final.
 */
async function generateSingleSignMontage() {
    const signSelect = document.getElementById('video-sign');
    const selectedSign = signSelect ? signSelect.value : null;

    if (!selectedSign) {
        alert("Veuillez d'abord sélectionner un signe astrologique.");
        return;
    }

    const confirmed = confirm(
        `Vous allez lancer le workflow complet pour ${getSignName(selectedSign)}.\n\n` +
        `Cela va générer l'horoscope, l'audio, la vidéo de constellation, puis les assembler.\n\n` +
        `Cette opération peut prendre quelques minutes. Continuer ?`
    );

    if (!confirmed) return;

    const loading = document.getElementById('video-loading');
    const resultDiv = document.getElementById('video-result');
    loading.classList.add('active');
    resultDiv.innerHTML = `<p style="color: #E6E6FA;">Lancement du workflow pour <strong>${selectedSign.toUpperCase()}</strong>...</p>
                           <p style="color: #aaa; font-size: 0.9em;">Étape 1/3: Génération Horoscope & Audio...</p>`;

    try {
        // Étape 1 : Appeler le NOUVEL endpoint de workflow
        const response = await fetch('/api/workflow/complete_sign_generation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            // Envoyez les paramètres nécessaires (sign, format, etc.)
            body: JSON.stringify({ 
                sign: selectedSign,
                format: document.getElementById('video-format').value || 'test',
                add_music: true
            })
        });

        // Mettre à jour le message pendant le traitement (même si ce n'est qu'une simulation)
        // Pour un vrai suivi, il faudrait des WebSockets, mais c'est un bon début.
        resultDiv.querySelector('p:last-child').textContent = 'Étape 2/3: Génération Vidéo Constellation...';
        
        const data = await response.json();
        
        resultDiv.querySelector('p:last-child').textContent = 'Étape 3/3: Montage final...';

        if (data.success) {
            const finalVideoPath = data.final_video_path || data.workflow_results?.synchronized_video?.video_path;
            const finalResult = data.workflow_results?.synchronized_video;

             resultDiv.innerHTML = `
                <div class="horoscope-result">
                    <h3 style="color: #00ff41;">✅ Workflow pour ${getSignName(selectedSign)} terminé !</h3>
                    <p>La vidéo finale synchronisée est prête.</p>
                    <p><strong>Chemin :</strong> ${finalVideoPath}</p>
                    ${finalResult ? `
                        <p style="color: #E6E6FA;"><strong>Durée :</strong> ${finalResult.transcription.duration.toFixed(1)}s</p>
                        <p style="color: #E6E6FA;"><strong>Taille :</strong> ${formatFileSize(finalResult.file_size)}</p>
                        <p style="color: #E6E6FA;"><strong>Musique :</strong> ${finalResult.has_music ? '✅' : '❌'}</p>
                    ` : ''}
                    <div style="margin-top: 20px;">
                        <button class="astro-button" onclick="downloadMontageVideo('${finalVideoPath.split('/').pop()}')">
                            📥 Télécharger la Vidéo Finale
                        </button>
                    </div>
                </div>
            `;
        } else {
            throw new Error(data.error || "Une erreur inconnue est survenue pendant le workflow.");
        }
    } catch (error) {
        showError(resultDiv, `Erreur du Workflow: ${error.message}`);
    } finally {
        loading.classList.remove('active');
    }
}

/**
 * Lance le workflow de génération complet pour les 12 signes.
 * Appelle un unique endpoint backend qui orchestre toutes les étapes.
 */
async function generateFullMontage() {
    const confirmed = confirm(
        '⚠️ Lancer le workflow complet pour les 12 signes ?\n\n' +
        'Le serveur va générer horoscope, audio, et vidéo pour chaque signe, puis les assembler.\n\n' +
        'Le processus peut prendre plus de 30 minutes. Continuer ?'
    );

    if (!confirmed) return;

    const loading = document.getElementById('video-loading');
    const resultDiv = document.getElementById('video-result');
    loading.classList.add('active');
    resultDiv.innerHTML = `<p style="color: #E6E6FA;">Lancement du workflow complet... Le serveur a beaucoup de travail !</p>
                           <p id="progress-text" style="color: #aaa; font-size: 0.9em;">Initialisation...</p>`;
    const progressText = document.getElementById('progress-text');

    try {
        // Un seul appel à l'endpoint qui orchestre tout
        const response = await fetch('/api/workflow/batch_complete_generation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                // On peut passer des paramètres globaux ici si besoin
                format: document.getElementById('video-format').value || 'youtube_short',
                add_music: true
            })
        });
        
        // Simuler une mise à jour de la progression
        if(progressText) progressText.textContent = 'Le serveur traite les signes... Cela peut prendre un certain temps.';

        const data = await response.json();

        if (data.success) {
            const summary = data.summary;
            const finalVideo = data.final_video;
            let resultsHtml = '';

            // Créer une liste détaillée des résultats par signe
            for (const sign in data.batch_results) {
                const result = data.batch_results[sign];
                const success = result.summary.completion_rate === 1;
                const color = success ? '#00ff41' : '#ffc107';
                const icon = success ? '✅' : '⚠️';
                
                resultsHtml += `
                    <div class="batch-result-item" style="border-left: 3px solid ${color};">
                        <strong>${icon} ${getSignName(sign)}</strong>
                        <span>${(result.summary.completion_rate * 100).toFixed(0)}% complété</span>
                    </div>
                `;
            }

            resultDiv.innerHTML = `
                <div class="horoscope-result">
                    <h3 style="color: #00ff41;">✅ Workflow de Lot Terminé !</h3>
                    
                    <div class="video-specs" style="margin-bottom: 20px;">
                        <div class="spec-item">
                            <div class="spec-label">Signes Traités</div>
                            <div class="spec-value">${summary.total_signs}</div>
                        </div>
                        <div class="spec-item">
                            <div class="spec-label">Réussites</div>
                            <div class="spec-value" style="color: #00ff41;">${summary.successful_signs}</div>
                        </div>
                        <div class="spec-item">
                            <div class="spec-label">Échecs</div>
                            <div class="spec-value" style="color: #ff4444;">${summary.failed_signs}</div>
                        </div>
                    </div>

                    <h4 style="color: #E6E6FA; margin-top: 20px;">Vidéo Finale Assemblée</h4>
                    ${finalVideo.success ? `
                        <p style="color: #E6E6FA;"><strong>Chemin :</strong> ${finalVideo.video_path}</p>
                        <p style="color: #E6E6FA;"><strong>Durée :</strong> ${finalVideo.total_duration.toFixed(1)}s</p>
                        <p style="color: #E6E6FA;"><strong>Clips :</strong> ${finalVideo.clips_count}</p>
                        <button class="astro-button" style="margin-top: 10px;" onclick="downloadMontageVideo('${finalVideo.video_path.split('/').pop()}')">
                            📥 Télécharger la Vidéo Finale
                        </button>
                    ` : `
                        <p style="color: #ffc107;">L'assemblage final a échoué. Vérifiez les clips individuels.</p>
                        <p style="color: #aaa;">${finalVideo.error || ''}</p>
                    `}
                    
                    <h4 style="color: #E6E6FA; margin-top: 20px;">Détails par signe</h4>
                    <div class="batch-results"><p style="color: #E6E6FA;">${resultsHtml}</p></div>
                </div>
            `;
        } else {
            throw new Error(`Erreur du workflow de lot : ${data.error}`);
        }

    } catch (error) {
        showError(resultDiv, error.message);
    } finally {
        loading.classList.remove('active');
    }
}

/**
 * Vérifie l'état du système au démarrage
 */
async function checkSystemHealth() {
    try {
        const response = await fetch('/health');
        const data = await response.json();
        
        console.log('État du système:', data);
        
        if (data.status === 'healthy') {
            return true;
        } else {
            console.warn('Système en état dégradé:', data);
            return false;
        }
    } catch (error) {
        console.error('Erreur lors de la vérification système:', error);
        return false;
    }
}

/**
 * Exporte les données de l'application
 */
function exportData() {
    const data = {
        horoscopes: loadFromLocalStorage('horoscopes', []),
        chatMessages: chatMessages,
        preferences: {
            selectedModel: selectedModel,
            currentSection: currentSection
        },
        exportDate: new Date().toISOString()
    };
    
    downloadFile(JSON.stringify(data, null, 2), `astro_data_${new Date().toISOString().split('T')[0]}.json`, 'application/json');
}

/**
 * Crée une vidéo synchronisée pour un seul signe
 */
async function createSynchronizedVideo() {
    const signSelect = document.getElementById('video-sign');
    const loading = document.getElementById('video-loading');
    const resultDiv = document.getElementById('video-result');
    
    const sign = signSelect.value;
    if (!sign) {
        alert('Sélectionnez un signe astrologique');
        return;
    }
    
    const confirmed = confirm(`Créer une vidéo synchronisée pour ${getSignName(sign)} ?\n\nCela inclut sous-titres Whisper + musique.`);
    if (!confirmed) return;
    
    loading.classList.add('active');
    resultDiv.innerHTML = '<p style="color: #E6E6FA;">Création vidéo synchronisée...</p>';
    
    try {
        const response = await fetch('/api/montage/create_single_video', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sign: sign, add_music: true })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const result = data.result;
            resultDiv.innerHTML = `
                <div class="horoscope-result">
                    <h3 style="color: #00ff41;">🎬 Vidéo synchronisée créée !</h3>
                    <p><strong>Signe:</strong> ${result.sign_name} ${getSignSymbol(result.sign)}</p>
                    <p><strong>Durée:</strong> ${result.transcription.duration.toFixed(1)}s</p>
                    <p><strong>Mots transcrits:</strong> ${result.transcription.word_count}</p>
                    <p><strong>Taille:</strong> ${formatFileSize(result.file_size)}</p>
                    <p><strong>Musique:</strong> ${result.has_music ? '✅' : '❌'}</p>
                    
                    <div style="margin: 15px 0; padding: 10px; background: rgba(0,0,0,0.3); border-radius: 5px; max-height: 100px; overflow-y: auto;">
                        <strong>Transcription Whisper:</strong><br>
                        ${result.transcription.full_text}
                    </div>
                    
                    <div style="display: flex; gap: 10px; margin-top: 15px;">
                        <button class="astro-button" onclick="downloadMontageVideo('${result.video_path.split('/').pop()}')">
                            📥 Télécharger
                        </button>
                        <button class="astro-button" onclick="copyText('${result.transcription.full_text.replace(/'/g, "\\'")}')">
                            📋 Copier Transcription
                        </button>
                    </div>
                </div>
            `;
        } else {
            showError(resultDiv, data.error);
        }
    } catch (error) {
        showError(resultDiv, `Erreur: ${error.message}`);
    } finally {
        loading.classList.remove('active');
    }
}

/**
 * Crée la vidéo complète avec tous les signes
 */
async function createCompleteVideo() {
    const confirmed = confirm('Créer la vidéo horoscope complète ?\n\nAssemble tous les signes disponibles.\nTemps estimé: 10-15 minutes.');
    if (!confirmed) return;
    
    const loading = document.getElementById('video-loading');
    const resultDiv = document.getElementById('video-result');
    
    loading.classList.add('active');
    resultDiv.innerHTML = '<p style="color: #E6E6FA;">Création vidéo complète en cours...</p>';
    
    try {
        const response = await fetch('/api/montage/create_full_video', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        
        const data = await response.json();
        
        if (data.success) {
            const result = data.result;
            resultDiv.innerHTML = `
                <div class="horoscope-result">
                    <h3 style="color: #00ff41;">🎉 Vidéo complète créée !</h3>
                    <p><strong>Clips assemblés:</strong> ${result.clips_count}</p>
                    <p><strong>Durée totale:</strong> ${result.total_duration.toFixed(1)}s</p>
                    <p><strong>Taille:</strong> ${formatFileSize(result.file_size)}</p>
                    <p><strong>Signes inclus:</strong> ${result.signs_included.length}/12</p>
                    
                    <div style="margin: 15px 0; padding: 10px; background: rgba(0,0,0,0.3); border-radius: 5px;">
                        <strong>Signes dans la vidéo:</strong><br>
                        ${result.signs_included.map(sign => `${getSignSymbol(sign)} ${getSignName(sign)}`).join(', ')}
                    </div>
                    
                    <div style="display: flex; gap: 10px; margin-top: 15px;">
                        <button class="astro-button" onclick="downloadMontageVideo('${result.video_path.split('/').pop()}')">
                            📥 Télécharger Vidéo Complète
                        </button>
                        <button class="astro-button" onclick="copyText('${result.video_path}')">
                            📋 Copier Chemin
                        </button>
                    </div>
                </div>
            `;
        } else {
            showError(resultDiv, data.error);
        }
    } catch (error) {
        showError(resultDiv, `Erreur: ${error.message}`);
    } finally {
        loading.classList.remove('active');
    }
}

/**
 * Vérifie le statut du serveur de montage
 */
async function checkMontageStatus() {
    try {
        const response = await fetch('/api/montage/status');
        const data = await response.json();
        
        if (data.success) {
            const status = data.status;
            const message = `🎬 STATUT SERVEUR MONTAGE

✅ Statut: ${status.whisper_available && status.ffmpeg_available ? 'Opérationnel' : 'Dégradé'}

🔧 Dépendances:
• Whisper: ${status.whisper_available ? '✅ Disponible' : '❌ Non installé'}
• ffmpeg: ${status.ffmpeg_available ? '✅ Disponible' : '❌ Non installé'}
• Musique: ${status.music_available ? '✅ Disponible' : '❌ Manquante'}

📁 Dossiers:
• Vidéos: ${status.directories.video_input}
• Audios: ${status.directories.audio_input}
• Sortie: ${status.directories.output}

🎵 Musique: ${status.music_path}`;
            
            alert(message);
        } else {
            alert(`❌ Erreur: ${data.error}`);
        }
    } catch (error) {
        alert(`❌ Erreur: ${error.message}`);
    }
}

/**
 * Télécharge une vidéo de montage
 */
function downloadMontageVideo(filename) {
    try {
        const link = document.createElement('a');
        link.href = `/api/montage/download/${filename}`;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        alert('✅ Téléchargement démarré !');
    } catch (error) {
        alert(`❌ Erreur: ${error.message}`);
    }
}

/**
 * Copie du texte dans le presse-papiers
 */
function copyText(text) {
    copyTextWithFallback(text).then(() => {
        alert('✅ Texte copié !');
    }).catch(() => {
        alert('❌ Erreur lors de la copie');
    });
}

// Nouvelles fonctions YouTube (Ajouter à la fin du fichier app.js)

/**
 * Vérifie le statut YouTube
 */
async function checkYouTubeStatus() {
    try {
        const response = await fetch('/api/youtube/status');
        const data = await response.json();
        
        if (data.success && data.youtube_connected) {
            const channel = data.channel_info;
            const available = data.available_videos_count;
            
            const message = `📤 STATUT YOUTUBE\n\n✅ Connecté\n📺 Chaîne: ${channel.title}\n👥 Abonnés: ${channel.subscribers}\n🎬 Vidéos publiées: ${channel.videos}\n📊 Vidéos disponibles: ${available}\n\n🔗 Chaîne: https://youtube.com/channel/${channel.channel_id}`;
            
            alert(message);
        } else {
            alert(`❌ YouTube non connecté\n\nErreur: ${data.error || 'Service indisponible'}`);
        }
    } catch (error) {
        alert(`❌ Erreur connexion: ${error.message}`);
    }
}

/**
 * Upload le signe sélectionné sur YouTube
 */
async function uploadCurrentSignToYouTube() {
    const signSelect = document.getElementById('video-sign');
    const sign = signSelect ? signSelect.value : null;
    
    if (!sign) {
        alert('Sélectionnez d\'abord un signe astrologique');
        return;
    }
    
    const privacyChoice = confirm(`📤 Upload ${getSignName(sign)} sur YouTube ?\n\n✅ OK = Vidéo PRIVÉE\n❌ Annuler = Ne pas upload`);
    if (!privacyChoice) return;
    
    // Option privacy (pour l'instant toujours privé)
    const privacy = 'private';
    
    try {
        // Afficher loading
        const loading = document.getElementById('video-loading');
        if (loading) loading.classList.add('active');
        
        const response = await fetch(`/api/youtube/upload_sign/${sign}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ privacy: privacy })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const successMessage = `✅ UPLOAD YOUTUBE RÉUSSI !\n\n📺 ${data.title}\n🔗 ${data.video_url}\n\n⚠️ Statut: ${privacy.toUpperCase()}\n📅 ${new Date(data.upload_time).toLocaleString()}\n\n▶️ Consultez YouTube Studio pour publier`;
            
            alert(successMessage);
            
            // Optionnel : ouvrir YouTube
            if (confirm('🌐 Ouvrir la vidéo sur YouTube ?')) {
                window.open(data.video_url, '_blank');
            }
        } else {
            alert(`❌ Upload échoué\n\nErreur: ${data.error}`);
        }
    } catch (error) {
        alert(`❌ Erreur: ${error.message}`);
    } finally {
        const loading = document.getElementById('video-loading');
        if (loading) loading.classList.remove('active');
    }
}

/**
 * Upload en lot sur YouTube
 */
async function uploadBatchToYouTube() {
    const confirmed = confirm('📺 Upload en lot sur YouTube ?\n\nToutes les vidéos disponibles seront uploadées en mode PRIVÉ.\n\nCela peut prendre plusieurs minutes.\n\nContinuer ?');
    if (!confirmed) return;
    
    try {
        const loading = document.getElementById('video-loading');
        const resultDiv = document.getElementById('video-result');
        
        if (loading) loading.classList.add('active');
        if (resultDiv) resultDiv.innerHTML = '<p style="color: #E6E6FA;">Upload en lot YouTube en cours...</p>';
        
        const response = await fetch('/api/youtube/upload_batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ privacy: 'private' })
        });
        
        const data = await response.json();
        
        if (data.success) {
            let resultsHtml = `
                <div class="horoscope-result">
                    <h3 style="color: #00ff41;">📺 Upload Batch YouTube Terminé !</h3>
                    <div class="video-specs">
                        <div class="spec-item">
                            <div class="spec-label">Total</div>
                            <div class="spec-value">${data.total}</div>
                        </div>
                        <div class="spec-item">
                            <div class="spec-label">Réussis</div>
                            <div class="spec-value" style="color: #00ff41;">${data.successful}</div>
                        </div>
                        <div class="spec-item">
                            <div class="spec-label">Échoués</div>
                            <div class="spec-value" style="color: #ff4444;">${data.failed}</div>
                        </div>
                    </div>
                    <h4 style="color: #E6E6FA; margin-top: 20px;">Résultats détaillés:</h4>
            `;
            
            data.results.forEach(result => {
                const statusColor = result.success ? '#00ff41' : '#ff4444';
                const statusIcon = result.success ? '✅' : '❌';
                
                resultsHtml += `
                    <div style="margin: 10px 0; padding: 10px; background: rgba(15,15,40,0.6); border-left: 3px solid ${statusColor}; border-radius: 5px;">
                        <strong>${statusIcon} ${getSignName(result.sign)}</strong>
                        ${result.success ? 
                            `<br><a href="${result.video_url}" target="_blank" style="color: #8A2BE2;">🔗 ${result.video_url}</a>` : 
                            `<br><span style="color: #ff4444;">${result.error}</span>`
                        }
                    </div>
                `;
            });
            
            resultsHtml += '</div>';
            
            if (resultDiv) resultDiv.innerHTML = resultsHtml;
            
            alert(`📺 Upload batch terminé !\n\n✅ ${data.successful} réussis\n❌ ${data.failed} échoués\n\n📋 Voir les détails ci-dessous`);
            
        } else {
            alert(`❌ Batch upload échoué: ${data.error}`);
        }
        
    } catch (error) {
        alert(`❌ Erreur: ${error.message}`);
    } finally {
        const loading = document.getElementById('video-loading');
        if (loading) loading.classList.remove('active');
    }
}



// =============================================================================
// GESTIONNAIRES D'ÉVÉNEMENTS ET INITIALISATION
// =============================================================================

/**
 * Initialisation de l'application
 */
// =============================================================================
// GESTIONNAIRES D'ÉVÉNEMENTS ET INITIALISATION UNIQUE
// =============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🌟 Initialisation UNIQUE de l\'application Astro Generator');
    
    // Définir la date d'aujourd'hui par défaut
    const today = new Date().toISOString().split('T')[0];
    const dateInputs = [
        'date-input',
        'daily-date-input', 
        'context-date-input',
        'video-date'
    ];
    
    dateInputs.forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) input.value = today;
    });
    
    // Charger le modèle sauvegardé
    const savedModel = localStorage.getItem('selectedModel');
    if (savedModel) {
        selectedModel = savedModel;
    }
    
    // Charger les modèles disponibles
    loadAvailableModels();
    
    // Gestionnaire pour le formulaire horoscope individuel
    const individualForm = document.getElementById('individual-form');
    if (individualForm) {
        individualForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const signSelect = document.getElementById('sign-select');
            const dateInput = document.getElementById('date-input');
            
            if (!signSelect || !signSelect.value) {
                alert('Veuillez sélectionner un signe astrologique');
                return;
            }
            
            generateIndividualHoroscope(signSelect.value, dateInput?.value || null);
        });
    }

    // Gestionnaire pour le chat
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendChatMessage();
            }
        });
    }

    // Gestionnaire pour le changement de modèle
    const modelSelect = document.getElementById('global-model-select');
    if (modelSelect) {
        modelSelect.addEventListener('change', changeModel);
    }
    
    // Ajouter les boutons ComfyUI après un délai pour s'assurer que le DOM est prêt
    setTimeout(() => {
        addComfyUIButtons();
    }, 500);
    
    // Configuration responsive
    setupResponsiveHandlers();
    
    // Vérification de l'état du système
    checkSystemHealth();
    
    console.log('✅ Initialisation terminée.');
});
/**
 * Configuration des gestionnaires responsive
 */
function setupResponsiveHandlers() {
    function checkResponsive() {
        const menuToggle = document.querySelector('.menu-toggle');
        const sidebar = document.getElementById('sidebar');
        
        if (window.innerWidth <= 768) {
            if (menuToggle) menuToggle.style.display = 'block';
        } else {
            if (menuToggle) menuToggle.style.display = 'none';
            if (sidebar) sidebar.classList.remove('open');
        }
    }
    
    checkResponsive();
    window.addEventListener('resize', checkResponsive);
    
    // Fermer le menu quand on clique ailleurs
    document.addEventListener('click', function(e) {
        const sidebar = document.getElementById('sidebar');
        const menuToggle = document.querySelector('.menu-toggle');
        
        if (window.innerWidth <= 768 && 
            sidebar && menuToggle &&
            !sidebar.contains(e.target) && 
            !menuToggle.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    });
}

// =============================================================================
// FONCTIONS GLOBALES POUR LA COMPATIBILITÉ
// =============================================================================

// Exposer les fonctions principales pour l'utilisation dans l'HTML
window.showSection = showSection;
window.toggleSidebar = toggleSidebar;
window.generateDailyHoroscopes = generateDailyHoroscopes;
window.getAstralContext = getAstralContext;

window.sendChatMessage = sendChatMessage;

window.generateComfyUIVideo = generateComfyUIVideo;
window.generateComfyUIBatchVideos = generateComfyUIBatchVideos;
window.checkComfyUIStatus = checkComfyUIStatus;
window.previewComfyUIPrompt = previewComfyUIPrompt;
window.downloadComfyUIVideo = downloadComfyUIVideo;
window.copyVideoInfo = copyVideoInfo;
window.showComfyUIBatchSummary = showComfyUIBatchSummary;

window.generateFullMontage = generateFullMontage;
// Exposer les nouvelles fonctions globalement
window.checkYouTubeStatus = checkYouTubeStatus;
window.uploadCurrentSignToYouTube = uploadCurrentSignToYouTube;
window.uploadBatchToYouTube = uploadBatchToYouTube;