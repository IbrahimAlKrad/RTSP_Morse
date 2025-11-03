// Based on prior work by M. Elvers (2025) - adapted for the Stream Processing Project.

using System.Buffers;

namespace Melanocetus.Utils
{
    /// <summary>
    /// Utility struct for renting a buffer of a certain type from an ArrayPool.
    /// Used to track the actual length of the buffer since renting from an ArrayPool returns fixed sized arrays.
    /// </summary>
    /// <typeparam name="T">The type the buffer stores.</typeparam>
    public struct RentedBuffer<T> : IDisposable
    {

        public T[] Buffer { get; private set; }

        public int Length { get; private set; }

        private bool _returned;

        public readonly int Capacity => Buffer.Length;

        private RentedBuffer(T[] buffer, int length)
        {
            Buffer = buffer;
            Length = length;
            _returned = false;
        }

        /// <summary>
        /// Creates a new rented buffer of the specified length.
        /// </summary>
        /// <param name="length">The length.</param>
        /// <returns>The buffer.</returns>
        /// <exception cref="ArgumentOutOfRangeException"></exception>
        public static RentedBuffer<T> Rent(int length)
        {
            if (length < 0) throw new ArgumentOutOfRangeException(nameof(length));

            return new RentedBuffer<T>(ArrayPool<T>.Shared.Rent(length), length);
        }

        public Span<T> AsSpan() => new Span<T>(Buffer, 0, Length);

        public ReadOnlyMemory<T> AsReadOnlyMemory() => new ReadOnlyMemory<T>(Buffer, 0, Length);

        /// <summary>
        /// Update the length, does not update the actual buffer.
        /// The capacity of the buffer does not always equal the length, so this is used for tracking how much of the buffer is actually used.
        /// </summary>
        /// <param name="newLength"></param>
        /// <exception cref="ArgumentOutOfRangeException"></exception>
        public void UpdateLength(int newLength)
        {
            if (Length == newLength) return;

            if (newLength < 0 || newLength > Capacity)
                throw new ArgumentOutOfRangeException(nameof(newLength));
            Length = newLength;
        }

        /// <summary>
        /// Ensure data fits in the buffer, if not, rent a new buffer and copy the data.
        /// </summary>
        /// <param name="data"></param>
        public void EnsureFitAndCopy(Span<T> data)
        {
            if (Capacity >= data.Length)
            {
                data.CopyTo(Buffer);
                Length = data.Length;
            }
            else
            {
                ArrayPool<T>.Shared.Return(Buffer, clearArray: false);
                Buffer = ArrayPool<T>.Shared.Rent(data.Length);
                data.CopyTo(Buffer);
                Length = data.Length;
            }
        }

        public void Dispose()
        {
            if (_returned) return;
            _returned = true;

            ArrayPool<T>.Shared.Return(Buffer, clearArray: false);

            Buffer = null!;
            Length = 0;
        }
    }
}
