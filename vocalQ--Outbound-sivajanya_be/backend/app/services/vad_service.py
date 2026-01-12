import torch
import logging
import numpy as np
import audioop

logger = logging.getLogger(__name__)

class VadService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VadService, cls).__new__(cls)
            cls._instance.model = None
            cls._instance.utils = None
            cls._instance.sampling_rate = 8000  # Twilio standard
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        try:
            logger.info("Loading Silero VAD model...")
            # Load model from PyTorch Hub
            self.model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                trust_repo=True
            )
            self.utils = utils
            logger.info("Silero VAD model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Silero VAD: {e}")

    def is_speech(self, audio_chunk_bytes: bytes) -> float:
        """
        Detects if speech is present in the provided audio chunk (G.711 u-law bytes).
        Returns the probability of speech (0.0 to 1.0).
        """
        if not self.model:
            return 0.0

        try:
            # 1. Convert u-law (bytes) -> PCM 16-bit (bytes)
            # Twilio sends mulaw. audioop.ulaw2lin converts to linear PCM. 
            # width=2 means 16-bit.
            pcm_data = audioop.ulaw2lin(audio_chunk_bytes, 2)

            # 2. Convert PCM 16-bit (bytes) -> Float32 (Tensor)
            # Create numpy array from bytes
            audio_int16 = np.frombuffer(pcm_data, dtype=np.int16)
            
            # Normalize Int16 to Float32 [-1, 1]
            audio_float32 = audio_int16.astype(np.float32) / 32768.0

            # 3. Create Torch Tensor
            tensor = torch.from_numpy(audio_float32)

            # 4. Predict
            # Silero expects (batch, time) or (time). 
            # Note: For continuous stream, maintaining state is better, 
            # but for simple probability check per chunk, this works.
            # We suppress gradient calculation for inference.
            with torch.no_grad():
                speech_prob = self.model(tensor, self.sampling_rate).item()

            return speech_prob

        except Exception as e:
            logger.error(f"VAD Processing Error: {e}")
            return 0.0

# Singleton instance
vad_service = VadService()
