#!/usr/bin/env python3
"""
Audio Sender - Captures audio from the microphone/system and streams it over LAN via UDP.

Usage:
    python sender.py <receiver_ip> [--port PORT] [--device DEVICE_INDEX]

Example:
    python sender.py 192.168.1.100
    python sender.py 192.168.1.100 --port 5000 --device 2
"""

import argparse
import socket
import sys
import signal

import pyaudio

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100


def list_devices(p: pyaudio.PyAudio) -> None:
    """Print all available audio input devices."""
    print("\nAvailable audio input devices:")
    print("-" * 50)
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            print(f"  [{i}] {info['name']} (inputs: {info['maxInputChannels']})")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Stream audio to a receiver over LAN")
    parser.add_argument("host", help="IP address of the receiver")
    parser.add_argument("--port", type=int, default=4000, help="UDP port (default: 4000)")
    parser.add_argument(
        "--device", type=int, default=None, help="Audio input device index (use --list to see devices)"
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

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    stream_kwargs = {
        "format": FORMAT,
        "channels": args.channels,
        "rate": args.rate,
        "input": True,
        "frames_per_buffer": CHUNK,
    }
    if args.device is not None:
        stream_kwargs["input_device_index"] = args.device

    try:
        stream = p.open(**stream_kwargs)
    except OSError as e:
        print(f"Error opening audio stream: {e}")
        print("Try using --list to see available devices and --device to pick one.")
        p.terminate()
        sys.exit(1)

    print(f"Connecting to receiver at {args.host}:{args.port}...")

    # Handshake: send CONNECT and wait for ACCEPT
    sock.settimeout(2.0)
    connected = False
    for attempt in range(1, 6):
        try:
            sock.sendto(b"CONNECT", (args.host, args.port))
            reply, _ = sock.recvfrom(64)
            if reply == b"ACCEPT":
                connected = True
                break
        except socket.timeout:
            print(f"  Attempt {attempt}/5 - no response, retrying...")

    if not connected:
        print("Failed to connect: receiver did not respond.")
        print("Make sure receiver.py is running and the IP/port are correct.")
        stream.stop_stream()
        stream.close()
        p.terminate()
        sock.close()
        sys.exit(1)

    print(f"\n--- Connected successfully to {args.host}:{args.port} ---")
    print(f"  Channels: {args.channels} | Rate: {args.rate} Hz | Chunk: {CHUNK}")
    print("  Streaming audio now. Press Ctrl+C to stop.\n")

    sock.settimeout(None)
    running = True

    def handle_signal(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        while running:
            data = stream.read(CHUNK, exception_on_overflow=False)
            sock.sendto(data, (args.host, args.port))
    except OSError as e:
        print(f"\nNetwork error: {e}")
    finally:
        print("\nStopping sender...")
        stream.stop_stream()
        stream.close()
        p.terminate()
        sock.close()
        print("Done.")


if __name__ == "__main__":
    main()
