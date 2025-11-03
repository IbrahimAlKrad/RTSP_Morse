// Based on prior work by M. Elvers (2025) - adapted for the Stream Processing Project.

using Melanocetus.Utils;

namespace Melanocetus.Codec
{
    /// <summary>
    /// Base class for codecs that encode and decode data between two types.
    /// </summary>
    /// <typeparam name="TSource">Source type which is received.</typeparam>
    /// <typeparam name="TDestination">Destination type which is converted to.</typeparam>
    public abstract class CodecBase<TSource, TDestination> : IDisposable where TDestination : unmanaged where TSource : unmanaged
    {

        private RentedBuffer<TDestination> _encodeBuffer = RentedBuffer<TDestination>.Rent(0);
        private RentedBuffer<TSource> _decodeBuffer = RentedBuffer<TSource>.Rent(0);


        public event Action<ReadOnlyMemory<TDestination>> Encoded;
        public event Action<ReadOnlyMemory<TSource>> Decoded;

        /// <summary>
        /// Encodes the source data into the destination type. Once it is encoded, it will invoke the Encoded event.
        /// </summary>
        /// <param name="source">The source data.</param>
        public void Encode(ReadOnlySpan<TSource> source)
        {
            int encodedLength = CalculateEncodeLength(source);

            EnsureCapacity(ref _encodeBuffer, encodedLength);
            EncodeCore(source, _encodeBuffer.AsSpan());

            _encodeBuffer.UpdateLength(encodedLength);

            Encoded?.Invoke(_encodeBuffer.AsReadOnlyMemory());
        }

        /// <summary>
        /// Decodes the source data into the source type. Once it is decoded, it will invoke the Decoded event.
        /// </summary>
        /// <param name="source">The source data.</param>
        public void Decode(ReadOnlySpan<TDestination> source)
        {
            int decodedLength = CalculateDecodeLength(source);

            EnsureCapacity(ref _decodeBuffer, decodedLength);
            DecodeCore(source, _decodeBuffer.AsSpan());

            _decodeBuffer.UpdateLength(decodedLength);

            Decoded?.Invoke(_decodeBuffer.AsReadOnlyMemory());
        }

        /// <summary>
        /// Encodes the source data directly into a span of the destination type.
        /// </summary>
        /// <param name="source">The source data.</param>
        /// <returns>The encoded data.</returns>
        public Span<TDestination> EncodeToMemory(ReadOnlySpan<TSource> source)
        {
            int encodedLength = CalculateEncodeLength(source);

            EnsureCapacity(ref _encodeBuffer, encodedLength);
            int actual = EncodeCore(source, _encodeBuffer.AsSpan());

            if (actual <= 0) actual = encodedLength;

            _encodeBuffer.UpdateLength(actual);

            return _encodeBuffer.AsSpan();
        }

        /// <summary>
        /// Decodes the source data directly into a span of the source type.
        /// </summary>
        /// <param name="source">The source data.</param>
        /// <returns>The decoded data.</returns>
        public Span<TSource> DecodeToMemory(ReadOnlySpan<TDestination> source)
        {
            int decodedLength = CalculateDecodeLength(source);

            EnsureCapacity(ref _decodeBuffer, decodedLength);
            int actual = DecodeCore(source, _decodeBuffer.AsSpan());

            if (actual <= 0) actual = decodedLength;

            _decodeBuffer.UpdateLength(actual);

            return _decodeBuffer.AsSpan();
        }

        /// <summary>
        /// Ensure the rented buffer has enough capacity for the needed length.
        /// </summary>
        /// <typeparam name="T">The type of data.</typeparam>
        /// <param name="buffer">The buffer.</param>
        /// <param name="needed">The size needed.</param>
        private static void EnsureCapacity<T>(ref RentedBuffer<T> buffer, int needed) where T : unmanaged
        {
            if (buffer.Buffer is null || buffer.Capacity < needed)
            {
                buffer.Dispose();
                buffer = RentedBuffer<T>.Rent(needed);
            }
        }

        public void Dispose()
        {
            _encodeBuffer.Dispose();
            _decodeBuffer.Dispose();
        }

        protected abstract int CalculateEncodeLength(ReadOnlySpan<TSource> source);

        protected abstract int EncodeCore(ReadOnlySpan<TSource> source, Span<TDestination> destinations);

        protected abstract int CalculateDecodeLength(ReadOnlySpan<TDestination> source);

        protected abstract int DecodeCore(ReadOnlySpan<TDestination> source, Span<TSource> destination);
    }
}
