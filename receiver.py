#!/usr/bin/env python3
"""
Audio Receiver - Receives audio streamed over LAN via UDP and plays it back.

Usage:
    python receiver.py [--port PORT] [--device DEVICE_INDEX]

Example:
    python receiver.py
    python receiver.py --port 5000 --device 3
"""

import argparse
import socket
import sys
import signal

import pyaudio

# Audio settings (must match sender)
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

# Max UDP packet size for audio data
BUFFER_SIZE = 4096


def list_devices(p: pyaudio.PyAudio) -> None:
    """Print all available audio output devices."""
    print("\nAvailable audio output devices:")
    print("-" * 50)
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxOutputChannels"] > 0:
            print(f"  [{i}] {info['name']} (outputs: {info['maxOutputChannels']})")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Receive and play audio streamed over LAN")
    parser.add_argument("--port", type=int, default=4000, help="UDP port to listen on (default: 4000)")
    parser.add_argument(
        "--device", type=int, default=None, help="Audio output device index (use --list to see devices)"
    )
    parser.add_argument("--channels", type=int, default=CHANNELS, help="Number of audio channels (default: 1)")
    parser.add_argument("--rate", type=int, default=RATE, help="Sample rate in Hz (default: 44100)")
    parser.add_argument("--list", action="store_true", help="List available audio devices and exit")
    args = parser.parse_args()

    p = pyaudio.PyAudio()

    if args.list:
        list_devices(p)
        p.terminate()
        sys.exit(0)

    stream_kwargs = {
        "format": FORMAT,
        "channels": args.channels,
        "rate": args.rate,
        "output": True,
        "frames_per_buffer": CHUNK,
    }
    if args.device is not None:
        stream_kwargs["output_device_index"] = args.device

    try:
        stream = p.open(**stream_kwargs)
    except OSError as e:
        print(f"Error opening audio stream: {e}")
        print("Try using --list to see available devices and --device to pick one.")
        p.terminate()
        sys.exit(1)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", args.port))
    sock.settimeout(1.0)

    print(f"Listening for audio on port {args.port}")
    print(f"  Channels: {args.channels} | Rate: {args.rate} Hz | Chunk: {CHUNK}")
    print("Press Ctrl+C to stop.\n")

    running = True

    def handle_signal(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        while running:
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                stream.write(data)
            except socket.timeout:
                continue
    except OSError as e:
        print(f"\nError: {e}")
    finally:
        print("\nStopping receiver...")
        stream.stop_stream()
        stream.close()
        p.terminate()
        sock.close()
        print("Done.")


if __name__ == "__main__":
    main()
