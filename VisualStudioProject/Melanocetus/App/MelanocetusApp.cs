using Melanocetus.Audio;
using Melanocetus.Config;
using Melanocetus.STT;
using Melanocetus.Utils;

namespace Melanocetus.App
{
    internal sealed class MelanocetApp : IDisposable
    {

        private readonly AppMetrics _metrics;
        
        private IAudioSource _source;
        
        private AudioDispatcher _dispatcher = null!;
        
        private VoskSink _sttSink = null!;
        
        private bool _started;

        public MelanocetApp(AppMetrics metrics) => _metrics = metrics;

        public void Start(IAudioSource source)
        {
            _source = source;
            _source.OnAudioAvailable += frame =>
            {
                Interlocked.Add(ref _metrics.SamplesThisSecond, frame.Length);
            };
            Config.Config.Runtime.RecordingSampleRate = (source as NaudioMicrophoneSource).SampleRate;

            _dispatcher = new AudioDispatcher(_source, 64);
            
            _sttSink = new VoskSink("models/vosk-model-small-de-0.15", 64);
            _sttSink.OnQueueChanged += q => _metrics.SttPendingPackets = q;
            _sttSink.OnFinal += text => DebugConsole.Log($"[STT]: (Final): {text}");
            _sttSink.OnPartial += text => DebugConsole.Log($"[STT]: (Partial): {text}");

            _dispatcher.AddSink(_sttSink);

            _dispatcher.Start();
            _started = true;
        }

        public void Stop()
        {
            if (!_started) return;
            _started = false;
            try { _dispatcher.Stop(); } catch { }
        }

        public void Dispose()
        {
            _dispatcher?.Dispose();
            (_source as IDisposable)?.Dispose();
        }
    }
}
