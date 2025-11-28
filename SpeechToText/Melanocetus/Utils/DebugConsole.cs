namespace Melanocetus.Utils
{
    internal static class DebugConsole
    {

        private static readonly object _lock = new();

        private static readonly ConsoleColor _headerFg = ConsoleColor.Black;
        private static readonly ConsoleColor _headerBg = ConsoleColor.Gray;

        private static string _headerText = "";

        private static bool _initialized = false;

        public static void Initialize(string initialHeader = "")
        {
            lock (_lock)
            {
                if (_initialized) return;

                Console.Clear();

                _initialized = true;
                _headerText = initialHeader;

                DrawHeaderInternal();

                Console.SetCursorPosition(0, Console.WindowTop + 1);
            }
        }

        public static void Log(string message)
        {
            lock (_lock)
            {
                Console.WriteLine(message);

                DrawHeaderInternal();

                // Keep cursor below header
                if (Console.CursorTop <= Console.WindowTop)
                    Console.SetCursorPosition(0, Console.WindowTop + 1);
            }
        }

        internal static void UpdateHeader(string text)
        {
            lock (_lock)
            {
                _headerText = text;
                DrawHeaderInternal();
            }
        }

        private static void DrawHeaderInternal()
        {
            int curLeft = Console.CursorLeft;
            int curTop = Console.CursorTop;

            int windowTop = Console.WindowTop;
            int width = Console.WindowWidth;

            string text = _headerText.Length > width ? _headerText[..width] : _headerText.PadRight(width);

            var fg = Console.ForegroundColor;
            var bg = Console.BackgroundColor;

            // Header
            Console.SetCursorPosition(0, windowTop);
            Console.ForegroundColor = _headerFg;
            Console.BackgroundColor = _headerBg;
            Console.Write(text);

            // Back to normal
            Console.ForegroundColor = fg;
            Console.BackgroundColor = bg;
            Console.SetCursorPosition(curLeft, curTop);
        }

    }
}
