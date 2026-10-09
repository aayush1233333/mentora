import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";

const CameraContext = createContext(null);

export const useCamera = () => useContext(CameraContext);

export function CameraProvider({ children }) {
  const streamRef = useRef(null);
  const previewVideoRef = useRef(null);
  const captureVideoRef = useRef(null);
  const captureCanvasRef = useRef(null);
  const timerRef = useRef(null);
  const captureHandlerRef = useRef(null);
  const [active, setActive] = useState(false);
  const [error, setError] = useState(null);

  const ensureCaptureElements = useCallback(() => {
    if (!captureVideoRef.current) {
      const video = document.createElement("video");
      video.autoplay = true;
      video.muted = true;
      video.playsInline = true;
      captureVideoRef.current = video;
    }

    if (!captureCanvasRef.current) {
      captureCanvasRef.current = document.createElement("canvas");
    }
  }, []);

  const syncPreviewStream = useCallback(async () => {
    const preview = previewVideoRef.current;
    const stream = streamRef.current;

    if (!preview) return;

    if (!stream) {
      preview.srcObject = null;
      return;
    }

    if (preview.srcObject !== stream) {
      preview.srcObject = stream;
    }

    try {
      await preview.play();
    } catch (_) {
      // Ignore autoplay race; the stream remains attached and will play on visibility.
    }
  }, []);

  const attachVideo = useCallback((element) => {
    previewVideoRef.current = element;
    void syncPreviewStream();
  }, [syncPreviewStream]);

  const detachVideo = useCallback((element) => {
    if (!previewVideoRef.current) return;
    if (element && previewVideoRef.current !== element) return;

    previewVideoRef.current.srcObject = null;
    previewVideoRef.current = null;
  }, []);

  const start = useCallback(async () => {
    if (streamRef.current) {
      setActive(true);
      setError(null);
      await syncPreviewStream();
      return streamRef.current;
    }

    ensureCaptureElements();

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: "user" },
        audio: false,
      });

      streamRef.current = stream;
      captureVideoRef.current.srcObject = stream;

      try {
        await captureVideoRef.current.play();
      } catch (_) {
        // Browsers may delay play() until metadata is available; capture loop guards readyState.
      }

      await syncPreviewStream();
      setActive(true);
      setError(null);
      return stream;
    } catch (err) {
      setActive(false);
      setError(err.message || "Camera access denied");
      throw err;
    }
  }, [ensureCaptureElements, syncPreviewStream]);

  const stopCapture = useCallback(() => {
    clearInterval(timerRef.current);
    timerRef.current = null;
    captureHandlerRef.current = null;
  }, []);

  const stop = useCallback(() => {
    stopCapture();

    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;

    if (captureVideoRef.current) {
      captureVideoRef.current.srcObject = null;
    }

    if (previewVideoRef.current) {
      previewVideoRef.current.srcObject = null;
    }

    setActive(false);
  }, [stopCapture]);

  const captureFrame = useCallback((quality = 0.7) => {
    const video = captureVideoRef.current;
    const canvas = captureCanvasRef.current;

    if (!video || !canvas || video.readyState < 2) return null;

    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    return canvas.toDataURL("image/jpeg", quality).split(",")[1];
  }, []);

  const startCapture = useCallback((onFrame, fps = 2) => {
  captureHandlerRef.current = onFrame;
  clearInterval(timerRef.current);

  let processing = false;

  timerRef.current = setInterval(async () => {
    if (processing) return;

    const b64 = captureFrame();
    if (!b64 || !captureHandlerRef.current) return;

    processing = true;

    try {
      await captureHandlerRef.current(b64);
    } finally {
      processing = false;
    }
  }, Math.round(1000 / fps));
}, [captureFrame]);

  useEffect(() => () => { stop(); }, [stop]);

  return (
    <CameraContext.Provider value={{ active, error, start, stop, attachVideo, detachVideo, captureFrame, startCapture, stopCapture }}>
      {children}
    </CameraContext.Provider>
  );
}

