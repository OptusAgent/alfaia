from datetime import datetime, timedelta
import pytest
from app.services.transcription_service import TranscriptionService, FALLBACK_AUDIO_ERROR_MSG


def test_transcricao_audio_sucesso():
    """Testa transcrição bem sucedida de áudio em texto (AC 1)."""
    sucesso, texto = TranscriptionService.transcrever_audio(midia_url="https://audio.example.com/test_audio.ogg")
    assert sucesso is True
    assert "vestido longo vermelho" in texto.lower()


def test_transcricao_audio_falha_retorna_fallback():
    """Testa se falhas de transcrição retornam o fallback amigável ao lead (AC 2, PRD §21.2)."""
    sucesso, texto = TranscriptionService.transcrever_audio(midia_url="https://audio.example.com/corrupted.ogg", simular_falha=True)
    assert sucesso is False
    assert texto == FALLBACK_AUDIO_ERROR_MSG
    assert texto == "Não consegui ouvir o áudio, pode escrever?"


def test_expurgo_audios_antigos_7_dias():
    """Testa expurgo de áudios com retenção superior a 7 dias (AC 3, S11, PRD §22)."""
    t0 = datetime.now()
    audios = [
        {"id": "audio_recente", "midia_url": "url1", "criado_em": t0 - timedelta(days=2)},
        {"id": "audio_antigo_8d", "midia_url": "url2", "criado_em": t0 - timedelta(days=8)},
        {"id": "audio_antigo_30d", "midia_url": "url3", "criado_em": t0 - timedelta(days=30)},
    ]

    expurgados = TranscriptionService.expurgar_audios_antigos(audios, dias_retencao=7, now=t0)

    assert len(expurgados) == 2
    assert "audio_antigo_8d" in expurgados
    assert "audio_antigo_30d" in expurgados
    assert "audio_recente" not in expurgados
