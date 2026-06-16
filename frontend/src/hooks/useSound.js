import { useEffect, useRef } from 'react';
import { Howl } from 'howler';

export function useSound(src, { volume = 0.5 } = {}) {
  const soundRef = useRef(null);

  useEffect(() => {
    soundRef.current = new Howl({
      src: [src],
      volume: volume,
      html5: true // 🔹 Важно для мобильных
    });

    return () => {
      soundRef.current?.unload();
    };
  }, [src, volume]);

  const play = () => {
    soundRef.current?.play();
  };

  return { play, sound: soundRef.current };
}