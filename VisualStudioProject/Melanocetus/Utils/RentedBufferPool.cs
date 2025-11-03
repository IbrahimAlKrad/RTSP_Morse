// Based on prior work by M. Elvers (2025) - adapted for the Stream Processing Project.

namespace Melanocetus.Utils
{
    /// <summary>
    /// Utility class for renting pools buffers of a specific type.
    /// </summary>
    /// <typeparam name="T">Type stored in the buffer.</typeparam>
    public class RentedBufferPool<T> : IDisposable
    {

        private readonly List<RentedBuffer<T>> _buffers;

        private int _currentBufferIndex = 0;

        private bool _initialized = false;

        private readonly object _lock = new();

        /// <summary>
        /// Initializes a new instance.
        /// </summary>
        /// <param name="buffers"></param>
        public RentedBufferPool(int buffers)
        {
            _buffers = new List<RentedBuffer<T>>(buffers);
            for (int i = 0; i < buffers; i++)
                _buffers.Add(RentedBuffer<T>.Rent(0));
        }

        /// <summary>
        /// Get a new buffer from the pool with the specified length.
        /// </summary>
        /// <param name="length">The requested length.</param>
        /// <returns>A buffer with the desired length.</returns>
        public RentedBuffer<T> GetBuffer(int length)
        {
            lock (_lock)
            {
                if (!_initialized)
                {
                    for (int i = 0; i < _buffers.Count; i++)
                        UpdateBufferSize(length, i);
                    _initialized = true;
                }

                var buffer = UpdateBufferSize(length, _currentBufferIndex);
                _currentBufferIndex = (_currentBufferIndex + 1) % _buffers.Count;

                return buffer;
            }
        }

        /// <summary>
        /// Update the size of the buffer at the specified index.
        /// </summary>
        /// <param name="length"></param>
        /// <param name="index"></param>
        /// <returns></returns>
        private RentedBuffer<T> UpdateBufferSize(int length, int index)
        {
            var rb = _buffers[index];                  // struct-Kopie lokal
            if (rb.Length == length) return rb;

            if (rb.Capacity < length)
            {
                rb.Dispose();
                rb = RentedBuffer<T>.Rent(length);
                _buffers[index] = rb;                  // zurückschreiben!
                return rb;
            }
            else
            {
                rb.UpdateLength(length);               // Länge der lokalen Kopie ändern
                _buffers[index] = rb;                  // zurückschreiben!
                return rb;
            }
        }


        public void Dispose()
        {
            lock (_lock)
            {
                foreach (var buffer in _buffers)
                {
                    if (buffer.Buffer != null)
                        buffer.Dispose();
                }
            }
        }
    }
}
