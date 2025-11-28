// Based on prior work by M. Elvers (2025) - adapted for the Stream Processing Project.

namespace Melanocetus.Codec
{
    /// <summary>
    /// Codec for encoding and decoding PCM audio data in 16-bit signed short format.
    /// </summary>
    public sealed class Pcm16ShortCodec : CodecBase<float, short>
    {
        /// <summary>
        /// Calculates the length of the encoded data based on the input float array. For PCM 16-bit, the length is equal to the number of samples.
        /// </summary>
        /// <param name="source">The audio data which should be encoded.</param>
        /// <returns>The length the encoded data would have.</returns>
        protected override int CalculateEncodeLength(ReadOnlySpan<float> source) => source.Length;

        /// <summary>
        /// Encodes the input float audio data into 16-bit signed short format.
        /// </summary>
        /// <param name="source">The source of the data.</param>
        /// <param name="dest">The destination to encode to.</param>
        /// <returns>The length of the encoded data.</returns>
        protected override int EncodeCore(ReadOnlySpan<float> source, Span<short> dest)
        {
            for (int i = 0; i < source.Length; i++)
            {
                float f = Math.Clamp(source[i], -1f, 1f);
                dest[i] = (short)MathF.Round(f * short.MaxValue);
            }
            return source.Length;
        }

        /// <summary>
        /// Calculates the length of the decoded data based on the input short array. For PCM 16-bit, the length is equal to the number of samples.
        /// </summary>
        /// <param name="source">The audio data which should be decoded.</param>
        /// <returns>The length the decoded data would have.</returns>
        protected override int CalculateDecodeLength(ReadOnlySpan<short> source) => source.Length;

        /// <summary>
        /// Decodes the input short audio data into float format.
        /// </summary>
        /// <param name="source">The source of the data.</param>
        /// <param name="dest">The destination to decode to.</param>
        /// <returns>The length of the decoded data.</returns>
        protected override int DecodeCore(ReadOnlySpan<short> source, Span<float> dest)
        {
            for (int i = 0; i < source.Length; i++)
            {
                dest[i] = source[i] / (float)short.MaxValue;
            }
            return source.Length;
        }

    }
}
