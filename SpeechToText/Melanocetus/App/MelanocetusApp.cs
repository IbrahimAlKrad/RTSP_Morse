using Melanocetus.Audio;
using Melanocetus.Config;
using Melanocetus.STT;
using Melanocetus.Utils;
using Confluent.Kafka;   
namespace Melanocetus.App
{
    internal sealed class MelanocetApp : IDisposable
    {
        private readonly AppMetrics _metrics;

        private IAudioSource _source;

        private AudioDispatcher _dispatcher = null!;

        private VoskSink _sttSink = null!;

        private bool _started;

        
        // Kafka Producer 
        
        private readonly IProducer<Null, string> _producer =
            new ProducerBuilder<Null, string>(
                new ProducerConfig { BootstrapServers = "localhost:9092" }).Build();

        // Kafka topic 
        private const string KafkaTopic = "TEXT";

        public MelanocetApp(AppMetrics metrics)
        {
            _metrics = metrics;
        }

        public void Start(IAudioSource source)
        {
            _source = source;
            _source.OnAudioAvailable += frame =>
            {
                Interlocked.Add(ref _metrics.SamplesThisSecond, frame.Length);
            };

            // Safe direct cast with null-forgiving operator
            Config.Config.Runtime.RecordingSampleRate = ((NaudioMicrophoneSource)source)!.SampleRate;

            _dispatcher = new AudioDispatcher(_source, 64);
            //changed to en-us model if you want another language change the path accordingly (de)
            _sttSink = new VoskSink("models/vosk-model-small-en-us-0.15", 64);
            _sttSink.OnQueueChanged += q => _metrics.SttPendingPackets = q;

            
            // SEND PARTIAL RESULTS TO KAFKA
            
            _sttSink.OnPartial += async text =>
            {
                DebugConsole.Log($"[STT]: (Partial): {text}");

                await _producer.ProduceAsync(
                    KafkaTopic,
                    new Message<Null, string> { Value = text }
                );
            };

            
            // SEND FINAL RESULTS TO KAFKA
            
            _sttSink.OnFinal += async text =>
            {
                DebugConsole.Log($"[STT]: (Final): {text}");

                await _producer.ProduceAsync(
                    KafkaTopic,
                    new Message<Null, string> { Value = text }
                );
            };

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

            // Dispose Kafka producer
            _producer?.Dispose();
        }
    }
}
