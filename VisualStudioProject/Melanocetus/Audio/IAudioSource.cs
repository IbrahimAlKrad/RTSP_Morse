using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Melanocetus.Audio
{
    internal interface IAudioSource : IDisposable
    {
        event Action<ReadOnlyMemory<float>> OnAudioAvailable;

        void Start();
        
        void Stop();
    }
}
