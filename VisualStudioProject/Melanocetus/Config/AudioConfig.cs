using Melanocetus.Utils;

namespace Melanocetus.Config
{
    internal class AudioConfig
    {
        public int TargetRecordingSampleRate { get; init; } = 24000;

        public int CodecSampleRate { get; init; } = 24000; // Originally used for OPUS, still included in case of future requirements

        public int FrameDurationMs { get; init; } = 20;

        public string? Device { get; init; }

        public int FrameSize => GetValidFrameSize(CodecSampleRate, FrameDurationMs);

        public int GetInputFrameSize(int recordingSampleRate) => (int)Math.Round((double)FrameSize * recordingSampleRate / CodecSampleRate);

        public int MaxPacketSize => 3 * FrameSize + 7;

        public void ValidateAndNormalize()
        {
            if (TargetRecordingSampleRate <= 0) throw new ArgumentOutOfRangeException(nameof(TargetRecordingSampleRate));
            if (CodecSampleRate <= 0) throw new ArgumentOutOfRangeException(nameof(CodecSampleRate));
            if (!IsValidOpusDuration(FrameDurationMs))
                DebugConsole.Log($"[Config] Invalid frame duration {FrameDurationMs} ms -> fallback 20 ms");
        }

        private static bool IsValidOpusDuration(int ms) => ms is 2 or 5 or 10 or 20 or 40 or 60;

        private static int GetValidFrameSize(int sampleRate, int durationMs)
        {
            var duration = IsValidOpusDuration(durationMs) ? durationMs : 20;
            // Samples per ms * duration
            return (int)Math.Round((sampleRate / 1000.0d) * duration);
        }

    }
}
