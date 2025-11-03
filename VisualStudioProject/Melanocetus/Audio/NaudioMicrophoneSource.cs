using Melanocetus.Utils;
using NAudio.CoreAudioApi;
using NAudio.Wave;
using System;

namespace Melanocetus.Audio
{
    internal sealed class NaudioMicrophoneSource : IAudioSource
    {
        public event Action<ReadOnlyMemory<float>>? OnAudioAvailable;

        public int SampleRate { get; }
        public string DeviceName { get; }

        private readonly WasapiCapture _capture;
        private readonly int _frameSamples;

        // Accumulator for reslicing variable WASAPI blocks into fixed frames
        private float[] _accum;
        private int _accumCount;

        private float _dcPrevIn, _dcPrevOut;
        private const float DcR = 0.995f;

        private volatile bool _started;

        public NaudioMicrophoneSource(int frameMs = 20)
            : this(new MMDeviceEnumerator().GetDefaultAudioEndpoint(DataFlow.Capture, Role.Multimedia), frameMs)
        {
        }

        public NaudioMicrophoneSource(MMDevice device, int frameMs = 20)
        {
            if (device is null) throw new ArgumentNullException(nameof(device));

            DeviceName = device.FriendlyName;

            // Use device default format for now
            _capture = new WasapiCapture(device);
            _capture.DataAvailable += OnDataAvailable;
            _capture.RecordingStopped += OnRecordingStopped;

            var wf = _capture.WaveFormat;
            SampleRate = wf.SampleRate;
            _frameSamples = Math.Max(1, SampleRate * frameMs / 1000);

            _accum = new float[_frameSamples * 10];
            _accumCount = 0;

            DebugConsole.Log($"[Audio] Using device '{DeviceName}' " +
                             $"({wf.Encoding}, {wf.SampleRate} Hz, {wf.Channels} ch, {wf.BitsPerSample} bit), " +
                             $"frame={_frameSamples} samples (~{frameMs} ms)");
        }

        public void Start()
        {
            if (_started) return;
            _started = true;
            _capture.StartRecording();
        }

        public void Stop()
        {
            if (!_started) return;
            _started = false;
            try { _capture.StopRecording(); } catch { }
        }

        private void OnDataAvailable(object? sender, WaveInEventArgs e)
        {
            var wf = _capture.WaveFormat;
            int channels = wf.Channels;
            int bytesPerSample = wf.BitsPerSample / 8;

            if (bytesPerSample <= 0 || channels <= 0) return;

            int totalSamples = e.BytesRecorded / bytesPerSample; // interleaved samples
            int frames = totalSamples / channels; // frames per channel
            if (frames <= 0) return;

            // Downmix to mono float[]
            var mono = new float[frames];

            try
            {
                if (wf.Encoding == WaveFormatEncoding.IeeeFloat && wf.BitsPerSample == 32)
                {
                    // 32-bit float interleaved
                    for (int i = 0; i < frames; i++)
                    {
                        int baseIdx = i * channels;
                        float sum = 0f;
                        for (int c = 0; c < channels; c++)
                            sum += BitConverter.ToSingle(e.Buffer, (baseIdx + c) * 4);
                        mono[i] = sum / channels;
                    }
                }
                else if (wf.Encoding == WaveFormatEncoding.Pcm && wf.BitsPerSample == 16)
                {
                    // 16-bit PCM interleaved
                    for (int i = 0; i < frames; i++)
                    {
                        int baseIdx = i * channels;
                        float sum = 0f;
                        for (int c = 0; c < channels; c++)
                        {
                            short s = BitConverter.ToInt16(e.Buffer, (baseIdx + c) * 2);
                            sum += s / 32768f;
                        }
                        mono[i] = sum / channels;
                    }
                }
                else
                {
                    // If everything fails, assume 16-bit PCM interleaved
                    for (int i = 0; i < frames; i++)
                    {
                        int baseIdx = i * channels;
                        float sum = 0f;
                        for (int c = 0; c < channels; c++)
                        {
                            short s = BitConverter.ToInt16(e.Buffer, (baseIdx + c) * bytesPerSample);
                            sum += s / 32768f;
                        }
                        mono[i] = sum / channels;
                    }
                }

                // DC-block
                EnsureAccumCapacity(_accumCount + frames);
                for (int i = 0; i < frames; i++)
                {
                    float x = mono[i];
                    float y = x - _dcPrevIn + DcR * _dcPrevOut;
                    _dcPrevIn = x;
                    _dcPrevOut = y;
                    _accum[_accumCount++] = y < -1f ? -1f : (y > 1f ? 1f : y);
                }

                // Copy fixed size frames out of accumulator
                while (_accumCount >= _frameSamples)
                {
                    var frame = new float[_frameSamples];
                    Array.Copy(_accum, 0, frame, 0, _frameSamples);

                    int remain = _accumCount - _frameSamples;
                    if (remain > 0)
                        Buffer.BlockCopy(_accum, _frameSamples * sizeof(float), _accum, 0, remain * sizeof(float));
                    _accumCount = remain;

                    try
                    {
                        OnAudioAvailable?.Invoke(frame.AsMemory());
                    }
                    catch (Exception ex)
                    {
                        DebugConsole.Log($"[Audio] OnAudioAvailable handler error: {ex}");
                    }
                }
            }
            catch (Exception ex)
            {
                DebugConsole.Log($"[Audio] Capture processing error: {ex}");
            }
        }

        private void OnRecordingStopped(object? sender, StoppedEventArgs e)
        {
            if (e.Exception != null)
                DebugConsole.Log($"[Audio] Recording stopped with error: {e.Exception}");
            else
                DebugConsole.Log("[Audio] Recording stopped.");
        }

        private void EnsureAccumCapacity(int needed)
        {
            if (needed <= _accum.Length) return;
            int newLen = Math.Max(needed, _accum.Length * 2);
            Array.Resize(ref _accum, newLen);
        }

        public void Dispose()
        {
            try { Stop(); } catch { }
            _capture.DataAvailable -= OnDataAvailable;
            _capture.RecordingStopped -= OnRecordingStopped;
            _capture.Dispose();
        }
    }
}
