// Based on prior work by M. Elvers (2025) - adapted for the Stream Processing Project.

using System.Collections.Concurrent;
using Vosk;
using Melanocetus.Utils;
using System.Text.Json;

namespace Melanocetus.STT
{
    /// <summary>
    /// Class to manage Vosk.
    /// </summary>
    public class VoskInstance : IDisposable
    {
        private readonly int _maxQueueLength;

        private readonly ConcurrentQueue<RentedBuffer<short>> _queue = new ConcurrentQueue<RentedBuffer<short>>();

        private readonly RentedBufferPool<short> _pool;

        private Model _model;
        private VoskRecognizer _recognizer;

        private volatile bool _initialized;
        private volatile bool _finished;

        /// <summary>
        /// Raised when a partial transcription is available.
        /// </summary>
        public event Action<string> OnPartial;

        /// <summary>
        /// Raised when a final transcription is available.
        /// </summary>
        public event Action<string> OnFinal;

        /// <summary>
        /// Raised when internal queue length changes.
        /// </summary>
        public event Action<int> OnQueueChanged;

        /// <summary>
        /// Creates a new instance of Vosk.
        /// </summary>
        /// <param name="modelFolder">Path to the model files.</param>
        /// <param name="poolSize">Size of the queue pool.</param>
        public VoskInstance(string modelFolder, int poolSize = 256, int maxQueueLength = 128)
        {
            _pool = new RentedBufferPool<short>(poolSize);
            _maxQueueLength = maxQueueLength;
            InitializeAsync(modelFolder);
        }

        /// <summary>
        /// Add a new sample to the queue.
        /// </summary>
        /// <param name="sample"></param>
        public void AddSample(ReadOnlyMemory<short> sample)
        {
            if (!_initialized) return;

            // Drop oldest sample if queue is full
            if (_queue.Count >= _maxQueueLength && _queue.TryDequeue(out var drop))
            {
                drop.Dispose();
                NotifyQueueChanged();
            }

            // Copy sample because it might be overwritten from outside before we actually use it
            var buffer = _pool.GetBuffer(sample.Length);
            sample.Span.CopyTo(buffer.AsSpan());
            buffer.UpdateLength(sample.Length);

            _queue.Enqueue(buffer);
            NotifyQueueChanged();
        }

        /// <summary>
        /// The main processing loop for Vosk.
        /// </summary>
        /// <returns></returns>
        private async Task ProcessLoopAsync()
        {
            DebugConsole.Log($"[STT]: Initialized Vosk.");
            while (!_finished)
            {
                if (!_queue.TryDequeue(out var buffer))
                {
                    await Task.Delay(1); // yield to free up cpu
                    continue;
                }

                NotifyQueueChanged();

                bool final = _recognizer.AcceptWaveform(buffer.Buffer, buffer.Length);
                buffer.Dispose();

                try
                {
                    if (final)
                        TriggerFinal(_recognizer.FinalResult());
                    else
                        TriggerPartial(_recognizer.PartialResult());
                }
                catch (Exception e)
                {
                    DebugConsole.Log($"[STT]: Callback error while processing: {e}");
                }
            }
        }

        /// <summary>
        /// Initializes Vosk asynchronously.
        /// </summary>
        /// <param name="modelFolderName"></param>
        private async void InitializeAsync(string modelFolderName)
        {
            Vosk.Vosk.SetLogLevel(0);

            // The small model only takes a few seconds since it is only a few MB in size. The larger model is 2GB+ and takes over a minute to load.
            // Async since otherwise Unity will freeze
            await Task.Run(() =>
            {
                // Resolve model path relative to executable if not absolute
                string path = Path.IsPathRooted(modelFolderName) ? modelFolderName : Path.Combine(AppContext.BaseDirectory, modelFolderName);

                _model = new Model(path);
                _recognizer = new VoskRecognizer(_model, 16000);
                _recognizer.SetMaxAlternatives(0);
                _recognizer.SetWords(true);
            });

            _initialized = true;
            _ = Task.Run(ProcessLoopAsync);
        }

        /// <summary>
        /// Trigger the final transcription event.
        /// </summary>
        /// <param name="json">The output from Vosk.</param>
        private void TriggerFinal(string json)
        {
            try
            {
                using var doc = JsonDocument.Parse(json);
                if (doc.RootElement.TryGetProperty("text", out var textProp))
                {
                    string text = textProp.GetString();
                    if (!string.IsNullOrEmpty(text))
                        OnFinal?.Invoke(text);
                }
            }
            catch (Exception e)
            {
                DebugConsole.Log($"[STT]: Final parse error: {e}");
            }
        }

        /// <summary>
        /// Trigger the partial transcription event.
        /// </summary>
        /// <param name="json">The output from Vosk.</param>
        private void TriggerPartial(string json)
        {
            try
            {
                using var doc = JsonDocument.Parse(json);
                if (doc.RootElement.TryGetProperty("partial", out var partProp))
                {
                    string part = partProp.GetString();
                    if (!string.IsNullOrEmpty(part))
                        OnPartial?.Invoke(part);
                }
            }
            catch (Exception e)
            {
                DebugConsole.Log($"[STT]: Partial parse error: {e}");
            }
        }

        private void NotifyQueueChanged()
        {
            var q = OnQueueChanged;
            if (q != null)
            {
                q(_queue.Count); // Already thread safe
            }
        }

        public void Dispose()
        {
            _finished = true;
            _initialized = false;
            while (_queue.TryDequeue(out var b)) b.Dispose();

            _recognizer?.Dispose();
            _model?.Dispose();
        }
    }
}
