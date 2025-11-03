// Based on prior work by M. Elvers (2025) - adapted for the Stream Processing Project.

namespace Melanocetus.Audio
{
    /// <summary>
    /// Interface for audio sinks that receive audio data.
    /// </summary>
    internal interface IAudioSink : IDisposable
    {
        /// <summary>
        /// Interface for audio sinks that receive audio data.
        /// </summary>
        public void OnAudioAvailable(ReadOnlyMemory<float> data);
    }
}
