using NAudio.Wave;

namespace Melanocetus.Audio
{
    using Melanocetus.STT;
    using NAudio.Wave;

    internal sealed class WavFileAudioSource : IAudioSource
    {
        public event Action<ReadOnlyMemory<float>>? OnAudioAvailable;

        public int SampleRate { get; private set; }

        private readonly AudioFileReader _reader;
        private readonly int _frameSamples;
        
        private volatile bool _running;

        private Thread? _thread;

        public WavFileAudioSource(string path, int frameMs)
        {
            _reader = new AudioFileReader(path);
            SampleRate = _reader.WaveFormat.SampleRate;
            _frameSamples = SampleRate * frameMs / 1000;
        }

        public void Start()
        {
            _running = true;
            _thread = new Thread(ReadLoop) { IsBackground = true };
            _thread.Start();
        }

        private void ReadLoop()
        {
            int ch = _reader.WaveFormat.Channels;
            var buf = new float[_frameSamples * ch];
            var mono = new float[_frameSamples];

            while (_running)
            {
                int read = _reader.Read(buf, 0, buf.Length);
                if (read == 0) break;

                int frames = read / ch;

                if (ch == 1)
                {
                    // Already mono
                    Array.Copy(buf, 0, mono, 0, frames);
                }
                else
                {
                    // average all channels to mono
                    for (int i = 0; i < frames; i++)
                    {
                        float sum = 0f;
                        int baseIdx = i * ch;
                        for (int c = 0; c < ch; c++) sum += buf[baseIdx + c];
                        mono[i] = sum / ch;
                    }
                }

                OnAudioAvailable?.Invoke(mono.AsMemory(0, frames));

                // Simulate "streaming"
                Thread.Sleep(Math.Max(1, 1000 * frames / SampleRate));
            }
        }


        public void Stop() => _running = false;

        public void Dispose() { _running = false; _reader.Dispose(); }
    }


}
