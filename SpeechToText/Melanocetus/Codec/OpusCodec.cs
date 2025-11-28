// Based on prior work by M. Elvers (2025) - adapted for the Stream Processing Project.

using OpusSharp.Core;
using System.Runtime.InteropServices;

namespace Melanocetus.Codec
{
    /// <summary>
    /// Class for encoding and decoding audio using the Opus codec.
    /// </summary>
    public class OpusCodec : CodecBase<float, byte>
    {

        private const int MaxOpusPacketSize = 1275; // https://datatracker.ietf.org/doc/html/rfc6716 -> 3.2.1 Frame Length Coding

        private OpusEncoder _encoder;
        private OpusDecoder _decoder;

        private readonly int _channels;
        private readonly int _samplesPerFrame;

        public OpusCodec(int channels = 1)
        {
            _channels = channels;

            _encoder = new OpusEncoder(Config.Config.Audio.CodecSampleRate, channels, OpusPredefinedValues.OPUS_APPLICATION_VOIP);
            _decoder = new OpusDecoder(Config.Config.Audio.CodecSampleRate, channels);

            _samplesPerFrame = Config.Config.Audio.FrameSize;
        }

        /// <summary>
        /// Rough estimate of the size of the encoded data for one frame.
        /// </summary>
        /// <returns></returns>
        public int EstimateSize()
        {
            return _samplesPerFrame * _channels;
        }

        /// <summary>
        /// Calculates the maximum size needed to decode the given source data.
        /// </summary>
        /// <param name="source">The data which should be decoded.</param>
        /// <returns>The size the decoded data would be.</returns>
        protected override int CalculateDecodeLength(ReadOnlySpan<byte> source) // Does not calculate the exact length, but a maximum size for one packet
        {
            return _samplesPerFrame * _channels;
        }

        /// <summary>
        /// Calculates the maximum size needed to encode the given source data.
        /// </summary>
        /// <param name="source">The data which should be encoded.</param>
        /// <returns>The size the decoded data would be.</returns>
        protected override int CalculateEncodeLength(ReadOnlySpan<float> source) // Does not calculate the exact length, but a maximum size since Opus only provides the size after encoding
        {
            return MaxOpusPacketSize;
        }

        /// <summary>
        /// Decodes the audio data into the specified destination.
        /// </summary>
        /// <param name="source">The source of the data.</param>
        /// <param name="destination">The destination to decode to.</param>
        /// <returns>The actual length of the decoded data.</returns>
        /// <exception cref="ArgumentException">Fired if the destination buffer is too small.</exception>
        protected override int DecodeCore(ReadOnlySpan<byte> source, Span<float> destination)
        {
            if (destination.Length < _samplesPerFrame * _channels)
                throw new ArgumentException($"Destination too small, need {_samplesPerFrame * _channels} floats");

            Span<byte> span = MemoryMarshal.CreateSpan(ref MemoryMarshal.GetReference(source), source.Length);

            return _decoder.Decode(span, source.Length, destination, _samplesPerFrame, false);
        }

        /// <summary>
        /// Encodes the audio data from the source into the specified destination.
        /// </summary>
        /// <param name="source">The source audio data.</param>
        /// <param name="destinations">The destination to encode to.</param>
        /// <returns>The actual length of the encoded data.</returns>
        /// <exception cref="ArgumentException">Fired if an unexpected amount of floats is passed.</exception>
        protected override int EncodeCore(ReadOnlySpan<float> source, Span<byte> destinations)
        {
            if (source.Length != _samplesPerFrame * _channels)
                throw new ArgumentException($"Expected exactly {_samplesPerFrame * _channels} floats, got {source.Length}");

            Span<float> span = MemoryMarshal.CreateSpan(ref MemoryMarshal.GetReference(source), source.Length);

            return _encoder.Encode(span, Config.Config.Audio.FrameSize, destinations, MaxOpusPacketSize);
        }
    }
}
