// Based on prior work by M. Elvers (2025) - adapted for the Stream Processing Project.

using Melanocetus.Audio;
using Melanocetus.Codec;
using Melanocetus.Resampling;
using Melanocetus.Utils;

namespace Melanocetus.STT
{
    /// <summary>
    /// <see cref="IAudioSink"/> to receive data for Vosk.
    /// </summary>
    public class VoskSink : IAudioSink, IDisposable
    {
        private const int TargetSampleRate = 16000;

        private readonly VoskInstance _voskInstance;

        private readonly int _bufferPoolSize;

        private readonly Pcm16ShortCodec _codec = new Pcm16ShortCodec();

        private readonly Action<int> _queueHandler;
        private readonly Action<string> _partialHandler;
        private readonly Action<string> _finalHandler;

        private RentedBuffer<float> _resampleBuffer;

        private RentedBufferPool<short> _pool;

        public event Action<int>? OnQueueChanged;
        public event Action<string>? OnPartial;
        public event Action<string>? OnFinal;

        public VoskSink(string modelFolderPath, int bufferPoolSize = 64)
        {
            _bufferPoolSize = bufferPoolSize;
            _pool = new RentedBufferPool<short>(_bufferPoolSize);
            _resampleBuffer = RentedBuffer<float>.Rent(0);
            _voskInstance = new VoskInstance(modelFolderPath, _bufferPoolSize, 128); // Use the small model for now, path could be configurable later

            _queueHandler = count => OnQueueChanged?.Invoke(count);
            _partialHandler = text => OnPartial?.Invoke(text);
            _finalHandler = text => OnFinal?.Invoke(text);

            _voskInstance.OnQueueChanged += _queueHandler;
            _voskInstance.OnPartial += _partialHandler;
            _voskInstance.OnFinal += _finalHandler;
        }

        /// <summary>
        /// Audio data available callback.
        /// </summary>
        /// <param name="data">The data.</param>
        public void OnAudioAvailable(ReadOnlyMemory<float> data)
        {
            if (Config.Config.Runtime.RecordingSampleRate == null || Config.Config.Runtime.RecordingSampleRate <= 0)
            {
                DebugConsole.Log("[STT]: Invalid recording sample rate in config.");
                return;
            }

            // Vosk requires 16kHz mono audio, so we need to resample
            LinearResampler.TryResample(data.Span, Config.Config.Runtime.RecordingSampleRate.Value, TargetSampleRate, ref _resampleBuffer);

            // Vosk requires 16-bit PCM audio, so we need to encode
            Span<short> encoded = _codec.EncodeToMemory(_resampleBuffer.AsSpan());
            var encodedBuffer = _pool.GetBuffer(encoded.Length);

            // Copy into buffer pool so the next call does not overwrite the data if it happens before we are finished
            encoded.CopyTo(encodedBuffer.AsSpan());
            encodedBuffer.UpdateLength(encoded.Length);

            _voskInstance.AddSample(encodedBuffer.AsReadOnlyMemory());
        }

        public void Dispose()
        {
            _voskInstance.OnQueueChanged -= _queueHandler;
            _voskInstance.OnPartial -= _partialHandler;
            _voskInstance.OnFinal -= _finalHandler;

            _resampleBuffer.Dispose();
            _pool.Dispose();
        }
    }
}
