namespace Melanocetus.Config
{
    internal static class Config
    {

        private static AppConfig? _instance;

        public static AppConfig Current
        {
            get
            {
                _instance ??= AppConfig.Load("melanocetus.json");
                return _instance;
            }
        }

        public static AudioConfig Audio => Current.Audio;

        public static RuntimeConfig Runtime => Current.Runtime;
    }
}
