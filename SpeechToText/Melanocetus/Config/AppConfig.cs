using System.Text.Json;

namespace Melanocetus.Config
{
    internal sealed class AppConfig
    {
        public AudioConfig Audio { get; init; } = new();

        public RuntimeConfig Runtime { get; init; } = new();

        public static AppConfig Load(string fileName)
        {
            string exeDir = AppContext.BaseDirectory;
            string fullPath = Path.Combine(exeDir, fileName);

            if (!File.Exists(fullPath))
                throw new FileNotFoundException($"Config not found: {fullPath}");

            var json = File.ReadAllText(fullPath);
            var cfg = JsonSerializer.Deserialize<AppConfig>(json, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            }) ?? new AppConfig();

            cfg.ValidateAndNormalize();
            return cfg;
        }

        public AppConfig WithRuntimeRecordingSampleRate(int recordingSampleRate)
        {
            return new AppConfig
            {
                Audio = Audio,
                Runtime = new RuntimeConfig { RecordingSampleRate = recordingSampleRate }
            };
        }

        private void ValidateAndNormalize()
        {
            Audio.ValidateAndNormalize();
            if (Runtime.RecordingSampleRate == null || Runtime.RecordingSampleRate <= 0)
                Runtime.RecordingSampleRate = Audio.TargetRecordingSampleRate;
        }
    }
}
