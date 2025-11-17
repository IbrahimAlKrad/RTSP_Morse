#!/usr/bin/env python

import numpy as np
import pyaudio
import math

from audio_app.operator import StreamOperator
from .generated import audio_chunk_pb2, morse_frame_pb2


class GoertzelOperator(
    StreamOperator[audio_chunk_pb2.AudioChunk, morse_frame_pb2.MorseFrame]
):
    INPUT_TYPE = audio_chunk_pb2.AudioChunk
    OUTPUT_TYPE = morse_frame_pb2.MorseFrame

    SOURCE_TOPIC = "raw_audio_topic"
    TARGET_TOPIC = "frequency_intensity"
    GROUP_ID = "goertzel-extractor-group"
    TARGET_KAFKA_KEY = b"400"

    TARGET_FREQUENCY = 400

    DTYPE_FROM_FORMAT = {
        pyaudio.paInt8: np.int8,
        pyaudio.paInt16: np.int16,
        pyaudio.paInt32: np.int32,
        pyaudio.paFloat32: np.float32,
    }

    MAX_AMP_FROM_FORMAT = {
        pyaudio.paInt8: np.iinfo(np.int8).max,
        pyaudio.paInt16: np.iinfo(np.int16).max,
        pyaudio.paInt32: np.iinfo(np.int32).max,
        pyaudio.paFloat32: 1.0,
    }

    def goertzel(self, samples, sample_rate, target_freq, max_sample_value):
        if target_freq >= sample_rate / 2:
            print(
                f"The target frequency ({target_freq}) is too high for the sample rate ({sample_rate})"
            )
        n = len(samples)
        k = int(0.5 + ((n * target_freq) / sample_rate))
        omega = (2.0 * math.pi * k) / n
        coeff = 2.0 * math.cos(omega)

        s_prev = 0.0
        s_prev2 = 0.0

        for sample in samples:
            s = sample + coeff * s_prev - s_prev2
            s_prev2 = s_prev
            s_prev = s

        power = s_prev2**2 + s_prev**2 - coeff * s_prev * s_prev2
        magnitude = math.sqrt(power)
        max_magnitude = (max_sample_value * n) / 2
        normalized_magnitude = magnitude / max_magnitude

        if normalized_magnitude > 1.0:
            self.print_warning(
                "clipping",
                f"Warning: Audio clipping detected! Normalized magnitude: {normalized_magnitude:.2f}",
            )

        return normalized_magnitude

    def process(
        self, input_msg: audio_chunk_pb2.AudioChunk
    ) -> morse_frame_pb2.MorseFrame:
        try:
            dtype = self.DTYPE_FROM_FORMAT[input_msg.data_format]
            max_amplitude = self.MAX_AMP_FROM_FORMAT[input_msg.data_format]
        except KeyError:
            self.on_process_error(
                ValueError(
                    f"Received chunk with unsupported format: {input_msg.data_format}"
                ),
                input_msg,
            )
            return

        audio_samples = np.frombuffer(input_msg.data, dtype=dtype)
        samples_float = audio_samples.astype(np.float64)
        normalized_magnitude = self.goertzel(
            samples_float, input_msg.sample_rate, self.TARGET_FREQUENCY, max_amplitude
        )
        clamped_magnitude = np.clip(normalized_magnitude, 0.0, 1.0)

        frame = morse_frame_pb2.MorseFrame()
        frame.magnitude = clamped_magnitude
        frame.frequency = self.TARGET_FREQUENCY

        return frame


if __name__ == "__main__":
    operator = GoertzelOperator()
    operator.run()
