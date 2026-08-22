import asyncio
import base64
import logging
from typing import Optional
from livekit import rtc
from livekit.agents import (
    DEFAULT_API_CONNECT_OPTIONS,
    APIConnectOptions,
    APIConnectionError,
    stt,
    utils,
)
from sarvamai import (
    AsyncSarvamAI,
    RealtimeAudioInput,
    RealtimeEnd,
    RealtimeFlush,
)

logger = logging.getLogger("sarvam_stt")


class SarvamRealtimeSpeechStream(stt.SpeechStream):
    """
    Real-time bidirectional WebSocket speech stream powered by Sarvam saaras:v3-realtime.
    Streams linear16 raw PCM audio directly over WebSockets and emits LiveKit SpeechEvents.
    """

    def __init__(
        self,
        *,
        stt_instance: "SarvamRealtimeSTT",
        api_key: str,
        language: str = "en-IN",
        model: str = "saaras:v3-realtime",
        mode: str = "transcribe",
        stream_type: str = "balanced",
        sample_rate: int = 16000,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ):
        super().__init__(stt=stt_instance, conn_options=conn_options, sample_rate=sample_rate)
        self._api_key = api_key
        self._language = language
        self._model = model
        self._mode = mode
        self._stream_type = stream_type
        self._sample_rate = sample_rate
        self._client = AsyncSarvamAI(api_subscription_key=self._api_key)

    async def _run(self) -> None:
        logger.info(
            f"Connecting to Sarvam Realtime STT WebSocket (model={self._model}, lang={self._language}, mode={self._mode})"
        )
        try:
            async with self._client.speech_to_text_realtime_streaming.connect(
                language_code=self._language,
                model=self._model,
                mode=self._mode,
                stream_type=self._stream_type,
                encoding="linear16",
                sample_rate=str(self._sample_rate),
            ) as ws:
                logger.info("Connected to Sarvam Realtime STT WebSocket successfully.")

                async def send_audio():
                    # 100ms buffer at 16kHz mono 16-bit = 3200 bytes
                    chunk_size = int(self._sample_rate * 0.1 * 2)
                    buf = bytearray()

                    try:
                        async for frame in self._input_ch:
                            if isinstance(frame, rtc.AudioFrame):
                                buf.extend(frame.data.tobytes())
                                while len(buf) >= chunk_size:
                                    chunk = bytes(buf[:chunk_size])
                                    del buf[:chunk_size]
                                    b64_audio = base64.b64encode(chunk).decode("utf-8")
                                    await ws.send_realtime_audio_input(
                                        RealtimeAudioInput(audio=b64_audio)
                                    )
                            elif isinstance(frame, stt.RecognizeStream._FlushSentinel):
                                if buf:
                                    b64_audio = base64.b64encode(bytes(buf)).decode("utf-8")
                                    buf.clear()
                                    await ws.send_realtime_audio_input(
                                        RealtimeAudioInput(audio=b64_audio)
                                    )
                                await ws.send_realtime_flush(RealtimeFlush())
                    except asyncio.CancelledError:
                        pass
                    finally:
                        try:
                            if buf:
                                b64_audio = base64.b64encode(bytes(buf)).decode("utf-8")
                                buf.clear()
                                await ws.send_realtime_audio_input(
                                    RealtimeAudioInput(audio=b64_audio)
                                )
                            await ws.send_realtime_end(RealtimeEnd())
                        except Exception as e:
                            logger.debug(f"Error ending realtime stream: {e}")

                async def receive_events():
                    try:
                        async for message in ws:
                            event = getattr(message, "event", None)
                            if event == "transcript.partial":
                                text = getattr(message, "text", "")
                                if text and text.strip():
                                    self._event_ch.send(
                                        stt.SpeechEvent(
                                            type=stt.SpeechEventType.INTERIM_TRANSCRIPT,
                                            alternatives=[
                                                stt.SpeechData(
                                                    language=self._language,
                                                    text=text.strip(),
                                                )
                                            ],
                                        )
                                    )
                            elif event == "transcript.final":
                                text = getattr(message, "text", "")
                                if text and text.strip():
                                    logger.info(f"Sarvam STT Final Transcript: '{text.strip()}'")
                                    self._event_ch.send(
                                        stt.SpeechEvent(
                                            type=stt.SpeechEventType.FINAL_TRANSCRIPT,
                                            alternatives=[
                                                stt.SpeechData(
                                                    language=self._language,
                                                    text=text.strip(),
                                                )
                                            ],
                                        )
                                    )
                            elif event == "speech.start" or event == "vad.speech_start":
                                self._event_ch.send(
                                    stt.SpeechEvent(type=stt.SpeechEventType.START_OF_SPEECH)
                                )
                            elif event == "speech.end" or event == "vad.speech_end":
                                self._event_ch.send(
                                    stt.SpeechEvent(type=stt.SpeechEventType.END_OF_SPEECH)
                                )
                            elif event == "error":
                                err_msg = getattr(message, "message", str(message))
                                is_fatal = getattr(message, "is_fatal", False)
                                logger.error(f"Sarvam Realtime STT Error: {err_msg} (fatal={is_fatal})")
                                if is_fatal:
                                    break
                            elif event == "session.end":
                                logger.debug("Sarvam STT session completed.")
                                break
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        logger.error(f"Error receiving Sarvam STT events: {e}")
                        raise

                await asyncio.gather(send_audio(), receive_events())

        except Exception as e:
            logger.error(f"Sarvam Realtime STT WebSocket connection failed: {e}")
            raise APIConnectionError(f"Sarvam STT WebSocket failed: {e}") from e


