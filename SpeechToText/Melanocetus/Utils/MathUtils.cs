namespace Melanocetus.Utils
{
    internal static class MathUtils
    {

        public static float Lerp(float a, float b, float t)
        {
            return a + (b - a) * t;
        }

        public static int CeilToInt(float f)
        {
            return (int)Math.Ceiling(f);
        }

    }
}
