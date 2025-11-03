// Based on prior work by M. Elvers (2025) - adapted for the Stream Processing Project.

using Melanocetus.Utils;

namespace Melanocetus.Audio
{

    internal sealed class AudioDispatcher : IDisposable
    {
        private readonly IAudioSource _source;

        private readonly List<IAudioSink> _audioSinks = new List<IAudioSink>();

        private readonly RentedBufferPool<float> _audioBufferQueue;

        private readonly object _lock = new();

        private bool _muted = false;
        private bool _started = false;
        private bool _disposed = false;

        public AudioDispatcher(IAudioSource source, int bufferQueueSize = 32)
        {
            _source = source ?? throw new ArgumentNullException(nameof(source));
            ArgumentOutOfRangeException.ThrowIfNegativeOrZero(bufferQueueSize);

            _audioBufferQueue = new RentedBufferPool<float>(bufferQueueSize);
            _source.OnAudioAvailable += OnAudioAvailableFromSource;
        }

        public void AddSink(IAudioSink sink)
        {
            if (sink == null) return;
            lock (_lock)
                _audioSinks.Add(sink);
        }

        public void RemoveSink(IAudioSink sink)
        {
            if (sink == null) return;
            lock (_lock)
                _audioSinks.Remove(sink);
        }

        public void Mute() => _muted = true;

        public void Unmute() => _muted = false;

        public void Start()
        {
            if (_disposed) throw new ObjectDisposedException(nameof(AudioDispatcher));
            if (_started) return;

            _started = true;
            _source.Start();
        }

        public void Stop()
        {
            if (_disposed) return;
            if (!_started) return;
            _started = false;
            _source.Stop();
        }

        private void OnAudioAvailableFromSource(ReadOnlyMemory<float> data)
        {
            if (_muted || data.Length == 0) return;

            // Data is copied into the internal buffer pool, it remains valid until the queue wraps around
            var buffer = _audioBufferQueue.GetBuffer(data.Length);
            data.Span.CopyTo(buffer.AsSpan());

            IAudioSink[] sinksSnapshot;
            lock (_lock)
                sinksSnapshot = _audioSinks.Count == 0 ? Array.Empty<IAudioSink>() : _audioSinks.ToArray();

            foreach (var sink in sinksSnapshot)
            {
                if (sink == null) continue;
                try
                {
                    // Each sink receives the audio data; if needed they copy it internally
                    sink.OnAudioAvailable(buffer.AsReadOnlyMemory());
                }
                catch (Exception ex)
                {
                    DebugConsole.Log($"[AudioDispatcher] Sink error: {ex.Message}");
                }
            }
        }

        public void Dispose()
        {
            if (_disposed) return;

            _disposed = true;

            _source.OnAudioAvailable -= OnAudioAvailableFromSource;

            try { _source.Stop(); } catch { }
            _source?.Dispose();

            lock (_lock)
            {
                foreach (var sink in _audioSinks)
                    sink?.Dispose();
                _audioSinks.Clear();
            }

            _audioBufferQueue.Dispose();
        }
    }
}