class SarvamRealtimeSTT(stt.STT):
    """
    LiveKit STT provider using Sarvam AI Saaras v3 realtime streaming over WebSockets.
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        language: str = "en-IN",
        model: str = "saaras:v3-realtime",
        mode: str = "transcribe",
        stream_type: str = "balanced",
        sample_rate: int = 16000,
    ):
        super().__init__(
            capabilities=stt.STTCapabilities(
                streaming=True,
                interim_results=True,
            )
        )
        self._api_key = (api_key or "").strip()
        self._language = language
        self._model = model
        self._mode = mode
        self._stream_type = stream_type
        self._sample_rate = sample_rate

    @property
    def model(self) -> str:
        return self._model

    @property
    def provider(self) -> str:
        return "Sarvam AI (Saaras v3 Realtime)"

    def stream(
        self,
        *,
        language: utils.NotGivenOr[str] = utils.NOT_GIVEN,
        conn_options: APIConnectOptions = DEFAULT_API_CONNECT_OPTIONS,
    ) -> stt.SpeechStream:
        resolved_lang = language if utils.is_given(language) else self._language
        return SarvamRealtimeSpeechStream(
            stt_instance=self,
            api_key=self._api_key,
            language=resolved_lang,
            model=self._model,
            mode=self._mode,
            stream_type=self._stream_type,
            sample_rate=self._sample_rate,
            conn_options=conn_options,
        )

    async def _recognize_impl(
        self,
        buffer: utils.AudioBuffer,
        *,
        language: utils.NotGivenOr[str] = utils.NOT_GIVEN,
        conn_options: APIConnectOptions,
    ) -> stt.SpeechEvent:
        resolved_lang = language if utils.is_given(language) else self._language
        wav_bytes = rtc.combine_audio_frames(buffer).to_wav_bytes()
        client = AsyncSarvamAI(api_subscription_key=self._api_key)
        resp = await client.speech_to_text.transcribe(
            file=wav_bytes,
            model="saaras:v3",
            language_code=resolved_lang,
            mode=self._mode,
        )
        transcript = getattr(resp, "transcript", "") or ""
        return stt.SpeechEvent(
            type=stt.SpeechEventType.FINAL_TRANSCRIPT,
            alternatives=[stt.SpeechData(language=resolved_lang, text=transcript)],
        )
