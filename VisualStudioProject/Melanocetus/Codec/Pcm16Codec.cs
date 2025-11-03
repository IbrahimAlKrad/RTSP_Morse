// Based on prior work by M. Elvers (2025) - adapted for the Stream Processing Project.

namespace Melanocetus.Codec
{
    /// <summary>
    /// Class for encoding and decoding audio data in PCM 16-bit format.
    /// </summary>
    public class Pcm16Codec : CodecBase<float, byte>
    {
        /// <summary>
        /// Calculazes the length of the encoded data based on the source.
        /// </summary>
        /// <param name="source">The source which will be encoded.</param>
        /// <returns>The size the encoded data would be.</returns>
        protected override int CalculateEncodeLength(ReadOnlySpan<float> source) => source.Length * sizeof(short);

        /// <summary>
        /// Encodes the source data into PCM 16-bit format.
        /// </summary>
        /// <param name="source">The source of the data.</param>
        /// <param name="destination">The destination to encode to.</param>
        /// <returns>The length of the encoded data.</returns>
        protected override int EncodeCore(ReadOnlySpan<float> source, Span<byte> destination)
        {
            for (int i = 0; i < source.Length; i++)
            {
                float f = Math.Clamp(source[i], -1f, 1f);
                short s = (short)MathF.Round(f * short.MaxValue);
                int pos = 2 * i;
                destination[pos] = (byte)(s & 0xFF);
                destination[pos + 1] = (byte)(((int)s >> 8) & 0xFF);
            }
            return source.Length * sizeof(short);
        }

        /// <summary>
        /// Calculates the length of the decoded data based on the source.
        /// </summary>
        /// <param name="source">The source which will be encoded.</param>
        /// <returns>The size the encoded data would be.</returns>
        protected override int CalculateDecodeLength(ReadOnlySpan<byte> source) => source.Length / sizeof(short);

        /// <summary>
        /// Decodes the source data from PCM 16-bit format into floats.
        /// </summary>
        /// <param name="source">The source which will be deocoded.</param>
        /// <param name="destination">The destination to be decoded to.</param>
        /// <returns>The length of the decoded data.</returns>
        protected override int DecodeCore(ReadOnlySpan<byte> source, Span<float> destination)
        {
            for (int i = 0; i < destination.Length; i++)
            {
                int pos = 2 * i;
                short s = (short)(source[pos] | (source[pos + 1] << 8));
                destination[i] = s / (float)short.MaxValue;
            }
            return source.Length / sizeof(short);
        }
    }
}
