import pytest
import datetime
from astro_server import AstroGenerator, HoroscopeResult

# Crée une instance unique du générateur pour tous les tests
@pytest.fixture(scope="module")
def generator():
    return AstroGenerator()

def test_get_season(generator):
    """Teste la fonction de détermination de la saison."""
    assert generator._get_season(datetime.date(2025, 7, 18)) == "summer"
    assert generator._get_season(datetime.date(2025, 1, 15)) == "winter"

def test_get_sign_metadata_success(generator):
    """Teste la récupération des métadonnées d'un signe connu."""
    metadata = generator.get_sign_metadata("pisces")
    assert metadata is not None
    assert metadata.name == "Poissons"
    assert metadata.element == "Eau"

def test_get_sign_metadata_failure(generator):
    """Teste la récupération pour un signe inconnu."""
    assert generator.get_sign_metadata("ophiuchus") is None

@pytest.mark.asyncio
async def test_generate_single_horoscope_runs(generator: AstroGenerator):
    """
    Teste que la génération d'horoscope s'exécute et retourne la bonne structure.
    """
    # result est bien un objet de type HoroscopeResult
    result = await generator.generate_single_horoscope("scorpio")
    assert isinstance(result, HoroscopeResult)
    assert result.sign == "Scorpion"
    assert isinstance(result.horoscope_text, str)
    assert len(result.horoscope_text) > 20 # On vérifie que du texte a bien été généré