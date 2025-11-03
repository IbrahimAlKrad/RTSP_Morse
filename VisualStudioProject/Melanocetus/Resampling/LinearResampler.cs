// Based on prior work by M. Elvers (2025) - adapted for the Stream Processing Project.

using Melanocetus.Utils;

namespace Melanocetus.Resampling
{
    /// <summary>
    /// Implements basic linear resampling of audio data.
    /// </summary>
    public class LinearResampler
    {

        /// <summary>
        /// Resamples the given audio data from sourceRate to targetRate.
        /// </summary>
        /// <param name="source">The source data.</param>
        /// <param name="sourceRate">The rate of the source data.</param>
        /// <param name="targetRate">The desired rate.</param>
        /// <param name="destination">The destination to resample to.</param>
        public static void TryResample(ReadOnlySpan<float> source, int sourceRate, int targetRate, ref RentedBuffer<float> destination)
        {
            if (sourceRate == targetRate)
            {
                source.CopyTo(destination.AsSpan());
                destination.UpdateLength(source.Length);
                return;
            }

            // exact integer length when rates share an integer factor, faster
            int targetLen = sourceRate == 0 ? 0 : sourceRate == targetRate ? source.Length : sourceRate * 2 == targetRate ? source.Length * 2 : MathUtils.CeilToInt((float)source.Length * targetRate / sourceRate);
            if (destination.Buffer == null || destination.Capacity < targetLen)
            {
                destination.Dispose();
                destination = RentedBuffer<float>.Rent(targetLen);
            }

            var dst = destination.Buffer;

            if (sourceRate * 2 == targetRate)
            {
                // 2x upsampling (e.g. 24kHz to 48kHz)
                for (int i = 0; i < source.Length; i++)
                {
                    float sample = source[i];
                    dst[i * 2] = sample;
                    dst[i * 2 + 1] = sample;
                }
                destination.UpdateLength(source.Length * 2);
                return;
            }

            for (int i = 0; i < targetLen; i++)
            {
                float pos = (float)i * sourceRate / targetRate; // exact
                int f = (int)pos; // floor
                int c = Math.Min(f + 1, source.Length - 1); // ceil
                float t = pos - f; // lerp factor
                dst[i] = MathUtils.Lerp(source[f], source[c], t);
            }
            destination.UpdateLength(targetLen);
        }


    }
}
