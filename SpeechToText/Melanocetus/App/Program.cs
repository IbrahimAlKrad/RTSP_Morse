using Melanocetus.Audio;
using Melanocetus.Config;
using Melanocetus.Utils;
using System.Timers;
using Timer = System.Timers.Timer;

namespace Melanocetus.App
{
    internal class Program
    {
        private static readonly Timer _timer = new Timer();
        private static readonly ManualResetEventSlim _quit = new(false);

        private static AppMetrics _metrics = new AppMetrics();

        static void Main(string[] args)
        {
            Console.CancelKeyPress += (_, e) => { e.Cancel = true; _quit.Set(); };

            DebugConsole.Initialize(" Melanocetus - In: 0.00 kbit/s - STT Queue: 0 packets ");

            Config.AppConfig.Load("melanocetus.json");
            var cfg = Config.Config.Audio;

            DebugConsole.Log($"[Config]: FrameSize: {cfg.FrameSize} - FrameDuration: {cfg.FrameDurationMs} " +
                             $"- CodecSampleRate: {cfg.CodecSampleRate} - TargetRate: {cfg.TargetRecordingSampleRate} " +
                             $"- Device: {cfg.Device}");

            using var app = new MelanocetApp(_metrics); // "using" so Dispose is called automatically

            //WavFileAudioSource source = new WavFileAudioSource("C:/Users/malte/Downloads/some_test_audio.wav", cfg.FrameSize);
            var source = new NaudioMicrophoneSource(cfg.FrameDurationMs);

            app.Start(source); // maybe start async?

            _timer.Interval = 1000; // 1s
            _timer.Elapsed += OnTimerElapsed;
            _timer.AutoReset = true;
            _timer.Start();

            _quit.Wait(); // Blocks and waits, but can be interrupted with Ctrl+C

            _timer.Stop();
            _timer.Dispose();

            app.Stop();
            DebugConsole.Log("[Shutdown] Bye. :(");
        }

        private static void OnTimerElapsed(object? sender, ElapsedEventArgs e)
        {
            // kbit/s -> (float = 32 Bit = 4 Bytes per sample, mono)
            var samplesPerSec = Interlocked.Exchange(ref _metrics.SamplesThisSecond, 0);
            double kbitPerSec = samplesPerSec * 4 /*bytes*/ * 8 /*bits*/ / 1000.0d;

            var sttQueued = _metrics.SttPendingPackets; // STT sets this
            DebugConsole.UpdateHeader($" Melanocetus - In: {kbitPerSec:0.00} kbit/s - STT Queue: {sttQueued} packets | {e.SignalTime:HH:mm:ss}");
        }
    }
}
